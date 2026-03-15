# -*- coding: utf-8 -*-
"""
07b_plot_thermal_sensitivity.py
Sensitivity Analysis (Option A): VP Full Polygon + Warm Season (Apr-Sep)
三面板：STL趋势 + 全年BACI + 暖季专项BACI
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

CONSTRUCTION_DATE = pd.Timestamp('2019-06-01')


def _sig_label(p):
    if p < 0.01:
        return 'Highly Significant'
    elif p < 0.05:
        return 'Significant'
    elif p < 0.10:
        return 'Marginal'
    return 'Not Significant'


def render_thermodynamic_chart(csv_path, output_image_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {csv_path}")
        return

    required = ['Sprawl_Zone_Core_mean', 'Control_Zone_mean']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[ERROR] CSV missing columns: {missing}")
        return

    df['system:time_start'] = pd.to_datetime(df['system:time_start'])
    df = df.sort_values('system:time_start').set_index('system:time_start')

    df_valid = df[['Sprawl_Zone_Core_mean', 'Control_Zone_mean']].dropna()
    df_valid['delta'] = df_valid['Sprawl_Zone_Core_mean'] - df_valid['Control_Zone_mean']

    print(f"Total valid observations: {len(df_valid)}")

    # ---------------------------------------------------------
    # 全年 BACI
    # ---------------------------------------------------------
    pre = df_valid.loc[:CONSTRUCTION_DATE, 'delta']
    post = df_valid.loc[CONSTRUCTION_DATE:, 'delta']

    t_stat, t_p = ttest_ind(pre, post, equal_var=False)
    u_stat, u_p = mannwhitneyu(pre, post, alternative='two-sided')

    print(f"\n=== Full-Year BACI ===")
    print(f"Pre  (n={len(pre)}): mean ΔT = {pre.mean():+.2f}°C ± {pre.std():.2f}")
    print(f"Post (n={len(post)}): mean ΔT = {post.mean():+.2f}°C ± {post.std():.2f}")
    print(f"Shift: {post.mean() - pre.mean():+.2f}°C | Welch p={t_p:.4f} | MW p={u_p:.4f}")

    # ---------------------------------------------------------
    # 暖季 BACI (Apr-Sep)
    # ---------------------------------------------------------
    summer = df_valid[df_valid.index.month.isin([4, 5, 6, 7, 8, 9])]
    s_pre = summer.loc[:CONSTRUCTION_DATE, 'delta']
    s_post = summer.loc[CONSTRUCTION_DATE:, 'delta']

    s_t_stat, s_t_p = ttest_ind(s_pre, s_post, equal_var=False)
    s_u_stat, s_u_p = mannwhitneyu(s_pre, s_post, alternative='two-sided')

    print(f"\n=== Warm-Season BACI (Apr-Sep) ===")
    print(f"Pre  (n={len(s_pre)}): mean ΔT = {s_pre.mean():+.2f}°C ± {s_pre.std():.2f}")
    print(f"Post (n={len(s_post)}): mean ΔT = {s_post.mean():+.2f}°C ± {s_post.std():.2f}")
    print(f"Shift: {s_post.mean() - s_pre.mean():+.2f}°C | Welch p={s_t_p:.4f} | MW p={s_u_p:.4f}")

    # ---------------------------------------------------------
    # STL 分解
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

    has_std = 'Sprawl_Zone_Core_std' in df.columns
    if has_std:
        std_raw = df[['Sprawl_Zone_Core_std']].dropna().resample('D').mean().interpolate(method='time')
        std_smooth = std_raw.iloc[:, 0].rolling(180, min_periods=30, center=True).mean().bfill().ffill()
        std_smooth = std_smooth.reindex(sprawl_trend.index).bfill().ffill()

    # ---------------------------------------------------------
    # 三面板绘图
    # ---------------------------------------------------------
    plt.style.use('dark_background')
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 14), dpi=400,
                                         gridspec_kw={'height_ratios': [3, 2, 2]}, sharex=True)

    # ========== 上面板：STL 趋势 ==========
    ax1.plot(sprawl_trend.index, sprawl_trend, color='#FF8C00', linewidth=3,
             label='Impact Zone (VP Full Polygon) — STL Trend')
    ax1.plot(control_trend.index, control_trend, color='#33CC33', linewidth=3, linestyle='-.',
             label='Control Zone (Park) — STL Trend')
    if has_std:
        ax1.fill_between(sprawl_trend.index, sprawl_trend - std_smooth, sprawl_trend + std_smooth,
                         color='#FF8C00', alpha=0.12, label=r'Spatial Variance ($\pm 1\sigma$)', linewidth=0)
    ax1.axvline(x=CONSTRUCTION_DATE, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.5)
    ax1.text(CONSTRUCTION_DATE + pd.Timedelta(days=30), sprawl_trend.max() * 0.95,
             'Construction', fontsize=9, fontname='Courier New', color='#AAAAAA')
    ax1.set_ylabel('LST Trend (°C)', fontsize=12, fontname='Courier New', color='#CCCCCC')
    ax1.set_title('Paired BACI Sensitivity Analysis: VP Full Polygon (L7+L8+L9)',
                  fontsize=15, fontweight='bold', fontname='Courier New', color='white', pad=15)
    ax1.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False,
               prop={'family': 'Courier New', 'size': 9})
    ax1.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax1.tick_params(axis='both', labelsize=10, colors='#AAAAAA')

    # ========== 中面板：全年 BACI ==========
    ax2.scatter(pre.index, pre.values, color='#66CCFF', alpha=0.5, s=15, zorder=3,
                label=f'Pre ΔT (n={len(pre)}, μ={pre.mean():+.2f}°C)')
    ax2.scatter(post.index, post.values, color='#FF6666', alpha=0.5, s=15, zorder=3,
                label=f'Post ΔT (n={len(post)}, μ={post.mean():+.2f}°C)')
    ax2.plot(delta_trend.index, delta_trend, color='#FFAA00', linewidth=1.5, alpha=0.6)
    ax2.axhline(y=0, color='#666666', linestyle='-', linewidth=1, alpha=0.4)
    ax2.hlines(y=pre.mean(), xmin=pre.index.min(), xmax=CONSTRUCTION_DATE,
               color='#66CCFF', linewidth=2.5, linestyle='--')
    ax2.hlines(y=post.mean(), xmin=CONSTRUCTION_DATE, xmax=post.index.max(),
               color='#FF6666', linewidth=2.5, linestyle='--')
    ax2.axvline(x=CONSTRUCTION_DATE, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.5)
    ax2.axvspan(df_valid.index.min(), CONSTRUCTION_DATE, alpha=0.04, color='#66CCFF')
    ax2.axvspan(CONSTRUCTION_DATE, df_valid.index.max(), alpha=0.04, color='#FF6666')

    fy_label = (f"Full-Year BACI: Welch p={t_p:.3e} ({_sig_label(t_p)}), "
                f"MW p={u_p:.3e} ({_sig_label(u_p)})")
    ax2.text(0.02, 0.06, fy_label, transform=ax2.transAxes, fontsize=9,
             fontfamily='Courier New', color='#FFCC00',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#111111', edgecolor='#FFCC00', alpha=0.8))
    ax2.set_ylabel(r'$\Delta$T Full-Year (°C)', fontsize=12, fontname='Courier New', color='#FF8888')
    ax2.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False,
               prop={'family': 'Courier New', 'size': 9})
    ax2.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax2.tick_params(axis='both', labelsize=10, colors='#AAAAAA')

    # ========== 下面板：暖季 BACI (Apr-Sep) ==========
    ax3.scatter(s_pre.index, s_pre.values, color='#66CCFF', alpha=0.7, s=40, marker='D', zorder=3,
                edgecolors='white', linewidth=0.5,
                label=f'Pre Warm-Season ΔT (n={len(s_pre)}, μ={s_pre.mean():+.2f}°C)')
    ax3.scatter(s_post.index, s_post.values, color='#FF4444', alpha=0.7, s=40, marker='D', zorder=3,
                edgecolors='white', linewidth=0.5,
                label=f'Post Warm-Season ΔT (n={len(s_post)}, μ={s_post.mean():+.2f}°C)')
    ax3.axhline(y=0, color='#666666', linestyle='-', linewidth=1, alpha=0.4)
    ax3.hlines(y=s_pre.mean(), xmin=s_pre.index.min(), xmax=CONSTRUCTION_DATE,
               color='#66CCFF', linewidth=2.5, linestyle='--')
    ax3.hlines(y=s_post.mean(), xmin=CONSTRUCTION_DATE, xmax=s_post.index.max(),
               color='#FF4444', linewidth=2.5, linestyle='--')
    ax3.axvline(x=CONSTRUCTION_DATE, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.5)
    ax3.axvspan(df_valid.index.min(), CONSTRUCTION_DATE, alpha=0.04, color='#66CCFF')
    ax3.axvspan(CONSTRUCTION_DATE, df_valid.index.max(), alpha=0.04, color='#FF6666')

    # 箭头标注 regime shift
    shift = s_post.mean() - s_pre.mean()
    mid_x = CONSTRUCTION_DATE + pd.Timedelta(days=365*2)
    ax3.annotate(f'UHI Shift: {shift:+.2f}°C',
                 xy=(mid_x, s_post.mean()), xytext=(mid_x, s_post.mean() + 2),
                 fontsize=11, fontweight='bold', color='#FF4444', fontfamily='Courier New',
                 arrowprops=dict(arrowstyle='->', color='#FF4444', lw=2),
                 ha='center')

    sj_label = (f"Warm-Season BACI (Apr-Sep): Welch p={s_t_p:.3e} ({_sig_label(s_t_p)}), "
                f"MW p={s_u_p:.3e} ({_sig_label(s_u_p)})")
    ax3.text(0.02, 0.06, sj_label, transform=ax3.transAxes, fontsize=9,
             fontfamily='Courier New', color='#00FF88',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#111111', edgecolor='#00FF88', alpha=0.8))
    ax3.set_ylabel(r'$\Delta$T Warm Season (°C)', fontsize=12, fontname='Courier New', color='#FF8888')
    ax3.set_xlabel('Temporal Axis (Years)', fontsize=12, fontname='Courier New', color='#CCCCCC')
    ax3.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False,
               prop={'family': 'Courier New', 'size': 9})
    ax3.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax3.tick_params(axis='both', labelsize=10, colors='#AAAAAA')
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax3.xaxis.set_major_locator(mdates.YearLocator())

    fig.text(0.98, 0.005,
             'Data: USGS Landsat 7+8+9 (TIRS) | Paired BACI — No NDBI Mask | STL-LOESS | Author: H. Li',
             fontsize=8, color='#888888', ha='right', va='bottom', fontfamily='Helvetica')

    plt.tight_layout()
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"\nSAVED: {output_image_path}")
    if os.environ.get('MPLBACKEND') != 'Agg':
        plt.show(block=False)


if __name__ == "__main__":
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_lst_sensitivity.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'thermodynamic_scar_sensitivity_chart.png')
    render_thermodynamic_chart(input_csv, output_png)