import json
import os

events = {
    '200-metres': {'base_time': 20.0, 'improvement_rate': 0.012},
    '400-metres': {'base_time': 44.5, 'improvement_rate': 0.02},
    '800-metres': {'base_time': 103.0, 'improvement_rate': 0.05},
    '1500-metres': {'base_time': 213.0, 'improvement_rate': 0.1},
    '5000-metres': {'base_time': 790.0, 'improvement_rate': 0.5},
    '10000-metres': {'base_time': 1650.0, 'improvement_rate': 1.0},
    'marathon': {'base_time': 7680.0, 'improvement_rate': 5.0},
    '3000-metres-steeplechase': {'base_time': 490.0, 'improvement_rate': 0.2}
}

notebook_template = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# {event_name} Analysis\n",
    "\n",
    "Historical analysis and future projections for the {event_name}."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import numpy as np\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "import sys\n",
    "import os\n",
    "\n",
    "# Add src to path\n",
    "sys.path.append(os.path.abspath('../'))\n",
    "\n",
    "from src.data_cleaner import DataCleaner\n",
    "from src.analysis_engine import AnalysisEngine\n",
    "from src.forecaster import TrackForecaster\n",
    "\n",
    "sns.set_theme(style='whitegrid')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Data Generation (Synthetic)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "start_year = 1980\n",
    "end_year = 2023\n",
    "years = list(range(start_year, end_year + 1))\n",
    "data = []\n",
    "base_time = {base_time}\n",
    "improvement_rate = {improvement_rate}\n",
    "\n",
    "np.random.seed(42)\n",
    "for y in years:\n",
    "    # Annual improvement trend\n",
    "    year_best = base_time - (y - start_year) * improvement_rate + (np.random.random() * (improvement_rate * 5))\n",
    "    for _ in range(50):\n",
    "        data.append({\n",
    "            'year': y,\n",
    "            'mark': f'{year_best + np.random.random() * (base_time * 0.05):.2f}',\n",
    "            'wind': '1.0',\n",
    "            'athlete': f'Athlete_{np.random.randint(1000)}',\n",
    "            'date': f'{y}-07-15',\n",
    "            'event': '{event_id}'\n",
    "        })\n",
    "\n",
    "df = pd.DataFrame(data)\n",
    "df.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Analysis"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "cleaner = DataCleaner()\n",
    "clean_df = cleaner.clean_scraped_data(df)\n",
    "\n",
    "engine = AnalysisEngine(clean_df)\n",
    "stats_df = engine.get_yearly_stats()\n",
    "stats_df.tail()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. Projection"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "forecaster = TrackForecaster(stats_df)\n",
    "forecast = forecaster.forecast(periods=20)\n",
    "\n",
    "plt.figure(figsize=(14, 7))\n",
    "plt.plot(stats_df['year'], stats_df['best'], 'ko', label='Historical Data')\n",
    "plt.plot(pd.to_datetime(forecast['ds']).dt.year, forecast['yhat'], color='green', label='Prophet Projection')\n",
    "plt.fill_between(pd.to_datetime(forecast['ds']).dt.year, forecast['yhat_lower'], forecast['yhat_upper'], color='green', alpha=0.2, label='Conformal Interval')\n",
    "\n",
    "plt.title(f'{event_name} World Record Projection', fontsize=16)\n",
    "plt.ylabel('Time (seconds)')\n",
    "plt.xlabel('Year')\n",
    "plt.gca().invert_yaxis()\n",
    "plt.legend()\n",
    "plt.show()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.10.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

os.makedirs('notebooks', exist_ok=True)

for event_id, params in events.items():
    event_name = event_id.replace('-', ' ').title()
    nb_content = json.loads(json.dumps(notebook_template))
    nb_content['cells'][0]['source'][0] = nb_content['cells'][0]['source'][0].replace('{event_name}', event_name)
    nb_content['cells'][0]['source'][2] = nb_content['cells'][0]['source'][2].replace('{event_name}', event_name)
    
    source = nb_content['cells'][3]['source']
    new_source = []
    for line in source:
        new_source.append(line.replace('{base_time}', str(params['base_time']))
                              .replace('{improvement_rate}', str(params['improvement_rate']))
                              .replace('{event_id}', event_id))
    nb_content['cells'][3]['source'] = new_source
    
    nb_content['cells'][7]['source'][8] = nb_content['cells'][7]['source'][8].replace('{event_name}', event_name)
    
    file_path = f'notebooks/{event_id}_analysis.ipynb'
    with open(file_path, 'w') as f:
        json.dump(nb_content, f, indent=1)
    print(f'Created {file_path}')
