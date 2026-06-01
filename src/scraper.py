import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import List, Dict

class WorldAthleticsScraper:
    BASE_URL = "https://worldathletics.org/records/toplists"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def get_top_list_url(self, event_code: str, year: int, gender: str = "men") -> str:
        # Example URL: https://worldathletics.org/records/toplists/sprints/100-metres/outdoor/men/senior/2023
        # Note: Actual URL structure may vary, need to verify on live site.
        return f"{self.BASE_URL}/sprints/{event_code}/outdoor/{gender}/senior/{year}"

    def scrape_year(self, event_code: str, year: int) -> pd.DataFrame:
        url = self.get_top_list_url(event_code, year)
        print(f"Scraping {event_code} for {year}...")
        
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            print(f"Failed to fetch data for {year}")
            return pd.DataFrame()

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'records-table'})
        
        if not table:
            return pd.DataFrame()

        # Parse table headers and rows
        # This is a placeholder for actual parsing logic
        data = []
        rows = table.find_all('tr')
        for row in rows[1:]: # Skip header
            cols = row.find_all('td')
            if len(cols) > 0:
                data.append({
                    "rank": cols[0].text.strip(),
                    "mark": cols[1].text.strip(),
                    "wind": cols[2].text.strip() if len(cols) > 2 else None,
                    "athlete": cols[3].text.strip() if len(cols) > 3 else None,
                    "date": cols[8].text.strip() if len(cols) > 8 else None,
                    "year": year,
                    "event": event_code
                })
        
        return pd.DataFrame(data)

    def scrape_historical(self, event_code: str, start_year: int, end_year: int) -> pd.DataFrame:
        all_data = []
        for year in range(start_year, end_year + 1):
            df = self.scrape_year(event_code, year)
            if not df.empty:
                all_data.append(df)
            time.sleep(1) # Polite scraping
        
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
