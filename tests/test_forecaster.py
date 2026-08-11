import numpy as np
import pandas as pd
import pytest

from src.forecaster import TrackForecaster


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (9.58, "9.58"),
        (59.99, "59.99"),
        (60.0, "1:00.00"),
        (100.91, "1:40.91"),
        (755.36, "12:35.36"),
        (3599.99, "59:59.99"),
        (3600.0, "1:00:00.00"),
        (7170.0, "1:59:30.00"),
        (7235.0, "2:00:35.00"),
    ],
)
def test_seconds_to_str(seconds, expected):
    assert TrackForecaster.seconds_to_str(seconds) == expected


def test_seconds_to_str_handles_missing():
    assert TrackForecaster.seconds_to_str(float("nan")) == "n/a"
    assert TrackForecaster.seconds_to_str(None) == "n/a"


@pytest.mark.parametrize(
    ("last", "target", "expected"), [(2026, 2046, 20), (2026, 2027, 1), (2001, 2026, 25)]
)
def test_periods_to_year(last, target, expected):
    assert TrackForecaster.periods_to_year(last, target) == expected


@pytest.mark.parametrize("target", [2026, 2020])
def test_periods_to_year_rejects_the_past(target):
    with pytest.raises(ValueError):
        TrackForecaster.periods_to_year(2026, target)


def _series(n=26, start=2001):
    years = np.arange(start, start + n)
    values = 10.3 - (years - start) * 0.008 + np.random.RandomState(0).rand(n) * 0.05
    return pd.DataFrame({"year": years, "best": values})


@pytest.mark.parametrize("cap", [None, 9.45])
def test_forecast_lands_exactly_on_the_target_year(cap):
    """freq='YE' against Jan-1 stamps used to land the horizon a year short."""
    forecast = TrackForecaster(_series(), cap=cap).forecast(target_year=2046)
    assert pd.to_datetime(forecast["ds"]).dt.year.max() == 2046
    assert pd.to_datetime(forecast["ds"]).dt.year.min() == 2001


def test_forecast_interval_brackets_the_point_estimate():
    forecast = TrackForecaster(_series(), cap=9.45).forecast(target_year=2046)
    assert (forecast["yhat_lower"] <= forecast["yhat"]).all()
    assert (forecast["yhat"] <= forecast["yhat_upper"]).all()


def test_logistic_fit_cannot_cross_the_assumed_floor():
    """The headline 'approaching the ceiling' reading is this constraint, by construction."""
    floor = 9.45
    forecast = TrackForecaster(_series(), cap=floor).forecast(target_year=2100)
    assert (forecast["yhat"] >= floor).all()


def test_floor_sensitivity_reports_the_spread():
    out = TrackForecaster(_series(), cap=9.45).floor_sensitivity(2046)
    assert "no_floor" in out and "floor" in out
    # A floor-free fit is unconstrained, so it must not agree exactly with the
    # floored one -- if it did, the floor would be doing no work.
    assert out["no_floor"] != pytest.approx(out["floor"], abs=1e-9)


def test_forecast_requires_a_horizon():
    with pytest.raises(ValueError):
        TrackForecaster(_series()).forecast()
