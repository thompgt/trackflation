import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.scraper import WorldAthleticsScraper
from src.data_cleaner import DataCleaner
from src.analysis_engine import AnalysisEngine
from src.forecaster import TrackForecaster

def main():
    parser = argparse.ArgumentParser(description="Trackflation: Analyze and project track performance.")
    parser.add_argument("--event", default="100-metres", help="Event code (e.g., 100-metres, 5000-metres)")
    parser.add_argument("--start", type=int, default=1974, help="Start year")
    parser.add_argument("--end", type=int, default=2024, help="End year")
    
    args = parser.parse_args()

    print(f"--- Running Trackflation Analysis for {args.event} ---")
    
    # In a real scenario, we'd scrape or load from local CSV
    # scraper = WorldAthleticsScraper()
    # raw_df = scraper.scrape_historical(args.event, args.start, args.end)
    
    print("Step 1: Loading Data (Simulated for this demo)...")
    # For demonstration, we'll create some synthetic trend data if no file exists
    try:
        df = pd.read_csv(f"data/{args.event}_historical.csv")
    except FileNotFoundError:
        print("No local data found. Run scraper first (Issue 2). Generating sample trend for visualization.")
        years = list(range(args.start, args.end + 1))
        data = []
        base_time = 10.3 # 100m base
        for y in years:
            # Add a slight improvement trend + noise
            year_best = base_time - (y - args.start) * 0.01 + (np.random.random() * 0.1)
            for _ in range(50):
                data.append({
                    "year": y,
                    "mark": f"{year_best + np.random.random() * 0.5:.2f}",
                    "wind": "1.2",
                    "athlete": "Athlete X",
                    "date": "2024-01-01",
                    "event": args.event
                })
        df = pd.DataFrame(data)

    print("Step 2: Cleaning Data...")
    cleaner = DataCleaner()
    clean_df = cleaner.clean_scraped_data(df)
    
    print("Step 3: Analyzing Trends...")
    engine = AnalysisEngine(clean_df)
    stats_df = engine.get_yearly_stats()
    slope = engine.calculate_improvement_rate(stats_df)
    print(f"Rate of Improvement: {abs(slope)*100:.3f} seconds per decade")
    
    print("Step 4: Forecasting Future Records...")
    forecaster = TrackForecaster(stats_df)
    forecast = forecaster.forecast(periods=20)
    
    future_2044 = forecast.iloc[-1]
    print(f"Projected {args.event} WR in 2044: {forecaster.seconds_to_str(future_2044['yhat'])}")
    print(f"Lower Bound (Optimistic): {forecaster.seconds_to_str(future_2044['yhat_lower'])}")

    print("Step 5: Visualizing...")
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=stats_df, x='year', y='best', label='Historical Best')
    plt.title(f"Performance Trend and Projection: {args.event}")
    plt.ylabel("Time (seconds)")
    plt.xlabel("Year")
    plt.savefig(f"{args.event}_projection.png")
    print(f"Chart saved as {args.event}_projection.png")

if __name__ == "__main__":
    import numpy as np # Needed for demo data
    main()
