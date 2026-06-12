"""
07_plot_thermal_chart.py
PRIMARY BACI LST Analysis: Full VP Development Polygon (~1 km², ~50 thermal pixels)
Landsat 7+8+9 Triple-Satellite Fusion
Mean-Shift OLS with Newey-West HAC standard errors + Mann-Whitney U

INPUT FILE NOTE: this PRIMARY analysis reads `ee-chart_lst_sensitivity.csv`,
which holds the FULL-POLYGON extraction (~50 thermal pixels). The companion
script 07b (the parking-lot SENSITIVITY check, ~3 pixels) reads `ee-chart_lst.csv`.
The two CSV filenames are counter-intuitive relative to their roles; see the
"LST input-file map" table in README §2 Phase II.B. Do not swap the inputs.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
import warnings
from scipy.stats import mannwhitneyu
import statsmodels.api as sm

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.figure")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSTRUCTION_DATE = pd.Timestamp('2021-06-01')

def get_robust_ci(series):
    if len(series) < 2: return series.mean(), 0, 0
    mean = series.mean()
    se = series.std() / np.sqrt(len(series))
    ci_half = 1.96 * se
    return mean, mean - ci_half, mean + ci_half

def run_hac_regression(delta_series, construction_date, label=""):
    """Run Mean-Shift OLS with Newey-West HAC standard errors."""
    post_dummy = (delta_series.index >= construction_date).astype(int)
    X = sm.add_constant(post_dummy)
    model = sm.OLS(delta_series.values, X)
    n_obs = len(delta_series)
    maxlags = int(np.ceil(n_obs ** (1/3)))
    results = model.fit(cov_type='HAC', cov_kwds={'maxlags': maxlags})
    
    coef = results.params[1]
    p = results.pvalues[1]
    ci_low, ci_high = results.conf_int()[1]
    
    print(f"  HAC OLS (maxlags={maxlags}): shift={coef:+.3f}°C | p={p:.4f} | 95% CI [{ci_low:.3f}, {ci_high:.3f}]")
    return coef, p, ci_low, ci_high

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
    df = df[~df.index.duplicated(keep='first')]

    df_valid = df[['Sprawl_Zone_Core_mean', 'Control_Zone_mean']].dropna()
    df_valid['delta'] = df_valid['Sprawl_Zone_Core_mean'] - df_valid['Control_Zone_mean']

    print(f"Total valid observations: {len(df_valid)}\n")

    # --- 1. FULL-YEAR BACI ANALYSIS ---
    pre = df_valid.loc[df_valid.index < CONSTRUCTION_DATE, 'delta']
    post = df_valid.loc[df_valid.index >= CONSTRUCTION_DATE, 'delta']
    
    pre_m, pre_low, pre_high = get_robust_ci(pre)
    post_m, post_low, post_high = get_robust_ci(post)
    
    _, mw_p = mannwhitneyu(pre, post, alternative='two-sided')

    print("=== Full-Year BACI ===")
    print(f"Pre  (n={len(pre)}): mean dT = {pre_m:+.2f}°C +/- {pre.std():.2f}")
    print(f"Post (n={len(post)}): mean dT = {post_m:+.2f}°C +/- {post.std():.2f}")
    hac_coef, hac_p, _, _ = run_hac_regression(df_valid['delta'], CONSTRUCTION_DATE, "Full-Year")
    print(f"  MW p={mw_p:.4f}\n")

    # --- 2. SUMMER-ONLY BACI ANALYSIS ---
    summer_mask = df_valid.index.month.isin([6, 7, 8])
    df_summer = df_valid[summer_mask]
    
    spre = df_summer.loc[df_summer.index < CONSTRUCTION_DATE, 'delta']
    spost = df_summer.loc[df_summer.index >= CONSTRUCTION_DATE, 'delta']
    
    spre_m, spre_low, spre_high = get_robust_ci(spre)
    spost_m, spost_low, spost_high = get_robust_ci(spost)
    
    _, s_mw_p = mannwhitneyu(spre, spost, alternative='two-sided')

    print("=== Summer-Only BACI (Jun-Aug) ===")
    print(f"Pre  (n={len(spre)}): mean dT = {spre_m:+.2f}°C +/- {spre.std():.2f}")
    print(f"Post (n={len(spost)}): mean dT = {spost_m:+.2f}°C +/- {spost.std():.2f}")
    s_hac_coef, s_hac_p, _, _ = run_hac_regression(df_summer['delta'], CONSTRUCTION_DATE, "Summer")
    print(f"  MW p={s_mw_p:.4f}")

    # Plotting
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), dpi=400, sharex=False)

    # --- Panel 1: Full-Year Delta ---
    ax1.scatter(df_valid.index, df_valid['delta'], color='#FF9933', alpha=0.5, s=15, zorder=2,
                label=r'Raw $\Delta$T (Impact $-$ Control)')
    ax1.axhline(y=0, color='#666666', linestyle='-', lw=1, zorder=1)
    
    ax1.hlines(pre_m, xmin=df_valid.index.min(), xmax=CONSTRUCTION_DATE, color='#FFCC00', lw=3, zorder=4,
               label=f'Pre Mean ({pre_m:+.2f}°C)')
    ax1.fill_between([df_valid.index.min(), CONSTRUCTION_DATE], pre_low, pre_high, color='#FFCC00', alpha=0.3,
                     zorder=3, label='95% CI (SEM)')
    
    ax1.hlines(post_m, xmin=CONSTRUCTION_DATE, xmax=df_valid.index.max(), color='#FF4444', lw=3, zorder=4,
               label=f'Post Mean ({post_m:+.2f}°C)')
    ax1.fill_between([CONSTRUCTION_DATE, df_valid.index.max()], post_low, post_high, color='#FF4444', alpha=0.3, zorder=3)
    
    ax1.axvline(x=CONSTRUCTION_DATE, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.5)
    
    fy_label = 'Full-Year DiD: {0:+.2f}°C \nHAC p={1:.4f} | MW p={2:.4f}'.format(hac_coef, hac_p, mw_p)
    ax1.text(0.02, 0.08, fy_label, transform=ax1.transAxes, fontsize=12, fontfamily='Courier New', color='#FFCC00',
             bbox=dict(facecolor='#111111', edgecolor='#FFCC00', alpha=0.8, boxstyle='round,pad=0.5'))
    
    ax1.set_title(r'Primary BACI: $\Delta$T (Full VP Polygon $-$ Control), Full Year',
                  fontsize=15, fontweight='bold', color='white', fontfamily='Courier New')
    ax1.set_ylabel(r'$\Delta$ LST (°C)', fontsize=12, fontfamily='Courier New', color='#CCCCCC')
    ax1.legend(loc='upper right', prop={'family': 'Courier New', 'size': 10}, frameon=False)
    ax1.grid(True, linestyle='--', alpha=0.2)

    # --- Panel 2: Summer-Only Delta ---
    ax2.scatter(df_summer.index, df_summer['delta'], color='#FF3333', alpha=0.7, s=25, zorder=2,
                label=r'Summer Raw $\Delta$T')
    ax2.axhline(y=0, color='#666666', linestyle='-', lw=1, zorder=1)
    
    ax2.hlines(spre_m, xmin=df_summer.index.min(), xmax=CONSTRUCTION_DATE, color='#00CC66', lw=3, zorder=4,
               label=f'Summer Pre Mean ({spre_m:+.2f}°C)')
    ax2.fill_between([df_summer.index.min(), CONSTRUCTION_DATE], spre_low, spre_high, color='#00CC66', alpha=0.3,
                     zorder=3, label='95% CI (SEM)')
    
    ax2.hlines(spost_m, xmin=CONSTRUCTION_DATE, xmax=df_summer.index.max(), color='#FF3333', lw=3, zorder=4,
               label=f'Summer Post Mean ({spost_m:+.2f}°C)')
    ax2.fill_between([CONSTRUCTION_DATE, df_summer.index.max()], spost_low, spost_high, color='#FF3333', alpha=0.3, zorder=3)
    
    ax2.axvline(x=CONSTRUCTION_DATE, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.5)
    
    sj_label = 'Summer DiD: {0:+.2f}°C \nHAC p={1:.4f}'.format(s_hac_coef, s_hac_p)
    ax2.text(0.02, 0.08, sj_label, transform=ax2.transAxes, fontsize=12, fontfamily='Courier New', color='#00FF88',
             bbox=dict(facecolor='#111111', edgecolor='#00FF88', alpha=0.8, boxstyle='round,pad=0.5'))
             
    ax2.set_title(r'Primary BACI Summer (Jun$-$Aug): Full VP Polygon', fontsize=14, fontweight='bold', color='white', fontfamily='Courier New')
    ax2.set_ylabel(r'Summer $\Delta$ LST (°C)', fontsize=12, fontfamily='Courier New', color='#CCCCCC')
    ax2.legend(loc='upper right', prop={'family': 'Courier New', 'size': 10}, frameon=False)
    ax2.grid(True, linestyle='--', alpha=0.2)

    fig.text(0.98, 0.02, 'Data: Landsat 7+8+9 | Method: Mean-Shift OLS + Newey-West HAC | Author: H. Li', 
             fontsize=9, color='#AAaaaa', ha='right', va='bottom', fontfamily='Helvetica')
             
    plt.tight_layout(pad=3.0)
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"\nSAVED: {output_image_path}")

if __name__ == '__main__':
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_lst_sensitivity.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'thermodynamic_scar_chart.png')
    render_thermodynamic_chart(input_csv, output_png)
