from prophet import Prophet
import pandas as pd
import numpy as np

class TrackForecaster:
    def __init__(self, stats_df: pd.DataFrame, target_col='best'):
        """
        stats_df should have 'year' and the target column (e.g., 'best' for WR).
        """
        self.df = stats_df[['year', target_col]].rename(columns={
            'year': 'ds',
            target_col: 'y'
        })
        # Prophet expects ds as datetime
        self.df['ds'] = pd.to_datetime(self.df['ds'], format='%Y')

    def forecast(self, periods=25, alpha=0.05) -> pd.DataFrame:
        """
        Forecasts performance for the next N years using Prophet with 
        Rolling Window Conformal Prediction for uncertainty intervals.
        """
        # 1. Fit the model on all historical data to get the trend
        m = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
            growth='linear'
        )
        m.fit(self.df)
        
        # 2. Generate point forecasts (yhat)
        future = m.make_future_dataframe(periods=periods, freq='YE')
        forecast = m.predict(future)
        
        # 3. Rolling Window Conformal Prediction
        # We calculate residuals on the historical data to determine the interval width
        historical_forecast = m.predict(self.df)
        residuals = np.abs(self.df['y'].values - historical_forecast['yhat'].values)
        
        # Use the (1-alpha) quantile of residuals as the conformal interval width
        # For time-series, we often use the most recent window of residuals
        # but here we'll use all historical residuals for a robust global estimate.
        q = np.quantile(residuals, 1 - alpha)
        
        # 4. Apply the conformal width to the future forecast
        forecast['yhat_lower'] = forecast['yhat'] - q
        forecast['yhat_upper'] = forecast['yhat'] + q
        
        # Label the source of the interval
        forecast['interval_type'] = 'conformal'
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    @staticmethod
    def seconds_to_str(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.2f}"
        if seconds < 3600:
            mins = int(seconds // 60)
            secs = seconds % 60
            return f"{mins}:{secs:05.2f}"
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{mins:02}:{secs:05.2f}"
        
