"""
ECOSTRESS_Night_TIER2_2026-06-16.py
====================================
T2 — ECOSTRESS day/night LST BACI DiD (LIVE RUN — data now available).

Supersedes the data-blocked stub `ECOSTRESS_Night_TIER2_2026-06-15.py`.
Cait completed the NASA Earthdata / AppEEARS point extraction:
  product  ECO_L2T_LSTE.002  (70 m, ISS non-sun-synchronous orbit, day + night)
  points   Impact/Treated 51.410315, -0.469366 ; Control 51.407395, -0.410459
  span     2018-07-01 -> 2026-03-31
  request  126592dd-1c43-4f82-83d1-d40279b5ddd3
  file     data/raw_telemetry/126592dd-.../ECO-L2T-LSTE-002-ECO-L2T-LSTE-002-results.csv

What this adds to the audit
---------------------------
ECOSTRESS is the only sensor giving NIGHT LST at the Shepperton site (Landsat/MODIS
on GEE are day overpasses). Night LST isolates stored/anthropogenic heat release with
no incoming-shortwave confound -> the cleanest independent test of the +1.08 C daytime
parking-core warming, and a check on the daytime cold-core anomaly.

Method (reuses the project's canonical DiD verbatim)
  delta = Impact - Control (per paired overpass; K==C for a difference)
  Post  = (t >= 2021-06-01);  OLS delta ~ const + Post
  HAC (Newey-West) maxlags = ceil(n**(1/3)) (Andrews 1991)
  Mann-Whitney U two-sided pre vs post as the non-parametric companion
  Day/night split by NOAA solar elevation (inline; no external dependency).

QA (per ECO_L2T_LSTE.002 User Guide v2, AppEEARS readme sec 4.6.2 / 5.1.2)
  keep LST not-NaN, cloud==0 (clear; LSTE QC bit does NOT carry cloud, mask separately),
  water==0, Mandatory-QA == "pixel produced by TES" (drop "not produced").
  Tile-overlap duplicates (same point in 2 MGRS tiles) averaged per (Category, Date).
  Primary = all produced-clear pixels; sensitivity = LST_accuracy <= 1.5 K only.

Author: Hanpu Li (Cait), 李含普
Evidence tier: ECOSTRESS = peer-reviewed (Fisher et al. 2020, WRR; Hook & Hulley 2022 DOI
  10.5067/ECOSTRESS/ECO_L2T_LSTE.002). No fabrication: every number below is live-printed.
"""
import os, glob
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import mannwhitneyu
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(ROOT, "data", "raw_telemetry")
VIS  = os.path.join(ROOT, "visualisations")
SPLIT = pd.Timestamp("2021-06-01", tz="UTC")
LON_IMPACT = -0.469366   # solar geometry ~identical at both points (<5 km apart)
LAT_IMPACT = 51.410315

LSTc   = "ECO_L2T_LSTE_002_LST"
CLOUDc = "ECO_L2T_LSTE_002_cloud"
WATERc = "ECO_L2T_LSTE_002_water"
QAc    = "ECO_L2T_LSTE_002_QC_Mandatory_QA_flags_Description"
ACCc   = "ECO_L2T_LSTE_002_QC_LST_accuracy_Description"

def ml(n):    return int(np.ceil(n ** (1/3)))
def stars(p): return "***" if p<.001 else "**" if p<.01 else "*" if p<.05 else "n.s."

def solar_elevation(t_utc, lat, lon):
    """NOAA solar-position; returns sun elevation (deg) above horizon. Vectorised."""
    t = pd.DatetimeIndex(t_utc)
    doy = t.dayofyear.to_numpy()
    hr  = t.hour + t.minute/60 + t.second/3600
    g = 2*np.pi/365 * (doy - 1 + (hr - 12)/24)                 # fractional-year angle
    decl = (0.006918 - 0.399912*np.cos(g) + 0.070257*np.sin(g)
            - 0.006758*np.cos(2*g) + 0.000907*np.sin(2*g)
            - 0.002697*np.cos(3*g) + 0.00148*np.sin(3*g))      # rad
    eqt = 229.18*(0.000075 + 0.001868*np.cos(g) - 0.032077*np.sin(g)
                  - 0.014615*np.cos(2*g) - 0.040849*np.sin(2*g))  # minutes
    tst = (hr*60 + eqt + 4*lon) % 1440                          # true solar time, min
    ha  = np.radians(tst/4 - 180)                               # hour angle, rad
    la  = np.radians(lat)
    cz  = np.sin(la)*np.sin(decl) + np.cos(la)*np.cos(decl)*np.cos(ha)
    return 90 - np.degrees(np.arccos(np.clip(cz, -1, 1)))

def did(delta, idx, split=SPLIT, verbose=True):
    """OLS delta~const+Post with HAC; Mann-Whitney pre/post. Returns dict (+prints)."""
    post = np.asarray(idx >= split, dtype=float)
    pre_m  = delta[idx <  split]
    post_m = delta[idx >= split]
    if len(pre_m) < 3 or len(post_m) < 3:
        return None
    res = sm.OLS(delta, sm.add_constant(post)).fit(
        cov_type="HAC", cov_kwds={"maxlags": ml(len(delta))})
    _, mwp = mannwhitneyu(pre_m, post_m, alternative="two-sided")
    out = dict(beta=res.params[1], p=res.pvalues[1], pre=pre_m.mean(),
               post=post_m.mean(), npre=len(pre_m), npost=len(post_m), mwp=mwp,
               overall=delta.mean())
    if verbose:
        print(f"    DiD = {out['beta']:+.3f} C   HAC p = {out['p']:.3e} ({stars(out['p'])})")
        print(f"    mean delta  pre={out['pre']:+.3f}  post={out['post']:+.3f}  "
              f"overall={out['overall']:+.3f} C   n_pre={out['npre']} n_post={out['npost']}")
        print(f"    Mann-Whitney pre vs post: p = {out['mwp']:.3e} ({stars(out['mwp'])})")
    return out

# ---------------------------------------------------------------- load + QA
csvs = glob.glob(os.path.join(RAW, "**", "*ECO-L2T-LSTE-002*results.csv"), recursive=True)
assert csvs, "ECOSTRESS results.csv not found under data/raw_telemetry/"
CSV = sorted(csvs)[0]
print("=" * 92)
print("T2  ECOSTRESS day/night LST  —  BACI DiD  (Impact - Control)")
print("=" * 92)
print("source:", os.path.relpath(CSV, ROOT))

df = pd.read_csv(CSV)
df["t"] = pd.to_datetime(df["Date"].str.replace(" UTC", "", regex=False), utc=True)
n0 = len(df)
m_prod  = ~df[QAc].str.startswith("Pixel not produced", na=False)
m_clear = df[CLOUDc] == 0
m_land  = df[WATERc] == 0
m_lst   = df[LSTc].notna()
keep = m_prod & m_clear & m_land & m_lst
print(f"\nrows {n0} -> produced {int(m_prod.sum())}, clear {int(m_clear.sum())}, "
      f"land {int(m_land.sum())}, LST-valid {int(m_lst.sum())} -> kept {int(keep.sum())}")
df = df[keep].copy()
df["good"] = df[ACCc].isin(["<1 K (Excellent performance)", "1 - 1.5 K (Good performance)",
                            "1.5 - 2 K (Marginal performance)"])  # <=2K accuracy

def pair(d):
    """Average tile-overlap duplicates, pivot Impact vs Control by overpass, K->C delta."""
    g = (d.groupby(["Category", "t"])[LSTc].mean().unstack("Category"))
    g = g.rename(columns={"Treated": "Impact"}).dropna(subset=["Impact", "Control"])
    g["delta"] = g["Impact"] - g["Control"]            # K == C for a difference
    el = solar_elevation(g.index, LAT_IMPACT, LON_IMPACT)
    g["elev"] = el
    g["night"] = el < 0
    return g.sort_index()

# ---------------------------------------------------------------- analysis
def run(d, tag):
    g = pair(d)
    print(f"\n{'-'*92}\n[{tag}]  paired overpasses = {len(g)}  "
          f"(night {int(g['night'].sum())} / day {int((~g['night']).sum())})")
    res = {}
    for regime, mask in [("NIGHT", g["night"]), ("DAY", ~g["night"])]:
        sub = g[mask]
        print(f"\n  ECOSTRESS {regime}  (n={len(sub)}, "
              f"LST {sub['Impact'].min()-273.15:.0f}..{sub['Impact'].max()-273.15:.0f} C):")
        res[regime] = (did(sub["delta"].values, sub.index), sub)
        # robustness: split moved to 2021-10-01 (project convention)
        r2 = did(sub["delta"].values, sub.index,
                 split=pd.Timestamp("2021-10-01", tz="UTC"), verbose=False)
        if r2: print(f"    [robustness, split 2021-10-01]  DiD = {r2['beta']:+.3f} C  "
                     f"p = {r2['p']:.3e} ({stars(r2['p'])})")
        # twilight check: how many overpasses sit within +/-6 deg of the terminator
        tw = int((np.abs(sub["elev"]) < 6).sum())
        print(f"    (overpasses within 6deg of terminator: {tw}/{len(sub)})")
    return g, res

g_all, res_all = run(df, "PRIMARY: all produced-clear pixels")
g_gd,  res_gd  = run(df[df["good"]], "SENSITIVITY: LST_accuracy <= 2 K")

# ---------------------------------------------------------------- figure
fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
for ax, regime in zip(axes, ["NIGHT", "DAY"]):
    sub = res_all[regime][1]
    pre, post = sub[sub.index < SPLIT], sub[sub.index >= SPLIT]
    ax.axhline(0, color="grey", lw=.8, zorder=0)
    ax.axvline(SPLIT, color="firebrick", ls="--", lw=1, zorder=1)
    ax.scatter(pre.index, pre["delta"], s=12, alpha=.5, color="tab:blue", label="pre")
    ax.scatter(post.index, post["delta"], s=12, alpha=.5, color="tab:orange", label="post")
    o = res_all[regime][0]
    if o:
        ax.hlines([o["pre"]],  pre.index.min(),  SPLIT, color="navy", lw=2)
        ax.hlines([o["post"]], SPLIT, post.index.max(), color="saddlebrown", lw=2)
        ax.set_title(f"ECOSTRESS {regime}  DiD={o['beta']:+.2f}C "
                     f"({stars(o['p'])}, n={o['npre']+o['npost']})")
    ax.set_xlabel("overpass date")
axes[0].set_ylabel("LST delta  (Impact - Control), C")
axes[0].legend(loc="upper left", fontsize=8)
fig.suptitle("Shepperton parking-core ECOSTRESS LST anomaly, day vs night (T2)", y=1.02)
fig.tight_layout()
OUT = os.path.join(VIS, "ECOSTRESS_DayNight_2026-06-16.png")
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print(f"\nfigure -> {os.path.relpath(OUT, ROOT)}")
print("=" * 92)
