import io
import json
import math
import numpy as np
import pandas as pd
import streamlit as st
from statistics_core import EXAMPLE, MAX_OBSERVATIONS, parse_values, run_test
from charts import distribution_chart, data_chart, qq_chart

st.set_page_config(page_title='One-sample t Lab', page_icon='📊', layout='wide')
st.title('One-sample t Lab')
st.write('Compare an average with a benchmark. Explore the evidence, then consider its business impact.')


def p_format(p):
    if p == 0:
        return '< 1e-300 (numerical limit)'
    return f'{p:.3g}' if p < 0.0001 else f'{p:.6f}'.rstrip('0').rstrip('.')


def bound_format(x):
    return '−∞' if x == -math.inf else '+∞' if x == math.inf else f'{x:.6g}'

with st.sidebar:
    st.header('Test settings')
    benchmark = st.number_input('Benchmark mean (μ₀)', value=3.0, format='%.6f')
    alternatives = {'Different from benchmark (two-sided)': 'two-sided',
                    'Above benchmark (right-tailed)': 'greater',
                    'Below benchmark (left-tailed)': 'less'}
    choice = st.selectbox('Alternative hypothesis', list(alternatives))
    alternative = alternatives[choice]
    alpha = st.slider('Significance level (α)', min_value=0.001, max_value=0.200,
                      value=0.050, step=0.001, format='%.3f')
    st.caption('Choose the direction and α before looking at the result. Changing α moves the rejection region, but does not change the p-value.')
    label = st.text_input('Measurement label', value='Delivery time')
    units = st.text_input('Units', value='days')
    practical = st.number_input('Meaningful absolute difference (optional)', value=0.0,
                                min_value=0.0, format='%.6f',
                                help='Use 0 to skip. This compares your threshold with the sample estimate, not a separate significance test.')

left, right = st.columns([1.1, 1.9], gap='large')
with left:
    st.subheader('Your sample')
    source = st.radio('Data source', ['Paste values', 'Upload CSV'], horizontal=True)
    try:
        if source == 'Paste values':
            raw = st.text_area('Observations', '\n'.join(str(v) for v in EXAMPLE), height=205,
                               help='Separate numbers with spaces, newlines, commas or semicolons. Use a decimal point, not a decimal comma.')
            st.caption('The starting data are a synthetic sample of ten delivery times.')
            values = parse_values(raw)
        else:
            uploaded = st.file_uploader('CSV file (maximum 2 MB)', type=['csv'])
            header = st.checkbox('CSV has a header row', value=True)
            separator = st.selectbox('CSV separator', [',', ';', '\\t'])
            if uploaded is None:
                st.info('Upload a CSV, then select its measurement column.')
                st.stop()
            if uploaded.size > 2*1024*1024:
                raise ValueError('The file exceeds 2 MB. Use a smaller CSV.')
            frame = pd.read_csv(io.BytesIO(uploaded.getvalue()), header=0 if header else None,
                                sep='\t' if separator == '\\t' else separator, dtype=str,
                                nrows=MAX_OBSERVATIONS+1, keep_default_na=False)
            if len(frame) > MAX_OBSERVATIONS:
                raise ValueError(f'Use at most {MAX_OBSERVATIONS:,} rows.')
            if frame.empty:
                raise ValueError('The CSV has no data rows.')
            column = st.selectbox('Measurement column', list(frame.columns))
            selected = frame[column].str.strip()
            blank = selected.eq('')
            drop_missing = st.checkbox('Exclude blank cells', value=False)
            if blank.any() and not drop_missing:
                raise ValueError(f'{int(blank.sum())} blank cells. Choose whether to exclude them.')
            if drop_missing and blank.any():
                st.warning(f'Excluded {int(blank.sum())} blank cells from the selected column.')
            numeric = pd.to_numeric(selected[~blank], errors='coerce')
            if numeric.isna().any():
                raise ValueError('The selected column contains nonnumeric entries. Fix them before testing.')
            values = numeric.to_numpy(dtype=float)
        result = run_test(values, benchmark, alpha, alternative)
    except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
        st.error(str(exc))
        st.stop()
    st.caption(f'{result.n:,} observations included. Values recalculate automatically.')
    if result.n < 30:
        st.info('Small sample: check for strong skew or outliers and consider whether an approximately normal population is plausible.')
    with st.expander('Sample summary'):
        st.dataframe(pd.DataFrame({'Measure': ['n', 'Mean', 'Sample SD', 'Standard error', 'Difference from benchmark'],
                                   'Value': [result.n, result.mean, result.sd, result.se, result.difference]}), hide_index=True)
        st.dataframe(pd.DataFrame({'Observation': np.arange(1, len(values)+1), 'Value': values}), hide_index=True, height=200)

with right:
    st.subheader('Test result')
    a, b, c = st.columns(3)
    a.metric('t statistic', f'{result.t:.4f}')
    b.metric('p-value', p_format(result.p))
    c.metric('Degrees of freedom', result.df)
    sign = {'two-sided': '≠', 'greater': '>', 'less': '<'}[alternative]
    st.write(f'**H₀: μ = {benchmark:g}**  **H₁: μ {sign} {benchmark:g}**')
    compare = '≤' if result.reject else '>'
    decision = 'Reject H₀' if result.reject else 'Do not reject H₀'
    message = f'{decision}: p {compare} α ({p_format(result.p)} {compare} {alpha:g}).'
    (st.success if result.reject else st.info)(message)
    direction = {'two-sided': 'differs from', 'greater': 'is above', 'less': 'is below'}[alternative]
    if result.reject:
        st.write(f'The sample provides statistical evidence that the population mean {direction} the benchmark, assuming the sampling and model assumptions hold.')
    else:
        st.write(f'This sample does not provide sufficient evidence that the population mean {direction} the benchmark. This does not establish equality.')
    confidence = 100*(1-alpha)
    ci_kind = 'two-sided interval' if alternative == 'two-sided' else 'one-sided confidence bound'
    st.write(f'**{confidence:g}% {ci_kind} for the population mean:** [{bound_format(result.ci_low)}, {bound_format(result.ci_high)}] {units}')
    st.write('**Critical value(s):** ' + ', '.join(f'{v:.4f}' for v in result.critical))
    if alternative == 'two-sided':
        rule = f't ≤ {result.critical[0]:.4f} or t ≥ {result.critical[1]:.4f}'
    elif alternative == 'greater':
        rule = f't ≥ {result.critical[0]:.4f}'
    else:
        rule = f't ≤ {result.critical[0]:.4f}'
    st.caption(f'Rejection rule: {rule}. The decision uses full precision, not rounded display values.')

st.divider()
visual, sample, explain = st.tabs(['Distribution and tails', 'Sample and assumptions', 'Meaning and calculation'])
with visual:
    st.subheader('Where does the observed statistic fall?')
    mode = st.radio('Shaded area', ['Rejection regions', 'p-value area'], horizontal=True)
    fig, outside, extent = distribution_chart(result, mode)
    st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False})
    if mode == 'Rejection regions':
        st.write(f'The orange rejection region has total probability α = **{alpha:g}** under H₀. Dashed orange lines show the critical values.')
    else:
        st.write(f'The teal area represents **p = {p_format(result.p)}** under H₀. It starts at the observed t in a one-sided test, or at ±|t| in a two-sided test.')
    st.caption('Solid teal line: observed t. Vertical height is probability density. Probability is area under the curve. Hover, zoom, pan or download the chart using its toolbar.')
    st.caption(f'The curve displays −{extent:.2f} to +{extent:.2f}. Tail shading continues mathematically to infinity. Probabilities use the full distribution, not just the visible shading.')
    if outside:
        st.warning('; '.join(outside) + ' lies outside the displayed range. Exact values appear above; no off-screen marker is drawn.')
with sample:
    st.plotly_chart(data_chart(values, benchmark), use_container_width=True, config={'displaylogo': False})
    st.write('The t-test needs an independent, representative sample of numerical measurements. For a small sample, the population should be approximately normal, without strong skew or influential outliers.')
    st.write('Independence and representativeness depend on how you collected the data. The charts cannot verify them.')
    st.plotly_chart(qq_chart(values), use_container_width=True, config={'displaylogo': False})
    st.caption('Normal Q–Q plot: points near the reference line support approximate normality. Large departures merit investigation. This is a diagnostic, not proof that the assumptions hold.')
with explain:
    st.subheader('The p-value in plain language')
    pct = '< 1e-298%' if result.p == 0 else f'{result.p*100:.4g}%'
    st.write(f'If the true population mean were **{benchmark:g} {units}**, and the assumptions held, the probability of a test statistic at least as extreme as the observed result in the direction(s) specified by H₁ would be **{pct}**.')
    st.write('The p-value is not the probability that H₀ is true, the percentage of problematic observations, or an explanation of what caused the difference.')
    st.subheader('Business interpretation')
    st.write(f'The estimated mean {label.lower()} is **{result.mean:.6g} {units}**, a difference of **{result.difference:+.6g} {units}** from the benchmark.')
    if practical > 0:
        meets = abs(result.difference) >= practical
        st.write(f'The absolute sample difference {"meets or exceeds" if meets else "is below"} your meaningful-difference threshold of {practical:g} {units}. This is a comparison of point estimates, not proof of practical equivalence or importance.')
    st.write('Assess the size of this difference against customer expectations, costs and service commitments. A statistically significant result alone does not identify a cause or determine the best action. Generalise only to the population represented by the sample.')
    st.subheader('Calculation')
    st.latex(r't=\frac{\bar{x}-\mu_0}{s/\sqrt{n}},\qquad df=n-1')
    st.write(f't = ({result.mean:.6g} − {benchmark:g}) / {result.se:.6g} = **{result.t:.6g}**')
    st.caption('The standard deviation uses n−1 in its denominator. The confidence level follows 1−α and the chosen test direction. A one-sided interval has an unbounded endpoint.')
    st.markdown('[SciPy one-sample test documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_1samp.html)')

report = result.record()
report.update(measurement_label=label, units=units, decision=decision,
              confidence_level=1-alpha, ci_kind=ci_kind,
              missing_handling='Blank cells excluded only if explicitly selected for CSV input',
              interpretation='p is conditional on H0 and model assumptions; statistical significance does not imply practical importance.')
d1, d2 = st.columns(2)
d1.download_button('Download test report (JSON)', json.dumps(report, indent=2, allow_nan=False),
                   file_name='one_sample_t_test_report.json', mime='application/json')
d2.download_button('Download included observations (CSV)', pd.DataFrame({'value': values}).to_csv(index=False),
                   file_name='tested_observations.csv', mime='text/csv')
st.caption('The app does not write uploaded data or results to a database or disk. Data are processed on the hosting server for your current session.')
