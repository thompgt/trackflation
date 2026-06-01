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

    def forecast(self, periods=25) -> pd.DataFrame:
        """Forecasts performance for the next N years."""
        m = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
            growth='linear'
        )
        m.fit(self.df)
        
        future = m.make_future_dataframe(periods=periods, freq='YE')
        forecast = m.predict(future)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    @staticmethod
    def seconds_to_str(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.2f}"
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}:{secs:05.2f}"
        
