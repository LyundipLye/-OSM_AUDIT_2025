# -*- coding: utf-8 -*-
"""
11_plot_evapotranspiration.py
Phase V: Physical Proxy for LST (Metabolic Rift)
Plots Actual Evapotranspiration (ET) collapse to prove latent heat conversion.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import warnings
from scipy.stats import ttest_ind, mannwhitneyu

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.figure")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONSTRUCTION_DATE = pd.Timestamp('2019-06-01')

def _sig_label(p):
    if p < 0.01:
        return 'Highly Significant'
    elif p < 0.05:
        return 'Significant'
    elif p < 0.10:
        return 'Marginal'
    return 'Not Significant'

def render_et_chart(csv_path, output_image_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {csv_path}")
        return

    required = ['Sprawl_ET_mean', 'Control_ET_mean']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[ERROR] ET CSV missing columns: {missing}")
        return

    df['system:time_start'] = pd.to_datetime(df['system:time_start'])
    df = df.sort_values('system:time_start').set_index('system:time_start')
    
    df_valid = df[['Sprawl_ET_mean', 'Control_ET_mean']].dropna()
    df_valid['delta'] = df_valid['Sprawl_ET_mean'] - df_valid['Control_ET_mean']

    # ---------------------------------------------------------
    # 统计 BACI 测试
    # ---------------------------------------------------------
    pre = df_valid.loc[df_valid.index < CONSTRUCTION_DATE, 'delta']
    post = df_valid.loc[df_valid.index >= CONSTRUCTION_DATE, 'delta']

    t_stat, t_p = ttest_ind(pre, post, equal_var=False)
    u_stat, u_p = mannwhitneyu(pre, post, alternative='two-sided')

    print(f"=== Evapotranspiration (ET) BACI Analysis ===")
    print(f"Pre  (n={len(pre)}): mean ΔET = {pre.mean():+.2f} mm/8-day")
    print(f"Post (n={len(post)}): mean ΔET = {post.mean():+.2f} mm/8-day")
    print(f"Shift: {post.mean() - pre.mean():+.2f} mm/8-day | Welch p={t_p:.2e} | MW p={u_p:.2e}")

    # ---------------------------------------------------------
    # 时间平滑处理 (消除强季节性噪音)
    # 因为 MODIS 是 8天合成，1个月大约 4 个点。使用 12 个点（约 3 个月）的滚动平均。
    # ---------------------------------------------------------
    sprawl_smooth = df_valid['Sprawl_ET_mean'].rolling(window=12, center=True, min_periods=4).mean()
    control_smooth = df_valid['Control_ET_mean'].rolling(window=12, center=True, min_periods=4).mean()
    delta_smooth = df_valid['delta'].rolling(window=12, center=True, min_periods=4).mean()

    # ---------------------------------------------------------
    # 绘图逻辑
    # ---------------------------------------------------------
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), dpi=400, 
                                   gridspec_kw={'height_ratios': [2, 1]}, sharex=True)

    # ========== 上面板：绝对 ET 趋势 ==========
    ax1.scatter(df_valid.index, df_valid['Sprawl_ET_mean'], color='#FF8C00', alpha=0.15, s=10)
    ax1.plot(sprawl_smooth.index, sprawl_smooth, color='#FF8C00', linewidth=2.5,
             label='Impact Zone (VP Full) — 3-Month Rolling ET')
    
    ax1.scatter(df_valid.index, df_valid['Control_ET_mean'], color='#33CC33', alpha=0.15, s=10)
    ax1.plot(control_smooth.index, control_smooth, color='#33CC33', linewidth=2.5, linestyle='-.',
             label='Control Zone (Park) — 3-Month Rolling ET')

    ax1.axvline(x=CONSTRUCTION_DATE, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.5)
    ax1.text(CONSTRUCTION_DATE + pd.Timedelta(days=30), ax1.get_ylim()[1] * 0.9,
             'Construction', fontsize=10, fontname='Courier New', color='#AAAAAA')

    ax1.set_title('Metabolic Rift: Latent Heat Flux (Evapotranspiration) Collapse',
                  fontsize=15, fontweight='bold', fontname='Courier New', color='white', pad=15)
    ax1.set_ylabel('Actual ET (mm / 8-day)', fontsize=12, fontname='Courier New', color='#CCCCCC')
    ax1.legend(loc='upper right', frameon=False, prop={'family': 'Courier New', 'size': 10})
    ax1.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax1.tick_params(axis='both', labelsize=10, colors='#AAAAAA')

    # ========== 下面板：Difference-in-Differences (ΔET) ==========
    ax2.plot(delta_smooth.index, delta_smooth, color='#00CCFF', linewidth=2, label='DiD Signal (Sprawl - Control)')
    ax2.axhline(y=0, color='#666666', linestyle='-', linewidth=1, alpha=0.5)
    
    # 绘制水平线 (均值)
    ax2.hlines(y=pre.mean(), xmin=pre.index.min(), xmax=CONSTRUCTION_DATE,
               color='#00CCFF', linewidth=2.5, linestyle='--')
    ax2.hlines(y=post.mean(), xmin=CONSTRUCTION_DATE, xmax=post.index.max(),
               color='#FF4444', linewidth=2.5, linestyle='--')
    
    ax2.axvline(x=CONSTRUCTION_DATE, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.5)
    ax2.axvspan(df_valid.index.min(), CONSTRUCTION_DATE, alpha=0.04, color='#00CCFF')
    ax2.axvspan(CONSTRUCTION_DATE, df_valid.index.max(), alpha=0.04, color='#FF4444')

    # 统计显著性标签
    sig_label = (f"Paired BACI T-Test: Welch p={t_p:.3e} ({_sig_label(t_p)})\n"
                 f"Net Regime Shift in ΔET: {post.mean() - pre.mean():+.2f} mm/8-day")
    ax2.text(0.02, 0.08, sig_label, transform=ax2.transAxes, fontsize=10,
             fontfamily='Courier New', color='#FFCC00',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#111111', edgecolor='#FFCC00', alpha=0.8))

    ax2.set_ylabel(r'$\Delta$ ET (mm / 8-day)', fontsize=12, fontname='Courier New', color='#00CCFF')
    ax2.set_xlabel('Temporal Axis (Years)', fontsize=12, fontname='Courier New', color='#CCCCCC')
    ax2.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax2.tick_params(axis='both', labelsize=10, colors='#AAAAAA')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.xaxis.set_major_locator(mdates.YearLocator())

    fig.text(0.98, 0.005,
             'Data: NASA MODIS MOD16A2GF (500m) | Method: BACI DiD | Author: H. Li',
             fontsize=8, color='#888888', ha='right', va='bottom', fontfamily='Helvetica')

    plt.tight_layout()
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"\\nSAVED ET: {output_image_path}")
    
    if os.environ.get('MPLBACKEND') != 'Agg':
        plt.show(block=False)

if __name__ == "__main__":
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_et.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'evapotranspiration_collapse_chart.png')
    render_et_chart(input_csv, output_png)
