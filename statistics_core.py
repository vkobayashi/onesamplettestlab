"""Validated one-sample inference. No session data is stored on disk."""
from dataclasses import dataclass, asdict
import math
import re
import numpy as np
from scipy import stats

MAX_OBSERVATIONS = 100_000
EXAMPLE = [2.8, 3.1, 3.4, 3.2, 3.7, 3.5, 3.0, 3.6, 3.3, 3.9]


def parse_values(text):
    tokens = [v for v in re.split(r"[\s,;]+", text.strip()) if v]
    if not tokens:
        raise ValueError("Enter at least two numeric observations.")
    if len(tokens) > MAX_OBSERVATIONS:
        raise ValueError(f"Use at most {MAX_OBSERVATIONS:,} observations.")
    try:
        values = np.asarray([float(v) for v in tokens], dtype=float)
    except ValueError:
        raise ValueError("Every pasted entry must be a number. Remove headers or upload a CSV instead.") from None
    if not np.all(np.isfinite(values)):
        raise ValueError("Values must be finite numbers. Remove NaN and infinity.")
    return values


@dataclass(frozen=True)
class Result:
    n: int
    df: int
    mean: float
    sd: float
    se: float
    benchmark: float
    difference: float
    t: float
    p: float
    alpha: float
    alternative: str
    critical: tuple
    ci_low: float
    ci_high: float
    reject: bool

    def record(self):
        # JSON uses null for the unbounded endpoint of a one-sided interval.
        out = asdict(self)
        for key in ['ci_low', 'ci_high']:
            if not math.isfinite(out[key]):
                out[key] = None
        return out


def run_test(values, benchmark=3.0, alpha=0.05, alternative='two-sided'):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not 2 <= values.size <= MAX_OBSERVATIONS:
        raise ValueError(f"Use a single numeric sample of 2 to {MAX_OBSERVATIONS:,} observations.")
    if not np.all(np.isfinite(values)) or not math.isfinite(benchmark):
        raise ValueError("Observations and benchmark must be finite numbers.")
    if not 0 < alpha < 1:
        raise ValueError("Alpha must lie strictly between 0 and 1.")
    if alternative not in ['two-sided', 'less', 'greater']:
        raise ValueError("Choose a valid alternative hypothesis.")
    with np.errstate(over='ignore', invalid='ignore'):
        mean = float(np.mean(values))
        sd = float(np.std(values, ddof=1))
    if not math.isfinite(mean) or not math.isfinite(sd):
        raise ValueError("These values exceed numerical limits. Rescale your measurements.")
    if sd == 0:
        raise ValueError("All observations are identical. The sample standard deviation is zero, so the t-test is undefined.")
    se = sd / math.sqrt(values.size)
    if se == 0 or abs(mean - benchmark) / se > 1e150:
        raise ValueError("Variation is too small relative to the measurements. Rescale or check measurement precision.")
    test = stats.ttest_1samp(values, benchmark, alternative=alternative)
    ci = test.confidence_interval(confidence_level=1-alpha)
    t, p = float(test.statistic), float(test.pvalue)
    if not math.isfinite(t) or not math.isfinite(p):
        raise ValueError("The calculation exceeded numerical limits. Rescale your measurements.")
    df = int(values.size - 1)
    if alternative == 'two-sided':
        critical = (-float(stats.t.isf(alpha/2, df)), float(stats.t.isf(alpha/2, df)))
    elif alternative == 'greater':
        critical = (float(stats.t.isf(alpha, df)),)
    else:
        critical = (float(stats.t.ppf(alpha, df)),)
    return Result(int(values.size), df, mean, sd, se, float(benchmark),
                  mean-benchmark, t, p, alpha, alternative, critical,
                  float(ci.low), float(ci.high), p <= alpha)


def tail_intervals(result, mode):
    """Intervals on the null t-distribution. Endpoints extend to infinity."""
    if mode == 'Rejection regions':
        if result.alternative == 'two-sided':
            return [(-np.inf, result.critical[0]), (result.critical[1], np.inf)]
        if result.alternative == 'greater':
            return [(result.critical[0], np.inf)]
        return [(-np.inf, result.critical[0])]
    if mode == 'p-value area':
        if result.alternative == 'two-sided':
            return [(-np.inf, -abs(result.t)), (abs(result.t), np.inf)]
        if result.alternative == 'greater':
            return [(result.t, np.inf)]
        return [(-np.inf, result.t)]
    raise ValueError('Unknown chart mode')
