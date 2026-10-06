import json
import numpy as np
import pytest
from scipy import stats
from statistics_core import EXAMPLE, parse_values, run_test, tail_intervals
from charts import distribution_chart


def area(intervals, df):
    return sum(stats.t.cdf(hi, df) - stats.t.cdf(lo, df) for lo, hi in intervals)


def test_lecture_example_against_saved_graphpad_output():
    r = run_test(EXAMPLE)
    assert r.mean == pytest.approx(3.350)
    assert r.t == pytest.approx(3.2796, abs=0.00005)
    assert r.p == pytest.approx(0.0095, abs=0.00005)
    assert r.critical == pytest.approx((-2.262157, 2.262157))
    assert r.reject and r.df == 9
    assert r.ci_low == pytest.approx(3.109, abs=0.0005)
    assert r.ci_high == pytest.approx(3.591, abs=0.0005)


@pytest.mark.parametrize('alternative', ['two-sided', 'greater', 'less'])
@pytest.mark.parametrize('benchmark', [2.8, 3.35, 4.0])
def test_visual_tail_areas_match_inference(alternative, benchmark):
    r = run_test(EXAMPLE, benchmark, 0.03, alternative)
    assert area(tail_intervals(r, 'p-value area'), r.df) == pytest.approx(r.p)
    assert area(tail_intervals(r, 'Rejection regions'), r.df) == pytest.approx(r.alpha)
    fig, _, _ = distribution_chart(r, 'p-value area')
    assert len(fig.data) >= 2


def test_opposite_one_sided_directions_are_complements():
    above = run_test(EXAMPLE, 3, alternative='greater')
    below = run_test(EXAMPLE, 3, alternative='less')
    assert above.p + below.p == pytest.approx(1)
    assert below.p > .99 and not below.reject
    assert above.p < .005 and above.reject
    assert above.ci_high == np.inf and below.ci_low == -np.inf
    assert json.loads(json.dumps(above.record(), allow_nan=False))['ci_high'] is None


def test_small_sample_analytic_symmetric_case():
    r = run_test([-1, 1], 0)
    assert r.t == 0 and r.p == 1 and not r.reject
    assert r.sd == pytest.approx(np.sqrt(2))
    r = run_test([-1, 1], 0, alternative='greater')
    assert r.p == .5
    assert r.critical[0] == pytest.approx(1/np.tan(.05*np.pi))


def test_alpha_changes_critical_not_p():
    a, b = run_test(EXAMPLE, alpha=.001), run_test(EXAMPLE, alpha=.05)
    assert a.p == b.p
    assert not a.reject and b.reject
    assert a.critical[1] > b.critical[1]


def test_extreme_plot_does_not_fake_on_screen_marker():
    r = run_test([1, 1.000001], 0, .001)
    _, outside, extent = distribution_chart(r, 'p-value area')
    assert extent == 50 and len(outside) == 3


@pytest.mark.parametrize('values', [[3, 3, 3], [1], [1, float('nan')], [1, float('inf')], []])
def test_invalid_samples_fail_clearly(values):
    with pytest.raises(ValueError):
        run_test(values)


def test_paste_parser():
    assert np.array_equal(parse_values('1, 2; 3\n4\t5e-1'), [1, 2, 3, 4, .5])
    for raw in ['words,2', 'nan 1', 'inf 1', '']:
        with pytest.raises(ValueError):
            parse_values(raw)
