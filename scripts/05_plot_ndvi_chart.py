import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# 1. 读取 GEE CSV
try:
    df = pd.read_csv('ee-chart-1.csv')
except FileNotFoundError:
    print("找不到 ee-chart-1.csv")
    exit()

# 2. 数据清洗
df['system:time_start'] = pd.to_datetime(df['system:time_start'])
df = df.dropna(subset=['NDVI']).sort_values('system:time_start')
df.set_index('system:time_start', inplace=True)

# 3. 365D 平滑 + 2018 基线
df['Structural_Trend'] = df['NDVI'].rolling('365D', min_periods=5).mean()
baseline_2018 = df.loc['2018', 'NDVI'].mean()

# 4. **动态 Y 轴**：基线+20% ~ 最低-20%，完美放大崩溃
ndvi_min = df['Structural_Trend'].min()
y_low = min(ndvi_min * 0.8, baseline_2018 * 0.6)  # 最低点下方 20%
y_high = baseline_2018 * 1.2  # 基线上方 20%
y_range = y_high - y_low

plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(14, 8), dpi=400)  # 更大尺寸

# 5. 绘图（同原）
ax.scatter(df.index, df['NDVI'], color='#555555', alpha=0.25, s=8, label='Raw (Seasonal Noise)')
ax.axhline(y=baseline_2018, color='#00FFCC', linestyle='--', linewidth=3, 
           label=f'2018 Baseline (~{baseline_2018:.3f})')
ax.plot(df.index, df['Structural_Trend'], color='#FF3333', linewidth=5, 
        label='Structural Trend (365D Rolling)', alpha=0.95)
ax.fill_between(df.index, df['Structural_Trend'], baseline_2018, 
                where=(df['Structural_Trend'] < baseline_2018), 
                color='#FF3333', alpha=0.25, interpolate=True, label='Permanent Loss')

# 6. **压迫 Y 轴**：制造垂直断崖
ax.set_ylim(y_low, y_high)
ax.set_title('Micro-Scale Spatial Audit: NDVI Collapse in Sprawl Zone (2018-2026)', 
             fontsize=18, fontweight='bold', fontname='Courier New', color='white', pad=25)
ax.set_ylabel('NDVI (Chlorophyll Reflectance)', fontsize=14, fontname='Courier New', color='#CCCCCC')
ax.set_xlabel('Temporal Axis (Years)', fontsize=14, fontname='Courier New', color='#CCCCCC')

ax.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
ax.legend(loc='upper right', frameon=False, prop={'family': 'Courier New', 'size': 11})

ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.xaxis.set_major_locator(mdates.YearLocator())

plt.tight_layout()
plt.savefig('NDVICollapseChart.png', facecolor='black', dpi=400, bbox_inches='tight')
print(f"SAVED: NDVICollapseChart.png (Y: {y_low:.3f} to {y_high:.3f})")
plt.show()
