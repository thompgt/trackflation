# Trackflation Project Plan

Analyze historical World Athletics top times over the last 50+ years to identify "performance inflation" and project future world records.

## Project Goals
1. **Data Acquisition**: Scrape or use APIs to collect the top 100 times for each track event (100m, 200m, 400m, 800m, 1500m, 5000m, 10000m, hurdles) per year from 1974 to present.
2. **Historical Analysis**: 
    - Identify events with the highest rate of improvement (slope of top times).
    - Analyze the "depth" of events (how much the gap between #1 and #100 has changed).
    - Factor in technological shifts (super spikes, track surfaces).
3. **Forecasting**: Use statistical models (Linear Regression, ARIMA, or Prophet) to project World Records for the next 20+ years.
4. **Visualization**: Create charts showing "Trackflation" across different eras.

## Technical Stack
- **Data**: `requests`, `beautifulsoup4`, `pandas`
- **Analysis**: `numpy`, `scipy`, `statsmodels`
- **Forecasting**: `prophet` or `scikit-learn`
- **Visualization**: `matplotlib`, `seaborn`

## Workflow
1. **Scraping Module**: Robust logic to navigate World Athletics historical rankings.
2. **Data Cleaning**: Standardizing formats, handling wind-aided times, and duplicates.
3. **Analysis Engine**: Statistical functions to calculate improvement rates and variance.
4. **Projection Model**: Training on historical data to estimate future limits.
5. **Report/CLI**: Simple interface to query specific event projections.
