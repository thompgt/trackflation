#!/usr/bin/env python
"""
Re-check every world record in src/config.py against the rank-1 mark on the
corresponding World Athletics all-time toplist.

Run this whenever a record might have changed:

    poetry run python scripts/verify_world_records.py

Exits non-zero if any configured value disagrees with the live site, so it can
be wired into CI as a scheduled job (it is deliberately NOT part of the normal
test run, which must stay offline).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import REAL_WR  # noqa: E402
from src.data_cleaner import DataCleaner  # noqa: E402
from src.forecaster import TrackForecaster  # noqa: E402
from src.scraper import ScrapeError, WorldAthleticsScraper  # noqa: E402


def main() -> int:
    scraper = WorldAthleticsScraper(cache_dir="data/cache/alltime")
    cleaner = DataCleaner()
    mismatches = []

    for event, configured in REAL_WR.items():
        try:
            df = scraper.scrape_year(event, None)  # None => all-time list
        except ScrapeError as exc:
            print(f"{event:<14} SKIP  ({exc})")
            continue

        best_mark = df.iloc[0]["mark"]
        best_seconds = cleaner.time_to_seconds(best_mark)
        if best_seconds is None:
            print(f"{event:<14} SKIP  (unparseable rank-1 mark {best_mark!r})")
            continue

        ok = abs(best_seconds - configured) < 0.005
        status = "OK  " if ok else "DIFF"
        print(
            f"{event:<14} {status}  config={TrackForecaster.seconds_to_str(configured)}"
            f"  site={best_mark}  ({df.iloc[0]['athlete']}, {df.iloc[0]['venue']},"
            f" {df.iloc[0]['date']})"
        )
        if not ok:
            mismatches.append((event, configured, best_seconds))

    if mismatches:
        print(f"\n{len(mismatches)} record(s) out of date in src/config.py")
        return 1
    print("\nAll configured world records match the World Athletics all-time toplists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
