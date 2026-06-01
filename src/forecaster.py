from prophet import Prophet
import pandas as pd
import numpy as np

class TrackForecaster:
    def __init__(self, stats_df: pd.DataFrame, target_col='best', cap=None):
        """
        stats_df should have 'year' and the target column (e.g., 'best' for WR).
        cap: The theoretical physical floor (limit) for the event.
        """
        self.df = stats_df[['year', target_col]].rename(columns={
            'year': 'ds',
            target_col: 'y'
        })
        self.df['ds'] = pd.to_datetime(self.df['ds'], format='%Y')
        self.cap = cap
        
        if self.cap:
            # Prophet Logistic Growth requires a 'cap' column.
            # Since we are predicting time (which decreases), we model the distance from the floor.
            self.df['y_orig'] = self.df['y']
            self.df['y'] = self.df['y'] - self.cap
            # We set a large dummy capacity for the 'distance from floor' to allow logistic decay
            self.df['cap'] = self.df['y'].max() * 2 

    def forecast(self, periods=25, alpha=0.05) -> pd.DataFrame:
        """
        Forecasts performance using Logistic Growth to simulate biological tapering.
        """
        growth = 'logistic' if self.cap else 'linear'
        
        m = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
            growth=growth
        )
        m.fit(self.df)
        
        future = m.make_future_dataframe(periods=periods, freq='YE')
        if self.cap:
            future['cap'] = self.df['cap'].max()
            
        forecast = m.predict(future)
        
        # Conformal Prediction on residuals
        historical_forecast = m.predict(self.df)
        residuals = np.abs(self.df['y'].values - historical_forecast['yhat'].values)
        q = np.quantile(residuals, 1 - alpha)
        
        forecast['yhat_lower'] = forecast['yhat'] - q
        forecast['yhat_upper'] = forecast['yhat'] + q
        
        if self.cap:
            # Transform back to absolute time
            for col in ['yhat', 'yhat_lower', 'yhat_upper']:
                forecast[col] = forecast[col] + self.cap
        
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
        
