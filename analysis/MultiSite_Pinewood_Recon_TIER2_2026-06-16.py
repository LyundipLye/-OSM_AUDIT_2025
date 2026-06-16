"""
MultiSite_Pinewood_Recon_TIER2_2026-06-16.py
=============================================
Multi-site widening (PhD-seed §4) — PINEWOOD reconnaissance.

PURPOSE: before any BACI on Pinewood, find out (a) IS there a greenbelt→built
conversion footprint, (b) how big, (c) WHEN — because Pinewood's major expansion
(PSDF / Pinewood East) is widely dated ~2016–2019, i.e. likely BEFORE the
Shepperton 2021-06 split. Imposing that split blindly would yield a misleading null
(see `_PHD_SEED_FRAMING_2026-06-16.md` §4). So this is reconnaissance, not a final DiD.

HONESTY ON GEOMETRY (standing rule: no fabricated coordinates):
  - AOI is anchored on the EXOGENOUS OSM Pinewood Studios footprint
    (relation 13016756, Nominatim bbox), NOT a hand-guessed polygon.
  - The Impact footprint is DATA-DERIVED: the centroid/area of the vegetation-loss
    cluster (Landsat NDVI 2014-16 baseline → 2023-25 recent). Reported with provenance.
  - The Control is DATA-DERIVED: mean of stable-vegetation pixels in the box
    (high baseline NDVI, near-zero change). No outcome-selection for the *control*.
  Endogeneity note: locating Impact on NDVI-loss is fine for *dating/sizing* the change;
  a confirmatory BACI must anchor Impact on the OSM/planning construction boundary.

Sensor: Landsat 8 (2013+) + 9 (2021+) C2 L2 SR, summer (May-Sep) annual NDVI means.
  30 m is adequate for a multi-hectare footprint and gives the temporal DEPTH (2014-2025)
  needed to date the change — more important here than Sentinel-2's 10 m.

Author: Hanpu Li (Cait), 李含普.  All numbers live-printed; no fabrication.
"""
import os, sys
import numpy as np
import pandas as pd
import ee
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ee.Initialize(project='stone-cathode-465519-a4')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw_telemetry")
VIS = os.path.join(ROOT, "visualisations")

# Pinewood Studios — OSM relation 13016756 (Nominatim), Iver Heath.
PINEWOOD_CENTER = [-0.5322, 51.5525]
PINEWOOD_BBOX = ee.Geometry.Rectangle([-0.5460, 51.5420, -0.5180, 51.5580])  # expanded around studio
YEARS = list(range(2014, 2026))
BASE_YRS, RECENT_YRS = (2014, 2016), (2023, 2025)

def prep_l89(img):
    qa = img.select('QA_PIXEL')
    mask = (qa.bitwiseAnd(1 << 1).eq(0).And(qa.bitwiseAnd(1 << 3).eq(0))
            .And(qa.bitwiseAnd(1 << 4).eq(0)).And(qa.bitwiseAnd(1 << 5).eq(0)))
    sr = img.select(['SR_B5', 'SR_B4']).multiply(0.0000275).add(-0.2)
    ndvi = sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
    return ndvi.updateMask(mask).copyProperties(img, ['system:time_start'])

l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').filterBounds(PINEWOOD_BBOX)
l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2').filterBounds(PINEWOOD_BBOX)
col = l8.merge(l9).map(prep_l89)

def summer_year(y):
    return col.filterDate(f"{y}-05-01", f"{y}-09-30").mean().set('year', y)

print("=" * 90)
print("PINEWOOD reconnaissance — Landsat summer NDVI 2014-2025 (multi-site widening)")
print("=" * 90)

base = ee.ImageCollection([summer_year(y) for y in range(BASE_YRS[0], BASE_YRS[1] + 1)]).mean().select('NDVI')
recent = ee.ImageCollection([summer_year(y) for y in range(RECENT_YRS[0], RECENT_YRS[1] + 1)]).mean().select('NDVI')
change = recent.subtract(base).rename('dNDVI')

# Data-derived footprints
loss_mask = change.lt(-0.20).And(base.gt(0.40))           # was vegetated, lost it
stable_mask = base.gt(0.50).And(change.abs().lt(0.05))    # vegetated & unchanged = control

px_ha = ee.Image.pixelArea().divide(1e4)
loss_ha = ee.Number(loss_mask.multiply(px_ha).reduceRegion(
    ee.Reducer.sum(), PINEWOOD_BBOX, scale=30, maxPixels=1e9).get('dNDVI'))
lonlat = ee.Image.pixelLonLat()
loss_centroid = lonlat.updateMask(loss_mask).reduceRegion(
    ee.Reducer.mean(), PINEWOOD_BBOX, scale=30, maxPixels=1e9)

loss_area_ha = round(loss_ha.getInfo() or 0.0, 2)
cen = loss_centroid.getInfo()
clon, clat = cen.get('longitude'), cen.get('latitude')
print(f"\nVegetation-loss footprint inside box: {loss_area_ha} ha")
print(f"Loss-cluster centroid (data-derived Impact): "
      f"{clat:.5f}, {clon:.5f}" if clon else "  (no loss cluster found)")

if clon is None:
    print("\nNo greenbelt-loss cluster detected at Pinewood in this box/threshold.")
    print("→ Pinewood may have NO post-2014 greenbelt conversion in this AOI "
          "(expansion likely earlier / within existing footprint). Recommend Sky Elstree instead.")
    sys.exit(0)

impact_geom = ee.Geometry.Point([clon, clat]).buffer(60)

# Annual NDVI series: data-derived Impact (loss centroid) vs stable-vegetation control
def annual_means(geom, mask=None):
    out = {}
    for y in YEARS:
        img = summer_year(y)
        if mask is not None:
            img = img.updateMask(mask)
        v = img.reduceRegion(ee.Reducer.mean(), geom, scale=30, maxPixels=1e9).get('NDVI')
        out[y] = v
    # one getInfo round-trip
    return ee.Dictionary(out).getInfo()

impact_series = annual_means(impact_geom)
control_series = annual_means(PINEWOOD_BBOX, mask=stable_mask)   # box-wide stable vegetation

df = pd.DataFrame({
    'year': YEARS,
    'Impact_NDVI': [impact_series.get(str(y)) for y in YEARS],
    'Control_NDVI': [control_series.get(str(y)) for y in YEARS],
})
df['delta'] = df['Impact_NDVI'] - df['Control_NDVI']
print("\nAnnual summer NDVI (Impact = loss cluster, Control = stable vegetation):")
print(df.to_string(index=False, float_format=lambda x: f"{x:.3f}" if pd.notna(x) else "  NaN"))

# Date the change: largest year-on-year drop in Impact
d = df.dropna(subset=['Impact_NDVI']).reset_index(drop=True)
d['yoy'] = d['Impact_NDVI'].diff()
if len(d) > 1 and d['yoy'].notna().any():
    drop_row = d.loc[d['yoy'].idxmin()]
    print(f"\nLargest Impact NDVI drop: {drop_row['yoy']:+.3f} into {int(drop_row['year'])} "
          f"→ implied construction window ~{int(drop_row['year'])-1}–{int(drop_row['year'])}.")
    print("  → use THIS per-site split for any Pinewood BACI, NOT the Shepperton 2021-06 split.")

out_csv = os.path.join(RAW, "pinewood_recon_ndvi_2026-06-16.csv")
df.to_csv(out_csv, index=False)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df['year'], df['Impact_NDVI'], 'o-', color='firebrick', label=f'Impact (loss cluster, {loss_area_ha} ha)')
ax.plot(df['year'], df['Control_NDVI'], 's-', color='seagreen', label='Control (stable vegetation)')
ax.axvspan(2021.42, 2021.42, color='blue', alpha=0)  # placeholder
ax.axvline(2021.42, color='grey', ls=':', lw=1, label='Shepperton split (2021-06, for ref)')
ax.set_xlabel('year'); ax.set_ylabel('summer NDVI')
ax.set_title(f'Pinewood reconnaissance — Landsat summer NDVI 2014-2025\n'
             f'data-derived loss footprint {loss_area_ha} ha @ {clat:.4f},{clon:.4f}')
ax.legend(fontsize=9); ax.grid(alpha=0.25)
fig.tight_layout()
figpath = os.path.join(VIS, "MultiSite_Pinewood_Recon_2026-06-16.png")
fig.savefig(figpath, dpi=150, bbox_inches='tight')
print(f"\nCSV  -> {os.path.relpath(out_csv, ROOT)}")
print(f"fig  -> {os.path.relpath(figpath, ROOT)}")
print("=" * 90)
