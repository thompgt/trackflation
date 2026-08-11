"""
Prophet-based forecasting for annual best / top-10 performance series.

Two things in here are assumptions rather than findings, and are called out
explicitly because earlier versions of this project presented them as results:

1. **The logistic floor.** With `cap` set, the series is re-expressed as
   `y - cap` and fitted with Prophet's logistic growth, which is bounded below
   by 0. The forecast therefore *cannot* cross `cap` -- so "times taper as they
   approach the physiological limit" is a restatement of the chosen floor, not
   evidence for one. Fit with `cap=None` for a floor-free linear comparison, and
   use `floor_sensitivity()` to see how much the horizon value moves when the
   assumed floor moves.

2. **The prediction interval.** This is *split* conformal: the last
   `calibration_years` seasons are held out, the model is refitted on the rest,
   and the interval half-width is the ceil((n+1)(1-alpha))-th smallest held-out
   absolute residual. Taking a residual quantile on the training rows (as this
   module used to) gives in-sample residuals and under-covers.
"""

from __future__ import annotations

import logging
import math
from typing import Dict, Optional

import numpy as np
import pandas as pd
from prophet import Prophet

log = logging.getLogger(__name__)


def _quiet_prophet():
    """Prophet/cmdstanpy log a wall of INFO per fit; keep CLI output readable."""
    for name in ("prophet", "cmdstanpy"):
        logging.getLogger(name).setLevel(logging.WARNING)


class TrackForecaster:
    def __init__(self, stats_df: pd.DataFrame, target_col: str = "best", cap: Optional[float] = None):
        """
        stats_df must have a 'year' column and the target column.
        cap: the *assumed* floor (fastest attainable time) for the event, or None
             for a floor-free linear fit.
        """
        self.df = (
            stats_df[["year", target_col]]
            .rename(columns={"year": "ds", target_col: "y"})
            .sort_values("ds")
            .reset_index(drop=True)
        )
        # Year *starts*: Prophet must step by 'YS' to match, otherwise the
        # horizon silently lands a year short of the labelled target.
        self.df["ds"] = pd.to_datetime(self.df["ds"].astype(int).astype(str), format="%Y")
        self.cap = cap
        _quiet_prophet()

    # ---------------------------------------------------------------- helpers

    def _prepare(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Shift into 'distance above the floor' space when a cap is set."""
        out = frame.copy()
        if self.cap is not None:
            out["y"] = out["y"] - self.cap
            out["cap"] = out["y"].max() * 2
        return out

    def _fit(self, frame: pd.DataFrame) -> Prophet:
        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
            growth="logistic" if self.cap is not None else "linear",
        )
        model.fit(frame)
        return model

    @staticmethod
    def periods_to_year(last_year: int, target_year: int) -> int:
        if target_year <= last_year:
            raise ValueError(f"target_year {target_year} must be after the last observed year {last_year}")
        return target_year - last_year

    # --------------------------------------------------------------- forecast

    def forecast(
        self,
        periods: Optional[int] = None,
        target_year: Optional[int] = None,
        alpha: float = 0.05,
        calibration_years: int = 8,
    ) -> pd.DataFrame:
        """
        Forecast to `target_year` (preferred) or for `periods` further years.

        Returns ds/yhat/yhat_lower/yhat_upper, with the interval calibrated by
        split conformal on the last `calibration_years` seasons.
        """
        last_year = int(self.df["ds"].dt.year.max())
        if target_year is not None:
            periods = self.periods_to_year(last_year, target_year)
        elif periods is None:
            raise ValueError("Pass either periods or target_year")

        train = self._prepare(self.df)
        model = self._fit(train)

        # 'YS' (year start) matches the Jan-1 timestamps built above. The old
        # 'YE' stepped to Dec-31 and lost a year over the horizon.
        future = model.make_future_dataframe(periods=periods, freq="YS")
        if self.cap is not None:
            future["cap"] = train["cap"].max()
        forecast = model.predict(future)

        max_year = int(pd.to_datetime(forecast["ds"]).dt.year.max())
        expected = last_year + periods
        assert max_year == expected, f"Forecast horizon is {max_year}, expected {expected}"

        q = self._conformal_halfwidth(alpha=alpha, calibration_years=calibration_years)
        forecast["yhat_lower"] = forecast["yhat"] - q
        forecast["yhat_upper"] = forecast["yhat"] + q

        if self.cap is not None:
            for col in ("yhat", "yhat_lower", "yhat_upper"):
                forecast[col] = forecast[col] + self.cap

        return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

    def _conformal_halfwidth(self, alpha: float, calibration_years: int) -> float:
        """
        Split-conformal half-width: refit on all but the last `calibration_years`
        seasons, then take the ceil((n+1)(1-alpha))-th smallest absolute residual
        on the held-out seasons. Falls back to in-sample residuals (with a
        warning) when there is too little history to hold anything out.
        """
        n_total = len(self.df)
        if n_total - calibration_years < 5 or calibration_years < 2:
            log.warning(
                "Only %d seasons available; falling back to in-sample residuals. "
                "The resulting interval has no coverage guarantee.",
                n_total,
            )
            train = self._prepare(self.df)
            model = self._fit(train)
            residuals = np.abs(train["y"].to_numpy() - model.predict(train)["yhat"].to_numpy())
            return float(np.quantile(residuals, 1 - alpha))

        split = n_total - calibration_years
        fit_part = self._prepare(self.df.iloc[:split])
        cal_part = self._prepare(self.df.iloc[split:])
        model = self._fit(fit_part)
        if self.cap is not None:
            cal_part = cal_part.assign(cap=fit_part["cap"].max())
        residuals = np.sort(
            np.abs(cal_part["y"].to_numpy() - model.predict(cal_part)["yhat"].to_numpy())
        )

        n = len(residuals)
        rank = math.ceil((n + 1) * (1 - alpha))
        if rank > n:
            # (n+1)(1-alpha) exceeds the sample: no finite interval is valid at
            # this alpha with this little calibration data. Use the max and say so.
            log.warning(
                "alpha=%.3f needs at least %d calibration points, have %d; "
                "using the largest residual (coverage is not guaranteed).",
                alpha,
                math.ceil(1 / alpha) - 1,
                n,
            )
            return float(residuals[-1])
        return float(residuals[rank - 1])

    # ------------------------------------------------------------ sensitivity

    def floor_sensitivity(
        self, target_year: int, spread: float = 0.10, alpha: float = 0.05
    ) -> Dict[str, float]:
        """
        Refit at floor x(1-spread), the stated floor, floor x(1+spread) and with no
        floor at all, and return the horizon value for each. The spread across
        these is how much of the projection is the floor assumption talking.
        """
        results: Dict[str, float] = {}
        base = self.cap
        variants: Dict[str, Optional[float]] = {"no_floor": None}
        if base is not None:
            variants.update(
                {
                    "floor_minus_10pct": base * (1 - spread),
                    "floor": base,
                    "floor_plus_10pct": base * (1 + spread),
                }
            )
        original = pd.concat(
            [self.df["ds"].dt.year.rename("year"), self.df["y"].rename("best")], axis=1
        )
        for label, cap in variants.items():
            try:
                sub = TrackForecaster(original, cap=cap)
                results[label] = float(
                    sub.forecast(target_year=target_year, alpha=alpha).iloc[-1]["yhat"]
                )
            except Exception as exc:  # a floor above the data makes logistic infeasible
                log.warning("floor_sensitivity variant %s failed: %s", label, exc)
        self.cap = base
        return results

    # ----------------------------------------------------------- formatting

    @staticmethod
    def seconds_to_str(seconds: float) -> str:
        if seconds is None or (isinstance(seconds, float) and math.isnan(seconds)):
            return "n/a"
        if seconds < 0:
            return f"-{TrackForecaster.seconds_to_str(-seconds)}"
        if seconds < 60:
            return f"{seconds:.2f}"
        if seconds < 3600:
            mins = int(seconds // 60)
            secs = seconds % 60
            return f"{mins}:{secs:05.2f}"
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{mins:02d}:{secs:05.2f}"
