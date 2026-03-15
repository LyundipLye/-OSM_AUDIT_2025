# -*- coding: utf-8 -*-
"""
07_plot_thermal_chart.py
GEE Triple-Satellite (L7+L8+L9) NDBI-Masked LST CSV
-> STL Decomposition + BACI Welch's t-test
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import warnings
from scipy.stats import ttest_ind, mannwhitneyu
from statsmodels.tsa.seasonal import STL

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.figure")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 施工时间节点 (Shepperton Studios 扩建)
CONSTRUCTION_DATE = pd.Timestamp('2019-06-01')


def render_thermodynamic_chart(csv_path, output_image_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {csv_path}")
        return

    # ---------------------------------------------------------
    # 数据验证与预处理
    # ---------------------------------------------------------
    required = ['Sprawl_Zone_Core_mean', 'Control_Zone_mean']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[ERROR] CSV missing columns: {missing}")
        return

    df['system:time_start'] = pd.to_datetime(df['system:time_start'])
    df = df.sort_values('system:time_start').set_index('system:time_start')

    # 直接在原始观测上计算 ΔT
    df_valid = df[['Sprawl_Zone_Core_mean', 'Control_Zone_mean']].dropna()
    df_valid['delta'] = df_valid['Sprawl_Zone_Core_mean'] - df_valid['Control_Zone_mean']
    
    print(f"Total valid observations: {len(df_valid)}")
    print(f"Date range: {df_valid.index.min().date()} to {df_valid.index.max().date()}")

    # ---------------------------------------------------------
    # BACI 统计检验 (Before-After-Control-Impact)
    # 在原始离散观测上执行，不依赖插值
    # ---------------------------------------------------------
    pre = df_valid.loc[:CONSTRUCTION_DATE, 'delta']
    post = df_valid.loc[CONSTRUCTION_DATE:, 'delta']
    
    t_stat, t_p = ttest_ind(pre, post, equal_var=False)
    u_stat, u_p = mannwhitneyu(pre, post, alternative='two-sided')
    
    print(f"\n=== BACI Results ===")
    print(f"Pre-construction (n={len(pre)}): mean ΔT = {pre.mean():+.2f}°C ± {pre.std():.2f}")
    print(f"Post-construction (n={len(post)}): mean ΔT = {post.mean():+.2f}°C ± {post.std():.2f}")
    print(f"Regime shift: {post.mean() - pre.mean():+.2f}°C")
    print(f"Welch's t-test: t={t_stat:.3f}, p={t_p:.4f}")
    print(f"Mann-Whitney U: U={u_stat:.0f}, p={u_p:.4f}")

    # ---------------------------------------------------------
    # STL 分解 (在插值日序列上，用于可视化趋势)
    # ---------------------------------------------------------
    df_sprawl = df[['Sprawl_Zone_Core_mean']].dropna().resample('D').mean().interpolate(method='time')
    df_control = df[['Control_Zone_mean']].dropna().resample('D').mean().interpolate(method='time')
    df_daily = pd.concat([df_sprawl, df_control], axis=1).dropna()
    df_daily.columns = ['LST_Sprawl', 'LST_Control']

    stl_sprawl = STL(df_daily['LST_Sprawl'], period=365, robust=True).fit()
    stl_control = STL(df_daily['LST_Control'], period=365, robust=True).fit()

    sprawl_trend = stl_sprawl.trend
    control_trend = stl_control.trend
    delta_trend = sprawl_trend - control_trend

    # UQ
    has_std = 'Sprawl_Zone_Core_std' in df.columns
    if has_std:
        std_raw = df[['Sprawl_Zone_Core_std']].dropna().resample('D').mean().interpolate(method='time')
        std_smooth = std_raw.iloc[:, 0].rolling(180, min_periods=30, center=True).mean().bfill().ffill()
        std_smooth = std_smooth.reindex(sprawl_trend.index).bfill().ffill()

    # ---------------------------------------------------------
    # 双面板绘图
    # ---------------------------------------------------------
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), dpi=400,
                                    gridspec_kw={'height_ratios': [3, 2]}, sharex=True)

    # ========== 上面板：STL 去季节化趋势 ==========
    ax1.plot(sprawl_trend.index, sprawl_trend, color='#FF8C00', linewidth=3,
             label='Sprawl Zone — Deseasonalized Trend (STL)')
    ax1.plot(control_trend.index, control_trend, color='#33CC33', linewidth=3, linestyle='-.',
             label='Control Zone — Deseasonalized Trend (STL)')

    if has_std:
        ax1.fill_between(sprawl_trend.index, sprawl_trend - std_smooth, sprawl_trend + std_smooth,
                         color='#FF8C00', alpha=0.12, label=r'Spatial Variance ($\pm 1\sigma$ UQ)', linewidth=0)

    ax1.axvline(x=CONSTRUCTION_DATE, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.5)
    ax1.text(CONSTRUCTION_DATE + pd.Timedelta(days=30), sprawl_trend.max() * 0.95,
             'Construction', fontsize=9, fontname='Courier New', color='#AAAAAA')

    ax1.set_ylabel('LST Trend (°C)', fontsize=13, fontname='Courier New', color='#CCCCCC')
    ax1.set_title('Thermodynamic Audit: L7+L8+L9 Triple-Satellite NDBI-Masked BACI Analysis',
                  fontsize=15, fontweight='bold', fontname='Courier New', color='white', pad=15)
    ax1.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False,
               prop={'family': 'Courier New', 'size': 10})
    ax1.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax1.tick_params(axis='both', labelsize=11, colors='#AAAAAA')

    # ========== 下面板：ΔT 散点 + BACI 前后比较 ==========
    # 原始离散观测散点
    ax2.scatter(pre.index, pre.values, color='#66CCFF', alpha=0.6, s=20, zorder=3,
                label=f'Pre-Construction ΔT (n={len(pre)}, μ={pre.mean():+.2f}°C)')
    ax2.scatter(post.index, post.values, color='#FF6666', alpha=0.6, s=20, zorder=3,
                label=f'Post-Construction ΔT (n={len(post)}, μ={post.mean():+.2f}°C)')

    # STL delta trend 线
    ax2.plot(delta_trend.index, delta_trend, color='#FFAA00', linewidth=2, alpha=0.7,
             label=r'$\Delta$ Trend (STL Sprawl − Control)')

    ax2.axhline(y=0, color='#666666', linestyle='-', linewidth=1, alpha=0.4)

    # 前后均值线
    ax2.hlines(y=pre.mean(), xmin=pre.index.min(), xmax=CONSTRUCTION_DATE,
               color='#66CCFF', linewidth=2.5, linestyle='--')
    ax2.hlines(y=post.mean(), xmin=CONSTRUCTION_DATE, xmax=post.index.max(),
               color='#FF6666', linewidth=2.5, linestyle='--')

    ax2.axvline(x=CONSTRUCTION_DATE, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.5)
    ax2.axvspan(df_valid.index.min(), CONSTRUCTION_DATE, alpha=0.04, color='#66CCFF')
    ax2.axvspan(CONSTRUCTION_DATE, df_valid.index.max(), alpha=0.04, color='#FF6666')

    # BACI 结果标注
    sig_t = 'Significant' if t_p < 0.05 else 'Not Significant'
    sig_u = 'Significant' if u_p < 0.05 else 'Not Significant'
    baci_label = (f"BACI Welch's t: p={t_p:.3e} ({sig_t})\n"
                  f"Mann-Whitney U: p={u_p:.3e} ({sig_u})")
    ax2.text(0.02, 0.06, baci_label, transform=ax2.transAxes, fontsize=10,
             fontfamily='Courier New', color='#FFCC00',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#111111', edgecolor='#FFCC00', alpha=0.8))

    ax2.set_ylabel(r'$\Delta$T Sprawl − Control (°C)', fontsize=13, fontname='Courier New', color='#FF8888')
    ax2.set_xlabel('Temporal Axis (Years)', fontsize=13, fontname='Courier New', color='#CCCCCC')
    ax2.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False,
               prop={'family': 'Courier New', 'size': 10})
    ax2.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax2.tick_params(axis='both', labelsize=11, colors='#AAAAAA')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.xaxis.set_major_locator(mdates.YearLocator())

    fig.text(0.98, 0.01,
             'Data: USGS Landsat 7+8+9 (TIRS) | NDBI Impervious Mask | STL-LOESS | Author: H. Li',
             fontsize=9, color='#888888', ha='right', va='bottom', fontfamily='Helvetica')

    plt.tight_layout()
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"\nSAVED: {output_image_path}")
    if os.environ.get('MPLBACKEND') != 'Agg':
        plt.show(block=False)


if __name__ == "__main__":
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_lst.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'thermodynamic_scar_chart.png')
    render_thermodynamic_chart(input_csv, output_png)