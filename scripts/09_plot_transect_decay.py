# -*- coding: utf-8 -*-
"""
09_plot_transect_decay.py
Phase IV: Spatial Transect Analysis with Statistical Tests
Plots the Post-minus-Pre LST Anomaly per distance ring.
Tests the decay gradient via Spearman rank correlation and
exponential decay regression.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings
from scipy.stats import spearmanr
from scipy.optimize import curve_fit

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.figure")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def render_decay_curve(csv_path, output_image_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {csv_path}")
        return

    required = ['Distance_m', 'Pre_LST_mean', 'Post_LST_mean']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[ERROR] CSV missing columns: {missing}")
        return

    df = df.dropna(subset=required).sort_values('Distance_m').reset_index(drop=True)
    
    dist = df['Distance_m'].values
    pre = df['Pre_LST_mean'].values
    post = df['Post_LST_mean'].values
    
    # Compute per-ring anomaly (Post - Pre)
    anomaly = post - pre
    
    # Background anomaly (mean of far-field 400-800m rings) as baseline
    far_mask = dist >= 400
    background_anomaly = anomaly[far_mask].mean()
    
    # Background-subtracted net thermal anomaly
    net_scar = anomaly - background_anomaly
    
    print("=== Spatial Transect Analysis ===")
    print(f"Core (0m) raw anomaly: {anomaly[0]:+.2f}°C")
    print(f"Background (400-800m) mean anomaly: {background_anomaly:+.2f}°C")
    print(f"Core net anomaly (above background): {net_scar[0]:+.2f}°C")
    print(f"Scar decays to background (~0) at: ~{dist[np.argmin(np.abs(net_scar[1:]))+1]:.0f}m")

    # ---------------------------------------------------------
    # Statistical Tests
    # ---------------------------------------------------------
    
    # 1. Spearman rank correlation: distance vs. net anomaly
    # Expect negative correlation (anomaly decreases with distance)
    rho, spearman_p = spearmanr(dist, net_scar)
    print(f"\n=== Statistical Tests ===")
    print(f"Spearman ρ (distance vs net anomaly): {rho:+.3f} | p={spearman_p:.4f}")
    
    # 2. Exponential decay regression: net_scar = A * exp(-k * dist) + C
    def exp_decay(x, A, k, C):
        return A * np.exp(-k * x) + C
    
    try:
        # Initial guesses: A = core anomaly, k = 1/200m, C = 0
        popt, pcov = curve_fit(exp_decay, dist, net_scar,
                               p0=[net_scar[0], 0.005, 0.0],
                               maxfev=10000)
        A_fit, k_fit, C_fit = popt
        perr = np.sqrt(np.diag(pcov))
        
        # Goodness of fit
        y_pred = exp_decay(dist, *popt)
        ss_res = np.sum((net_scar - y_pred) ** 2)
        ss_tot = np.sum((net_scar - net_scar.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Half-life distance (where anomaly drops to A/2)
        half_life = np.log(2) / k_fit if k_fit > 0 else float('inf')
        
        print(f"Exponential Decay Fit: A={A_fit:.3f}°C, k={k_fit:.5f}/m, C={C_fit:.3f}°C")
        print(f"  R² = {r_squared:.3f}")
        print(f"  Half-life distance = {half_life:.0f}m")
        print(f"  Standard errors: σ_A={perr[0]:.3f}, σ_k={perr[1]:.5f}, σ_C={perr[2]:.3f}")
        fit_success = True
    except (RuntimeError, ValueError) as e:
        print(f"Exponential decay fit failed: {e}")
        print("Falling back to linear regression.")
        fit_success = False
        # Linear fallback
        coeffs = np.polyfit(dist, net_scar, 1)
        slope, intercept = coeffs
        y_pred = np.polyval(coeffs, dist)
        ss_res = np.sum((net_scar - y_pred) ** 2)
        ss_tot = np.sum((net_scar - net_scar.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        print(f"Linear Fit: slope={slope:.5f}°C/m, R²={r_squared:.3f}")

    # ---------------------------------------------------------
    # Two-panel plot
    # ---------------------------------------------------------
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), dpi=400,
                                   gridspec_kw={'height_ratios': [1, 1]})

    # ========== Upper panel: Absolute LST dual curves ==========
    ax1.plot(dist, pre, color='#33CC33', linewidth=3, marker='o', markersize=6,
             label='Pre-Construction (JJA 2016-2018)')
    ax1.plot(dist, post, color='#FF4500', linewidth=3, marker='s', markersize=6,
             label='Post-Construction (JJA 2023-2025)')
    ax1.fill_between(dist, pre, post, color='#AAAAAA', alpha=0.1)
    ax1.axvline(x=0, color='#FFFFFF', linestyle='--', linewidth=1.5, alpha=0.5)
    ax1.set_ylabel('Mean Summer LST (°C)', fontsize=12, fontname='Courier New', color='#CCCCCC')
    ax1.set_title('Spatial Transect (0-800m): Absolute LST vs. Net Thermal Scar',
                  fontsize=14, fontweight='bold', fontname='Courier New', color='white', pad=15)
    ax1.legend(loc='upper right', frameon=True, facecolor='#111111', edgecolor='#444444',
               prop={'family': 'Courier New', 'size': 10})
    ax1.grid(True, color='#333333', linestyle=':', linewidth=1.5, alpha=0.6)
    ax1.tick_params(axis='both', labelsize=10, colors='#AAAAAA')
    ax1.text(0.02, 0.06,
             f'Note: 2016-18 summers were ~{abs(background_anomaly):.1f}°C warmer than 2023-25 regionally.\n'
             f'Absolute comparison is confounded. See lower panel for controlled analysis.',
             transform=ax1.transAxes, fontsize=9, fontfamily='Courier New', color='#FFCC00',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#111111', edgecolor='#FFCC00', alpha=0.8))

    # ========== Lower panel: Net Thermal Anomaly (background-subtracted) ==========
    colors = ['#FF0000' if v > 0 else '#3399FF' for v in net_scar]
    ax2.bar(dist, net_scar, width=40, color=colors, alpha=0.8, edgecolor='white', linewidth=0.5)
    ax2.axhline(y=0, color='#AAAAAA', linestyle='-', linewidth=1.5, alpha=0.7)
    ax2.axvline(x=0, color='#FFFFFF', linestyle='--', linewidth=1.5, alpha=0.5)
    
    # Overlay the regression fit curve
    dist_smooth = np.linspace(0, dist.max(), 200)
    if fit_success:
        ax2.plot(dist_smooth, exp_decay(dist_smooth, *popt), color='#FFFF00', linewidth=2,
                 linestyle='--', label=f'Exp. decay fit (R²={r_squared:.3f}, t½={half_life:.0f}m)')
    else:
        ax2.plot(dist_smooth, np.polyval(coeffs, dist_smooth), color='#FFFF00', linewidth=2,
                 linestyle='--', label=f'Linear fit (R²={r_squared:.3f})')
    
    # Annotate core anomaly value
    ax2.annotate(f'Net Anomaly: {net_scar[0]:+.2f}°C',
                 xy=(0, net_scar[0]), xytext=(120, net_scar[0] + 0.5),
                 fontsize=12, fontweight='bold', color='#FF4444', fontfamily='Courier New',
                 arrowprops=dict(arrowstyle='->', color='#FF4444', lw=2))

    ax2.set_ylabel('Net Thermal Anomaly (°C above background)', fontsize=12, fontname='Courier New', color='#FF8888')
    ax2.set_xlabel('Distance from Impact Zone Boundary (meters)', fontsize=12, fontname='Courier New', color='#CCCCCC')
    ax2.grid(True, color='#333333', linestyle=':', linewidth=1.5, alpha=0.6)
    ax2.tick_params(axis='both', labelsize=10, colors='#AAAAAA')
    ax2.legend(loc='upper right', frameon=True, facecolor='#111111', edgecolor='#444444',
               prop={'family': 'Courier New', 'size': 10})
    
    # Statistical annotation box
    sig_star = "***" if spearman_p < 0.001 else "**" if spearman_p < 0.01 else "*" if spearman_p < 0.05 else "n.s."
    stats_text = f'Spearman ρ = {rho:+.3f} (p={spearman_p:.4f}) {sig_star}'
    ax2.text(0.02, 0.88, stats_text,
             transform=ax2.transAxes, fontsize=10, fontfamily='Courier New', color='#00FF88',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#111111', edgecolor='#00FF88', alpha=0.8))

    fig.text(0.98, 0.005,
             'Data: USGS Landsat 7+8+9 (100m) | Method: Background-Subtracted + Spearman + Exp. Decay | Author: H. Li',
             fontsize=8, color='#666666', ha='right', va='bottom', fontfamily='Helvetica')

    plt.tight_layout()
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"\nSAVED TRANSECT: {output_image_path}")
    if os.environ.get('MPLBACKEND') != 'Agg':
        plt.show(block=False)

if __name__ == "__main__":
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_decay.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'spatial_transect_chart.png')
    render_decay_curve(input_csv, output_png)
