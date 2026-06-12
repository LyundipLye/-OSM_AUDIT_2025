"""
05_plot_ndvi_chart.py
NDVI DiD Analysis: GEE-exported NDVI CSV with Seasonal Mann-Kendall trend test
and Mean-Shift OLS with Newey-West HAC standard errors.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import warnings
import pymannkendall as mk
import statsmodels.api as sm

# Suppress interactive mode warnings for CLI execution
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.figure")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    
    print(f"  [{label}] HAC OLS (maxlags={maxlags}): shift={coef:+.4f} | p={p:.2e} | 95% CI [{ci_low:.4f}, {ci_high:.4f}]")
    return coef, p, ci_low, ci_high


def plot_ndvi_collapse(csv_path, output_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {csv_path}")
        return

    # ---------------------------------------------------------
    # Data preprocessing (DiD Domain Only)
    # ---------------------------------------------------------
    df['system:time_start'] = pd.to_datetime(df['system:time_start'])
    df = df.sort_values('system:time_start').set_index('system:time_start')
    
    df_raw = df[['Sprawl_Zone_Core_mean', 'Sprawl_Zone_Core_std', 'Control_Zone_mean', 'Control_Zone_std']].dropna().copy()
    df_raw.rename(columns={'Sprawl_Zone_Core_mean': 'NDVI_Sprawl', 'Control_Zone_mean': 'NDVI_Control',
                           'Sprawl_Zone_Core_std': 'NDVI_Sprawl_Std'}, inplace=True)
    
    df_raw['Delta_NDVI'] = df_raw['NDVI_Sprawl'] - df_raw['NDVI_Control']
    CONSTRUCTION_DATE = pd.Timestamp('2021-06-01')

    pre = df_raw.loc[df_raw.index < CONSTRUCTION_DATE, 'Delta_NDVI']
    post = df_raw.loc[df_raw.index >= CONSTRUCTION_DATE, 'Delta_NDVI']
    pre_m, pre_low, pre_high = get_robust_ci(pre)
    post_m, post_low, post_high = get_robust_ci(post)

    # Mean-Shift OLS with Newey-West HAC standard errors
    hac_coef, hac_p, hac_ci_low, hac_ci_high = run_hac_regression(
        df_raw['Delta_NDVI'], CONSTRUCTION_DATE, "NDVI DiD")
    
    # Seasonal Mann-Kendall test
    delta_monthly = df_raw['Delta_NDVI'].resample('ME').mean().dropna()
    mk_monthly = mk.seasonal_test(delta_monthly, period=12)
    print(f"[PRIMARY] DiD Seasonal MK (monthly, period=12): trend={mk_monthly.trend}, p={mk_monthly.p:.6f}")

    y_low = df_raw['Delta_NDVI'].min() - 0.05
    y_high = max(df_raw['Delta_NDVI'].max() + 0.1, 0.2)

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 8), dpi=400)

    ax.scatter(df_raw.index, df_raw['Delta_NDVI'], color='#FF3333', alpha=0.5, s=20, marker='o', label=r'Raw $\Delta$NDVI (Impact $-$ Control)')
    ax.axhline(y=0, color='#666666', linestyle='-', linewidth=1, alpha=0.5)

    ax.hlines(y=pre_m, xmin=df_raw.index.min(), xmax=CONSTRUCTION_DATE, color='#66CCFF', linewidth=4, zorder=4, label=f'Pre Mean ({pre_m:+.2f})')
    ax.fill_between([df_raw.index.min(), CONSTRUCTION_DATE], pre_low, pre_high, color='#66CCFF', alpha=0.2, zorder=2, label='95% CI (SEM, Pre)')
    
    ax.hlines(y=post_m, xmin=CONSTRUCTION_DATE, xmax=df_raw.index.max(), color='#FF4444', linewidth=4, zorder=4, label=f'Post Mean ({post_m:+.2f})')
    ax.fill_between([CONSTRUCTION_DATE, df_raw.index.max()], post_low, post_high, color='#FF4444', alpha=0.2, zorder=2, label='95% CI (SEM, Post)')

    ax.axvline(x=CONSTRUCTION_DATE, color='#FFFFFF', linestyle=':', linewidth=1.5, alpha=0.5)
    
    p_str_hac = '< 1e-10' if hac_p < 1e-10 else f'= {hac_p:.3e}'
    p_str_mk = '< 1e-10' if mk_monthly.p < 1e-10 else f'= {mk_monthly.p:.3e}'
    
    mk_label = 'DiD Shift: {0} $\\rightarrow$ {1} ($\\Delta$={2:+.2f})\nHAC OLS p {3}\nSeasonal MK p {4}'.format(
        round(pre_m, 2), round(post_m, 2), hac_coef, p_str_hac, p_str_mk)
    ax.text(0.02, 0.04, mk_label, transform=ax.transAxes, fontsize=12,
            fontfamily='Courier New', color='#FFCC00', bbox=dict(facecolor='#111111', edgecolor='#FFCC00', alpha=0.8, boxstyle='round,pad=0.5'))

    ax.set_ylim(y_low, y_high)
    ax.set_title(r'NDVI DiD Analysis: $\Delta$NDVI (Impact $-$ Control)', 
                 fontsize=16, fontweight='bold', fontname='Courier New', color='white', pad=20)
    ax.set_ylabel(r'$\Delta$NDVI (Impact $-$ Control)', fontsize=14, fontname='Courier New', color='#CCCCCC')
    ax.set_xlabel('Temporal Axis (Years)', fontsize=14, fontname='Courier New', color='#CCCCCC')

    ax.grid(True, color='#333333', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.legend(loc='upper right', frameon=False, prop={'family': 'Courier New', 'size': 11})
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())

    fig.text(0.98, 0.02, 'Data: ESA Sentinel-2 | Method: DiD + HAC OLS + Seasonal Mann-Kendall | Author: H. Li', 
             fontsize=9, color='#888888', ha='right', va='bottom', fontfamily='Helvetica')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"SAVED: {output_path}")
    if os.environ.get('MPLBACKEND') != 'Agg':
        plt.show(block=False)

if __name__ == '__main__':
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_ndvi.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'NDVICollapseChart.png')
    plot_ndvi_collapse(input_csv, output_png)
