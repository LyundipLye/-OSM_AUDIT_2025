"""
ECOSTRESS_Night_TIER2_2026-06-15.py
====================================
T2 — ECOSTRESS night-time LST analysis.

STATUS: DATA-BLOCKED. ECOSTRESS is NOT available on Google Earth Engine.
Must be accessed via:
  1. NASA AppEEARS (https://appeears.earthdatacloud.nasa.gov/) — point/area extraction
  2. NASA LP DAAC (https://lpdaac.usgs.gov/) — bulk download
  3. NASA CMR API (https://cmr.earthdata.nasa.gov/) — programmatic search

Required: NASA Earthdata login (free).
Product: ECO_L2T_LSTE v002 (ECOSTRESS Land Surface Temperature & Emissivity)
         70 m resolution, ISS orbit (variable overpass times, day + night)

This script is READY-TO-RUN once ECOSTRESS data is downloaded to:
  data/raw_telemetry/ecostress_night_lst.csv

Expected CSV format:
  date, day_night, Impact_LST_mean, Control_LST_mean

Author: Hanpu Li (Cait), 李含普
Evidence tier: ECOSTRESS = peer-reviewed (Fisher et al. 2020, WRR).
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import mannwhitneyu
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw_telemetry")
VIS = os.path.join(ROOT, "visualisations")
SPLIT = pd.Timestamp("2021-06-01")

def ml(n): return int(np.ceil(n ** (1 / 3)))
def stars(p): return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "n.s."

# ====================================================================
# AppEEARS request specification (for Cait to submit)
# ====================================================================
print("=" * 90)
print("T2 ECOSTRESS NIGHT-TIME LST — DATA-BLOCKED")
print("=" * 90)
print()
print("ECOSTRESS is NOT on Google Earth Engine. To obtain the data:")
print()
print("1. Go to https://appeears.earthdatacloud.nasa.gov/")
print("2. Log in with NASA Earthdata credentials (free registration)")
print("3. Submit a 'Point' extraction request with:")
print("   - Product: ECO_L2T_LSTE.002")
print("   - Layer: SDS_LST (Land Surface Temperature)")
print("   - Coordinates:")
print("     Impact (parking core centroid): -0.469366, 51.410315")
print("     Control (stable greenbelt):     -0.410459, 51.407395")
print("   - Date range: 2018-07-01 to 2026-03-15")
print("   - Output: CSV")
print()
print("4. Or submit an 'Area' request with the parking core polygon:")
print("   [-0.4677, 51.4088], [-0.4669, 51.4094], [-0.4693, 51.4107],")
print("   [-0.4703, 51.4099], [-0.4677, 51.4088]")
print()
print("5. Download the CSV and save as: data/raw_telemetry/ecostress_night_lst.csv")
print("6. Re-run this script.")
print()

# Check if data exists
eco_path = os.path.join(RAW, "ecostress_night_lst.csv")
if not os.path.exists(eco_path):
    print(f"⚠️  Data file NOT FOUND: {eco_path}")
    print("   This task is DATA-BLOCKED until ECOSTRESS data is downloaded.")
    print()
    print("EXPECTED ANALYSIS (to be run once data is available):")
    print("  - Separate day vs night overpasses")
    print("  - BACI DiD on night ΔLST (Impact − Control), pre/post 2021-06-01")
    print("  - Compare night warm-core vs Landsat day cold-core (−1.5°C)")
    print("  - If night shows warming: independent UHI confirmation")
    print("  - If night shows no warming: further limits thermal claim to daytime only")
    print()
    print("COVERAGE CAVEAT:")
    print("  ECOSTRESS launched 2018-06-29 on ISS. Pre-period is only ~3 years.")
    print("  ISS orbit is non-sun-synchronous: overpass times vary, reducing")
    print("  temporal consistency vs Landsat. Power may be limited.")
    print()
    print("Reference: Fisher, J.B. et al. (2020). ECOSTRESS: NASA's Next Generation")
    print("  Mission to Measure Evapotranspiration From the International Space Station.")
    print("  Water Resources Research, 56(4), e2019WR026058. DOI: 10.1029/2019WR026058")
    print()
    print("NOT YET RUN — needs NASA Earthdata login + AppEEARS extraction.")
    print("=" * 90)
else:
    print(f"✅ Data file found: {eco_path}")
    print("   Running analysis...")

    # Load and process
    eco = pd.read_csv(eco_path)
    eco['t'] = pd.to_datetime(eco['date'])
    eco = eco.sort_values('t').set_index('t')

    for regime in ['night', 'day']:
        sub = eco[eco['day_night'] == regime].copy()
        if len(sub) < 10:
            print(f"\n  {regime}: n={len(sub)} — too few observations, skipping")
            continue
        sub['delta'] = sub['Impact_LST_mean'] - sub['Control_LST_mean']
        post = np.asarray(sub.index >= SPLIT, dtype=float)
        X = sm.add_constant(post)
        res = sm.OLS(sub['delta'].values, X).fit(
            cov_type="HAC", cov_kwds={"maxlags": ml(len(sub))})
        pre = sub.loc[sub.index < SPLIT, 'delta']
        pst = sub.loc[sub.index >= SPLIT, 'delta']
        _, mwp = mannwhitneyu(pre, pst, alternative="two-sided")
        print(f"\n  ECOSTRESS {regime}:")
        print(f"    DiD = {res.params[1]:+.4f} °C  HAC p = {res.pvalues[1]:.4e} ({stars(res.pvalues[1])})")
        print(f"    MW p = {mwp:.4e} ({stars(mwp)})  n_pre={len(pre)}  n_post={len(pst)}")
