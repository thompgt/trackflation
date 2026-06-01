import pandas as pd
import numpy as np
from scipy import stats

class AnalysisEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def get_yearly_stats(self) -> pd.DataFrame:
        """Calculates median, top 1, and top 10 times per year."""
        stats_df = self.df.groupby('year')['seconds'].agg([
            ('best', 'min'),
            ('top_10_avg', lambda x: x.nsmallest(10).mean()),
            ('median', 'median'),
            ('count', 'count')
        ]).reset_index()
        return stats_df

    def calculate_improvement_rate(self, stats_df: pd.DataFrame, col='top_10_avg') -> float:
        """Calculates the annual improvement rate using linear regression slope."""
        if len(stats_df) < 2: return 0.0
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            stats_df['year'], 
            stats_df[col]
        )
        return slope # Seconds improved per year

    def detect_anomalies(self, stats_df: pd.DataFrame) -> List[int]:
        """Identifies years with significant performance jumps."""
        # Simple z-score check on year-over-year changes
        yoy_change = stats_df['top_10_avg'].diff().dropna()
        z_scores = stats.zscore(yoy_change)
        anomaly_years = stats_df['year'].iloc[1:][np.abs(z_scores) > 2].tolist()
        return anomaly_years
