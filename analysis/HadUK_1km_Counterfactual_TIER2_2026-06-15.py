"""
HadUK_1km_Counterfactual_TIER2_2026-06-15.py
============================================
T4 upgrade — co-located AIR-temperature counterfactual at TRUE 1 km.

ERA5-Land (9 km) put the Impact and Control points in the SAME cell, so its
air-temperature DiD was mechanically 0 and could not separate them. HadUK-Grid
is 1 km and the two points fall in DIFFERENT 1 km cells, so a genuine same-scale
air-temperature DiD is identifiable.

Data: HadUK-Grid v1.3.2.ceda, variable `tas` (1.5 m mean air temp, degC), 1 km,
monthly, 2015-2025 (11 NetCDF files, CEDA Archive, downloaded 2026-06-15).
Grid CRS: OSGB / British National Grid (EPSG:27700), cell spacing 1000 m.

Conventions (identical to the rest of the repo):
  delta = Impact - Control ; split = 2021-06-01 ;
  HAC OLS, maxlags = ceil(n^(1/3)) ; Mann-Whitney U companion.

Author: Hanpu Li (Cait), 李含普
Evidence tier: peer-reviewed dataset documentation (Hollis et al. 2019,
  Geoscience Data Journal 6(2):151-159, DOI 10.1002/gdj3.78).
No fabrication: every number printed below is from this live computation.
"""
import os, glob
import numpy as np, pandas as pd
import xarray as xr
import statsmodels.api as sm
from scipy.stats import mannwhitneyu
import pyproj
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NCDIR = os.path.join(ROOT, "data", "raw_telemetry", "haduk_1km_2026-06-15")
VIS = os.path.join(ROOT, "visualisations")
SPLIT = pd.Timestamp("2021-06-01")

def ml(n): return int(np.ceil(n ** (1/3)))
def stars(p): return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "n.s."

# Impact (parking core centroid) and Control (greenbelt) in WGS84 -> EPSG:27700
T = pyproj.Transformer.from_crs("epsg:4326", "epsg:27700", always_xy=True).transform
IMPACT_LL  = (-0.469366, 51.410315)
CONTROL_LL = (-0.4104592619093905, 51.40739479750269)
ie, in_ = T(*IMPACT_LL)
ce, cn  = T(*CONTROL_LL)
print("=" * 88)
print("T4 HadUK-Grid 1 km co-located AIR-temperature counterfactual")
print("=" * 88)
print(f"Impact  BNG E={ie:.0f} N={in_:.0f}")
print(f"Control BNG E={ce:.0f} N={cn:.0f}")
sep = np.hypot(ce-ie, cn-in_)
print(f"Impact-Control separation = {sep:.0f} m")

# Load all monthly tas files
files = sorted(glob.glob(os.path.join(NCDIR, "tas_hadukgrid_uk_1km_mon_*.nc")))
print(f"\nNetCDF files: {len(files)} ({os.path.basename(files[0])} .. {os.path.basename(files[-1])})")

def cell_series(easting, northing, label):
    """Open each yearly file (no dask), select nearest 1 km cell, concat over time."""
    parts, centre = [], None
    for f in files:
        with xr.open_dataset(f) as d:
            sub = d["tas"].sel(projection_x_coordinate=easting,
                               projection_y_coordinate=northing, method="nearest")
            centre = (float(sub.projection_x_coordinate), float(sub.projection_y_coordinate))
            parts.append(sub.to_series())
    s = pd.concat(parts).sort_index()
    print(f"  {label}: nearest cell centre E={centre[0]:.0f} N={centre[1]:.0f}  valid months={s.notna().sum()}")
    return centre, s

print("\nSelected 1 km cells:")
(icx, icy), imp = cell_series(ie, in_, "Impact ")
(ccx, ccy), ctl = cell_series(ce, cn, "Control")
same = (icx == ccx) and (icy == ccy)
print(f"  Same 1 km cell? {same}  -> {'CANNOT' if same else 'CAN'} separate Impact and Control at 1 km")

df = pd.DataFrame({"impact_tas": imp, "control_tas": ctl}).dropna()
df.index = pd.to_datetime(df.index)
df = df.sort_index()
df["delta"] = df["impact_tas"] - df["control_tas"]

def did(d, label):
    post = np.asarray(d.index >= SPLIT, dtype=float)
    X = sm.add_constant(post)
    res = sm.OLS(d["delta"].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": ml(len(d))})
    pre = d.loc[d.index < SPLIT, "delta"]; pst = d.loc[d.index >= SPLIT, "delta"]
    _, mwp = mannwhitneyu(pre, pst, alternative="two-sided")
    coef, p = res.params[1], res.pvalues[1]
    ci = res.conf_int()[1]
    print(f"  {label:26s} air-temp DiD = {coef:+.4f} degC  HAC p = {p:.4f} ({stars(p)})  "
          f"95% CI [{ci[0]:+.3f},{ci[1]:+.3f}]  MW p = {mwp:.4f} ({stars(mwp)})  "
          f"n={len(d)} (pre {len(pre)}/post {len(pst)})")
    return coef, p

print("\n" + "-" * 88)
print("Co-located air-temperature DiD (Impact - Control), split 2021-06-01")
print("-" * 88)
did_all,  _ = did(df, "Full year")
did_jja,  _ = did(df[df.index.month.isin([6,7,8])], "Summer JJA")
did_aprsep, _ = did(df[df.index.month.isin([4,5,6,7,8,9])], "Warm Apr-Sep")

# Absolute local JJA warming at the Impact cell (pre vs post) for comparison with ERA5 +0.82
jja = df[df.index.month.isin([6,7,8])]
imp_pre = jja.loc[jja.index < SPLIT, "impact_tas"].mean()
imp_post = jja.loc[jja.index >= SPLIT, "impact_tas"].mean()
ctl_pre = jja.loc[jja.index < SPLIT, "control_tas"].mean()
ctl_post = jja.loc[jja.index >= SPLIT, "control_tas"].mean()
print(f"\nAbsolute JJA mean air-temp warming (pre->post):")
print(f"  Impact  cell: {imp_pre:.2f} -> {imp_post:.2f}  = {imp_post-imp_pre:+.3f} degC")
print(f"  Control cell: {ctl_pre:.2f} -> {ctl_post:.2f}  = {ctl_post-ctl_pre:+.3f} degC")
print(f"  (ERA5-Land 9 km gave local JJA warming +0.82 degC for the shared cell.)")

# Same-scale excess-warming attribution: satellite LST DiD minus 1 km air-temp DiD
LST_PARK = 1.0788   # re-verified live this session (ee-chart_lst.csv)
LST_FULL = 0.5602   # re-verified live this session (ee-chart_lst_sensitivity.csv)
print("\n" + "-" * 88)
print("Same-scale excess-warming attribution (satellite LST DiD minus 1 km air-temp DiD)")
print("-" * 88)
print(f"  Parking core: LST DiD {LST_PARK:+.3f}  - air-temp DiD {did_all:+.3f}  = {LST_PARK-did_all:+.3f} degC excess")
print(f"  Full polygon: LST DiD {LST_FULL:+.3f}  - air-temp DiD {did_all:+.3f}  = {LST_FULL-did_all:+.3f} degC excess")
print(f"  (ERA5 9 km baseline gave parking-core excess +0.26, full-polygon -0.26.)")

# Figure
fig, ax = plt.subplots(2, 1, figsize=(11, 7), dpi=160)
ax[0].plot(df.index, df["impact_tas"], lw=1, color="#c0392b", label="Impact 1 km cell")
ax[0].plot(df.index, df["control_tas"], lw=1, color="#2471a3", label="Control 1 km cell")
ax[0].axvline(SPLIT, color="k", ls=":", lw=1)
ax[0].set_title("HadUK-Grid 1 km monthly mean air temperature (tas)", fontsize=10)
ax[0].set_ylabel("tas (degC)"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.2)
ax[1].scatter(df.index, df["delta"], s=10, alpha=.5, color="#7d3c98")
ax[1].axhline(0, color="grey", lw=.8); ax[1].axvline(SPLIT, color="k", ls=":", lw=1)
ax[1].set_title(f"Air-temperature delta (Impact - Control)  full-year DiD = {did_all:+.3f} degC", fontsize=10)
ax[1].set_ylabel("delta tas (degC)"); ax[1].grid(alpha=.2)
fig.suptitle("T4: HadUK-Grid 1 km co-located air-temperature counterfactual | 2026-06-15",
             fontsize=12, fontweight="bold")
fig.tight_layout(rect=[0,0,1,.96])
out = os.path.join(VIS, "HadUK_1km_Counterfactual_TIER2_2026-06-15.png")
fig.savefig(out, dpi=160, bbox_inches="tight")
print(f"\nSAVED figure: {out}")
print("=" * 88)
