import nbformat as nbf
import os

# Physical Floors (Caps) for tapering growth
caps = {
    '100m': 9.45,
    '200m': 18.90,
    '400m': 42.50,
    '800m': 99.50,
    '1500m': 204.00,
    '5000m': 745.00,
    '10000m': 1550.00,
    'Marathon': 7020.00,
    'Steeplechase': 465.00
}

def update_notebook(file_path, event_name, is_sprint):
    with open(file_path, 'r', encoding='utf-8') as f:
        nb = nbf.read(f, as_version=4)
    
    # Define EDA cell
    markdown_eda = nbf.v4.new_markdown_cell(f"## 3. Visual Exploratory Data Analysis\n\nWe analyze the trends, distributions, and depth of the {event_name} over the past 50 years.")
    if 'id' in markdown_eda: del markdown_eda['id']
    
    eda_code = f"""
plt.figure(figsize=(15, 30))

# Plot 1: Time Series Trend
plt.subplot(6, 1, 1)
sns.lineplot(data=stats_df, x='year', y='best', label='Yearly Best', color='red', marker='o')
sns.lineplot(data=stats_df, x='year', y='top_10_avg', label='Top 10 Average', color='blue', linestyle='--')
plt.title(\"{event_name}: Historical Performance Trend (1974-2024)\")
plt.gca().invert_yaxis()
plt.ylabel(\"Time (seconds)\")

# Plot 2: Decadal Boxplot
plt.subplot(6, 1, 2)
clean_df['decade'] = (clean_df['year'] // 10) * 10
sns.boxplot(data=clean_df, x='decade', y='seconds')
plt.title(\"{event_name}: Distribution of Marks by Decade\")
plt.gca().invert_yaxis()
plt.ylabel(\"Time (seconds)\")

# Plot 3: Summary Statistics (Mean vs Median)
plt.subplot(6, 1, 3)
plt.plot(stats_df['year'], stats_df['median'], label='Median', color='orange')
plt.plot(stats_df['year'], stats_df['top_10_avg'], label='Top 10 Avg', color='blue')
plt.title(\"{event_name}: Median vs Top 10 Average\")
plt.gca().invert_yaxis()
plt.ylabel(\"Time (seconds)\")
plt.legend()

# Plot 4: Performance Depth (Gap between Rank 1 and 50)
plt.subplot(6, 1, 4)
depth = clean_df.groupby('year').apply(lambda x: x['seconds'].nsmallest(min(50, len(x))).max() - x['seconds'].min())
plt.plot(depth.index, depth.values, color='purple', marker='x')
plt.title(\"{event_name}: Performance Depth (Gap between Rank 1 and Rank 50)\")
plt.ylabel(\"Seconds Gap\")

# Plot 5: Correlation Heatmap
plt.subplot(6, 1, 5)
sns.heatmap(stats_df[['best', 'top_10_avg', 'median', 'count']].corr(), annot=True, cmap='coolwarm')
plt.title(\"Correlation of Yearly Metrics\")

# Plot 6: Cumulative Improvement
plt.subplot(6, 1, 6)
improv = (stats_df['best'].iloc[0] - stats_df['best']) / stats_df['best'].iloc[0] * 100
plt.fill_between(stats_df['year'], improv, color='green', alpha=0.3)
plt.plot(stats_df['year'], improv, color='green')
plt.title(\"{event_name}: Cumulative Improvement % since 1974\")
plt.ylabel(\"% Improved\")

plt.tight_layout()
plt.show()
"""
    if is_sprint:
        eda_code += f"""
# Plot 7: Wind Impact (Sprint specific)
plt.figure(figsize=(10, 6))
sns.scatterplot(data=clean_df[clean_df['wind'] != '0.0'], x='wind', y='seconds', alpha=0.3)
plt.title(\"{event_name}: Impact of Wind on Performance\")
plt.gca().invert_yaxis()
plt.show()
"""
    code_eda = nbf.v4.new_code_cell(eda_code.strip())
    if 'id' in code_eda: del code_eda['id']

    # Define Projection cell
    markdown_proj = nbf.v4.new_markdown_cell(f"## 4. Performance Projections (Next 20 Years)\n\nUsing the Prophet model with **Logistic Growth** and **Rolling Window Conformal Prediction** to forecast where the {event_name} World Record might be in 2046.")
    if 'id' in markdown_proj: del markdown_proj['id']
    
    proj_code = f"""
forecaster = TrackForecaster(stats_df, cap={caps[event_name]})
forecast = forecaster.forecast(periods=20)

plt.figure(figsize=(14, 7))
plt.plot(stats_df['year'], stats_df['best'], 'ko', label='Historical Data')
plt.plot(pd.to_datetime(forecast['ds']).dt.year, forecast['yhat'], color='green', label='Prophet Projection (Tapered)')
plt.fill_between(pd.to_datetime(forecast['ds']).dt.year, forecast['yhat_lower'], forecast['yhat_upper'], color='green', alpha=0.2, label='Conformal Interval')

plt.title(\"{event_name} World Record Projection (2026-2046)\", fontsize=16)
plt.ylabel('Time (seconds)')
plt.xlabel('Year')
plt.gca().invert_yaxis()
plt.legend()
plt.show()

proj_2046 = forecast.iloc[-1]['yhat']
print(f\"Projected {event_name} WR in 2046: {{forecaster.seconds_to_str(proj_2046)}}\")
"""
    code_proj = nbf.v4.new_code_cell(proj_code.strip())
    if 'id' in code_proj: del code_proj['id']

    # Rebuild notebook cells
    new_cells = []
    section_count = 0
    for cell in nb.cells:
        if cell.cell_type == 'markdown' and ('## 1.' in cell.source or '## 2.' in cell.source):
            new_cells.append(cell)
            section_count += 1
        elif section_count < 2 or cell.cell_type == 'code':
            if section_count <= 2:
                new_cells.append(cell)
        
        if section_count == 2 and cell.cell_type == 'code':
            new_cells.append(markdown_eda)
            new_cells.append(code_eda)
            new_cells.append(markdown_proj)
            new_cells.append(code_proj)
            break
            
    nb.cells = new_cells
    
    with open(file_path, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)

notebooks = [
    ('notebooks/analysis.ipynb', '100m', True),
    ('notebooks/200-metres_analysis.ipynb', '200m', True),
    ('notebooks/400-metres_analysis.ipynb', '400m', False),
    ('notebooks/800-metres_analysis.ipynb', '800m', False),
    ('notebooks/1500-metres_analysis.ipynb', '1500m', False),
    ('notebooks/5000-metres_analysis.ipynb', '5000m', False),
    ('notebooks/10000-metres_analysis.ipynb', '10000m', False),
    ('notebooks/marathon_analysis.ipynb', 'Marathon', False),
    ('notebooks/3000-metres-steeplechase_analysis.ipynb', 'Steeplechase', False)
]

for path, event, is_sprint in notebooks:
    if os.path.exists(path):
        print(f"Updating {path}...")
        update_notebook(path, event, is_sprint)
