#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
13_metoffice_temperature_analysis.py
Phase VII: Independent Ground Truth — UK Met Office Regional Temperature

Downloads HadUK-Grid 1km monthly mean air temperature for SE England
from the Met Office National Climate Information Centre. Compares
regional temperature trends with the satellite-derived LST to test
whether observed thermal anomalies exceed the regional climate baseline.

DATA SOURCE: https://www.metoffice.gov.uk/research/climate/maps-and-data
DATASET: HadUK-Grid Areal Series — England SE and Central S (Tmean)
RESOLUTION: 1 km gridded climate data, station-interpolated
UPDATE CADENCE: Monthly
NO GEE DEPENDENCY — this is a fully independent validation pipeline.
"""

import os
import io
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from urllib.request import urlopen
from urllib.error import URLError

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.figure")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSTRUCTION_DATE = pd.Timestamp('2021-06-01')

METOFFICE_URL = (
    'https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/'
    'Tmean/date/England_SE_and_Central_S.txt'
)
CACHE_FILE = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'metoffice_se_england_tmean.csv')

MONTH_COLS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


def download_metoffice_data(url, cache_path):
    """Download and parse Met Office HadUK-Grid areal series."""
    if os.path.exists(cache_path):
        print(f"  [CACHE] Using cached data: {cache_path}")
        return pd.read_csv(cache_path)

    print(f"  Downloading from Met Office: {url}")
    try:
        response = urlopen(url, timeout=30)
        raw = response.read().decode('utf-8')
    except (URLError, TimeoutError) as e:
        print(f"  [ERROR] Download failed: {e}")
        print(f"  Falling back to cached file if available.")
        if os.path.exists(cache_path):
            return pd.read_csv(cache_path)
        return None

    # Parse the fixed-width format (skip header lines)
    lines = raw.strip().split('\n')
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('year'):
            header_idx = i
            break

    if header_idx is None:
        print("[ERROR] Could not find header row in Met Office data")
        return None

    headers = lines[header_idx].split()
    data_lines = []
    for line in lines[header_idx + 1:]:
        parts = line.split()
        if len(parts) >= 13 and parts[0].isdigit():
            row = {'year': int(parts[0])}
            for j, month in enumerate(MONTH_COLS):
                try:
                    row[month] = float(parts[j + 1])
                except (ValueError, IndexError):
                    row[month] = np.nan
            data_lines.append(row)

    df = pd.DataFrame(data_lines)
    df.to_csv(cache_path, index=False)
    print(f"  -> Parsed {len(df)} years, saved to {cache_path}")
    return df


def run_metoffice_analysis(output_path):
    """Main analysis: compare regional climate with satellite-LST epoch."""
    
    print("=" * 72)
    print("PHASE VII: UK MET OFFICE GROUND TRUTH — REGIONAL TEMPERATURE ANALYSIS")
    print("=" * 72)
    print(f"Data: HadUK-Grid 1km Areal Series (England SE & Central S)")
    print(f"Source: Met Office National Climate Information Centre")
    
    df = download_metoffice_data(METOFFICE_URL, CACHE_FILE)
    if df is None:
        return

    # Focus on study period + context (2010-present)
    df_study = df[df['year'] >= 2010].copy()
    
    # Compute summer mean (JJA) and annual mean
    df_study['summer_mean'] = df_study[['jun', 'jul', 'aug']].mean(axis=1)
    df_study['annual_mean'] = df_study[MONTH_COLS].mean(axis=1)
    df_study['warm_season'] = df_study[['apr', 'may', 'jun', 'jul', 'aug', 'sep']].mean(axis=1)
    
    # Pre/Post construction split
    pre_years = df_study[df_study['year'] < 2021]
    post_years = df_study[df_study['year'] >= 2021]
    
    pre_summer = pre_years['summer_mean'].mean()
    post_summer = post_years['summer_mean'].mean()
    pre_annual = pre_years['annual_mean'].mean()
    post_annual = post_years['annual_mean'].mean()
    
    print(f"\n--- Regional Temperature Summary (Study Period) ---")
    print(f"  Pre-construction  (2010-2020):")
    print(f"    Summer (JJA): {pre_summer:.2f}°C")
    print(f"    Annual:       {pre_annual:.2f}°C")
    print(f"  Post-construction (2021-present):")
    print(f"    Summer (JJA): {post_summer:.2f}°C")
    print(f"    Annual:       {post_annual:.2f}°C")
    print(f"  Regional Δ Summer: {post_summer - pre_summer:+.2f}°C")
    print(f"  Regional Δ Annual: {post_annual - pre_annual:+.2f}°C")
    
    # Long-term trend (1960-present) for climate context
    df_long = df[df['year'] >= 1960].copy()
    df_long['summer_mean'] = df_long[['jun', 'jul', 'aug']].mean(axis=1)
    df_long['annual_mean'] = df_long[MONTH_COLS].mean(axis=1)
    
    # Linear trend via polyfit
    years_arr = df_long['year'].values.astype(float)
    coeffs_summer = np.polyfit(years_arr, df_long['summer_mean'].values, 1)
    coeffs_annual = np.polyfit(years_arr, df_long['annual_mean'].values, 1)
    
    print(f"\n--- Long-Term Climate Trend (1960-present) ---")
    print(f"  Summer warming rate: {coeffs_summer[0]*10:+.3f}°C/decade")
    print(f"  Annual warming rate: {coeffs_annual[0]*10:+.3f}°C/decade")
    
    # Key question: does satellite-observed ΔT at Shepperton EXCEED regional ΔT?
    print(f"\n--- Satellite vs. Regional Comparison ---")
    print(f"  If satellite ΔLST >> regional ΔT, the signal is local (anthropogenic).")
    print(f"  If satellite ΔLST ≈ regional ΔT, the signal is climate-driven.")
    print(f"  Regional summer ΔT = {post_summer - pre_summer:+.2f}°C (Met Office)")
    print(f"  (Compare with satellite ΔLST from 07_plot_thermal_chart.py)")

    # ---------------------------------------------------------
    # Plotting: 2-panel figure
    # ---------------------------------------------------------
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), dpi=300,
                                    gridspec_kw={'height_ratios': [2, 1]})
    
    # === Panel 1: Long-term temperature trend ===
    years_long = df_long['year'].values
    
    ax1.plot(years_long, df_long['summer_mean'], color='#FF6633',
             linewidth=2, marker='o', markersize=3, alpha=0.8, label='Summer (JJA)')
    ax1.plot(years_long, df_long['annual_mean'], color='#33CCFF',
             linewidth=2, marker='s', markersize=3, alpha=0.8, label='Annual Mean')
    
    # Trend lines
    ax1.plot(years_long, np.polyval(coeffs_summer, years_long),
             color='#FF6633', linewidth=2, linestyle='--', alpha=0.5,
             label=f'Summer trend ({coeffs_summer[0]*10:+.2f}°C/decade)')
    ax1.plot(years_long, np.polyval(coeffs_annual, years_long),
             color='#33CCFF', linewidth=2, linestyle='--', alpha=0.5,
             label=f'Annual trend ({coeffs_annual[0]*10:+.2f}°C/decade)')
    
    # Mark construction period
    ax1.axvspan(2021, 2024, color='#FF4444', alpha=0.1, label='Construction Period')
    ax1.axvline(x=2021, color='white', linestyle=':', linewidth=1.5, alpha=0.5)
    
    ax1.set_title('UK Met Office: SE England Mean Air Temperature (1960–present)',
                  fontsize=14, fontweight='bold', fontfamily='Courier New', color='white')
    ax1.set_ylabel('Temperature (°C)', fontsize=12, fontfamily='Courier New', color='#CCCCCC')
    ax1.legend(loc='upper left', frameon=True, facecolor='#111111', edgecolor='#444444',
               prop={'family': 'Courier New', 'size': 9})
    ax1.grid(True, linestyle='--', alpha=0.2)
    ax1.tick_params(colors='#AAAAAA')
    
    # === Panel 2: Study-period anomaly from 2010-2020 baseline ===
    baseline_summer = pre_summer
    baseline_annual = pre_annual
    
    df_study_plot = df_study.copy()
    df_study_plot['summer_anom'] = df_study_plot['summer_mean'] - baseline_summer
    df_study_plot['annual_anom'] = df_study_plot['annual_mean'] - baseline_annual
    
    years_study = df_study_plot['year'].values
    summer_anom = df_study_plot['summer_anom'].values
    
    bar_colors = ['#FF4444' if y >= 2021 else '#33CC33' for y in years_study]
    ax2.bar(years_study, summer_anom, color=bar_colors, alpha=0.85,
            edgecolor='white', linewidth=0.5)
    ax2.axhline(0, color='#888888', linestyle='-', lw=1)
    ax2.axvline(x=2020.5, color='white', linestyle=':', linewidth=1.5, alpha=0.5)
    
    # Annotate the regional shift
    regional_shift = post_summer - pre_summer
    ax2.text(0.98, 0.92,
             f'Regional Summer ΔT: {regional_shift:+.2f}°C\n(2021+ vs 2010-2020 baseline)',
             transform=ax2.transAxes, fontsize=11, fontfamily='Courier New',
             color='#FFCC00', ha='right', va='top',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#111111', edgecolor='#FFCC00', alpha=0.8))
    
    ax2.set_title('Summer Temperature Anomaly (vs. 2010–2020 Pre-Construction Baseline)',
                  fontsize=13, fontweight='bold', fontfamily='Courier New', color='white')
    ax2.set_ylabel('Anomaly (°C)', fontsize=12, fontfamily='Courier New', color='#CCCCCC')
    ax2.set_xlabel('Year', fontsize=12, fontfamily='Courier New', color='#CCCCCC')
    ax2.grid(True, axis='y', linestyle='--', alpha=0.2)
    ax2.tick_params(colors='#AAAAAA')
    
    fig.text(0.5, 0.005,
             'Data: Met Office HadUK-Grid 1km (station-interpolated) | No satellite/GEE dependency | Author: H. Li',
             fontsize=9, color='#888888', ha='center', va='bottom', fontfamily='Helvetica')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"\nSAVED: {output_path}")


if __name__ == '__main__':
    output = os.path.join(PROJECT_ROOT, 'visualisations', 'metoffice_temperature_analysis.png')
    run_metoffice_analysis(output)
