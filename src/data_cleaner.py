import pandas as pd
import re

class DataCleaner:
    @staticmethod
    def time_to_seconds(time_str: str) -> float:
        """Converts MM:SS.ms or SS.ms to float seconds."""
        if not time_str or not isinstance(time_str, str):
            return None
        
        # Remove any non-numeric characters except : and .
        clean_time = re.sub(r'[^0-9:.]', '', time_str)
        
        try:
            if ':' in clean_time:
                parts = clean_time.split(':')
                if len(parts) == 2:
                    return int(parts[0]) * 60 + float(parts[1])
                elif len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            else:
                return float(clean_time)
        except ValueError:
            return None

    def clean_scraped_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        new_df = df.copy()
        
        # Convert marks to seconds
        new_df['seconds'] = new_df['mark'].apply(self.time_to_seconds)
        
        # Handle wind-aided marks (filter out if wind > 2.0)
        def is_wind_legal(wind_str):
            if not wind_str: return True
            try:
                return float(re.sub(r'[^0-9.-]', '', wind_str)) <= 2.0
            except:
                return True
        
        new_df = new_df[new_df['wind'].apply(is_wind_legal)]
        
        # Drop duplicates and rows with missing seconds
        new_df = new_df.dropna(subset=['seconds'])
        new_df = new_df.drop_duplicates(subset=['athlete', 'mark', 'date'])
        
        return new_df
