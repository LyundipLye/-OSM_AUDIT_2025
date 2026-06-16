"""
ReferenceET_TIER2_2026-06-15.py  (v2 — fixed ERA5-Land band handling)
======================================================================
T3 — Reference-ET normalisation using ERA5-Land PET from GEE.

Instead of computing FAO-56 from scratch (which had an ee.Element bug in v1),
use ERA5-Land's native 'potential_evaporation_hourly' band, which is the ERA5
FAO-56 Penman-Monteith reference ET₀ (Muñoz-Sabater et al. 2021, ESSD).

Pipeline:
  1. Extract monthly PET (potential_evaporation_hourly, sum→mm/day) for
     Impact and Control from GEE
  2. Load archived MODIS actual ET (ee-chart_et.csv)
  3. Compute ETa/ET₀ ratio (crop-coefficient-style normalisation)
  4. Re-run BACI DiD on normalised series (HAC, MW)
  5. Window robustness + 2019 drought diagnostic
  6. Generate comparison figure

Author: Hanpu Li (Cait), 李含普
Evidence tier: ERA5-Land = peer-reviewed (Muñoz-Sabater et al. 2021, ESSD);
  MOD16A2GF = peer-reviewed (Mu et al. 2011, RSE).
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
import calendar

ee.Initialize(project='stone-cathode-465519-a4')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw_telemetry")
VIS = os.path.join(ROOT, "visualisations")
SPLIT = pd.Timestamp("2021-06-01")

def ml(n):
    return int(np.ceil(n ** (1 / 3)))

def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "n.s."

# ====================================================================
# 1. Define polygons (same as scripts/10_gee_evapotranspiration.js)
# ====================================================================
IMPACT_POLY = ee.Geometry.Polygon([[
    [-0.4758927487043363, 51.41217153384681],
    [-0.47417613493480504, 51.409200313379166],
    [-0.4710862301496488, 51.40735324117383],
    [-0.47027083860912144, 51.405479323562865],
    [-0.4644343517927152, 51.40454233596011],
    [-0.45975657927074254, 51.40778155441695],
    [-0.4637047909406644, 51.40791540148267],
    [-0.4710862301496488, 51.412225067579875],
    [-0.4758927487043363, 51.41217153384681]
]])

CONTROL_POLY = ee.Geometry.Point([-0.4104592619093905, 51.40739479750269]).buffer(500)

# ====================================================================
# 2. Extract ERA5-Land PET monthly from GEE
# ====================================================================
print("=" * 90)
print("T3 REFERENCE-ET NORMALISATION — ERA5-Land PET (potential_evaporation_hourly)")
print("=" * 90)
print("\nStep 1: Extracting monthly PET from ERA5-Land via GEE...")
print("  Collection: ECMWF/ERA5_LAND/HOURLY")
print("  Band: potential_evaporation_hourly (de-accumulated, m/hour)")
print("  Conversion: sum hourly → mm/month → mm/day")
print("  Period: 2015-01 to 2025-12")

era5 = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')

et0_records = []
for year in range(2015, 2026):
    for month in range(1, 13):
        if year == 2025 and month > 12:
            break
        start = f"{year}-{month:02d}-01"
        if month == 12:
            end = f"{year + 1}-01-01"
        else:
            end = f"{year}-{month + 1:02d}-01"

        days_in_month = calendar.monthrange(year, month)[1]

        try:
            # Sum hourly PET over the month
            era5_month = era5.filterDate(start, end).select('potential_evaporation_hourly')
            pet_sum = era5_month.sum()  # sum of hourly values in m

            # Convert: m → mm (×1000), sign convention (negative=upward flux, so negate)
            pet_mm_month = ee.Image(pet_sum).multiply(-1000)
            pet_mm_day = pet_mm_month.divide(days_in_month)

            # Extract for Impact and Control
            val_i = pet_mm_day.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=IMPACT_POLY,
                scale=11132, bestEffort=True
            ).getInfo().get('potential_evaporation_hourly')

            val_c = pet_mm_day.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=CONTROL_POLY,
                scale=11132, bestEffort=True
            ).getInfo().get('potential_evaporation_hourly')

            et0_records.append({
                't': pd.Timestamp(start),
                'ET0_impact_mm_day': val_i,
                'ET0_control_mm_day': val_c,
            })

            if month == 6:  # Print June values as sanity check
                print(f"    {start}: PET_impact={val_i:.2f}  PET_control={val_c:.2f} mm/day  [{year}]")

        except Exception as e:
            print(f"    {start}: ERROR — {e}")
            et0_records.append({
                't': pd.Timestamp(start),
                'ET0_impact_mm_day': None,
                'ET0_control_mm_day': None,
            })

    sys.stdout.flush()

et0_df = pd.DataFrame(et0_records).set_index('t').dropna()
print(f"\n  ET₀ monthly records: {len(et0_df)}")
print(f"  ET₀ impact range: {et0_df['ET0_impact_mm_day'].min():.2f} – "
      f"{et0_df['ET0_impact_mm_day'].max():.2f} mm/day")
print(f"  ET₀ control range: {et0_df['ET0_control_mm_day'].min():.2f} – "
      f"{et0_df['ET0_control_mm_day'].max():.2f} mm/day")

# ====================================================================
# 3. Load actual ET and merge with ET₀
# ====================================================================
print("\nStep 2: Building normalised ET series...")

et_actual = pd.read_csv(os.path.join(RAW, "ee-chart_et.csv"))
et_actual['t'] = pd.to_datetime(et_actual['system:time_start'])
et_actual = et_actual.sort_values('t').set_index('t')
et_actual = et_actual[['Sprawl_ET_mean', 'Control_ET_mean']].dropna()
print(f"  Actual ET records: {len(et_actual)} (8-day, MOD16A2GF)")

# Assign each 8-day observation its month's ET₀
et_m = et_actual.copy()
et_m['ym'] = et_m.index.to_period('M')
et0_df_m = et0_df.copy()
et0_df_m['ym'] = et0_df_m.index.to_period('M')
et0_lookup = et0_df_m.set_index('ym')

et_m = et_m.join(et0_lookup, on='ym', how='inner')

# Convert ET₀ from mm/day to mm/8-day to match MODIS cadence
et_m['ET0_impact_8d'] = et_m['ET0_impact_mm_day'] * 8
et_m['ET0_control_8d'] = et_m['ET0_control_mm_day'] * 8

# Mask out months where ET₀ < 0.5 mm/8-day (winter — denominator too small)
valid = (et_m['ET0_impact_8d'] > 0.5) & (et_m['ET0_control_8d'] > 0.5)
et_norm = et_m[valid].copy()

# Compute normalised ratio
et_norm['ratio_impact'] = et_norm['Sprawl_ET_mean'] / et_norm['ET0_impact_8d']
et_norm['ratio_control'] = et_norm['Control_ET_mean'] / et_norm['ET0_control_8d']
et_norm['delta_raw'] = et_norm['Sprawl_ET_mean'] - et_norm['Control_ET_mean']
et_norm['delta_norm'] = et_norm['ratio_impact'] - et_norm['ratio_control']

print(f"  Merged records (ET₀ > 0.5 mm/8d): {len(et_norm)}")
print(f"  Ratio impact range: {et_norm['ratio_impact'].min():.3f} – "
      f"{et_norm['ratio_impact'].max():.3f}")
print(f"  Ratio control range: {et_norm['ratio_control'].min():.3f} – "
      f"{et_norm['ratio_control'].max():.3f}")

# ====================================================================
# 4. BACI DiD on raw vs normalised ET
# ====================================================================
print("\n" + "=" * 90)
print("Step 3: BACI DiD — RAW vs NORMALISED ET")
print("=" * 90)

def run_did(series, split, label):
    if len(series) == 0:
        print(f"  {label:40s}  EMPTY — cannot run")
        return None
    post = np.asarray(series.index >= split, dtype=float)
    if post.sum() == 0 or (1 - post).sum() == 0:
        print(f"  {label:40s}  SINGLE-PERIOD — cannot run")
        return None
    X = sm.add_constant(post)
    res = sm.OLS(series.values, X).fit(cov_type="HAC", cov_kwds={"maxlags": ml(len(series))})
    pre_vals = series[series.index < split]
    pst_vals = series[series.index >= split]
    _, mwp = mannwhitneyu(pre_vals, pst_vals, alternative="two-sided")
    coef = res.params[1]
    p = res.pvalues[1]
    print(f"  {label:40s}  DiD = {coef:+.4f}  HAC p = {p:.4e} ({stars(p)})  "
          f"MW p = {mwp:.4e} ({stars(mwp)})  n_pre={len(pre_vals)}  n_post={len(pst_vals)}")
    return coef, p, mwp, len(pre_vals), len(pst_vals)

# Raw ET (full dataset, archived — re-confirm baseline)
et_raw_full = et_actual.copy()
et_raw_full['delta'] = et_raw_full['Sprawl_ET_mean'] - et_raw_full['Control_ET_mean']
r_raw = run_did(et_raw_full['delta'], SPLIT, "ET raw (full, all months)")

# Raw ET on the normalisation-valid subset
r_raw_sub = run_did(et_norm['delta_raw'], SPLIT, "ET raw (ET₀>0.5 subset)")

# Normalised ET
r_norm = run_did(et_norm['delta_norm'], SPLIT, "ET normalised (ETa/ET₀)")

# ====================================================================
# 5. Window robustness on normalised ET
# ====================================================================
print("\n" + "=" * 90)
print("Step 4: WINDOW ROBUSTNESS on normalised ET")
print("=" * 90)

windows = {
    "full-year": list(range(1, 13)),
    "warm Apr-Sep": [4, 5, 6, 7, 8, 9],
    "summer JJA": [6, 7, 8],
    "grow Mar-Oct": [3, 4, 5, 6, 7, 8, 9, 10],
}

for wname, wmonths in windows.items():
    mask = et_norm.index.month.isin(wmonths)
    sub = et_norm[mask]
    n_pre = len(sub[sub.index < SPLIT])
    n_post = len(sub[sub.index >= SPLIT])
    if n_pre < 5 or n_post < 5:
        print(f"  ET normalised [{wname:15s}]  SKIPPED (n_pre={n_pre}, n_post={n_post})")
        continue
    run_did(sub['delta_norm'], SPLIT, f"ET normalised [{wname}]")

# ====================================================================
# 6. 2019 drought diagnostic
# ====================================================================
print("\n" + "=" * 90)
print("Step 5: 2019 DROUGHT DIAGNOSTIC — does normalisation absorb it?")
print("=" * 90)
print(f"  {'Year':4s}  {'n':>3s}  {'Δ_raw':>8s}  {'Δ_norm':>8s}  {'ET₀_impact':>11s}  {'ET₀_control':>12s}")

for year in range(2015, 2026):
    yr_mask = et_norm.index.year == year
    if yr_mask.sum() == 0:
        continue
    yr = et_norm[yr_mask]
    mean_raw = yr['delta_raw'].mean()
    mean_norm = yr['delta_norm'].mean()
    mean_et0i = yr['ET0_impact_8d'].mean()
    mean_et0c = yr['ET0_control_8d'].mean()
    marker = " ← DROUGHT" if year == 2019 else ""
    print(f"  {year}  {yr_mask.sum():3d}  {mean_raw:+8.3f}  {mean_norm:+8.4f}  "
          f"{mean_et0i:11.2f}  {mean_et0c:12.2f}{marker}")

# ====================================================================
# 7. Figure
# ====================================================================
print("\nStep 6: Generating comparison figure...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=180)

# Panel A: Raw ET delta
ax = axes[0, 0]
ax.scatter(et_raw_full.index, et_raw_full['delta'], s=3, alpha=0.3, color='#FF8C00')
ax.axhline(0, color='grey', lw=0.8)
ax.axvline(SPLIT, color='k', ls=':', lw=1.2)
ax.set_title('(A) Raw ΔET (Impact − Control)', fontsize=11)
ax.set_ylabel('ΔET (mm/8-day)')
ax.grid(alpha=0.2)

# Panel B: Normalised ET delta
ax = axes[0, 1]
ax.scatter(et_norm.index, et_norm['delta_norm'], s=3, alpha=0.3, color='#3399FF')
ax.axhline(0, color='grey', lw=0.8)
ax.axvline(SPLIT, color='k', ls=':', lw=1.2)
ax.set_title('(B) Normalised Δ(ETa/ET₀) (Impact − Control)', fontsize=11)
ax.set_ylabel('Δ(ETa/ET₀)')
ax.grid(alpha=0.2)

# Panel C: Annual means
ax = axes[1, 0]
et_norm_c = et_norm.copy()
et_norm_c['year'] = et_norm_c.index.year
ann_raw = et_norm_c.groupby('year')['delta_raw'].mean()
ann_norm = et_norm_c.groupby('year')['delta_norm'].mean()
x = np.arange(len(ann_raw))
w = 0.35
ax.bar(x - w/2, ann_raw.values, w, label='Raw ΔET', color='#FF8C00', alpha=0.8)
ax.bar(x + w/2, ann_norm.values, w, label='Normalised Δ(ET/ET₀)', color='#3399FF', alpha=0.8)
ax.set_xticks(x)
ax.set_xticklabels(ann_raw.index, rotation=45)
ax.axhline(0, color='grey', lw=0.8)
if 2021 in ann_raw.index:
    split_x = list(ann_raw.index).index(2021)
    ax.axvline(split_x - 0.5, color='k', ls=':', lw=1.2)
ax.set_title('(C) Annual mean Δ: raw vs normalised', fontsize=11)
ax.set_ylabel('Mean annual Δ')
ax.legend(fontsize=8)
ax.grid(alpha=0.2)

# Panel D: ET₀ time series
ax = axes[1, 1]
ax.plot(et0_df.index, et0_df['ET0_impact_mm_day'], 'o-', ms=2, color='#FF8C00',
        alpha=0.6, label='ET₀ Impact')
ax.plot(et0_df.index, et0_df['ET0_control_mm_day'], 'o-', ms=2, color='#33CC33',
        alpha=0.6, label='ET₀ Control')
ax.axvline(SPLIT, color='k', ls=':', lw=1.2)
ax.set_title('(D) ERA5-Land Reference ET₀ (PET)', fontsize=11)
ax.set_ylabel('ET₀ (mm/day)')
ax.legend(fontsize=8)
ax.grid(alpha=0.2)

fig.suptitle("T3: Reference-ET Normalisation — ERA5-Land PET vs MODIS ETa | 2026-06-15",
             fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.96])

figpath = os.path.join(VIS, "ReferenceET_TIER2_2026-06-15.png")
fig.savefig(figpath, dpi=180, bbox_inches='tight')
print(f"  SAVED: {figpath}")

# ====================================================================
# 8. Summary
# ====================================================================
print("\n" + "=" * 90)
print("T3 SUMMARY")
print("=" * 90)
if r_norm is not None:
    print(f"  Raw ET DiD:        {r_raw[0]:+.4f}  (HAC p={r_raw[1]:.4e}, {stars(r_raw[1])})")
    print(f"  Normalised ET DiD: {r_norm[0]:+.4f}  (HAC p={r_norm[1]:.4e}, {stars(r_norm[1])})")
    if r_norm[1] < 0.05:
        print("  → Normalisation RESCUES ET significance. Land-cover effect persists after")
        print("    removing meteorological/drought confound.")
    else:
        print("  → Normalisation CONFIRMS ET remains n.s. The drought confound is not the")
        print("    sole explanation; the signal is genuinely weak/absent in the DiD framework.")
        print("    ET's status as 'directional qualitative support only' is now principled,")
        print("    not an artefact of the ad-hoc 2019 exclusion.")
print("=" * 90)
