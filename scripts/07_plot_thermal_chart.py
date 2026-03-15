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
import warnings
from scipy import stats
from scipy.signal import savgol_filter

# Suppress interactive mode warnings for CLI execution
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.figure")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def render_thermodynamic_chart(csv_path, output_image_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {csv_path}")
        return

    if 'Sprawl_Zone_Core_mean' not in df.columns or 'Sprawl_Zone_Core_std' not in df.columns:
        print("[ERROR] CSV missing '_mean' or '_std' columns. Did you update the GEE LST script for UQ?")
        return

    # 提取 Sprawl Core 进行分析 (包含 Mean 和 StdDev)
    df_sprawl = df[['system:time_start', 'Sprawl_Zone_Core_mean', 'Sprawl_Zone_Core_std']].copy()
    df_sprawl.rename(columns={'Sprawl_Zone_Core_mean': 'LST_Celsius', 'Sprawl_Zone_Core_std': 'LST_Std'}, inplace=True)
    df_sprawl = df_sprawl.dropna(subset=['LST_Celsius'])
    df_sprawl['system:time_start'] = pd.to_datetime(df_sprawl['system:time_start'])
    df_sprawl = df_sprawl.sort_values('system:time_start').set_index('system:time_start')
    
    # 提取 Control Zone (可选)
    if 'Control_Zone_mean' in df.columns:
        df_control = df[['system:time_start', 'Control_Zone_mean', 'Control_Zone_std']].copy()

    print(f"Data points: {len(df_sprawl)}")
    
    # 将 df_sprawl 赋值回 df 保持下游代码兼容
    df = df_sprawl

    # ---------------------------------------------------------
    # 数据预处理与平滑 (Savitzky-Golay)
    # ---------------------------------------------------------
    # 线性插值填补云遮挡导致的缺失值
    # 线性插值填补云遮挡导致的缺失值 (同时插值均值和方差)
    df_daily = df[['LST_Celsius', 'LST_Std']].resample('D').mean().interpolate(method='time').dropna()
    
    # Savitzky-Golay 滤波 (365天窗口，3阶多项式，保留季节性极值)
    df_daily['LST_SG'] = savgol_filter(df_daily['LST_Celsius'], window_length=365, polyorder=3)
    
    # 平滑化空间方差包络带 (UQ)
    df_daily['LST_Std_SG'] = df_daily['LST_Std'].rolling('180D', min_periods=30, center=True).mean().bfill().ffill()
    df_daily['LST_Upper'] = df_daily['LST_SG'] + df_daily['LST_Std_SG']
    df_daily['LST_Lower'] = df_daily['LST_SG'] - df_daily['LST_Std_SG']

    # ---------------------------------------------------------
    # 线性回归与 95% 置信区间 (95% CI)
    # ---------------------------------------------------------
    x_ordinal = df.index.map(pd.Timestamp.toordinal).values
    y = df['LST_Celsius'].values
    
    # 线性拟合 (1阶)
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_ordinal, y)
    y_pred = intercept + slope * x_ordinal
    
    # 计算 95% 置信区间 (自由度 = n - 2)
    t_val = stats.t.ppf(0.975, len(x_ordinal) - 2)
    residuals = y - y_pred
    mse = np.sum(residuals**2) / (len(x_ordinal) - 2)
    x_mean = np.mean(x_ordinal)
    ssx = np.sum((x_ordinal - x_mean)**2)
    se_fit = np.sqrt(mse * (1/len(x_ordinal) + (x_ordinal - x_mean)**2 / ssx))
    
    y_ci_upper = y_pred + t_val * se_fit
    y_ci_lower = y_pred - t_val * se_fit

    net_increase = y_pred[-1] - y_pred[0]
    print(f"Net temperature trend: {'+' if net_increase > 0 else ''}{net_increase:.2f} °C")

    # 绘图
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 8), dpi=400)
    
    ax.scatter(df.index, df['LST_Celsius'], color='#888888', alpha=0.4, s=15, 
               label='Raw LST Observations (Cloud-masked)')
    ax.plot(df_daily.index, df_daily['LST_SG'], color='#FF8C00', linewidth=2.5, alpha=0.9, 
            label='Savitzky-Golay Filtered (Seasonal Noise Removed)')
            
    # Uncertainty Quantification (UQ) Error Band (± 1 StdDev)
    ax.fill_between(df_daily.index, df_daily['LST_Lower'], df_daily['LST_Upper'],
                    color='#FF8C00', alpha=0.15, label=r'Spatial Thermal Variance ($\pm 1\sigma$ UQ)', linewidth=0)
            
    # 新增：合并了净增温和统计显著性的统一趋势线
    ax.plot(df.index, y_pred, color='#FF0000', linestyle='--', linewidth=3, 
            label=f'Structural Trendline (Net Δ: +{net_increase:.2f}°C, p = {p_value:.3e})')
            
    ax.fill_between(df.index, y_ci_lower, y_ci_upper, color='#FFCC00', alpha=0.2, label='95% Confidence Interval (LinReg)')

    ax.set_title('Thermodynamic Spatial Audit: Algorithmic Metabolism in the Sprawl Zone (2015-2023)', 
                 fontsize=18, fontweight='bold', fontname='Courier New', color='white', pad=25)
    ax.set_ylabel('Land Surface Temperature (°C)', fontsize=14, fontname='Courier New', color='#CCCCCC')
    ax.set_xlabel('Temporal Axis (Years)', fontsize=14, fontname='Courier New', color='#CCCCCC')
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.tick_params(axis='both', which='major', labelsize=12, colors='#AAAAAA')
    ax.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False, prop={'family': 'Courier New', 'size': 11})

    # 添加数据源署名
    fig.text(0.98, 0.02, 'Data: USGS Landsat 8 (TIRS) | Projection: EPSG:27700 | Author: H. Li', 
             fontsize=9, color='#888888', ha='right', va='bottom', fontfamily='Helvetica')

    plt.tight_layout()
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"SAVED: {output_image_path}")
    # 仅当在非 headless 环境下才调用 show 
    if os.environ.get('MPLBACKEND') != 'Agg':
        plt.show(block=False)

if __name__ == "__main__":
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_lst.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'thermodynamic_scar_chart.png')
    render_thermodynamic_chart(input_csv, output_png)