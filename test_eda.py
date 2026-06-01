import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Mock classes for testing the EDA code
class DataCleaner:
    def clean_scraped_data(self, df):
        df['seconds'] = df['mark'].astype(float)
        df['decade'] = (df['year'] // 10) * 10
        return df

class AnalysisEngine:
    def __init__(self, df): self.df = df
    def get_yearly_stats(self):
        return self.df.groupby('year')['seconds'].agg([
            ('best', 'min'),
            ('top_10_avg', lambda x: x.nsmallest(10).mean()),
            ('median', 'median'),
            ('count', 'count')
        ]).reset_index()

# Generate sample data
years = range(1974, 2025)
data = []
for y in years:
    for r in range(1, 101):
        data.append({
            "year": y, "mark": 10.5 - (y-1974)*0.01 + np.random.random()*0.5,
            "wind": np.random.uniform(-2, 4), "athlete": f"A{r}", "event": "100m"
        })
df = pd.DataFrame(data)
clean_df = DataCleaner().clean_scraped_data(df)
stats_df = AnalysisEngine(clean_df).get_yearly_stats()

# EDA Code to be inserted into notebooks
def run_eda(clean_df, stats_df, event_name="100m", is_sprint=True):
    plt.figure(figsize=(15, 20))
    
    # Plot 1: Time Series Trend
    plt.subplot(5, 1, 1)
    sns.lineplot(data=stats_df, x='year', y='best', label='Yearly Best', color='red')
    sns.lineplot(data=stats_df, x='year', y='top_10_avg', label='Top 10 Avg', color='blue', linestyle='--')
    plt.title(f"{event_name}: Historical Performance Trend")
    plt.gca().invert_yaxis()
    
    # Plot 2: Decadal Boxplot
    plt.subplot(5, 1, 2)
    clean_df['decade'] = (clean_df['year'] // 10) * 10
    sns.boxplot(data=clean_df, x='decade', y='seconds')
    plt.title(f"{event_name}: Distribution of Marks by Decade")
    plt.gca().invert_yaxis()
    
    # Plot 3: Depth Analysis (Gap between #1 and #50)
    plt.subplot(5, 1, 3)
    depth = clean_df.groupby('year').apply(lambda x: x['seconds'].nsmallest(50).max() - x['seconds'].min())
    plt.plot(depth.index, depth.values, color='purple', marker='x')
    plt.title(f"{event_name}: Performance Depth (Gap between Rank 1 and 50)")
    plt.ylabel("Seconds Gap")
    
    # Plot 4: Correlation Heatmap
    plt.subplot(5, 1, 4)
    sns.heatmap(stats_df[['best', 'top_10_avg', 'median', 'count']].corr(), annot=True, cmap='coolwarm')
    plt.title("Correlation of Yearly Metrics")
    
    # Plot 5: Cumulative Improvement
    plt.subplot(5, 1, 5)
    improv = (stats_df['best'].iloc[0] - stats_df['best']) / stats_df['best'].iloc[0] * 100
    plt.fill_between(stats_df['year'], improv, color='green', alpha=0.3)
    plt.plot(stats_df['year'], improv, color='green')
    plt.title(f"{event_name}: Cumulative Improvement % since {stats_df['year'].min()}")
    plt.ylabel("% Improved")
    
    plt.tight_layout()
    plt.show()
    
    if is_sprint:
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=clean_df, x='wind', y='seconds', alpha=0.3)
        plt.title(f"{event_name}: Impact of Wind on Performance")
        plt.gca().invert_yaxis()
        plt.show()

run_eda(clean_df, stats_df)
