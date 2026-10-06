import numpy as np
import plotly.graph_objects as go
from scipy import stats
from statistics_core import tail_intervals

TEAL = '#087F8C'
ORANGE = '#C95528'


def distribution_chart(result, mode):
    # Finite plotting window protects readability for df=1 or extreme observations.
    extent = min(50., max(6., abs(result.t)*1.15, max(abs(c) for c in result.critical)*1.25))
    x = np.linspace(-extent, extent, 2201)
    fig = go.Figure()
    color = 'rgba(201,85,40,0.30)' if mode == 'Rejection regions' else 'rgba(8,127,140,0.32)'
    for i, (lo, hi) in enumerate(tail_intervals(result, mode)):
        lo, hi = max(lo, -extent), min(hi, extent)
        if lo >= hi:
            continue
        section = np.unique(np.concatenate(([lo], x[(x > lo) & (x < hi)], [hi])))
        fig.add_trace(go.Scatter(x=section, y=stats.t.pdf(section, result.df),
                                mode='lines', line=dict(width=0), fill='tozeroy',
                                fillcolor=color, name=mode, legendgroup='area', showlegend=i == 0,
                                hovertemplate='t = %{x:.3f}<br>Density = %{y:.4f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=x, y=stats.t.pdf(x, result.df), mode='lines',
                            name=f'Null t-distribution (df = {result.df})', line=dict(color='#243F50', width=3),
                            hovertemplate='t = %{x:.3f}<br>Density = %{y:.4f}<extra></extra>'))
    outside = []
    for i, critical in enumerate(result.critical):
        if abs(critical) <= extent:
            fig.add_vline(x=critical, line_color=ORANGE, line_dash='dash', line_width=2)
            fig.add_annotation(x=critical, y=1.03 + 0.065*(i % 2), yref='paper',
                               text=f'Critical {critical:.3f}', showarrow=False, font=dict(color=ORANGE))
        else:
            outside.append(f'Critical value {critical:.3f}')
    if abs(result.t) <= extent:
        fig.add_vline(x=result.t, line_color=TEAL, line_width=3)
        fig.add_annotation(x=result.t, y=1.21, yref='paper', text=f'Observed t = {result.t:.3f}',
                           showarrow=False, font=dict(color=TEAL))
    else:
        outside.append(f'Observed t {result.t:.3f}')
    fig.update_layout(height=470, template='plotly_white',
                      margin=dict(l=30, r=25, t=100, b=65),
                      xaxis_title='t statistic under H₀', yaxis_title='Probability density',
                      xaxis=dict(range=[-extent, extent], zeroline=True),
                      legend=dict(orientation='h', y=-0.2), hovermode='closest',
                      font=dict(family='Arial', size=14))
    return fig, outside, extent


def data_chart(values, benchmark):
    fig = go.Figure(go.Scatter(x=list(range(1, len(values)+1)), y=values,
                               mode='markers', name='Observation', marker=dict(color=TEAL, size=8),
                               hovertemplate='Observation %{x}<br>Value %{y:.5g}<extra></extra>'))
    fig.add_hline(y=benchmark, line_dash='dash', line_color=ORANGE,
                  annotation_text=f'Benchmark = {benchmark:g}')
    fig.add_hline(y=float(np.mean(values)), line_color=TEAL,
                  annotation_text=f'Sample mean = {np.mean(values):.5g}', annotation_position='bottom right')
    fig.update_layout(template='plotly_white', height=370, xaxis_title='Observation number (input order)',
                      yaxis_title='Measured value', margin=dict(t=35,b=45), showlegend=False)
    return fig


def qq_chart(values):
    theoretical, ordered = stats.probplot(values, dist='norm', fit=False)
    fig = go.Figure(go.Scatter(x=theoretical, y=ordered, mode='markers', marker=dict(color=TEAL)))
    (_, _), (slope, intercept, _) = stats.probplot(values, dist='norm')
    fig.add_trace(go.Scatter(x=[theoretical[0], theoretical[-1]],
                            y=[intercept+slope*theoretical[0], intercept+slope*theoretical[-1]],
                            mode='lines', line=dict(color=ORANGE), name='Reference line'))
    fig.update_layout(template='plotly_white', height=360, showlegend=False,
                      xaxis_title='Theoretical normal quantiles', yaxis_title='Ordered sample values')
    return fig
