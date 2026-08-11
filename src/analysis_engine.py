"""Season-level statistics over a cleaned toplist frame."""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd
from scipy import stats

# Number of seasons averaged at each end when computing cumulative improvement.
# A single season's minimum is the minimum of a small sample and is far too
# noisy to anchor a percentage against.
BASELINE_WINDOW = 3


class AnalysisEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def get_yearly_stats(self) -> pd.DataFrame:
        """Season best, top-10 mean, median and depth count."""
        stats_df = (
            self.df.groupby("year")["seconds"]
            .agg(
                [
                    ("best", "min"),
                    ("top_10_avg", lambda x: x.nsmallest(10).mean()),
                    ("median", "median"),
                    ("count", "count"),
                ]
            )
            .reset_index()
            .sort_values("year")
            .reset_index(drop=True)
        )
        return stats_df

    # -------------------------------------------------------------- baselines

    @staticmethod
    def baseline_level(stats_df: pd.DataFrame, col: str = "top_10_avg") -> float:
        """Mean of `col` over the first BASELINE_WINDOW seasons."""
        return float(stats_df.sort_values("year")[col].head(BASELINE_WINDOW).mean())

    @staticmethod
    def recent_level(stats_df: pd.DataFrame, col: str = "top_10_avg") -> float:
        """Mean of `col` over the last BASELINE_WINDOW seasons."""
        return float(stats_df.sort_values("year")[col].tail(BASELINE_WINDOW).mean())

    # ---------------------------------------------------------------- trends

    def calculate_improvement_rate(self, stats_df: pd.DataFrame, col: str = "top_10_avg") -> float:
        """
        OLS slope of `col` on year, in seconds per year.

        Caveat, deliberately not buried: the default target is a top-10 mean and
        the alternative ('best') is an annual minimum. Annual extremes are
        extreme-value rather than Gaussian distributed, with heteroskedastic
        errors and a field size that drifts across seasons, so the OLS standard
        error and p-value from this fit are not interpretable as significance
        tests. The slope is reported as a descriptive trend only; use
        `depth_adjusted_rate` when the number of ranked marks varies.
        """
        if len(stats_df) < 2:
            return 0.0
        result = stats.linregress(stats_df["year"], stats_df[col])
        return float(result.slope)

    def depth_adjusted_rate(self, stats_df: pd.DataFrame, col: str = "top_10_avg") -> Dict[str, float]:
        """
        Slope of `col` on year controlling for the number of ranked marks that
        season, so a growing toplist is not read as improvement. Returns the
        year coefficient and the count coefficient.
        """
        if len(stats_df) < 3:
            return {"year": 0.0, "count": 0.0}
        design = np.column_stack(
            [
                np.ones(len(stats_df)),
                stats_df["year"].to_numpy(float),
                stats_df["count"].to_numpy(float),
            ]
        )
        coefficients, *_ = np.linalg.lstsq(design, stats_df[col].to_numpy(float), rcond=None)
        return {"year": float(coefficients[1]), "count": float(coefficients[2])}

    # ------------------------------------------------------------- anomalies

    def detect_anomalies(self, stats_df: pd.DataFrame, threshold: float = 3.0) -> List[int]:
        """
        Seasons whose year-on-year change in `top_10_avg` is an outlier.

        Uses a median/MAD robust z-score rather than mean/SD: a single large
        structural break inflates the SD it would be tested against, so the very
        jumps this project looks for were the least likely to be flagged.
        """
        ordered = stats_df.sort_values("year").reset_index(drop=True)
        yoy = ordered["top_10_avg"].diff()
        valid = yoy.dropna()
        if len(valid) < 3:
            return []

        median = float(np.median(valid))
        # 0.6745 rescales the MAD to a standard-deviation-equivalent for normal data.
        scale = float(np.median(np.abs(valid - median))) / 0.6745
        if scale == 0:
            # Degenerate MAD (more than half the diffs identical); fall back to
            # the IQR, which is also outlier-resistant.
            q1, q3 = np.percentile(valid, [25, 75])
            scale = float(q3 - q1) / 1.349
        if scale == 0:
            return []
        robust_z = (valid - median) / scale

        flagged = valid.index[np.abs(robust_z) > threshold]
        return ordered.loc[flagged, "year"].astype(int).tolist()
