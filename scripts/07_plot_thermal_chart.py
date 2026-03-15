# -*- coding: utf-8 -*-
"""
07_plot_thermal_chart.py
GEE 导出的 LST CSV -> 365D 滚动均线 + 线性回归趋势线
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def render_thermodynamic_chart(csv_path, output_image_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {csv_path}")
        return

    df = df.dropna(subset=['LST_Celsius'])
    df['system:time_start'] = pd.to_datetime(df['system:time_start'])
    df = df.sort_values('system:time_start').set_index('system:time_start')

    print(f"Data points: {len(df)}")

    # 365D 滚动均线（消除季节性噪音）
    df['Rolling_Mean'] = df['LST_Celsius'].rolling('365D', min_periods=1).mean()

    # 线性回归趋势线 (y = mx + c)
    x_num = mdates.date2num(df.index)
    z = np.polyfit(x_num, df['LST_Celsius'].values, 1)
    p = np.poly1d(z)
    df['Trendline'] = p(x_num)

    net_increase = df['Trendline'].iloc[-1] - df['Trendline'].iloc[0]
    print(f"Net temperature trend: {'+' if net_increase > 0 else ''}{net_increase:.2f} °C")

    # 绘图
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    
    ax.scatter(df.index, df['LST_Celsius'], color='#888888', alpha=0.4, s=15, 
               label='Raw LST Observations (Cloud-masked)')
    ax.plot(df.index, df['Rolling_Mean'], color='#FF8C00', linewidth=2.5, alpha=0.9, 
            label='365-Day Rolling Mean (Seasonal Noise Removed)')
    ax.plot(df.index, df['Trendline'], color='#FF0000', linestyle='--', linewidth=3, 
            label=f'Structural Trendline (Net Δ: +{net_increase:.2f}°C)')

    ax.set_title('Thermodynamic Spatial Audit: Algorithmic Metabolism in the Sprawl Zone (2015-2023)', 
                 fontsize=18, fontweight='bold', color='white', pad=20, fontfamily='monospace')
    ax.set_ylabel('Land Surface Temperature (°C)', fontsize=14, fontweight='bold', color='#CCCCCC')
    ax.set_xlabel('Temporal Axis (Years)', fontsize=14, fontweight='bold', color='#CCCCCC')
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.tick_params(axis='both', which='major', labelsize=12, colors='#AAAAAA')
    ax.grid(True, color='#333333', linestyle=':', linewidth=1)
    ax.legend(loc='upper left', fontsize=12, frameon=True, facecolor='#111111', edgecolor='#444444')

    plt.tight_layout()
    plt.savefig(output_image_path, facecolor=fig.get_facecolor(), edgecolor='none')
    print(f"SAVED: {output_image_path}")
    plt.show()

if __name__ == "__main__":
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'thermodynamic_scar_chart.png')
    render_thermodynamic_chart(input_csv, output_png)