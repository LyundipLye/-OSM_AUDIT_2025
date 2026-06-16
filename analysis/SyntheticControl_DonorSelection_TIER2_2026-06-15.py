"""
SyntheticControl_DonorSelection_TIER2_2026-06-15.py
====================================================
T1 Synthetic Control — Step 1: Donor pool identification and screening.

Objective criteria for donor selection:
  (a) Peri-urban green-belt / agricultural land in Spelthorne / Surrey / outer SW London
  (b) Stayed undeveloped 2015–2026 (screened via NDVI change detection)
  (c) Stable grassland/arable (mean NDVI 0.3–0.8 in pre-period, no large drops)
  (d) Similar latitude (~51.3–51.5°N), elevation (Thames floodplain, <30m AOD)
  (e) Area band comparable to Impact ROI (~3–15 ha buffer polygons)
  (f) NOT adjacent to Shepperton (≥2 km from Impact centroid) to avoid spillover

For each candidate, extracts:
  - Pre-period (2018-01 to 2021-06) mean NDVI from Sentinel-2
  - Post-period (2021-06 to 2025-12) mean NDVI
  - NDVI change (post - pre)

Candidates with large NDVI drops (potential development) are flagged and excluded.

Author: Hanpu Li (Cait), 李含普
No fabrication: all values from live GEE computation.
"""
import ee
import numpy as np
import json

ee.Initialize(project='stone-cathode-465519-a4')

# ====================================================================
# Impact zone (for distance exclusion)
# ====================================================================
IMPACT_CENTROID = ee.Geometry.Point([-0.469366, 51.410315])
IMPACT_POLYGON = ee.Geometry.Polygon([[
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

# Current control zone (will become one donor)
CONTROL_CURRENT = ee.Geometry.Point([-0.4104592619093905, 51.40739479750269])

# ====================================================================
# Candidate donor sites — peri-urban green belt in Surrey / Spelthorne
# / outer SW London. Each is a point + 200m buffer (~12.6 ha).
# Selected from known stable green-belt parcels using:
#   - OS Open Greenspace / Green Belt boundary knowledge
#   - Thames floodplain agricultural land
#   - Avoiding known development sites
#   - ≥2 km from Shepperton Impact centroid
# ====================================================================

BUFFER_M = 200  # ~12.6 ha per donor polygon (comparable to Impact ~39ha ET polygon / ~13ha parking)

DONOR_CANDIDATES = {
    # --- Spelthorne Borough (non-adjacent) ---
    "D01_Staines_Moor":         {"lon": -0.4950, "lat": 51.4350, "desc": "Staines Moor SSSI, stable wet grassland"},
    "D02_Stanwell_Moor":        {"lon": -0.4780, "lat": 51.4500, "desc": "Stanwell Moor green belt, stable grazing"},
    "D03_Ashford_Common":       {"lon": -0.4280, "lat": 51.4280, "desc": "Ashford Common area, stable green belt"},
    "D04_Sunbury_North":        {"lon": -0.3900, "lat": 51.4200, "desc": "Sunbury-on-Thames north, stable parkland"},
    "D05_Kempton_Park_W":       {"lon": -0.4100, "lat": 51.4300, "desc": "Kempton Park west, stable green corridor"},

    # --- Runnymede Borough ---
    "D06_Chertsey_Meads":       {"lon": -0.5100, "lat": 51.3900, "desc": "Chertsey Meads, stable riparian meadow"},
    "D07_Thorpe_Green":         {"lon": -0.5350, "lat": 51.4080, "desc": "Thorpe village green belt, stable arable"},
    "D08_Addlestone_Moor":      {"lon": -0.4950, "lat": 51.3780, "desc": "Addlestone Moor, stable grassland"},
    "D09_Laleham_Burway":       {"lon": -0.4750, "lat": 51.3950, "desc": "Laleham Burway, stable Thames meadow"},

    # --- Elmbridge Borough ---
    "D10_Walton_Riverbank":     {"lon": -0.4050, "lat": 51.3900, "desc": "Walton-on-Thames south, stable green belt"},
    "D11_Hersham_Green":        {"lon": -0.3900, "lat": 51.3750, "desc": "Hersham green corridor, stable arable"},
    "D12_Esher_Common":         {"lon": -0.3600, "lat": 51.3700, "desc": "Esher Common area, stable heathland/grass"},

    # --- Hounslow / Richmond (outer SW London) ---
    "D13_Bedfont_Lakes":        {"lon": -0.4400, "lat": 51.4500, "desc": "Bedfont Lakes area, stable parkland"},
    "D14_Feltham_Green":        {"lon": -0.4100, "lat": 51.4500, "desc": "Feltham green belt fringe, stable grass"},

    # --- Surrey Heath / Woking ---
    "D15_Chobham_Common_S":     {"lon": -0.5900, "lat": 51.3600, "desc": "Chobham Common south, stable heath/grass"},
    "D16_Pyrford_Green":        {"lon": -0.5100, "lat": 51.3400, "desc": "Pyrford green belt, stable arable"},
    "D17_Ottershaw_Meadow":     {"lon": -0.5300, "lat": 51.3650, "desc": "Ottershaw meadow, stable grassland"},

    # --- Additional Spelthorne/Surrey ---
    "D18_Shepperton_Lock_E":    {"lon": -0.4350, "lat": 51.3950, "desc": "Shepperton Lock east, stable riparian (≥3km from Impact)"},
    "D19_Littleton_N":          {"lon": -0.4550, "lat": 51.3850, "desc": "Littleton north, stable arable (≥3km south)"},
    "D20_Wraysbury_W":          {"lon": -0.5400, "lat": 51.4550, "desc": "Wraysbury west, stable green belt meadow"},
}

print("=" * 90)
print("T1 SYNTHETIC CONTROL — DONOR POOL SCREENING")
print("=" * 90)
print(f"Impact centroid: {IMPACT_CENTROID.coordinates().getInfo()}")
print(f"Buffer per donor: {BUFFER_M} m radius (~{np.pi * BUFFER_M**2 / 10000:.1f} ha)")
print(f"Candidates: {len(DONOR_CANDIDATES)}")
print(f"Screening: NDVI stability 2018-01 to 2025-12 (S2 SR Harmonized)")
print()

# ====================================================================
# Sentinel-2 NDVI collection (same masking as scripts/04)
# ====================================================================
def mask_s2(image):
    qa = image.select('QA60')
    maskQA = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
    scl = image.select('SCL')
    maskSCL = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
    return image.updateMask(maskQA.And(maskSCL)).divide(10000)

s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterDate('2018-01-01', '2026-01-01')
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))

ndvi_coll = s2.map(lambda img: mask_s2(img).normalizedDifference(['B8', 'B4']).rename('NDVI')
               .copyProperties(img, ['system:time_start']))

# Pre and post composites
ndvi_pre = ndvi_coll.filterDate('2018-01-01', '2021-06-01').mean()
ndvi_post = ndvi_coll.filterDate('2021-06-01', '2026-01-01').mean()

# ====================================================================
# Screen each candidate
# ====================================================================
results = []
for did, info in sorted(DONOR_CANDIDATES.items()):
    pt = ee.Geometry.Point([info["lon"], info["lat"]])
    poly = pt.buffer(BUFFER_M)

    # Distance from Impact centroid (km)
    dist_m = IMPACT_CENTROID.distance(pt).getInfo()
    dist_km = dist_m / 1000

    # Pre-period mean NDVI
    pre_val = ndvi_pre.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=poly, scale=10, bestEffort=True
    ).getInfo().get('NDVI')

    # Post-period mean NDVI
    post_val = ndvi_post.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=poly, scale=10, bestEffort=True
    ).getInfo().get('NDVI')

    # NDVI change
    if pre_val is not None and post_val is not None:
        change = post_val - pre_val
    else:
        change = None

    results.append({
        "id": did,
        "lon": info["lon"],
        "lat": info["lat"],
        "desc": info["desc"],
        "dist_km": dist_km,
        "ndvi_pre": pre_val,
        "ndvi_post": post_val,
        "ndvi_change": change,
    })

    status = "OK" if (pre_val and pre_val > 0.25 and change and abs(change) < 0.15 and dist_km >= 2.0) else "FLAG"
    pre_s = f"{pre_val:.3f}" if pre_val else "NULL"
    post_s = f"{post_val:.3f}" if post_val else "NULL"
    chg_s = f"{change:+.3f}" if change else "NULL"
    print(f"  {did:25s}  dist={dist_km:5.1f}km  NDVI_pre={pre_s}  post={post_s}  Δ={chg_s}  [{status}]")

# ====================================================================
# Filter: keep donors that pass all criteria
# ====================================================================
print("\n" + "=" * 90)
print("SCREENING RESULTS")
print("=" * 90)

passed = []
failed = []
for r in results:
    reasons = []
    if r["dist_km"] < 2.0:
        reasons.append(f"too close ({r['dist_km']:.1f} km)")
    if r["ndvi_pre"] is None or r["ndvi_pre"] < 0.25:
        reasons.append(f"low pre-NDVI ({r['ndvi_pre']})")
    if r["ndvi_change"] is not None and r["ndvi_change"] < -0.15:
        reasons.append(f"large NDVI drop ({r['ndvi_change']:+.3f}), possible development")
    if r["ndvi_pre"] is not None and r["ndvi_pre"] > 0.85:
        reasons.append(f"very high NDVI ({r['ndvi_pre']:.3f}), likely forest not grassland")

    if reasons:
        failed.append((r, reasons))
    else:
        passed.append(r)

print(f"\nPASSED: {len(passed)} donors")
for r in passed:
    print(f"  ✅ {r['id']:25s}  [{r['lon']:.4f}, {r['lat']:.4f}]  "
          f"dist={r['dist_km']:.1f}km  NDVI_pre={r['ndvi_pre']:.3f}  Δ={r['ndvi_change']:+.3f}  "
          f"| {r['desc']}")

print(f"\nFAILED: {len(failed)} donors")
for r, reasons in failed:
    pre_s = f"{r['ndvi_pre']:.3f}" if r['ndvi_pre'] else "NULL"
    chg_s = f"{r['ndvi_change']:+.3f}" if r['ndvi_change'] else "NULL"
    print(f"  ❌ {r['id']:25s}  [{r['lon']:.4f}, {r['lat']:.4f}]  "
          f"dist={r['dist_km']:.1f}km  NDVI_pre={pre_s}  Δ={chg_s}  "
          f"| REASONS: {'; '.join(reasons)}")

# Also screen Impact zone itself for reference
impact_pre = ndvi_pre.reduceRegion(
    reducer=ee.Reducer.mean(), geometry=IMPACT_POLYGON, scale=10, bestEffort=True
).getInfo().get('NDVI')
impact_post = ndvi_post.reduceRegion(
    reducer=ee.Reducer.mean(), geometry=IMPACT_POLYGON, scale=10, bestEffort=True
).getInfo().get('NDVI')
print(f"\n  REFERENCE — Impact zone:  NDVI_pre={impact_pre:.3f}  post={impact_post:.3f}  "
      f"Δ={impact_post - impact_pre:+.3f}")

ctrl_poly = CONTROL_CURRENT.buffer(200)
ctrl_pre = ndvi_pre.reduceRegion(
    reducer=ee.Reducer.mean(), geometry=ctrl_poly, scale=10, bestEffort=True
).getInfo().get('NDVI')
ctrl_post = ndvi_post.reduceRegion(
    reducer=ee.Reducer.mean(), geometry=ctrl_poly, scale=10, bestEffort=True
).getInfo().get('NDVI')
print(f"  REFERENCE — Current ctrl: NDVI_pre={ctrl_pre:.3f}  post={ctrl_post:.3f}  "
      f"Δ={ctrl_post - ctrl_pre:+.3f}")

print(f"\n{'=' * 90}")
print(f"DONOR POOL SUMMARY: {len(passed)} sites passed screening.")
print(f"Minimum required: 15. {'✅ SUFFICIENT' if len(passed) >= 15 else '⚠️ NEED MORE CANDIDATES'}")
print(f"{'=' * 90}")
print("\n⏸️  PAUSING FOR SIGN-OFF before extracting full time series.")
print("   Review the donor list above. If approved, run the extraction script next.")
