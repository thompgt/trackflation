import pandas as pd
import pytest

from src.data_cleaner import DataCleaner

cleaner = DataCleaner()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # SS.ms
        ("9.58", 9.58),
        ("43.03", 43.03),
        # MM:SS.ms
        ("1:40.91", 100.91),
        ("3:26.00", 206.00),
        ("12:35.36", 755.36),
        ("26:11.00", 1571.00),
        # HH:MM:SS -- this branch was entirely unexercised before these tests
        ("1:59:30", 7170.0),
        ("2:00:35", 7235.0),
        ("2:01:09.00", 7269.0),
        # Qualifier suffixes/prefixes World Athletics attaches to marks
        ("9.58A", 9.58),
        ("10.1h", 10.1),
        ("+2:03:38", 7418.0),
    ],
)
def test_time_to_seconds(text, expected):
    assert cleaner.time_to_seconds(text) == pytest.approx(expected)


@pytest.mark.parametrize("bad", [None, "", "   ", "abc", "1:2:3:4", 9.58, [], ":"])
def test_time_to_seconds_rejects_garbage(bad):
    assert cleaner.time_to_seconds(bad) is None


@pytest.mark.parametrize(
    "seconds", [9.58, 19.19, 43.03, 100.91, 206.0, 755.36, 1571.0, 7170.0, 472.11, 3599.99]
)
def test_seconds_to_str_round_trips(seconds):
    """seconds_to_str and time_to_seconds must be inverses to 2dp."""
    from src.forecaster import TrackForecaster

    text = TrackForecaster.seconds_to_str(seconds)
    assert cleaner.time_to_seconds(text) == pytest.approx(seconds, abs=0.005)


@pytest.mark.parametrize(
    ("wind", "expected"),
    [("+1.3", 1.3), ("-0.2", -0.2), ("0.0", 0.0), ("2.0", 2.0), ("", None), (None, None), ("x", None)],
)
def test_parse_wind(wind, expected):
    assert cleaner.parse_wind(wind) == expected


def _row(**kw):
    base = {
        "event": "100m",
        "athlete": "A",
        "mark": "9.90",
        "wind": "+1.0",
        "date": "01 JAN 2023",
        "venue": "Somewhere",
    }
    base.update(kw)
    return base


def test_wind_rule_applies_to_sprints_only():
    df = pd.DataFrame(
        [
            _row(event="100m", athlete="legal", wind="+2.0"),
            _row(event="100m", athlete="aided", wind="+2.5"),
            _row(event="100m", athlete="nowind", wind=""),
            _row(event="Marathon", athlete="mar", mark="2:01:09", wind=""),
            _row(event="5000m", athlete="five", mark="12:35.36", wind=""),
        ]
    )
    out = cleaner.clean_scraped_data(df)
    kept = set(out["athlete"])
    assert kept == {"legal", "mar", "five"}, kept


def test_dedupe_keeps_distinct_performances():
    df = pd.DataFrame(
        [
            _row(athlete="A"),
            _row(athlete="A"),  # exact duplicate -> dropped
            _row(athlete="B"),  # same time, same day, different athlete -> kept
            _row(athlete="A", venue="Elsewhere"),  # same athlete, other meet -> kept
        ]
    )
    out = cleaner.clean_scraped_data(df)
    assert len(out) == 3


def test_unparseable_marks_are_dropped():
    df = pd.DataFrame([_row(mark="9.90"), _row(athlete="B", mark="DNF")])
    out = cleaner.clean_scraped_data(df)
    assert len(out) == 1
    assert out.iloc[0]["seconds"] == pytest.approx(9.90)


def test_empty_frame_passes_through():
    assert cleaner.clean_scraped_data(pd.DataFrame()).empty
