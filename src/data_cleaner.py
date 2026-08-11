"""Cleaning for scraped World Athletics toplist rows."""

from __future__ import annotations

import logging
import re
from typing import Optional

import pandas as pd

from src.config import EVENT_METADATA

log = logging.getLogger(__name__)

# The +2.0 m/s limit is a rule of the sprints and horizontal jumps. It is not
# recorded, and not meaningful, for 5000m and above or for road races.
MAX_LEGAL_WIND = 2.0

# Columns that together identify one performance. Two athletes can run the same
# time on the same day, and one athlete can run twice in a season, so the key
# has to include the venue.
RESULT_KEY = ["event", "athlete", "mark", "date", "venue"]


class DataCleaner:
    @staticmethod
    def time_to_seconds(time_str: object) -> Optional[float]:
        """Convert 'H:MM:SS.ms', 'MM:SS.ms' or 'SS.ms' to float seconds."""
        if time_str is None or not isinstance(time_str, str):
            return None

        # Strip qualifiers ('h' hand-timed, 'A' altitude, '+' en-route, etc.)
        clean_time = re.sub(r"[^0-9:.]", "", time_str).strip()
        if not clean_time:
            return None

        try:
            if ":" in clean_time:
                parts = clean_time.split(":")
                if len(parts) == 2:
                    return int(parts[0]) * 60 + float(parts[1])
                if len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                return None
            return float(clean_time)
        except ValueError:
            return None

    @staticmethod
    def parse_wind(wind_str: object) -> Optional[float]:
        """Parse a wind reading to m/s. Returns None when absent or unparseable."""
        if wind_str is None or not isinstance(wind_str, str):
            return None
        cleaned = re.sub(r"[^0-9.+-]", "", wind_str).strip()
        if not cleaned or cleaned in {"+", "-", "."}:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    def clean_scraped_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        new_df = df.copy()

        new_df["seconds"] = new_df["mark"].apply(self.time_to_seconds)
        dropped_marks = int(new_df["seconds"].isna().sum())
        new_df = new_df.dropna(subset=["seconds"])
        if dropped_marks:
            log.info("Dropped %d row(s) with an unparseable mark", dropped_marks)

        new_df = self._filter_wind(new_df)

        before = len(new_df)
        key = [c for c in RESULT_KEY if c in new_df.columns]
        new_df = new_df.drop_duplicates(subset=key)
        if before != len(new_df):
            log.info("Dropped %d duplicate result row(s) on %s", before - len(new_df), key)

        return new_df.reset_index(drop=True)

    def _filter_wind(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply the +2.0 m/s legality rule to sprint events only.

        Rows with a missing or unparseable wind reading in a sprint event are
        dropped rather than assumed legal -- the previous `except: return True`
        kept both, which silently admitted wind-aided marks.
        """
        if "wind" not in df.columns or "event" not in df.columns:
            return df

        sprint_events = {name for name, meta in EVENT_METADATA.items() if meta["is_sprint"]}
        is_sprint = df["event"].isin(sprint_events)
        if not is_sprint.any():
            return df

        wind = df.loc[is_sprint, "wind"].apply(self.parse_wind)
        unparseable = int(wind.isna().sum())
        illegal = int((wind > MAX_LEGAL_WIND).sum())
        keep_sprint = wind.notna() & (wind <= MAX_LEGAL_WIND)

        if unparseable:
            log.info("Dropped %d sprint row(s) with a missing/unparseable wind reading", unparseable)
        if illegal:
            log.info("Dropped %d wind-aided sprint row(s) (> %.1f m/s)", illegal, MAX_LEGAL_WIND)

        return pd.concat([df.loc[~is_sprint], df.loc[is_sprint][keep_sprint]]).sort_index()
