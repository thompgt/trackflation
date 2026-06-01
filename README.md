# Trackflation

Analyze historical World Athletics top times and project future world records using **Rolling Window Conformal Prediction**.

## Features
- **Historical Scraper**: Collects top track times since 1974.
- **Trend Analysis**: Quantifies the rate of improvement ("inflation") per event.
- **Conformal Prediction**: Provides statistically sound uncertainty intervals for future performance limits.
- **Future Projections**: Estimates WRs for the next 20+ years using Prophet + CP.

## Cumulative Analysis (1974-2044)

The table below shows historical best times and our AI-driven projections for the next 20 years.

| Event        | 2000       | 2010       | Current (2024)   | 20-yr Prediction (2044)   |
|:-------------|:-----------|:-----------|:-----------------|:--------------------------|
| 100m         | 10.00      | 9.88       | 9.73             | 9.43                      |
| 200m         | 20.00      | 19.79      | 19.54            | 19.02                     |
| 400m         | 43.51      | 43.09      | 42.59            | 41.55                     |
| 800m         | 1:41.52    | 1:40.47    | 1:39.22          | 1:36.62                   |
| 1500m        | 3:28.04    | 3:25.95    | 3:23.45          | 3:18.25                   |
| 5000m        | 12:45.13   | 12:38.84   | 12:31.35         | 12:15.56                  |
| 10000m       | 26:30.26   | 26:17.68   | 26:02.70         | 25:31.05                  |
| Marathon     | 2:05:56.09 | 2:05:03.67 | 2:04:01.23       | 2:01:48.79                |
| Steeplechase | 7:50.09    | 7:45.89    | 7:40.90          | 7:30.40                   |

*Note: Data for 2000-2024 is simulated for demonstration; 2044 is the median projection (yhat).*

## Visualizations

Detailed analysis notebooks with plots are available for each event:
- [100m Analysis](notebooks/analysis.ipynb)
- [200m Analysis](notebooks/200-metres_analysis.ipynb)
- [400m Analysis](notebooks/400-metres_analysis.ipynb)
- [800m Analysis](notebooks/800-metres_analysis.ipynb)
- [1500m Analysis](notebooks/1500-metres_analysis.ipynb)
- [5000m Analysis](notebooks/5000-metres_analysis.ipynb)
- [10000m Analysis](notebooks/10000-metres_analysis.ipynb)
- [Marathon Analysis](notebooks/marathon_analysis.ipynb)
- [Steeplechase Analysis](notebooks/3000-metres-steeplechase_analysis.ipynb)

## Setup
1. `python -m venv venv`
2. `.\venv\Scripts\activate`
3. `pip install -r requirements.txt`

## Methodology: Conformal Prediction
Unlike standard time-series models that assume normal error distributions, we use **Rolling Window Conformal Prediction**. This method calculates the historical residuals of the Prophet model and uses their quantiles to scale the prediction intervals. This ensures that the intervals are robust to the "spiky" nature of track improvements.
