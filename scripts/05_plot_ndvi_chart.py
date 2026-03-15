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
    df = df.sort_values('system:time_start').set_index('system:time_start')
        
    # 提取 Sprawl Core 进行衰减绘图 (要求包含 Mean 和 StdDev)
    if 'Sprawl_Zone_Core_mean' not in df.columns or 'Sprawl_Zone_Core_std' not in df.columns:
         print("[ERROR] CSV missing '_mean' or '_std' columns. Did you update the GEE script for UQ?")
         return

    df_sprawl = df[['Sprawl_Zone_Core_mean', 'Sprawl_Zone_Core_std']].copy()
    df_sprawl.rename(columns={'Sprawl_Zone_Core_mean': 'NDVI_Sprawl', 'Sprawl_Zone_Core_std': 'NDVI_Sprawl_Std'}, inplace=True)
    
    # 提取 Control Zone 作为对照
    df_control = df[['Control_Zone_mean', 'Control_Zone_std']].copy()
    df_control.rename(columns={'Control_Zone_mean': 'NDVI_Control', 'Control_Zone_std': 'NDVI_Control_Std'}, inplace=True)
    
    # 将离散的卫星过境数据重采样为连续的每日时间序列，并线性插值填补云遮挡导致的缺失值
    df_daily_sprawl = df_sprawl.resample('D').mean().interpolate(method='time')
    df_daily_control = df_control.resample('D').mean().interpolate(method='time')
    
    df_daily = pd.concat([df_daily_sprawl, df_daily_control], axis=1).dropna()
    df_daily['Delta_NDVI'] = df_daily['NDVI_Sprawl'] - df_daily['NDVI_Control']
    
    # Savitzky-Golay 滤波 (保留植被生长的季节性波峰波谷特征)
    df_daily['Sprawl_SG'] = savgol_filter(df_daily['NDVI_Sprawl'], window_length=365, polyorder=3)
    df_daily['Control_SG'] = savgol_filter(df_daily['NDVI_Control'], window_length=365, polyorder=3)
    df_daily['Delta_SG'] = savgol_filter(df_daily['Delta_NDVI'], window_length=365, polyorder=3)
    
    # 平滑化空间方差包络带 (UQ)
    df_daily['Sprawl_Std_SG'] = df_daily['NDVI_Sprawl_Std'].rolling('180D', min_periods=30, center=True).mean().bfill().ffill()
    df_daily['Sprawl_Upper'] = df_daily['Sprawl_SG'] + df_daily['Sprawl_Std_SG']
    df_daily['Sprawl_Lower'] = df_daily['Sprawl_SG'] - df_daily['Sprawl_Std_SG']

    # 2018 基线 (使用原始 Sprawl NDVI 数据计算)
    baseline_2018 = df_daily.loc['2018', 'NDVI_Sprawl'].mean()

    # 进阶严谨法：季节性 Mann-Kendall (Seasonal MK) 与双重差分 (DiD)
    # 对 Delta_SG 信号执行季节性 MK 检验，完全剥离区域气候变暖和年度周期的干扰
    mk_result = mk.seasonal_test(df_daily['Delta_SG'].dropna(), period=365)
    print(f"DiD Seasonal MK test: trend={mk_result.trend}, p={mk_result.p:.6f}, "
          f"tau={mk_result.Tau:.4f}, slope={mk_result.slope:.6f}/obs")

    # 动态 Y 轴范围
    ndvi_min_sg = df_daily['Sprawl_SG'].min()
    ndvi_min_raw = df_daily['NDVI_Sprawl'].min()
    
    y_low = min(ndvi_min_sg * 0.8, baseline_2018 * 0.6, ndvi_min_raw - 0.05)
    y_high = max(df_daily['Control_SG'].max() * 1.05, baseline_2018 * 1.2)

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 8), dpi=400)

    ax.scatter(df_daily.index, df_daily['NDVI_Sprawl'], color='#555555', alpha=0.25, s=8, label='Raw Sprawl (Seasonal Noise)')
    ax.axhline(y=baseline_2018, color='#00FFCC', linestyle='--', linewidth=3, 
               label=f'2018 Sprawl Baseline (~{baseline_2018:.3f})')
               
    ax.plot(df_daily.index, df_daily['Sprawl_SG'], color='#FF3333', linewidth=4, 
            label='Sprawl Trend (Anthropogenic Collapse)', alpha=0.95)
            
    # Uncertainty Quantification (UQ) Error Band (± 1 StdDev)
    ax.fill_between(df_daily.index, df_daily['Sprawl_Lower'], df_daily['Sprawl_Upper'],
                    color='#FF3333', alpha=0.15, label='Spatial Variance ($\pm 1\sigma$ UQ)', linewidth=0)
            
    # 新增 Control Zone 绿带对照线
    ax.plot(df_daily.index, df_daily['Control_SG'], color='#33CC33', linewidth=3, linestyle='-.',
            label='Control Zone Trend (Climate Baseline)', alpha=0.8)

    # 用浅红色阴影填充低于 2018 基线的部分以突显损失面积
    ax.fill_between(df_daily.index, df_daily['Sprawl_SG'], baseline_2018, 
                    where=(df_daily['Sprawl_SG'] < baseline_2018), 
                    color='#FF3333', alpha=0.25, interpolate=True, label='Net Permanent Loss')

    # Mann-Kendall 结果标注 (DiD + Seasonal)
    sig = 'Significant' if mk_result.p < 0.05 else 'Not Significant'
    p_str = '< 1.000e-100' if mk_result.p == 0.0 else f'= {mk_result.p:.3e}'
    mk_label = r'DiD Seasonal MK ($\Delta$ NDVI): τ={:.3f}, p {} ({})'.format(mk_result.Tau, p_str, sig)
    ax.text(0.02, 0.02, mk_label, transform=ax.transAxes, fontsize=11,
            fontfamily='Courier New', color='#FFCC00',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#111111', edgecolor='#FFCC00', alpha=0.8))

    ax.set_ylim(y_low, y_high)
    ax.set_title('Micro-Scale Spatial Audit: NDVI Collapse in Sprawl Zone (2018-2026)', 
                 fontsize=18, fontweight='bold', fontname='Courier New', color='white', pad=25)
    ax.set_ylabel('NDVI (Chlorophyll Reflectance)', fontsize=14, fontname='Courier New', color='#CCCCCC')
    ax.set_xlabel('Temporal Axis (Years)', fontsize=14, fontname='Courier New', color='#CCCCCC')

    ax.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, prop={'family': 'Courier New', 'size': 11})
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
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_ndvi.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'NDVICollapseChart.png')
    plot_ndvi_collapse(input_csv, output_png)
