# One-sample t Lab

An interactive Streamlit app for teaching and performing one-sample t-tests. Suitable for introductory business statistics. No statistical coding is required by the user.

## Features

- Paste observations or upload a CSV and choose its numeric measurement column.
- Choose a benchmark mean, a two-sided/right-tailed/left-tailed alternative, and alpha.
- Calculate sample mean, sample SD, standard error, t, degrees of freedom, p-value, critical values and a matching confidence interval or one-sided bound.
- Explore the null t-distribution: switch between rejection-region shading and p-value shading. Hover, zoom, pan, and export figures with the Plotly toolbar.
- View sample observations and a normal Q–Q diagnostic.
- Read a conditional p-value explanation and a practical business interpretation.
- Download a JSON test report or CSV of the included observations.
- Includes the synthetic three-day delivery benchmark example.

## Deploy on Render

1. Extract this ZIP. Put the **contents** of `one-sample-t-lab/` in the root of a new GitHub repository. Include `.streamlit/config.toml` and `render.yaml`.
2. Push the repository to GitHub.
3. In Render choose **New → Blueprint**, connect that repository and select `render.yaml`.
4. Review the service and plan, then deploy. The included Blueprint requests the Free plan. Select a different plan if needed for your account or use.
5. Open the generated `onrender.com` URL when the deployment completes.

The project is prepared for deployment but has not been deployed to your account.

### Manual Web Service setup

If you prefer Render's **New → Web Service**:

- Runtime: Python
- Root Directory: leave empty when the project files are at the repository root
- Build Command: `pip install -r requirements.txt`
- Start Command: `streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT --server.headless=true`
- Environment variable: `PYTHON_VERSION=3.12.10`
- Health Check Path: `/_stcore/health`

If you retain the enclosing folder in your repository, set the service Root Directory to `one-sample-t-lab` instead. Render requires the app to bind to `0.0.0.0` and recommends using its `PORT` variable. The Blueprint and command above do both. No API keys, database or persistent disk are needed. Free services may sleep while idle and take time to wake up.

## Run locally

Use Python 3.12:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows alternative
# .venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

## Data input

Paste numbers separated by spaces, newlines, commas or semicolons. Use a decimal point: `3.5`, not `3,5`. Do not include a header in pasted data.

CSV files can have a header or no header. Choose comma, semicolon or tab as the separator and select one measurement column. A checked `Exclude blank cells` option excludes blanks and reports the count. Other nonnumeric entries, including NaN markers, trigger an error. The app never silently converts invalid entries or selects only convenient observations.

Limit: 2 MB per CSV and 100,000 observations. Use at least two observations with nonzero sample variance. Upload `sample_delivery.csv` with its header enabled to reproduce the example.

## Statistical interpretation

H0 is that the population mean equals the benchmark. The t statistic is `(sample mean − benchmark) / standard error`, with `df = n − 1`. The sample SD uses `ddof=1`.

For a two-sided test, p includes both tails beyond `±abs(t)` and the rejection region allocates `alpha/2` to each tail. A right-tailed test shades above the observed t and a left-tailed test shades below it. A one-sided p-value can exceed 0.5 when the sample points opposite to the chosen alternative.

The app rejects H0 when `p <= alpha`, using full numerical precision. Choose alpha and direction before seeing results. Changing alpha changes the critical values and confidence interval, but not the statistic or p-value for the same data, benchmark and direction.

The confidence level is `1 − alpha`. For two-sided tests the mean interval is bounded on both sides. For right-tailed tests the upper endpoint is infinite, and for left-tailed tests the lower endpoint is infinite. JSON reports use `null` for these unbounded endpoints and label the interval kind.

The p-value is conditional on H0 and model assumptions. It is not the probability H0 is true. Not rejecting H0 does not prove equality. Statistical significance does not establish commercial importance or identify a cause. The optional meaningful-difference threshold compares only the point estimate, not a formal test of equivalence.

Use an independent, representative sample. For small samples, the population should be approximately normal without strong skew or influential outliers. Diagnostic plots cannot establish independence or representative sampling.

The chart's finite display window is capped at ±50 to preserve readability for extreme statistics or very heavy tails. Off-screen statistics and critical values are explicitly reported. All probabilities use the full distribution, including tails beyond the visible chart.

## Privacy

The app processes data on the server in the current session. Application code does not save observations or reports to files or a database. It does not provide authentication or a retention guarantee for the hosting platform. Use an appropriate hosting arrangement for confidential data.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover the GraphPad lecture example, analytically known symmetric cases, p-value and rejection-region areas, wrong-direction one-sided tests, alpha changes, numerical/input guards and Streamlit interaction flows.

Expected delivery result: mean 3.350, t approximately 3.2796, df 9, two-sided p approximately 0.0095, critical values approximately ±2.2622 at alpha 0.05.

## Files

- `app.py`: Streamlit interface
- `statistics_core.py`: validation and statistical inference
- `charts.py`: interactive distribution and diagnostic charts
- `render.yaml`: Render deployment Blueprint
- `requirements.txt`: tested runtime dependency versions
- `.streamlit/config.toml`: theme and server configuration
- `sample_delivery.csv`: synthetic example
- `tests/`: automated tests

## Primary documentation

- [SciPy one-sample t-test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_1samp.html)
- [Render web services and port binding](https://render.com/docs/web-services)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
- [Render Python version](https://render.com/docs/python-version)
- [Streamlit app testing](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)
