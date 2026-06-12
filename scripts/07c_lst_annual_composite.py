"""
07c_lst_annual_composite.py
Annual Composite LST Analysis: Noise Reduction via Temporal Aggregation

Instead of testing 700+ noisy individual overpasses, this script
aggregates ΔT to annual summer (JJA) means, yielding ~10 independent
observations with greatly reduced variance. This enables:
  - Welch's t-test (valid: annual means are approximately i.i.d.)
  - Cohen's d effect size (practical significance)
  - Year-by-year bar chart of thermal evolution
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import warnings
from scipy.stats import ttest_ind

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.figure")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSTRUCTION_YEAR = 2021


def cohens_d(group1, group2):
    """Compute Cohen's d effect size."""
    n1, n2 = len(group1), len(group2)
    var1, var2 = group1.var(), group2.var()
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    return (group2.mean() - group1.mean()) / pooled_std if pooled_std > 0 else 0


def run_annual_composite(csv_path, output_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {csv_path}")
        return

    df['system:time_start'] = pd.to_datetime(df['system:time_start'])
    df = df.sort_values('system:time_start').set_index('system:time_start')
    df_valid = df[['Sprawl_Zone_Core_mean', 'Control_Zone_mean']].dropna()
    df_valid['delta'] = df_valid['Sprawl_Zone_Core_mean'] - df_valid['Control_Zone_mean']

    # Filter to summer (JJA) only
    summer = df_valid[df_valid.index.month.isin([6, 7, 8])].copy()
    summer['year'] = summer.index.year

    # Annual summer means
    annual = summer.groupby('year')['delta'].agg(['mean', 'std', 'count']).reset_index()
    annual.columns = ['year', 'mean_delta', 'std_delta', 'n_obs']
    annual['se'] = annual['std_delta'] / np.sqrt(annual['n_obs'])

    pre = annual[annual['year'] < CONSTRUCTION_YEAR]['mean_delta']
    post = annual[annual['year'] >= CONSTRUCTION_YEAR]['mean_delta']

    pre_mean = pre.mean()
    post_mean = post.mean()
    shift = post_mean - pre_mean

    # Welch's t-test on annual means (valid: ~i.i.d.)
    t_stat, welch_p = ttest_ind(pre, post, equal_var=False)
    d = cohens_d(pre, post)

    print("=" * 60)
    print("ANNUAL COMPOSITE LST ANALYSIS (Summer JJA Means)")
    print("=" * 60)
    print(f"\nPer-overpass observations: {len(summer)}")
    print(f"Annual composites: {len(annual)} years")
    for _, row in annual.iterrows():
        marker = " ← construction" if row['year'] == CONSTRUCTION_YEAR else ""
        print(f"  {int(row['year'])}: ΔT = {row['mean_delta']:+.3f}°C  (n={int(row['n_obs'])}, σ={row['std_delta']:.2f}){marker}")

    print(f"\nPre-construction  (n={len(pre)} years): mean ΔT = {pre_mean:+.3f}°C")
    print(f"Post-construction (n={len(post)} years): mean ΔT = {post_mean:+.3f}°C")
    print(f"Shift: {shift:+.3f}°C")
    print(f"Welch t-test: t={t_stat:.3f}, p={welch_p:.4f}")
    print(f"Cohen's d: {d:.3f} ", end="")
    if abs(d) < 0.2:
        print("(negligible)")
    elif abs(d) < 0.5:
        print("(small)")
    elif abs(d) < 0.8:
        print("(medium)")
    else:
        print("(large)")

    # ---------------------------------------------------------
    # Plotting
    # ---------------------------------------------------------
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)

    years = annual['year'].values
    means = annual['mean_delta'].values
    ses = annual['se'].values

    bar_colors = []
    for yr in years:
        if yr == CONSTRUCTION_YEAR:
            bar_colors.append('#FFAA00')
        elif yr < CONSTRUCTION_YEAR:
            bar_colors.append('#33CC33')
        else:
            bar_colors.append('#FF4444')

    ax.bar(years, means, color=bar_colors, alpha=0.85, edgecolor='white', linewidth=0.5,
           yerr=1.96 * ses, capsize=5, error_kw={'color': '#AAAAAA', 'lw': 1.5})
    ax.axhline(0, color='#888888', linestyle='-', lw=1)
    ax.axhline(pre_mean, color='#33CC33', linestyle='--', lw=2, alpha=0.6,
               label=f'Pre Mean ({pre_mean:+.2f}°C)')
    ax.axhline(post_mean, color='#FF4444', linestyle='--', lw=2, alpha=0.6,
               label=f'Post Mean ({post_mean:+.2f}°C)')
    ax.axvline(x=CONSTRUCTION_YEAR - 0.5, color='white', linestyle=':', lw=1.5, alpha=0.5)

    # Annotate shift
    mid_x = (years.min() + years.max()) / 2
    ax.annotate(f'Shift: {shift:+.2f}°C',
                xy=(CONSTRUCTION_YEAR + 1, post_mean),
                xytext=(CONSTRUCTION_YEAR + 2.5, max(means) + 0.3),
                fontsize=13, fontweight='bold', color='#FFCC00', fontfamily='Courier New',
                arrowprops=dict(arrowstyle='->', color='#FFCC00', lw=2))

    # Stats box
    sig = "***" if welch_p < 0.001 else "**" if welch_p < 0.01 else "*" if welch_p < 0.05 else "n.s."
    stats_text = f"Welch p = {welch_p:.4f} ({sig})\nCohen's d = {d:.2f}"
    ax.text(0.02, 0.94, stats_text, transform=ax.transAxes, fontsize=12,
            fontfamily='Courier New', color='#FFCC00', va='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#111111', edgecolor='#FFCC00', alpha=0.8))

    ax.set_title(r"Annual Summer Composite $\Delta$T (Impact $-$ Control)",
                 fontsize=15, fontweight='bold', fontfamily='Courier New', color='white')
    ax.set_ylabel(r'Mean Summer $\Delta$LST (°C)', fontsize=12, fontfamily='Courier New', color='#CCCCCC')
    ax.set_xlabel('Year', fontsize=12, fontfamily='Courier New', color='#CCCCCC')
    ax.set_xticks(years)
    ax.legend(loc='upper right', frameon=False, prop={'family': 'Courier New', 'size': 11})
    ax.grid(True, axis='y', linestyle='--', alpha=0.2)

    ax.text(0.98, 0.02,
            f'Green=pre | Orange=construction year | Red=post | Error bars=95% CI (SEM)',
            transform=ax.transAxes, fontsize=9, color='#AAAAAA', ha='right', fontfamily='Courier New')

    fig.text(0.5, 0.005,
             'Data: Landsat 7+8+9 | Method: Annual JJA Composite + Welch t-test + Cohen\'s d | Author: H. Li',
             fontsize=9, color='#888888', ha='center', va='bottom', fontfamily='Helvetica')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"\nSAVED: {output_path}")


if __name__ == '__main__':
    # Use the full VP polygon (primary) data
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_lst_sensitivity.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'lst_annual_composite.png')
    run_annual_composite(input_csv, output_png)

    # Also run on the parking-lot data
    print("\n" + "=" * 60)
    input_csv2 = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_lst.csv')
    output_png2 = os.path.join(PROJECT_ROOT, 'visualisations', 'lst_annual_composite_parking.png')
    run_annual_composite(input_csv2, output_png2)
