import nbformat as nbf
import os

def update_notebook(file_path, event_name, is_sprint):
    with open(file_path, 'r', encoding='utf-8') as f:
        nb = nbf.read(f, as_version=4)
    
    # Define new cells
    markdown_cell = nbf.v4.new_markdown_cell(f"## 3. Visual Exploratory Data Analysis\n\nWe analyze the trends, distributions, and depth of the {event_name} over the past 50 years.")
    
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
    
    code_cell = nbf.v4.new_code_cell(eda_code.strip())
    
    # Logic to find insertion point
    new_cells = []
    inserted = False
    skip_next_code = False
    
    for i, cell in enumerate(nb.cells):
        if skip_next_code:
            if cell.cell_type == 'code':
                skip_next_code = False
                continue
            skip_next_code = False
            
        # Check if this is an existing EDA/Visualization section we want to replace
        if cell.cell_type == 'markdown' and ('3. Visual' in cell.source or '3. Visualizing' in cell.source):
            new_cells.append(markdown_cell)
            new_cells.append(code_cell)
            inserted = True
            skip_next_code = True # Skip the old code cell that followed
            continue
            
        # Check if we reached the projection section and haven't inserted yet
        if not inserted and cell.cell_type == 'markdown' and ('Projection' in cell.source or '4. Performance' in cell.source):
            new_cells.append(markdown_cell)
            new_cells.append(code_cell)
            inserted = True
            
        new_cells.append(cell)

    if not inserted:
        new_cells.append(markdown_cell)
        new_cells.append(code_cell)

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
