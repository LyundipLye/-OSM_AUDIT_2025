"""
SyntheticControl_Analysis_TIER2_2026-06-15.py
============================================
T1 — Synthetic Control Method (SCM) analysis (Robust Parallel ThreadPool version).

Goal: replace the single hand-picked Control polygon with a weighted
synthetic control constructed from the 19 stable green-belt donor polygons.

Method:
  1. Extract monthly Sentinel-2 NDVI (2018-01 to 2025-12) for NDVI core and donors.
  2. Extract monthly Landsat 8/9 LST (2018-01 to 2025-12) for parking core and donors.
  3. Fit SCM weights on pre-period (2018-01 to 2021-05).
  4. Perform in-space placebos for all 19 donors to compute permutation p-values.
  5. Perform in-time placebo (fake split at 2019-06-01).
  6. Generate figures and output results.

Author: Hanpu Li (Cait), 李含普
"""
import ee
import os
import sys
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from concurrent.futures import ThreadPoolExecutor
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ee.Initialize(project='stone-cathode-465519-a4')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw_telemetry")
VIS = os.path.join(ROOT, "visualisations")
SPLIT = pd.Timestamp("2021-06-01")

# ====================================================================
# Geometries
# ====================================================================
NDVI_IMPACT = ee.Geometry.Point([-0.469366, 51.410315]).buffer(100)
PARKING_CORE = ee.Geometry.Polygon([[
    [-0.4676848515978538, 51.40882742185046],
    [-0.4669123754015647, 51.409429716784295],
    [-0.46926006378714025, 51.41065315692719],
    [-0.4703222185570377, 51.40986350085904],
    [-0.4676848515978538, 51.40882742185046]
]])

PASSED_DONORS = {
    "D01": {"lon": -0.4950, "lat": 51.4350, "desc": "Staines Moor"},
    "D02": {"lon": -0.4780, "lat": 51.4500, "desc": "Stanwell Moor"},
    "D03": {"lon": -0.4280, "lat": 51.4280, "desc": "Ashford Common"},
    "D04": {"lon": -0.3900, "lat": 51.4200, "desc": "Sunbury North"},
    "D05": {"lon": -0.4100, "lat": 51.4300, "desc": "Kempton Park W"},
    "D06": {"lon": -0.5100, "lat": 51.3900, "desc": "Chertsey Meads"},
    "D07": {"lon": -0.5350, "lat": 51.4080, "desc": "Thorpe Green"},
    "D08": {"lon": -0.4950, "lat": 51.3780, "desc": "Addlestone Moor"},
    "D10": {"lon": -0.4050, "lat": 51.3900, "desc": "Walton Riverbank"},
    "D11": {"lon": -0.3900, "lat": 51.3750, "desc": "Hersham Green"},
    "D12": {"lon": -0.3600, "lat": 51.3700, "desc": "Esher Common"},
    "D13": {"lon": -0.4400, "lat": 51.4500, "desc": "Bedfont Lakes"},
    "D14": {"lon": -0.4100, "lat": 51.4500, "desc": "Feltham Green"},
    "D15": {"lon": -0.5900, "lat": 51.3600, "desc": "Chobham Common S"},
    "D16": {"lon": -0.5100, "lat": 51.3400, "desc": "Pyrford Green"},
    "D17": {"lon": -0.5300, "lat": 51.3650, "desc": "Ottershaw Meadow"},
    "D18": {"lon": -0.4350, "lat": 51.3950, "desc": "Shepperton Lock E"},
    "D19": {"lon": -0.4550, "lat": 51.3850, "desc": "Littleton N"},
    "D20": {"lon": -0.5400, "lat": 51.4550, "desc": "Wraysbury W"},
}

print("=" * 90)
print("T1 SYNTHETIC CONTROL METHOD ANALYSIS (ROBUST THREADED RUN)")
print("=" * 90)
sys.stdout.flush()

# Build FeatureCollection
features = []
features.append(ee.Feature(NDVI_IMPACT, {'id': 'Treated_NDVI'}))
features.append(ee.Feature(PARKING_CORE, {'id': 'Treated_LST'}))
for did, info in PASSED_DONORS.items():
    geom = ee.Geometry.Point([info["lon"], info["lat"]]).buffer(200)
    features.append(ee.Feature(geom, {'id': did}))
fc = ee.FeatureCollection(features)

n_months = 8 * 12  # 2018-01 to 2025-12

# ====================================================================
# 1. Extract monthly NDVI in parallel
# ====================================================================
print("\nStep 1: Extracting monthly NDVI from Sentinel-2 (2018-2025) using ThreadPool...")
sys.stdout.flush()

def mask_s2(image):
    qa = image.select('QA60')
    maskQA = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
    scl = image.select('SCL')
    maskSCL = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
    return image.updateMask(maskQA.And(maskSCL)).divide(10000)

s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(fc.geometry().bounds())
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))

# Fetch-failure registers (thread-safe under CPython GIL via list.append).
# A month that is genuinely cloud-empty (size==0) is NOT a failure; only an
# *exception* (quota / network / auth) is logged here, so the coverage guard
# below cannot be fooled by legitimately missing winter imagery.
NDVI_FAIL = []
LST_FAIL = []

def fetch_ndvi_month(i):
    year = 2018 + i // 12
    month = 1 + i % 12
    start = f"{year}-{month:02d}-01"
    end = f"{year+1}-01-01" if month == 12 else f"{year}-{month+1:02d}-01"

    try:
        s2_month = s2.filterDate(start, end)
        size = s2_month.size().getInfo()
        if size == 0:
            return []

        ndvi_month = s2_month.map(lambda img: mask_s2(img).normalizedDifference(['B8', 'B4']).rename('NDVI'))
        monthly = ndvi_month.mean()
        features = monthly.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=10).getInfo()['features']
        rows = []
        for f in features:
            p = f['properties']
            if p.get('mean') is not None:
                rows.append({'t': pd.Timestamp(start), 'id': p['id'], 'val': p['mean']})
        return rows
    except Exception as e:
        NDVI_FAIL.append((i, start, repr(e)))   # do NOT swallow silently
        return []

def report_fetch_failures(fails, n_months, label):
    """Loudly surface swallowed GEE errors; abort-flag if coverage is compromised.

    Reports pre/post-split separately: an SCM is fitted ONLY on the pre-period, so a
    handful of failures concentrated in the (shorter) pre-window hurts the weights far
    more than the same count spread over the whole record (reviewer point A). A global
    5%-of-96 guard (~5 months) can hide a 12% pre-period hole, so we guard each window.
    """
    if not fails:
        print(f"  [{label}] 0 fetch errors / {n_months} months.")
        return
    # month index i -> date; pre if date < SPLIT
    def is_pre(i):
        return pd.Timestamp(f"{2018 + i // 12}-{1 + i % 12:02d}-01") < SPLIT
    n_pre_months = sum(1 for i in range(n_months) if is_pre(i))
    n_post_months = n_months - n_pre_months
    pre_fail = sum(1 for i, *_ in fails if is_pre(i))
    post_fail = len(fails) - pre_fail
    print(f"  ⚠️  [{label}] {len(fails)}/{n_months} months ERRORED (not cloud-empty): "
          f"pre {pre_fail}/{n_pre_months}, post {post_fail}/{n_post_months}")
    for i, s, e in fails[:10]:
        print(f"        idx {i} {s}: {e}")
    if (pre_fail > 0.05 * n_pre_months) or (post_fail > 0.05 * n_post_months):
        print(f"  🔴 [{label}] >5% of EITHER window errored — SCM weights (fitted on pre) "
              f"may be unreliable. Re-run (lower max_workers / check GEE quota) before trusting.")
    sys.stdout.flush()

records_ndvi = []
with ThreadPoolExecutor(max_workers=8) as executor:   # 8 < GEE free-tier concurrency cap
    results = executor.map(fetch_ndvi_month, range(n_months))
    for res in results:
        records_ndvi.extend(res)
report_fetch_failures(NDVI_FAIL, n_months, "NDVI")

ndvi_long = pd.DataFrame(records_ndvi)
ndvi_df = ndvi_long.pivot(index='t', columns='id', values='val').dropna()
print(f"  Valid monthly NDVI records (all-donor complete months): {len(ndvi_df)}  "
      f"[{ndvi_df.index.min():%Y-%m} .. {ndvi_df.index.max():%Y-%m}]")
sys.stdout.flush()

# ====================================================================
# 2. Extract monthly LST in parallel
# ====================================================================
print("\nStep 2: Extracting monthly LST from Landsat 8 and 9 (2018-2025) using ThreadPool...")
sys.stdout.flush()

def prep_l89(image):
    qa = image.select('QA_PIXEL')
    mask = (qa.bitwiseAnd(1 << 1).eq(0)
            .And(qa.bitwiseAnd(1 << 3).eq(0))
            .And(qa.bitwiseAnd(1 << 4).eq(0))
            .And(qa.bitwiseAnd(1 << 5).eq(0)))
    lst = image.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15).rename('LST')
    return lst.updateMask(mask).copyProperties(image, ['system:time_start'])

l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').filterBounds(fc.geometry().bounds())
l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2').filterBounds(fc.geometry().bounds())
l89 = l8.merge(l9).map(prep_l89).select('LST')

def fetch_lst_month(i):
    year = 2018 + i // 12
    month = 1 + i % 12
    start = f"{year}-{month:02d}-01"
    end = f"{year+1}-01-01" if month == 12 else f"{year}-{month+1:02d}-01"
    
    try:
        l89_month = l89.filterDate(start, end)
        size = l89_month.size().getInfo()
        if size == 0:
            return []

        monthly = l89_month.mean()
        features = monthly.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=30).getInfo()['features']
        rows = []
        for f in features:
            p = f['properties']
            if p.get('mean') is not None:
                rows.append({'t': pd.Timestamp(start), 'id': p['id'], 'val': p['mean']})
        return rows
    except Exception as e:
        LST_FAIL.append((i, start, repr(e)))   # do NOT swallow silently
        return []

records_lst = []
with ThreadPoolExecutor(max_workers=8) as executor:   # 8 < GEE free-tier concurrency cap
    results = executor.map(fetch_lst_month, range(n_months))
    for res in results:
        records_lst.extend(res)
report_fetch_failures(LST_FAIL, n_months, "LST")

lst_long = pd.DataFrame(records_lst)
lst_df = lst_long.pivot(index='t', columns='id', values='val').dropna()
print(f"  Valid monthly LST records (all-donor complete months): {len(lst_df)}  "
      f"[{lst_df.index.min():%Y-%m} .. {lst_df.index.max():%Y-%m}]")
sys.stdout.flush()

# ====================================================================
# 3. SCM Optimization Engine
# ====================================================================
def fit_scm(y_treat, X_donors):
    """Outer-only SCM: minimise pre-period ||x1 - X0 W||^2 over the simplex
    (W >= 0, sum W = 1).

    SIMPLIFICATION — declared explicitly: this fixes the variable-importance
    matrix V = I (all pre-period months weighted equally), i.e. it does NOT run
    the Abadie, Diamond & Hainmueller (2010) nested V-optimisation that packages
    such as `Synth` (R) and `pysyncon` use. V = I is a defensible, literature-used
    choice when the pre-period predictor set is a short time series of the same
    variable (here monthly NDVI/LST), but a reviewer familiar with the nested
    estimator will notice the difference, so it is stated here and in the results
    md rather than implied. The roadmap's "nested V-optimisation" spec is therefore
    a known divergence from this implementation.
    """
    J = X_donors.shape[1]
    X0 = X_donors.values
    x1 = y_treat.values
    
    def loss(W):
        return np.sum((x1 - X0 @ W) ** 2)
    
    W0 = np.ones(J) / J
    bounds = [(0.0, 1.0) for _ in range(J)]
    constraints = {'type': 'eq', 'fun': lambda W: np.sum(W) - 1.0}
    
    res = minimize(loss, W0, method='SLSQP', bounds=bounds, constraints=constraints)
    return res.x

def run_scm_pipeline(df, treat_col, donor_cols, split_date, label, verbose=True):
    df_pre = df[df.index < split_date]
    df_post = df[df.index >= split_date]
    
    # Fit SCM
    y_pre = df_pre[treat_col]
    X_pre = df_pre[donor_cols]
    W = fit_scm(y_pre, X_pre)
    
    # Generate Synthetic unit. Wrap as a Series on df.index so the gap below
    # aligns by label, not by position — robust to any later reindex/concat.
    X_all = df[donor_cols].values
    synthetic = pd.Series(X_all @ W, index=df.index)

    gap = df[treat_col] - synthetic
    
    # RMSPE
    pre_rmspe = np.sqrt(np.mean(gap[df.index < split_date] ** 2))
    post_rmspe = np.sqrt(np.mean(gap[df.index >= split_date] ** 2))
    ratio = post_rmspe / pre_rmspe if pre_rmspe > 0 else 0
    
    if verbose:
        print(f"\n  SCM Weights for {label}:")
        sorted_weights = sorted(zip(donor_cols, W), key=lambda x: x[1], reverse=True)
        for name, w in sorted_weights:
            if w > 0.01:
                print(f"    {name}: {w:.4f} ({PASSED_DONORS[name]['desc']})")
                
        pre_gap_mean = gap[df.index < split_date].mean()
        post_gap_mean = gap[df.index >= split_date].mean()
        effect = post_gap_mean - pre_gap_mean
        print(f"    Pre-treatment gap mean:  {pre_gap_mean:+.4f}")
        print(f"    Post-treatment gap mean: {post_gap_mean:+.4f}")
        print(f"    SCM Treatment Effect:    {effect:+.4f}")
        print(f"    RMSPE: pre={pre_rmspe:.4f}  post={post_rmspe:.4f}  ratio={ratio:.4f}")
        sys.stdout.flush()
        
    return W, synthetic, gap, ratio

# ====================================================================
# 4. SCM Execution: NDVI
# ====================================================================
print("\n" + "=" * 90)
print("### Fitting SCM for NDVI Core")
print("=" * 90)
sys.stdout.flush()
donor_names = list(PASSED_DONORS.keys())
W_ndvi, synth_ndvi, gap_ndvi, ratio_ndvi = run_scm_pipeline(ndvi_df, 'Treated_NDVI', donor_names, SPLIT, "NDVI Core")

# SCM In-space Placebos for NDVI
print("\n  Running in-space placebos for NDVI...")
sys.stdout.flush()
placebo_ratios_ndvi = []
placebo_gaps_ndvi = {}
for i, d in enumerate(donor_names):
    other_donors = [x for x in donor_names if x != d]
    _, _, p_gap, p_ratio = run_scm_pipeline(ndvi_df, d, other_donors, SPLIT, f"Placebo {d}", verbose=False)
    placebo_ratios_ndvi.append(p_ratio)
    placebo_gaps_ndvi[d] = p_gap

# Calculate permutation p-value
all_ratios_ndvi = [ratio_ndvi] + placebo_ratios_ndvi
rank_ndvi = sum(1 for r in all_ratios_ndvi if r >= ratio_ndvi)
p_perm_ndvi = rank_ndvi / len(all_ratios_ndvi)
print(f"\n  NDVI Permutation p-value: {p_perm_ndvi:.4f} (Rank {rank_ndvi} / {len(all_ratios_ndvi)})")
sys.stdout.flush()

# ====================================================================
# 5. SCM Execution: LST
# ====================================================================
print("\n" + "=" * 90)
print("### Fitting SCM for LST Parking Core")
print("=" * 90)
sys.stdout.flush()
W_lst, synth_lst, gap_lst, ratio_lst = run_scm_pipeline(lst_df, 'Treated_LST', donor_names, SPLIT, "LST Parking Core")

# SCM In-space Placebos for LST
print("\n  Running in-space placebos for LST...")
sys.stdout.flush()
placebo_ratios_lst = []
placebo_gaps_lst = {}
for i, d in enumerate(donor_names):
    other_donors = [x for x in donor_names if x != d]
    _, _, p_gap, p_ratio = run_scm_pipeline(lst_df, d, other_donors, SPLIT, f"Placebo {d}", verbose=False)
    placebo_ratios_lst.append(p_ratio)
    placebo_gaps_lst[d] = p_gap

# Calculate permutation p-value
all_ratios_lst = [ratio_lst] + placebo_ratios_lst
rank_lst = sum(1 for r in all_ratios_lst if r >= ratio_lst)
p_perm_lst = rank_lst / len(all_ratios_lst)
print(f"\n  LST Permutation p-value: {p_perm_lst:.4f} (Rank {rank_lst} / {len(all_ratios_lst)})")
sys.stdout.flush()

# ====================================================================
# 6. SCM In-time Placebos (2019 Fake Split)
# ====================================================================
print("\n" + "=" * 90)
print("### Fitting In-time Placebo (2019 Fake Split)")
print("=" * 90)
sys.stdout.flush()
FAKE_SPLIT = pd.Timestamp("2019-06-01")
pre_fake_ndvi = ndvi_df[ndvi_df.index < SPLIT]
_, _, gap_fake_ndvi, _ = run_scm_pipeline(pre_fake_ndvi, 'Treated_NDVI', donor_names, FAKE_SPLIT, "In-time NDVI", verbose=True)

pre_fake_lst = lst_df[lst_df.index < SPLIT]
_, _, gap_fake_lst, _ = run_scm_pipeline(pre_fake_lst, 'Treated_LST', donor_names, FAKE_SPLIT, "In-time LST", verbose=True)

# In-time placebo treatment effect (should be ~0 if no spurious pre-trend).
def _intime_effect(gap, fake_split):
    return gap[gap.index >= fake_split].mean() - gap[gap.index < fake_split].mean()
effect_fake_ndvi = _intime_effect(gap_fake_ndvi, FAKE_SPLIT)
effect_fake_lst = _intime_effect(gap_fake_lst, FAKE_SPLIT)
print(f"\n  In-time placebo effects (fake 2019 split): "
      f"NDVI = {effect_fake_ndvi:+.4f},  LST = {effect_fake_lst:+.4f} °C "
      f"(expect ~0 → validates no spurious pre-trend)")
sys.stdout.flush()

# ====================================================================
# 7. Generate Figures
# ====================================================================
print("\nStep 7: Generating SCM figures...")
sys.stdout.flush()

fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=180)

# Panel A: NDVI treated vs synthetic
ax = axes[0, 0]
ax.plot(ndvi_df.index, ndvi_df['Treated_NDVI'], 'k-', label='Treated (Shepperton)')
ax.plot(ndvi_df.index, synth_ndvi, 'r--', label='Synthetic Control')
ax.axvline(SPLIT, color='blue', ls=':', lw=1.2, label='Split (2021-06)')
ax.set_title('(A) NDVI Core: Treated vs Synthetic', fontsize=11)
ax.set_ylabel('NDVI')
ax.legend(fontsize=9)
ax.grid(alpha=0.2)

# Panel B: NDVI gap path (placebos) + in-time placebo (fake 2019 split)
ax = axes[0, 1]
for d, g in placebo_gaps_ndvi.items():
    ax.plot(g.index, g, color='grey', alpha=0.3, lw=0.8)   # g.index, not ndvi_df.index
ax.plot(gap_ndvi.index, gap_ndvi, 'r-', lw=2, label='Treated Gap (real 2021 split)')
ax.plot(gap_fake_ndvi.index, gap_fake_ndvi, color='dodgerblue', lw=1.8,
        label='In-time placebo gap (fake 2019 split)')
ax.axhline(0, color='black', lw=0.8)
ax.axvline(SPLIT, color='blue', ls=':', lw=1.2)
ax.axvline(FAKE_SPLIT, color='dodgerblue', ls=':', lw=1.0)
ax.set_title(f'(B) NDVI Gap vs 19 Placebos\nPermutation p = {p_perm_ndvi:.4f}  |  '
             f'in-time effect = {effect_fake_ndvi:+.4f}', fontsize=11)
ax.set_ylabel('ΔNDVI')
ax.legend(fontsize=8)
ax.grid(alpha=0.2)

# Panel C: LST treated vs synthetic
ax = axes[1, 0]
ax.plot(lst_df.index, lst_df['Treated_LST'], 'k-', label='Treated (Shepperton)')
ax.plot(lst_df.index, synth_lst, 'r--', label='Synthetic Control')
ax.axvline(SPLIT, color='blue', ls=':', lw=1.2, label='Split (2021-06)')
ax.set_title('(C) LST Parking Core: Treated vs Synthetic', fontsize=11)
ax.set_ylabel('LST (°C)')
ax.legend(fontsize=9)
ax.grid(alpha=0.2)

# Panel D: LST gap path (placebos) + in-time placebo (fake 2019 split)
ax = axes[1, 1]
for d, g in placebo_gaps_lst.items():
    ax.plot(g.index, g, color='grey', alpha=0.3, lw=0.8)   # g.index, not lst_df.index
ax.plot(gap_lst.index, gap_lst, 'r-', lw=2, label='Treated Gap (real 2021 split)')
ax.plot(gap_fake_lst.index, gap_fake_lst, color='dodgerblue', lw=1.8,
        label='In-time placebo gap (fake 2019 split)')
ax.axhline(0, color='black', lw=0.8)
ax.axvline(SPLIT, color='blue', ls=':', lw=1.2)
ax.axvline(FAKE_SPLIT, color='dodgerblue', ls=':', lw=1.0)
ax.set_title(f'(D) LST Gap vs 19 Placebos\nPermutation p = {p_perm_lst:.4f}  |  '
             f'in-time effect = {effect_fake_lst:+.4f}', fontsize=11)
ax.set_ylabel('ΔLST (°C)')
ax.legend(fontsize=8)
ax.grid(alpha=0.2)

fig.suptitle("T1: Synthetic Control Analysis (SCM) vs 19 Green-Belt Placebos "
             "(+ in-time placebo) | re-run 2026-06-16", fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.95])
figpath = os.path.join(VIS, "SyntheticControl_Analysis_TIER2_2026-06-16.png")
fig.savefig(figpath, dpi=180, bbox_inches='tight')
print(f"  SAVED: {figpath}")

# ====================================================================
# 8. Save CSV Data
# ====================================================================
ndvi_scm_csv = os.path.join(RAW, "ndvi_scm_results.csv")
lst_scm_csv = os.path.join(RAW, "lst_scm_results.csv")
pd.DataFrame({'Treated_NDVI': ndvi_df['Treated_NDVI'], 'Synthetic_NDVI': synth_ndvi, 'Gap_NDVI': gap_ndvi}).to_csv(ndvi_scm_csv)
pd.DataFrame({'Treated_LST': lst_df['Treated_LST'], 'Synthetic_LST': synth_lst, 'Gap_LST': gap_lst}).to_csv(lst_scm_csv)
print(f"  CSV SAVED: {ndvi_scm_csv}")
print(f"  CSV SAVED: {lst_scm_csv}")

# --- Reproducibility: persist donor weights + inference (previously only printed) ---
weights_csv = os.path.join(RAW, "scm_weights.csv")
pd.DataFrame({'Weight_NDVI': pd.Series(W_ndvi, index=donor_names),
              'Weight_LST':  pd.Series(W_lst,  index=donor_names)}
             ).rename_axis('donor').to_csv(weights_csv)
summary_csv = os.path.join(RAW, "scm_summary.csv")
pd.DataFrame([
    {'metric': 'NDVI', 'scm_effect': gap_ndvi[gap_ndvi.index >= SPLIT].mean() - gap_ndvi[gap_ndvi.index < SPLIT].mean(),
     'rmspe_ratio': ratio_ndvi, 'perm_p': p_perm_ndvi, 'perm_rank': rank_ndvi,
     'n_perm': len(all_ratios_ndvi), 'intime_effect_2019': effect_fake_ndvi,
     'n_months': len(ndvi_df), 'n_fetch_errors': len(NDVI_FAIL),
     'pre_start': f"{ndvi_df.index.min():%Y-%m}", 'post_end': f"{ndvi_df.index.max():%Y-%m}"},
    {'metric': 'LST', 'scm_effect': gap_lst[gap_lst.index >= SPLIT].mean() - gap_lst[gap_lst.index < SPLIT].mean(),
     'rmspe_ratio': ratio_lst, 'perm_p': p_perm_lst, 'perm_rank': rank_lst,
     'n_perm': len(all_ratios_lst), 'intime_effect_2019': effect_fake_lst,
     'n_months': len(lst_df), 'n_fetch_errors': len(LST_FAIL),
     'pre_start': f"{lst_df.index.min():%Y-%m}", 'post_end': f"{lst_df.index.max():%Y-%m}"},
]).to_csv(summary_csv, index=False)
print(f"  CSV SAVED: {weights_csv}")
print(f"  CSV SAVED: {summary_csv}")

print("\n" + "=" * 90)
print("T1 SYNTHETIC CONTROL ANALYSIS COMPLETE")
print("=" * 90)
sys.stdout.flush()
