import numpy as np
import pandas as pd
import pytest

from src.analysis_engine import AnalysisEngine


def _stats(values, start=2001, counts=None):
    years = list(range(start, start + len(values)))
    return pd.DataFrame(
        {
            "year": years,
            "best": values,
            "top_10_avg": values,
            "median": values,
            "count": counts if counts is not None else [100] * len(values),
        }
    )


def test_get_yearly_stats():
    df = pd.DataFrame(
        {"year": [2001] * 12 + [2002] * 12, "seconds": list(range(12)) + list(range(100, 112))}
    )
    out = AnalysisEngine(df).get_yearly_stats()
    assert list(out["year"]) == [2001, 2002]
    assert out.loc[0, "best"] == 0
    assert out.loc[0, "top_10_avg"] == pytest.approx(np.mean(range(10)))
    assert out.loc[0, "count"] == 12


def test_detect_anomalies_finds_a_structural_break():
    rng = np.random.RandomState(0)
    values = np.array([10.0 - 0.01 * i for i in range(26)]) + rng.randn(26) * 0.005
    values[15:] -= 0.5  # step change in the 16th season
    flagged = AnalysisEngine(pd.DataFrame()).detect_anomalies(_stats(values))
    assert flagged == [2016]


def test_detect_anomalies_is_index_safe_after_filtering():
    """The old positional mask misaligned once the frame had been filtered."""
    rng = np.random.RandomState(0)
    values = np.array([10.0 - 0.01 * i for i in range(26)]) + rng.randn(26) * 0.005
    values[15:] -= 0.5
    stats_df = _stats(values)
    filtered = stats_df[stats_df["year"] >= 2005]
    assert AnalysisEngine(pd.DataFrame()).detect_anomalies(filtered) == [2016]


def test_detect_anomalies_ignores_a_smooth_series():
    values = [10.0 - 0.01 * i for i in range(26)]
    assert AnalysisEngine(pd.DataFrame()).detect_anomalies(_stats(values)) == []


def test_detect_anomalies_handles_short_series():
    assert AnalysisEngine(pd.DataFrame()).detect_anomalies(_stats([10.0, 9.9])) == []


def test_baseline_and_recent_use_a_multi_year_window():
    values = [10.0, 20.0, 30.0] + [0.0] * 5 + [1.0, 2.0, 3.0]
    stats_df = _stats(values)
    assert AnalysisEngine.baseline_level(stats_df) == pytest.approx(20.0)
    assert AnalysisEngine.recent_level(stats_df) == pytest.approx(2.0)


def test_improvement_rate_recovers_a_known_slope():
    values = [10.0 - 0.02 * i for i in range(26)]
    rate = AnalysisEngine(pd.DataFrame()).calculate_improvement_rate(_stats(values))
    assert rate == pytest.approx(-0.02)


def test_improvement_rate_on_too_little_data():
    assert AnalysisEngine(pd.DataFrame()).calculate_improvement_rate(_stats([10.0])) == 0.0


def test_depth_adjusted_rate_separates_year_from_field_size():
    n = 26
    counts = [50 + i for i in range(n)]
    # Value depends only on the year, not on field size.
    values = [10.0 - 0.02 * i for i in range(n)]
    out = AnalysisEngine(pd.DataFrame()).depth_adjusted_rate(_stats(values, counts=counts))
    assert set(out) == {"year", "count"}
    assert out["year"] + out["count"] == pytest.approx(-0.02, abs=1e-6)
