import argparse
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

from src.analysis_engine import AnalysisEngine
from src.config import (
    ALPHA,
    BIOLOGICAL_FLOORS,
    END_YEAR,
    EVENT_METADATA,
    PROJECTION_TARGET_YEAR,
    REAL_WR,
    START_YEAR,
)
from src.data_cleaner import DataCleaner
from src.forecaster import TrackForecaster
from src.scraper import ScrapeError, WorldAthleticsScraper
from src.utils.logger import log

DATA_DIR = Path("data")
RAW_PATH = DATA_DIR / "raw" / "toplists.csv"
CLEAN_PATH = DATA_DIR / "processed" / "toplists_clean.csv"
REPORTS_DIR = Path("reports")


class TrackflationCLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Trackflation CLI")
        self.subparsers = self.parser.add_subparsers(dest="command", help="Available commands")

        scrape = self.subparsers.add_parser(
            "scrape", help="Download World Athletics season toplists into data/raw/"
        )
        scrape.add_argument("--event", choices=list(EVENT_METADATA), action="append",
                            help="Event to scrape (repeatable). Default: all events.")
        scrape.add_argument("--start-year", type=int, default=START_YEAR)
        scrape.add_argument("--end-year", type=int, default=END_YEAR)

        run_event = self.subparsers.add_parser(
            "run-event", help="Analyse and forecast a single event from scraped data"
        )
        run_event.add_argument("--event", required=True, choices=list(EVENT_METADATA))

        self.subparsers.add_parser(
            "compare-all", help="Write cross-event comparison figures into reports/"
        )
        self.subparsers.add_parser(
            "generate-report", help="Write the cumulative improvement table into reports/"
        )

    def run(self, argv: Optional[List[str]] = None):
        args = self.parser.parse_args(argv)
        if args.command == "scrape":
            self.scrape(args.event or list(EVENT_METADATA), args.start_year, args.end_year)
        elif args.command == "run-event":
            self.run_event_analysis(args.event)
        elif args.command == "compare-all":
            self.compare_all_events()
        elif args.command == "generate-report":
            self.generate_cumulative_report()
        else:
            self.parser.print_help()

    # ------------------------------------------------------------------ data

    def scrape(self, events: List[str], start_year: int, end_year: int):
        scraper = WorldAthleticsScraper()
        frames = []
        for event in events:
            log.info(f"Scraping {event} {start_year}-{end_year}...")
            try:
                frames.append(scraper.scrape_historical(event, start_year, end_year))
            except ScrapeError as exc:
                log.error(f"{event}: {exc}")
        if not frames:
            raise SystemExit("Nothing scraped; aborting.")
        raw = pd.concat(frames, ignore_index=True)
        RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
        raw.to_csv(RAW_PATH, index=False)
        log.info(f"Wrote {len(raw)} raw rows to {RAW_PATH}")

        clean = DataCleaner().clean_scraped_data(raw)
        CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
        clean.to_csv(CLEAN_PATH, index=False)
        log.info(f"Wrote {len(clean)} cleaned rows to {CLEAN_PATH}")

    @staticmethod
    def load_clean(event: Optional[str] = None) -> pd.DataFrame:
        if not CLEAN_PATH.exists():
            raise SystemExit(
                f"{CLEAN_PATH} not found. Run `trackflation scrape` first "
                "to download the World Athletics toplists."
            )
        df = pd.read_csv(CLEAN_PATH)
        if event is not None:
            df = df[df["event"] == event]
            if df.empty:
                raise SystemExit(f"No cleaned rows for event {event!r}; scrape it first.")
        return df

    # -------------------------------------------------------------- analysis

    def run_event_analysis(self, event_name: str):
        log.info(f"Starting analysis for {event_name}")
        clean_df = self.load_clean(event_name)

        engine = AnalysisEngine(clean_df)
        stats_df = engine.get_yearly_stats()
        log.info(
            f"{len(clean_df)} marks across {len(stats_df)} seasons "
            f"({stats_df['year'].min()}-{stats_df['year'].max()})"
        )

        rate = engine.calculate_improvement_rate(stats_df)
        log.info(f"Top-10 mean trend: {rate:+.4f} s/year (OLS on an extreme-value statistic; see docstring)")

        anomalies = engine.detect_anomalies(stats_df)
        log.info(f"Anomalous seasons (robust MAD z-score): {anomalies or 'none'}")

        forecaster = TrackForecaster(stats_df, cap=BIOLOGICAL_FLOORS[event_name])
        forecast = forecaster.forecast(target_year=PROJECTION_TARGET_YEAR, alpha=ALPHA)
        final = forecast.iloc[-1]
        final_year = pd.to_datetime(final["ds"]).year
        log.info(
            f"Projected {event_name} best in {final_year}: "
            f"{TrackForecaster.seconds_to_str(final['yhat'])} "
            f"[{TrackForecaster.seconds_to_str(final['yhat_lower'])}, "
            f"{TrackForecaster.seconds_to_str(final['yhat_upper'])}]"
        )
        log.info(
            "  (logistic fit assumes an unobserved floor of "
            f"{TrackForecaster.seconds_to_str(BIOLOGICAL_FLOORS[event_name])}; "
            "compare the floor-free linear fit below)"
        )
        linear = TrackForecaster(stats_df, cap=None).forecast(
            target_year=PROJECTION_TARGET_YEAR, alpha=ALPHA
        )
        log.info(
            f"  linear (no floor assumed): "
            f"{TrackForecaster.seconds_to_str(linear.iloc[-1]['yhat'])}"
        )
        return stats_df, forecast

    def generate_cumulative_report(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        df = self.load_clean()
        rows = []
        for event in EVENT_METADATA:
            sub = df[df["event"] == event]
            if sub.empty:
                continue
            stats_df = AnalysisEngine(sub).get_yearly_stats()
            baseline = AnalysisEngine.baseline_level(stats_df)
            latest = AnalysisEngine.recent_level(stats_df)
            rows.append(
                {
                    "Event": event,
                    "Seasons": f"{int(stats_df['year'].min())}-{int(stats_df['year'].max())}",
                    "Baseline top-10 mean": TrackForecaster.seconds_to_str(baseline),
                    "Recent top-10 mean": TrackForecaster.seconds_to_str(latest),
                    "Improvement %": round(100 * (baseline - latest) / baseline, 2),
                    "World record": TrackForecaster.seconds_to_str(REAL_WR[event]),
                }
            )
        table = pd.DataFrame(rows)
        out_csv = REPORTS_DIR / "cumulative_improvement.csv"
        out_md = REPORTS_DIR / "cumulative_improvement.md"
        table.to_csv(out_csv, index=False)
        out_md.write_text(table.to_markdown(index=False), encoding="utf-8")
        log.info(f"Wrote {out_csv} and {out_md}")
        print(table.to_markdown(index=False))
        return table

    def compare_all_events(self):
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        df = self.load_clean()

        series = {}
        totals = {}
        for event in EVENT_METADATA:
            sub = df[df["event"] == event]
            if sub.empty:
                continue
            stats_df = AnalysisEngine(sub).get_yearly_stats()
            baseline = AnalysisEngine.baseline_level(stats_df)
            series[event] = (
                stats_df["year"].to_numpy(),
                100 * (baseline - stats_df["top_10_avg"].to_numpy()) / baseline,
            )
            totals[event] = 100 * (baseline - AnalysisEngine.recent_level(stats_df)) / baseline

        span = f"{int(df['year'].min())}-{int(df['year'].max())}"

        fig, ax = plt.subplots(figsize=(12, 7))
        for event, (years, pct) in series.items():
            ax.plot(years, pct, marker="o", markersize=3, label=event)
        ax.set_title(
            f"Cumulative improvement in top-10 season mean vs baseline ({span})\n"
            "Source: World Athletics season toplists, men's senior outdoor"
        )
        ax.set_xlabel("Year")
        ax.set_ylabel("Improvement vs baseline (%)")
        ax.axhline(0, color="grey", linewidth=0.8)
        ax.legend(ncol=3, fontsize=9)
        fig.tight_layout()
        line_path = REPORTS_DIR / "improvement_comparison_line.png"
        fig.savefig(line_path, dpi=120)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10, 6))
        ordered = sorted(totals.items(), key=lambda kv: kv[1])
        ax.barh([k for k, _ in ordered], [v for _, v in ordered], color="#0B7261")
        ax.set_title(
            f"Total improvement in top-10 season mean ({span})\n"
            "Source: World Athletics season toplists, men's senior outdoor"
        )
        ax.set_xlabel("Improvement vs baseline (%)")
        fig.tight_layout()
        bar_path = REPORTS_DIR / "improvement_comparison_bar.png"
        fig.savefig(bar_path, dpi=120)
        plt.close(fig)

        log.info(f"Wrote {line_path} and {bar_path}")
        return line_path, bar_path


def main(argv: Optional[List[str]] = None):
    TrackflationCLI().run(argv if argv is not None else sys.argv[1:])


if __name__ == "__main__":
    main()
