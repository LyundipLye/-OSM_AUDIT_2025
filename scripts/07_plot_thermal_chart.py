# -*- coding: utf-8 -*-
"""
07_plot_thermal_chart.py
GEE 导出的 LST CSV -> STL 时间序列分解 + DiD Mann-Kendall 趋势检验
双面板可视化：上层趋势对比 + 下层 DiD 信号放大
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import warnings
import pymannkendall as mk
from statsmodels.tsa.seasonal import STL

# Suppress interactive mode warnings for CLI execution
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.figure")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def render_thermodynamic_chart(csv_path, output_image_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {csv_path}")
        return

    # ---------------------------------------------------------
    # 数据验证
    # ---------------------------------------------------------
    required = ['Sprawl_Zone_Core_mean', 'Sprawl_Zone_Core_std',
                'Control_Zone_mean', 'Control_Zone_std']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[ERROR] CSV missing columns: {missing}. Did you update the GEE LST script?")
        return

    # ---------------------------------------------------------
    # 数据预处理
    # ---------------------------------------------------------
    df['system:time_start'] = pd.to_datetime(df['system:time_start'])
    df = df.sort_values('system:time_start').set_index('system:time_start')

    df_sprawl = df[['Sprawl_Zone_Core_mean', 'Sprawl_Zone_Core_std']].copy()
    df_sprawl.rename(columns={
        'Sprawl_Zone_Core_mean': 'LST_Sprawl',
        'Sprawl_Zone_Core_std': 'LST_Sprawl_Std'
    }, inplace=True)

    df_control = df[['Control_Zone_mean', 'Control_Zone_std']].copy()
    df_control.rename(columns={
        'Control_Zone_mean': 'LST_Control',
        'Control_Zone_std': 'LST_Control_Std'
    }, inplace=True)

    df_daily_sprawl = df_sprawl.resample('D').mean().interpolate(method='time')
    df_daily_control = df_control.resample('D').mean().interpolate(method='time')
    df_daily = pd.concat([df_daily_sprawl, df_daily_control], axis=1).dropna()

    print(f"Raw data points: {len(df_sprawl.dropna())}")
    print(f"Interpolated daily points: {len(df_daily)}")

    # ---------------------------------------------------------
    # STL 分解
    # ---------------------------------------------------------
    stl_sprawl = STL(df_daily['LST_Sprawl'], period=365, robust=True).fit()
    stl_control = STL(df_daily['LST_Control'], period=365, robust=True).fit()

    sprawl_trend = stl_sprawl.trend
    control_trend = stl_control.trend
    delta_trend = sprawl_trend - control_trend

    # ---------------------------------------------------------
    # Mann-Kendall 检验
    # ---------------------------------------------------------
    mk_result = mk.original_test(delta_trend.dropna())
    print(f"STL DiD MK test: trend={mk_result.trend}, p={mk_result.p:.6f}, "
          f"tau={mk_result.Tau:.4f}, slope={mk_result.slope:.6f}/day")

    net_did = delta_trend.iloc[-1] - delta_trend.iloc[0]
    print(f"Net DiD trend shift: {net_did:+.2f} °C")

    # 施工时间节点 (Shepperton Studios 扩建 ~2019)
    construction_date = pd.Timestamp('2019-06-01')

    # 前后期均值
    pre_mean = delta_trend.loc[:construction_date].mean()
    post_mean = delta_trend.loc[construction_date:].mean()
    print(f"Pre-construction mean ΔT: {pre_mean:+.2f} °C")
    print(f"Post-construction mean ΔT: {post_mean:+.2f} °C")
    print(f"Regime shift: {post_mean - pre_mean:+.2f} °C")

    # UQ
    std_smooth = df_daily['LST_Sprawl_Std'].rolling('180D', min_periods=30, center=True).mean().bfill().ffill()

    # ---------------------------------------------------------
    # 双面板绘图
    # ---------------------------------------------------------
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), dpi=400,
                                    gridspec_kw={'height_ratios': [3, 2]}, sharex=True)

    # ========== 上面板：去季节化趋势对比 ==========
    ax1.plot(sprawl_trend.index, sprawl_trend, color='#FF8C00', linewidth=3,
             label='Sprawl Zone — Deseasonalized Trend (STL)')
    ax1.plot(control_trend.index, control_trend, color='#33CC33', linewidth=3, linestyle='-.',
             label='Control Zone — Deseasonalized Trend (STL)')

    # UQ 误差带
    ax1.fill_between(sprawl_trend.index, sprawl_trend - std_smooth, sprawl_trend + std_smooth,
                     color='#FF8C00', alpha=0.15, label=r'Spatial Thermal Variance ($\pm 1\sigma$ UQ)', linewidth=0)

    # 施工时间标线
    ax1.axvline(x=construction_date, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.6)
    ax1.text(construction_date, ax1.get_ylim()[0] if ax1.get_ylim()[0] != 0 else 15,
             '  Construction\n  Phase', fontsize=9, fontname='Courier New',
             color='#AAAAAA', va='bottom')

    ax1.set_ylabel('LST Trend (°C)', fontsize=13, fontname='Courier New', color='#CCCCCC')
    ax1.set_title('Thermodynamic Spatial Audit: STL-Decomposed UHI Trend (2015-2026)',
                  fontsize=16, fontweight='bold', fontname='Courier New', color='white', pad=15)
    ax1.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False,
               prop={'family': 'Courier New', 'size': 10})
    ax1.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax1.tick_params(axis='both', labelsize=11, colors='#AAAAAA')

    # ========== 下面板：ΔTrend (DiD 信号放大) ==========
    ax2.plot(delta_trend.index, delta_trend, color='#FF4444', linewidth=2.5,
             label=r'$\Delta$ Trend (Sprawl − Control)')
    ax2.axhline(y=0, color='#666666', linestyle='-', linewidth=1, alpha=0.5)

    # 前后期均值水平线
    pre_idx = delta_trend.loc[:construction_date].index
    post_idx = delta_trend.loc[construction_date:].index
    ax2.hlines(y=pre_mean, xmin=pre_idx[0], xmax=pre_idx[-1],
               color='#66CCFF', linewidth=2.5, linestyle='--', label=f'Pre-Construction Mean ({pre_mean:+.2f}°C)')
    ax2.hlines(y=post_mean, xmin=post_idx[0], xmax=post_idx[-1],
               color='#FF6666', linewidth=2.5, linestyle='--', label=f'Post-Construction Mean ({post_mean:+.2f}°C)')

    # 施工时间标线
    ax2.axvline(x=construction_date, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.6)

    # 前后期色块
    ax2.axvspan(delta_trend.index[0], construction_date, alpha=0.06, color='#66CCFF')
    ax2.axvspan(construction_date, delta_trend.index[-1], alpha=0.06, color='#FF6666')

    # MK 标注
    sig = 'Significant' if mk_result.p < 0.05 else 'Not Significant'
    p_str = '< 1.000e-100' if mk_result.p == 0.0 else f'= {mk_result.p:.3e}'
    mk_label = r'STL DiD MK ($\Delta$ LST Trend): τ={:.3f}, p {} ({})'.format(mk_result.Tau, p_str, sig)
    ax2.text(0.02, 0.06, mk_label, transform=ax2.transAxes, fontsize=10,
             fontfamily='Courier New', color='#FFCC00',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#111111', edgecolor='#FFCC00', alpha=0.8))

    ax2.set_ylabel(r'$\Delta$ LST Trend (°C)', fontsize=13, fontname='Courier New', color='#FF8888')
    ax2.set_xlabel('Temporal Axis (Years)', fontsize=13, fontname='Courier New', color='#CCCCCC')
    ax2.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False,
               prop={'family': 'Courier New', 'size': 10})
    ax2.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax2.tick_params(axis='both', labelsize=11, colors='#AAAAAA')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.xaxis.set_major_locator(mdates.YearLocator())

    # 数据源署名
    fig.text(0.98, 0.01, 'Data: USGS Landsat 8 (TIRS) | Decomposition: STL-LOESS | Author: H. Li',
             fontsize=9, color='#888888', ha='right', va='bottom', fontfamily='Helvetica')

    plt.tight_layout()
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"SAVED: {output_image_path}")
    if os.environ.get('MPLBACKEND') != 'Agg':
        plt.show(block=False)


if __name__ == "__main__":
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_lst.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'thermodynamic_scar_chart.png')
    render_thermodynamic_chart(input_csv, output_png)