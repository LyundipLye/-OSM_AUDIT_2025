"""
11_plot_evapotranspiration.py
MODIS MOD16A2GF Evapotranspiration DiD Analysis
Implements Mean-Shift OLS Regression with Newey-West HAC standard errors
to test for a statistically significant regime shift in latent heat flux.
Includes annual bar decomposition of the DiD signal.
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

    pre = df_valid.loc[df_valid.index < CONSTRUCTION_DATE, 'delta']
    post = df_valid.loc[df_valid.index >= CONSTRUCTION_DATE, 'delta']

    pre_m, pre_low, pre_high = get_robust_ci(pre)
    post_m, post_low, post_high = get_robust_ci(post)

    # ---------------------------------------------------------
    # Mean-Shift OLS Regression with Newey-West HAC standard errors
    # Model: delta_ET = alpha + beta * PostDummy + epsilon
    # Newey-West HAC prevents artificial p-value inflation from
    # temporal autocorrelation in the 8-day ET time series.
    # ---------------------------------------------------------
    post_dummy = (df_valid.index >= CONSTRUCTION_DATE).astype(int)
    X = sm.add_constant(post_dummy)
    model = sm.OLS(df_valid['delta'].values, X)
    
    # maxlags = int(n^(1/3)) is a standard bandwidth choice (Andrews, 1991)
    n_obs = len(df_valid)
    maxlags = int(np.ceil(n_obs ** (1/3)))
    results = model.fit(cov_type='HAC', cov_kwds={'maxlags': maxlags})
    
    hac_coef = results.params[1]  # beta = mean shift
    hac_p = results.pvalues[1]
    hac_ci_low, hac_ci_high = results.conf_int()[1]
    
    # Mann-Whitney U as non-parametric reference
    _, mw_p = mannwhitneyu(pre, post, alternative='two-sided')

    print("=== Evapotranspiration (ET) DiD Analysis ===")
    print(f"Pre  (n={len(pre)}): mean dET = {pre_m:.2f} mm/8-day +/- {pre.std():.2f}")
    print(f"Post (n={len(post)}): mean dET = {post_m:.2f} mm/8-day +/- {post.std():.2f}")
    print(f"Mean-Shift OLS (Newey-West HAC, maxlags={maxlags}):")
    print(f"  Shift: {hac_coef:+.3f} mm/8-day | HAC p={hac_p:.2e} | 95% CI [{hac_ci_low:.3f}, {hac_ci_high:.3f}]")
    print(f"  MW p={mw_p:.2e}")

    # ---------------------------------------------------------
    # Annual bar decomposition
    # ---------------------------------------------------------
    df_valid['year'] = df_valid.index.year
    annual_delta = df_valid.groupby('year')['delta'].agg(['mean', 'count', 'std'])
    annual_delta['se'] = annual_delta['std'] / np.sqrt(annual_delta['count'])
    
    print("\n=== Annual ΔET Decomposition ===")
    for yr, row in annual_delta.iterrows():
        print(f"  {yr}: mean ΔET = {row['mean']:+.2f} mm/8-day (n={row['count']:.0f})")

    # ---------------------------------------------------------
    # Plotting: 2-panel figure
    # ---------------------------------------------------------
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), dpi=400,
                                    gridspec_kw={'height_ratios': [3, 2]})

    # === Panel 1: Time Series Scatter ===
    ax1.scatter(df_valid.index, df_valid['delta'], color='#00CCFF', alpha=0.4, s=15, zorder=2,
                label=r'Raw 8-day $\Delta$ET (Impact $-$ Control)')
    
    # Zero baseline
    ax1.axhline(0, color='#666666', linestyle='-', lw=1, zorder=1)

    # BACI Step Functions with SEM CI
    ax1.hlines(pre_m, xmin=df_valid.index.min(), xmax=CONSTRUCTION_DATE, color='#FFCC00', lw=3, zorder=4,
               label=f'Pre Mean ({pre_m:+.2f})')
    ax1.fill_between([df_valid.index.min(), CONSTRUCTION_DATE], pre_low, pre_high, color='#FFCC00', alpha=0.3, zorder=3,
                     label='95% CI (SEM)')

    ax1.hlines(post_m, xmin=CONSTRUCTION_DATE, xmax=df_valid.index.max(), color='#FF4444', lw=3, zorder=4,
               label=f'Post Mean ({post_m:+.2f})')
    ax1.fill_between([CONSTRUCTION_DATE, df_valid.index.max()], post_low, post_high, color='#FF4444', alpha=0.3, zorder=3)

    # BACI split marker (mid-point of the documented 2020-2023 conversion window;
    # must match CONSTRUCTION_DATE used for the pre/post regime-shift test above)
    ax1.axvline(x=CONSTRUCTION_DATE, color='white', linestyle=':', lw=1.5, alpha=0.6, zorder=5)
    ax1.annotate(f'BACI Split ({CONSTRUCTION_DATE.strftime("%b %Y")})', xy=(CONSTRUCTION_DATE, ax1.get_ylim()[1] * 0.9),
                 xytext=(10, 0), textcoords='offset points', rotation=90,
                 fontsize=10, color='white', alpha=0.8, fontfamily='Courier New', va='top')

    # Shift annotation arrow
    if post_m < pre_m:
        ax1.annotate(f'Regime Shift:\n{post_m - pre_m:+.2f} mm/8-day',
                 xy=(CONSTRUCTION_DATE + pd.Timedelta(days=180), post_m),
                 xytext=(CONSTRUCTION_DATE + pd.Timedelta(days=180), pre_m),
                 fontsize=14, fontweight='bold', color='#FF4444', fontfamily='Courier New',
                 arrowprops=dict(arrowstyle='->', color='#FF4444', lw=2), ha='center')

    def _sig_label(p):
        if p < 0.001: return "***"
        if p < 0.01: return "**"
        if p < 0.05: return "*"
        return "n.s."

    sig_label = 'DiD Shift: {0:+.2f}\nHAC p={1:.2e} ({2})\nMW p={3:.2e}'.format(
        hac_coef, hac_p, _sig_label(hac_p), mw_p)
    ax1.text(0.02, 0.06, sig_label, transform=ax1.transAxes, fontsize=12,
             fontfamily='Courier New', color='#FFCC00',
             bbox=dict(facecolor='#111111', edgecolor='#FFCC00', alpha=0.8, boxstyle='round,pad=0.5'))

    ax1.set_title(r'Evapotranspiration DiD Analysis: $\Delta$ET Regime Shift (MODIS MOD16A2GF)', 
                  fontsize=16, fontweight='bold', color='white', fontfamily='Courier New', pad=15)
    ax1.set_ylabel(r'8-day $\Delta$ET (mm/8-day) [Impact $-$ Control]', fontsize=12, color='#CCCCCC', fontfamily='Courier New')
    ax1.grid(True, linestyle='--', alpha=0.2, color='#FFFFFF')
    ax1.legend(loc='lower left', frameon=False, prop={'family': 'Courier New', 'size': 10})

    # === Panel 2: Annual Bar Decomposition ===
    years = annual_delta.index.values
    means = annual_delta['mean'].values
    ses = annual_delta['se'].values
    # Highlight the BACI split year so the bar chart agrees with the regime-shift
    # test above (CONSTRUCTION_DATE). Previously hardcoded to 2019, which
    # contradicted the 2021-06-01 split used for the statistics.
    construction_year = CONSTRUCTION_DATE.year
    
    bar_colors = []
    for yr, m in zip(years, means):
        if yr == construction_year:
            bar_colors.append('#FFAA00')  # Construction year highlighted
        elif m < 0:
            bar_colors.append('#FF4444')  # Negative = ET suppression
        else:
            bar_colors.append('#33CC33')  # Positive = ET surplus
    
    ax2.bar(years, means, color=bar_colors, alpha=0.85, edgecolor='white', linewidth=0.5,
            yerr=1.96 * ses, capsize=4, error_kw={'color': '#AAAAAA', 'lw': 1})
    ax2.axhline(0, color='#888888', linestyle='-', lw=1)
    ax2.axhline(pre_m, color='#FFCC00', linestyle='--', lw=1.5, alpha=0.6, label=f'Pre-Construction Mean ({pre_m:+.2f})')
    ax2.axvline(x=construction_year - 0.5, color='white', linestyle=':', lw=1.5, alpha=0.5)
    
    # Annotate construction year
    construction_idx = list(years).index(construction_year) if construction_year in years else None
    if construction_idx is not None:
        ax2.annotate(f'{means[construction_idx]:+.2f}',
                     xy=(construction_year, means[construction_idx]),
                     xytext=(0, -20 if means[construction_idx] < 0 else 15),
                     textcoords='offset points', ha='center',
                     fontsize=11, fontweight='bold', color='#FFAA00', fontfamily='Courier New')

    ax2.set_title(r'Annual $\Delta$ET Decomposition (Year-by-Year DiD)', 
                  fontsize=14, fontweight='bold', color='white', fontfamily='Courier New')
    ax2.set_ylabel(r'Mean Annual $\Delta$ET (mm/8-day)', fontsize=12, color='#CCCCCC', fontfamily='Courier New')
    ax2.set_xlabel('Year', fontsize=12, color='#CCCCCC', fontfamily='Courier New')
    ax2.set_xticks(years)
    ax2.legend(loc='lower left', frameon=False, prop={'family': 'Courier New', 'size': 10})
    ax2.grid(True, axis='y', linestyle='--', alpha=0.2, color='#FFFFFF')
    
    ax2.text(0.98, 0.92, 'Orange = construction year | Red = ET suppression | Green = ET surplus',
             transform=ax2.transAxes, fontsize=9, color='#AAAAAA', ha='right', va='top', fontfamily='Courier New')

    fig.text(0.98, 0.005, 'Data: MODIS MOD16A2GF | Method: Mean-Shift OLS + Newey-West HAC | Author: H. Li', 
             fontsize=9, color='#888888', ha='right', va='bottom', fontfamily='Helvetica')

    plt.tight_layout()
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"\nSAVED ET: {output_image_path}")

if __name__ == '__main__':
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_et.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'evapotranspiration_collapse_chart.png')
    render_et_chart(input_csv, output_png)
