"""
NonVP_ComparatorAnalysis_TIER2_2026-06-15.py
=============================================
T7 — Non-VP Comparator Case (Longcross Garden Village) analysis.

Goal: extract NDVI and LST for the Longcross Garden Village green-belt release
and run the BACI DiD comparison to test if it exhibits the same biophysical
hardening signature as Shepperton.

Method:
  1. Define Longcross Impact (residential development polygon) and Control (nearby stable green belt)
  2. Extract Sentinel-2 NDVI (2018-01 to 2025-12)
  3. Extract Landsat 8/9 LST (2018-01 to 2025-12)
  4. Run BACI DiD on both series with Split = 2020-01-01 (construction start)
  5. Generate figure and output results

Author: Hanpu Li (Cait), 李含普
"""
import ee
import os
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import mannwhitneyu
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ee.Initialize(project='stone-cathode-465519-a4')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw_telemetry")
VIS = os.path.join(ROOT, "visualisations")
SPLIT = pd.Timestamp("2020-01-01")  # Outline approved 2019, built 2020-2023

def ml(n): return int(np.ceil(n ** (1 / 3)))
def stars(p): return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "n.s."

# ====================================================================
# 1. Polygons
# ====================================================================
# Longcross development footprint
LONGCROSS_IMPACT = ee.Geometry.Polygon([[
    [-0.5710, 51.3800],
    [-0.5710, 51.3880],
    [-0.5580, 51.3880],
    [-0.5580, 51.3800],
    [-0.5710, 51.3800]
]])

# Longcross control (stable green belt ~2 km east)
LONGCROSS_CONTROL = ee.Geometry.Point([-0.545, 51.370]).buffer(200)

print("=" * 90)
print("T7 NON-VP COMPARATOR: LONGCROSS GARDEN VILLAGE")
print("=" * 90)

# ====================================================================
# 2. Extract Sentinel-2 NDVI
# ====================================================================
print("\nStep 1: Extracting monthly NDVI from Sentinel-2...")

def mask_s2(image):
    qa = image.select('QA60')
    maskQA = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
    scl = image.select('SCL')
    maskSCL = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
    return image.updateMask(maskQA.And(maskSCL)).divide(10000)

s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(LONGCROSS_IMPACT)
      .filterDate('2018-01-01', '2026-01-01')
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))

ndvi_coll = s2.map(lambda img: mask_s2(img).normalizedDifference(['B8', 'B4']).rename('NDVI')
               .copyProperties(img, ['system:time_start'])).sort('system:time_start')

# Map monthly composites to make it robust and comparable
ndvi_records = []
for year in range(2018, 2026):
    for month in range(1, 13):
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"
        try:
            monthly = ndvi_coll.filterDate(start, end).mean()
            val_i = monthly.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=LONGCROSS_IMPACT, scale=10, bestEffort=True
            ).getInfo().get('NDVI')
            val_c = monthly.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=LONGCROSS_CONTROL, scale=10, bestEffort=True
            ).getInfo().get('NDVI')
            
            if val_i is not None and val_c is not None:
                ndvi_records.append({'t': pd.Timestamp(start), 'ndvi_impact': val_i, 'ndvi_control': val_c})
        except Exception as e:
            pass

ndvi_df = pd.DataFrame(ndvi_records).set_index('t').dropna()
ndvi_df['delta_ndvi'] = ndvi_df['ndvi_impact'] - ndvi_df['ndvi_control']
print(f"  Valid monthly NDVI records: {len(ndvi_df)}")
print(f"  NDVI pre-split: {(ndvi_df.index < SPLIT).sum()}, post-split: {(ndvi_df.index >= SPLIT).sum()}")

# ====================================================================
# 3. Extract Landsat 8/9 LST
# ====================================================================
print("\nStep 2: Extracting LST from Landsat 8 and 9...")

def prep_l89(image):
    qa = image.select('QA_PIXEL')
    mask = (qa.bitwiseAnd(1 << 1).eq(0)
            .And(qa.bitwiseAnd(1 << 3).eq(0))
            .And(qa.bitwiseAnd(1 << 4).eq(0))
            .And(qa.bitwiseAnd(1 << 5).eq(0)))
    lst = image.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15).rename('LST')
    return lst.updateMask(mask).copyProperties(image, ['system:time_start'])

l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').filterBounds(LONGCROSS_IMPACT).filterDate('2018-01-01', '2026-01-01')
l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2').filterBounds(LONGCROSS_IMPACT).filterDate('2021-09-01', '2026-01-01')
l89 = l8.merge(l9).map(prep_l89).select('LST').sort('system:time_start')

# Extract LST time series
lst_records = []
lst_list = l89.map(lambda img: ee.Feature(None, {
    'lst_impact': img.reduceRegion(ee.Reducer.mean(), LONGCROSS_IMPACT, 30, bestEffort=True).get('LST'),
    'lst_control': img.reduceRegion(ee.Reducer.mean(), LONGCROSS_CONTROL, 30, bestEffort=True).get('LST')
}).set('system:time_start', img.get('system:time_start'))).getInfo()['features']

for f in lst_list:
    p = f['properties']
    if p.get('lst_impact') is not None and p.get('lst_control') is not None:
        t = pd.Timestamp(p['system:time_start'], unit='ms')
        lst_records.append({
            't': t,
            'lst_impact': p['lst_impact'],
            'lst_control': p['lst_control'],
        })

lst_df = pd.DataFrame(lst_records).sort_values('t').set_index('t').dropna()
lst_df['delta_lst'] = lst_df['lst_impact'] - lst_df['lst_control']
print(f"  Valid LST observations: {len(lst_df)}")
print(f"  LST pre-split: {(lst_df.index < SPLIT).sum()}, post-split: {(lst_df.index >= SPLIT).sum()}")

# ====================================================================
# 4. Run BACI DiD
# ====================================================================
print("\n" + "=" * 90)
print("Step 3: BACI DiD Analysis — Longcross Garden Village")
print("=" * 90)

def run_did(df, col, split, label):
    post = np.asarray(df.index >= split, dtype=float)
    X = sm.add_constant(post)
    res = sm.OLS(df[col].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": ml(len(df))})
    pre_vals = df.loc[df.index < split, col]
    pst_vals = df.loc[df.index >= split, col]
    _, mwp = mannwhitneyu(pre_vals, pst_vals, alternative="two-sided")
    coef = res.params[1]
    p = res.pvalues[1]
    print(f"  {label:30s} DiD = {coef:+.4f}  HAC p = {p:.4e} ({stars(p)})  MW p = {mwp:.4e} ({stars(mwp)})")
    return coef, p, mwp

coef_ndvi, p_ndvi, mw_ndvi = run_did(ndvi_df, 'delta_ndvi', SPLIT, "NDVI (S2 monthly)")
coef_lst, p_lst, mw_lst = run_did(lst_df, 'delta_lst', SPLIT, "LST (Landsat 8/9)")

# ====================================================================
# 5. Generate Figure
# ====================================================================
print("\nStep 4: Generating comparator analysis figure...")
fig, axes = plt.subplots(2, 2, figsize=(12, 9), dpi=180)

# Panel A: NDVI Series
ax = axes[0, 0]
ax.plot(ndvi_df.index, ndvi_df['ndvi_impact'], 'o-', ms=3, color='#883399', alpha=0.6, label='Longcross Impact')
ax.plot(ndvi_df.index, ndvi_df['ndvi_control'], 'o-', ms=3, color='#22aa55', alpha=0.6, label='Longcross Control')
ax.axvline(SPLIT, color='k', ls=':', lw=1.2)
ax.set_title('(A) Longcross Monthly NDVI', fontsize=10)
ax.set_ylabel('NDVI')
ax.legend(fontsize=8)
ax.grid(alpha=0.2)

# Panel B: NDVI delta
ax = axes[0, 1]
ax.scatter(ndvi_df.index, ndvi_df['delta_ndvi'], s=15, alpha=0.5, color='#883399')
ax.axhline(0, color='grey', lw=0.8)
ax.axvline(SPLIT, color='k', ls=':', lw=1.2)
ax.set_title(f'(B) ΔNDVI (Impact−Control)\nDiD = {coef_ndvi:+.4f} (p={p_ndvi:.1e})', fontsize=10)
ax.set_ylabel('ΔNDVI')
ax.grid(alpha=0.2)

# Panel C: LST Series
ax = axes[1, 0]
ax.plot(lst_df.index, lst_df['lst_impact'], 'o-', ms=2, color='#CC2222', alpha=0.5, label='Longcross Impact')
ax.plot(lst_df.index, lst_df['lst_control'], 'o-', ms=2, color='#22aa55', alpha=0.5, label='Longcross Control')
ax.axvline(SPLIT, color='k', ls=':', lw=1.2)
ax.set_title('(C) Longcross Land Surface Temp (LST)', fontsize=10)
ax.set_ylabel('LST (°C)')
ax.legend(fontsize=8)
ax.grid(alpha=0.2)

# Panel D: LST delta
ax = axes[1, 1]
ax.scatter(lst_df.index, lst_df['delta_lst'], s=8, alpha=0.4, color='#CC2222')
ax.axhline(0, color='grey', lw=0.8)
ax.axvline(SPLIT, color='k', ls=':', lw=1.2)
ax.set_title(f'(D) ΔLST (Impact−Control)\nDiD = {coef_lst:+.3f}°C (p={p_lst:.3f})', fontsize=10)
ax.set_ylabel('ΔLST (°C)')
ax.grid(alpha=0.2)

fig.suptitle("T7: Longcross Garden Village Non-VP Comparator Analysis | 2026-06-15", fontsize=12, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94])
figpath = os.path.join(VIS, "NonVP_ComparatorAnalysis_TIER2_2026-06-15.png")
fig.savefig(figpath, dpi=180, bbox_inches='tight')
print(f"  SAVED: {figpath}")

# ====================================================================
# 6. Save data to csv
# ====================================================================
ndvi_csv = os.path.join(RAW, "longcross_ndvi_monthly.csv")
lst_csv = os.path.join(RAW, "longcross_lst_raw.csv")
ndvi_df.to_csv(ndvi_csv)
lst_df.to_csv(lst_csv)
print(f"  CSV SAVED: {ndvi_csv}")
print(f"  CSV SAVED: {lst_csv}")

print("\n" + "=" * 90)
print("T7 COMPARATOR ANALYSIS COMPLETE")
print("=" * 90)
