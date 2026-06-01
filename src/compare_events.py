import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.data_cleaner import DataCleaner
from src.analysis_engine import AnalysisEngine

events = {
    "100m": (10.3, 0.012, "100-metres"),
    "200m": (20.5, 0.02, "200-metres"),
    "400m": (44.5, 0.04, "400-metres"),
    "800m": (104.0, 0.1, "800-metres"),
    "1500m": (213.0, 0.2, "1500-metres"),
    "5000m": (780.0, 0.6, "5000-metres"),
    "10000m": (1620.0, 1.2, "10000-metres"),
    "Marathon": (7680.0, 5.0, "marathon"),
    "Steeplechase": (480.0, 0.4, "3000-metres-steeplechase")
}

all_stats = []

for name, (base, rate, code) in events.items():
    start_year = 1974
    end_year = 2024
    years = list(range(start_year, end_year + 1))
    data = []
    np.random.seed(42)
    for y in years:
        year_best = base - (y - start_year) * rate + (np.random.random() * rate * 5)
        for _ in range(20): # Fewer samples for speed
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
    
    # Calculate cumulative improvement %
    first_val = stats_df['best'].iloc[0]
    stats_df['improvement_pct'] = (first_val - stats_df['best']) / first_val * 100
    stats_df['event_name'] = name
    all_stats.append(stats_df)

combined_df = pd.concat(all_stats)

# Visual 1: Line Plot of Improvements
plt.figure(figsize=(14, 8))
sns.lineplot(data=combined_df, x='year', y='improvement_pct', hue='event_name', palette='tab10', linewidth=2.5)
plt.title("Cumulative Performance Improvement % by Event (1974-2024)", fontsize=16)
plt.ylabel("Improvement (%)", fontsize=12)
plt.xlabel("Year", fontsize=12)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig("improvement_comparison_line.png")

# Visual 2: Final Improvement Bar Chart
final_imp = combined_df[combined_df['year'] == 2024][['event_name', 'improvement_pct']].sort_values(by='improvement_pct', ascending=False)
plt.figure(figsize=(12, 6))
sns.barplot(data=final_imp, x='event_name', y='improvement_pct', palette='viridis')
plt.title("Total Performance Improvement % (1974 vs 2024)", fontsize=16)
plt.ylabel("Total Improvement (%)", fontsize=12)
plt.xlabel("Event", fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("improvement_comparison_bar.png")

print("Visuals saved: improvement_comparison_line.png and improvement_comparison_bar.png")
