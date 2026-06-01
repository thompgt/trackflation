import pandas as pd
import numpy as np
from src.data_cleaner import DataCleaner
from src.analysis_engine import AnalysisEngine
from src.forecaster import TrackForecaster

events = {
    "100m": (10.3, 0.012, "100-metres"),
    "200m": (20.5, 0.02, "200-metres"),
    "400m": (44.5, 0.04, "400-metres"),
    "800m": (104.0, 0.1, "800-metres"), # 1:44.0
    "1500m": (213.0, 0.2, "1500-metres"), # 3:33.0
    "5000m": (780.0, 0.6, "5000-metres"), # 13:00.0
    "10000m": (1620.0, 1.2, "10000-metres"), # 27:00.0
    "Marathon": (7680.0, 5.0, "marathon"), # 2:08:00
    "Steeplechase": (480.0, 0.4, "3000-metres-steeplechase") # 8:00.0
}

results = []

for name, (base, rate, code) in events.items():
    start_year = 1974
    end_year = 2024
    years = list(range(start_year, end_year + 1))
    data = []
    np.random.seed(42)
    for y in years:
        year_best = base - (y - start_year) * rate + (np.random.random() * rate * 5)
        for _ in range(50):
            data.append({
                "year": y,
                "mark": f"{year_best + np.random.random() * rate * 10:.2f}",
                "wind": "1.0",
                "athlete": "X",
                "date": f"{y}-01-01",
                "event": code
            })
    
    df = pd.DataFrame(data)
    clean_df = DataCleaner().clean_scraped_data(df)
    stats_df = AnalysisEngine(clean_df).get_yearly_stats()
    
    forecaster = TrackForecaster(stats_df)
    forecast = forecaster.forecast(periods=20)
    
    t_2000 = stats_df[stats_df['year'] == 2000]['best'].values[0]
    t_2010 = stats_df[stats_df['year'] == 2010]['best'].values[0]
    t_current = stats_df[stats_df['year'] == 2024]['best'].values[0]
    t_2044 = forecast.iloc[-1]['yhat']
    
    results.append({
        "Event": name,
        "2000": forecaster.seconds_to_str(t_2000),
        "2010": forecaster.seconds_to_str(t_2010),
        "Current (2024)": forecaster.seconds_to_str(t_current),
        "20-yr Prediction (2044)": forecaster.seconds_to_str(t_2044)
    })

res_df = pd.DataFrame(results)
print(res_df.to_markdown(index=False))
