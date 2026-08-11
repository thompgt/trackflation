"""
Scraper for the World Athletics season toplists.

The toplist pages are server-rendered, so a plain HTTP GET plus an HTML parse is
sufficient -- no browser or JSON API is required. Columns are resolved *by header
name* rather than by fixed position, and a missing or renamed column raises
rather than silently yielding empty/misaligned data.

Coverage note: World Athletics toplists only go back to 2001. Requests for
earlier seasons return a page with no results table; `scrape_year` raises
`NoResultsError` for those so the caller can distinguish "no data for this
season" from "the parser broke".
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.config import DISCIPLINE_GROUPS, EVENT_METADATA

log = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://worldathletics.org/records/toplists"

# Header labels we require on every toplist table, mapped to our output columns.
REQUIRED_COLUMNS: Dict[str, str] = {
    "Rank": "rank",
    "Mark": "mark",
    "WIND": "wind",
    "Competitor": "athlete",
    "Venue": "venue",
    "Date": "date",
}


class ScrapeError(RuntimeError):
    """Raised when a toplist page cannot be fetched or parsed as expected."""


class NoResultsError(ScrapeError):
    """Raised when a page loads fine but holds no toplist (e.g. a pre-2001 season)."""


class WorldAthleticsScraper:
    """Fetches and parses World Athletics season toplists, with an on-disk cache."""

    def __init__(
        self,
        cache_dir: str | os.PathLike[str] = "data/cache",
        base_url: Optional[str] = None,
        delay: Optional[float] = None,
        max_retries: int = 3,
    ):
        self.base_url = base_url or os.environ.get(
            "TRACKFLATION_WA_BASE_URL", DEFAULT_BASE_URL
        )
        self.delay = (
            delay
            if delay is not None
            else float(os.environ.get("TRACKFLATION_SCRAPE_DELAY", "1.0"))
        )
        self.max_retries = max_retries
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "trackflation/0.1 (research project; "
                    "https://github.com/thompgt/trackflation)"
                )
            }
        )

    # ------------------------------------------------------------------ URLs

    def get_top_list_url(
        self, event_name: str, year: Optional[int], gender: str = "men"
    ) -> str:
        """
        Build a toplist URL.

        `year=None` requests the all-time list. Note that an *unrecognised* year
        segment (e.g. the string "alltime") does not error -- World Athletics
        quietly serves the current season instead -- so the all-time list must be
        requested by omitting the segment and passing the query parameters below.
        """
        if event_name not in EVENT_METADATA:
            raise KeyError(f"Unknown event {event_name!r}")
        code = EVENT_METADATA[event_name]["code"]
        group = DISCIPLINE_GROUPS[event_name]
        stem = f"{self.base_url}/{group}/{code}/outdoor/{gender}/senior"
        if year is None:
            return f"{stem}?regionType=world&timing=electronic"
        return f"{stem}/{int(year)}"

    # ------------------------------------------------------------------ HTTP

    def _fetch(self, url: str, cache_key: str) -> str:
        """GET `url` with retries, caching the body under `cache_key`."""
        cache_path = self.cache_dir / f"{cache_key}.html"
        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8", errors="replace")

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                body = response.text
                cache_path.write_text(body, encoding="utf-8")
                time.sleep(self.delay)  # polite scraping
                return body
            except requests.RequestException as exc:  # noqa: PERF203
                last_error = exc
                if attempt < self.max_retries:
                    backoff = 2 ** (attempt - 1)
                    log.warning(
                        "GET %s failed (attempt %d/%d): %s -- retrying in %ss",
                        url,
                        attempt,
                        self.max_retries,
                        exc,
                        backoff,
                    )
                    time.sleep(backoff)
        raise ScrapeError(f"Failed to fetch {url} after {self.max_retries} attempts: {last_error}")

    # --------------------------------------------------------------- Parsing

    @staticmethod
    def _parse_table(html: str, url: str) -> pd.DataFrame:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", {"class": "records-table"})
        if table is None:
            raise NoResultsError(f"No results table on {url}")

        rows = table.find_all("tr")
        if len(rows) < 2:
            raise NoResultsError(f"Results table on {url} has no data rows")

        headers = [cell.get_text(strip=True) for cell in rows[0].find_all(["th", "td"])]
        # Schema assertion: fail loudly if World Athletics renames/reorders columns.
        missing = [label for label in REQUIRED_COLUMNS if label not in headers]
        if missing:
            raise ScrapeError(
                f"Toplist schema changed on {url}: missing column(s) {missing}. "
                f"Saw headers: {headers}"
            )
        index_of = {label: headers.index(label) for label in REQUIRED_COLUMNS}

        records: List[Dict[str, Optional[str]]] = []
        for row in rows[1:]:
            cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
            if len(cells) < len(headers):
                continue  # spacer / malformed row
            records.append(
                {
                    out: cells[index_of[label]]
                    for label, out in REQUIRED_COLUMNS.items()
                }
            )

        if not records:
            raise NoResultsError(f"Results table on {url} produced no parseable rows")
        return pd.DataFrame(records)

    # ------------------------------------------------------------- Public API

    def scrape_year(
        self, event_name: str, year: Optional[int], gender: str = "men"
    ) -> pd.DataFrame:
        """
        Return the toplist for one (event, year), or the all-time list for
        `year=None`. Raises on fetch failure, schema change or no results.
        """
        url = self.get_top_list_url(event_name, year, gender)
        code = EVENT_METADATA[event_name]["code"]
        html = self._fetch(url, cache_key=f"{code}_{gender}_{year or 'alltime'}")
        df = self._parse_table(html, url)
        df["year"] = year
        df["event"] = event_name
        df["gender"] = gender
        return df

    def scrape_historical(
        self,
        event_name: str,
        start_year: int,
        end_year: int,
        gender: str = "men",
    ) -> pd.DataFrame:
        """Scrape a span of seasons, skipping (and logging) seasons with no toplist."""
        frames: List[pd.DataFrame] = []
        for year in range(start_year, end_year + 1):
            try:
                frames.append(self.scrape_year(event_name, year, gender))
            except NoResultsError as exc:
                log.info("Skipping %s %s: %s", event_name, year, exc)
        if not frames:
            raise ScrapeError(
                f"No seasons scraped for {event_name} {start_year}-{end_year}. "
                "World Athletics toplists only cover 2001 onwards."
            )
        return pd.concat(frames, ignore_index=True)

    def scrape_events(
        self,
        event_names: Iterable[str],
        start_year: int,
        end_year: int,
        gender: str = "men",
    ) -> pd.DataFrame:
        """Scrape several events into one long frame."""
        frames = [
            self.scrape_historical(name, start_year, end_year, gender)
            for name in event_names
        ]
        return pd.concat(frames, ignore_index=True)
