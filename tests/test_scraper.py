"""Offline tests for the scraper: URL construction and HTML parsing only.

Nothing here touches the network. Live checks live in
scripts/verify_world_records.py, which is run on a schedule, not in CI.
"""

import pandas as pd
import pytest

from src.scraper import NoResultsError, ScrapeError, WorldAthleticsScraper

HEADER = (
    "<tr><th>Rank</th><th>Mark</th><th>WIND</th><th>Competitor</th><th>DOB</th>"
    "<th></th><th>Pos</th><th></th><th>Venue</th><th>Date</th><th>Results Score</th></tr>"
)
ROW = (
    "<tr><td>1</td><td>9.83</td><td>+1.3</td><td>Zharnel HUGHES</td><td>13 JUL 1995</td>"
    "<td>GBR</td><td>1</td><td></td><td>Icahn Stadium, New York, NY (USA)</td>"
    "<td>24 JUN 2023</td><td>1266</td></tr>"
)


def _page(body: str) -> str:
    return f"<html><body><table class='records-table'>{body}</table></body></html>"


@pytest.fixture()
def scraper(tmp_path):
    return WorldAthleticsScraper(cache_dir=tmp_path / "cache", delay=0)


def test_url_uses_the_right_discipline_group(scraper):
    assert scraper.get_top_list_url("100m", 2023).endswith(
        "/sprints/100-metres/outdoor/men/senior/2023"
    )
    # The original scraper hardcoded "sprints" for every event, which 404-equivalents
    # for distance and road events.
    assert "/middlelong/5000-metres/" in scraper.get_top_list_url("5000m", 2023)
    assert "/road-running/marathon/" in scraper.get_top_list_url("Marathon", 2023)


def test_all_time_url_omits_the_year_segment(scraper):
    """An unrecognised year segment silently serves the current season instead."""
    url = scraper.get_top_list_url("100m", None)
    assert url.endswith("/senior?regionType=world&timing=electronic")
    assert "alltime" not in url


def test_unknown_event_raises(scraper):
    with pytest.raises(KeyError):
        scraper.get_top_list_url("caber toss", 2023)


def test_parse_table_extracts_columns_by_name(scraper):
    df = scraper._parse_table(_page(HEADER + ROW), "http://x")
    assert list(df.columns) == ["rank", "mark", "wind", "athlete", "venue", "date"]
    row = df.iloc[0]
    assert row["mark"] == "9.83"
    assert row["wind"] == "+1.3"
    assert row["athlete"] == "Zharnel HUGHES"
    # The original code read cols[8] as the date, which is actually the venue.
    assert row["date"] == "24 JUN 2023"
    assert row["venue"].startswith("Icahn Stadium")


def test_missing_table_raises_no_results(scraper):
    with pytest.raises(NoResultsError):
        scraper._parse_table("<html><body>nothing here</body></html>", "http://x")


def test_header_only_table_raises_no_results(scraper):
    with pytest.raises(NoResultsError):
        scraper._parse_table(_page(HEADER), "http://x")


def test_renamed_column_raises_rather_than_returning_empty(scraper):
    """A schema change must fail loudly, not yield a silently empty frame."""
    broken = HEADER.replace("<th>Mark</th>", "<th>Result</th>")
    with pytest.raises(ScrapeError, match="schema changed"):
        scraper._parse_table(_page(broken + ROW), "http://x")


def test_fetch_uses_the_cache(scraper, tmp_path):
    (scraper.cache_dir / "key.html").write_text(_page(HEADER + ROW), encoding="utf-8")
    # No network: a cache hit must not construct a request.
    scraper.session = None  # type: ignore[assignment]
    body = scraper._fetch("http://never-called", "key")
    assert "records-table" in body


def test_scrape_year_annotates_rows(scraper):
    (scraper.cache_dir / "100-metres_men_2023.html").write_text(
        _page(HEADER + ROW), encoding="utf-8"
    )
    scraper.session = None  # type: ignore[assignment]
    df = scraper.scrape_year("100m", 2023)
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["year"] == 2023
    assert df.iloc[0]["event"] == "100m"
    assert df.iloc[0]["gender"] == "men"
