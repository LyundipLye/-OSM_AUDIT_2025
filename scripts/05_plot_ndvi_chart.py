"""
05_plot_ndvi_chart.py
GEE 导出的 NDVI CSV -> 365D 滚动均线 + 2018 基线 + Mann-Kendall 趋势检验
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import warnings
import pymannkendall as mk
from scipy.signal import savgol_filter

# Suppress interactive mode warnings for CLI execution
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.figure")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def plot_ndvi_collapse(csv_path, output_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {csv_path}")
        return

    # ---------------------------------------------------------
    # 数据预处理与高级信号滤波 (Savitzky-Golay)
    # ---------------------------------------------------------
    df['system:time_start'] = pd.to_datetime(df['system:time_start'])
    
    # 因为现在的 CSV 是综合输出的，我们需要分离 Sprawl_Core 和 Control_Zone 甚至是敏感分析点
    if 'Sprawl_Zone_Core' not in df.columns:
        print("[ERROR] CSV format invalid. Cannot find 'Sprawl_Zone_Core' column. Did you run the latest GEE script?")
        return
        
    df = df.sort_values('system:time_start').set_index('system:time_start')
    
    # 提取 Sprawl Core 进行衰减绘图
    df_sprawl = df[['Sprawl_Zone_Core']].copy()
    df_sprawl.rename(columns={'Sprawl_Zone_Core': 'NDVI'}, inplace=True)
    
    # 提取 Control Zone 作为对照
    df_control = df[['Control_Zone']].copy()
    
    # 将离散的卫星过境数据重采样为连续的每日时间序列，并线性插值填补云遮挡导致的缺失值
    df_daily = df_sprawl[['NDVI']].resample('D').mean().interpolate(method='time')
    
    # 丢弃头尾全空的无效数据段
    df_daily = df_daily.dropna()
    
    # Savitzky-Golay 滤波 (相比于普通 Rolling Mean，更精确保留植被生长的季节性波峰波谷特征)
    # Window size 365 days, Polynomial order 3
    df_daily['NDVI_SG'] = savgol_filter(df_daily['NDVI'], window_length=365, polyorder=3)

    # 2018 基线 (使用原始NDVI数据计算)
    baseline_2018 = df_daily.loc['2018', 'NDVI'].mean()

    # Mann-Kendall 趋势检验 (对平滑后的数据进行检验)
    mk_result = mk.original_test(df_daily['NDVI_SG'].dropna())
    print(f"Mann-Kendall test: trend={mk_result.trend}, p={mk_result.p:.6f}, "
          f"tau={mk_result.Tau:.4f}, slope={mk_result.slope:.6f}/obs")

    # 动态 Y 轴范围
    ndvi_min_sg = df_daily['NDVI_SG'].min()
    ndvi_min_raw = df_sprawl['NDVI'].min()
    
    y_low = min(ndvi_min_sg * 0.8, baseline_2018 * 0.6, ndvi_min_raw - 0.05)
    y_high = baseline_2018 * 1.2

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 8), dpi=400)

    ax.scatter(df_sprawl.index, df_sprawl['NDVI'], color='#555555', alpha=0.25, s=8, label='Raw (Seasonal Noise)')
    ax.axhline(y=baseline_2018, color='#00FFCC', linestyle='--', linewidth=3, 
               label=f'2018 Baseline (~{baseline_2018:.3f})')
    ax.plot(df_daily.index, df_daily['NDVI_SG'], color='#FF3333', linewidth=5, 
            label='Structural Trend (365D Savitzky-Golay)', alpha=0.95)
    ax.fill_between(df_daily.index, df_daily['NDVI_SG'], baseline_2018, 
                    where=(df_daily['NDVI_SG'] < baseline_2018), 
                    color='#FF3333', alpha=0.25, interpolate=True, label='Permanent Loss')

    # Mann-Kendall 结果标注
    sig = 'Significant' if mk_result.p < 0.05 else 'Not Significant'
    p_str = '< 0.001' if mk_result.p < 0.001 else f'= {mk_result.p:.4f}'
    mk_label = f'Mann-Kendall: τ={mk_result.Tau:.3f}, p {p_str} ({sig})'
    ax.text(0.02, 0.02, mk_label, transform=ax.transAxes, fontsize=11,
            fontfamily='Courier New', color='#FFCC00',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#111111', edgecolor='#FFCC00', alpha=0.8))

    ax.set_ylim(y_low, y_high)
    ax.set_title('Micro-Scale Spatial Audit: NDVI Collapse in Sprawl Zone (2018-2026)', 
                 fontsize=18, fontweight='bold', fontname='Courier New', color='white', pad=25)
    ax.set_ylabel('NDVI (Chlorophyll Reflectance)', fontsize=14, fontname='Courier New', color='#CCCCCC')
    ax.set_xlabel('Temporal Axis (Years)', fontsize=14, fontname='Courier New', color='#CCCCCC')

    ax.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.legend(loc='upper right', frameon=False, prop={'family': 'Courier New', 'size': 11})
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())

    # 添加数据源署名
    fig.text(0.98, 0.02, 'Data: ESA Sentinel-2 (S2_SR_HARMONIZED) | Projection: EPSG:27700 | Author: H. Li', 
             fontsize=9, color='#888888', ha='right', va='bottom', fontfamily='Helvetica')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"SAVED: {output_path}")
    # 仅当在非 headless 环境下才调用 show 
    if os.environ.get('MPLBACKEND') != 'Agg':
        plt.show(block=False)


if __name__ == "__main__":
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_ndvi_2018_2026.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'NDVICollapseChart.png')
    plot_ndvi_collapse(input_csv, output_png)
