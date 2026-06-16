"""
ParallelTrends_FDR_2026-06-15.py
(a) Parallel-trends / pre-trend test for each BACI/DiD pipeline.
(b) Full p-value matrix of every significance test the project has reported,
    with Benjamini-Hochberg FDR control.

All p-values are computed live from the archived CSVs (no transcription),
reusing the project's conventions:
  delta = Impact - Control ; split CONSTRUCTION_DATE = 2021-06-01 ;
  HAC maxlags = ceil(n^(1/3)) (Andrews 1991).

ROI -> file mapping (note: filenames are inverted vs role, per README):
  NDVI            -> ee-chart_ndvi.csv          (Sprawl_Zone_Core - Control_Zone)
  LST full polygon-> ee-chart_lst_sensitivity.csv  (script 07, PRIMARY)
  LST parking core-> ee-chart_lst.csv              (script 07b, SENSITIVITY)
  ET              -> ee-chart_et.csv            (Sprawl_ET - Control_ET)
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import mannwhitneyu, ttest_ind
import pymannkendall as mk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw_telemetry")
SPLIT = pd.Timestamp("2021-06-01")


def ml(n):
    return int(np.ceil(n ** (1 / 3)))


def load_delta(fname, impact, control):
    df = pd.read_csv(os.path.join(RAW, fname))
    df["t"] = pd.to_datetime(df["system:time_start"])
    df = df.sort_values("t").set_index("t")
    df = df[[impact, control]].dropna()
    df["delta"] = df[impact] - df[control]
    return df


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "n.s."


# ----------------------------------------------------------------------
# (a) PARALLEL-TRENDS / PRE-TREND TESTS
# Pre-period only: delta ~ const + time(years). Slope ~ 0 => parallel.
# ----------------------------------------------------------------------
def pretrend(df, label):
    pre = df.loc[df.index < SPLIT].copy()
    t0 = pre.index.min()
    pre["yrs"] = (pre.index - t0).days / 365.25
    X = sm.add_constant(pre["yrs"].values)
    res = sm.OLS(pre["delta"].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": ml(len(pre))})
    slope = res.params[1]
    p = res.pvalues[1]
    ci = res.conf_int()[1]
    return dict(label=label, n=len(pre), slope=slope, p=p, ci=ci,
                span=pre["yrs"].max())


def run_parallel():
    metrics = [
        (load_delta("ee-chart_ndvi.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean"), "NDVI (core)"),
        (load_delta("ee-chart_lst_sensitivity.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean"), "LST full polygon (07)"),
        (load_delta("ee-chart_lst.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean"), "LST parking core (07b)"),
        (load_delta("ee-chart_et.csv", "Sprawl_ET_mean", "Control_ET_mean"), "ET (11)"),
    ]
    print("=" * 78)
    print("(a) PARALLEL-TRENDS PRE-TEST  | pre-period delta ~ time(years), HAC SE")
    print("    H0: pre-period slope = 0 (Impact and Control trend in parallel)")
    print("=" * 78)
    rows = []
    for df, lab in metrics:
        r = pretrend(df, lab)
        rows.append(r)
        verdict = "PASS (slope n.s.)" if r["p"] >= .05 else "FLAG (slope sig.)"
        print(f"{lab:24s} n_pre={r['n']:3d} span={r['span']:.1f}yr | "
              f"slope={r['slope']:+.4f}/yr | HAC p={r['p']:.4f} ({stars(r['p'])}) "
              f"| 95% CI [{r['ci'][0]:+.4f},{r['ci'][1]:+.4f}] -> {verdict}")
    return rows


# ----------------------------------------------------------------------
# (b) FULL p-VALUE MATRIX + BH-FDR
# ----------------------------------------------------------------------
def hac_did(df, mask=None, label=""):
    d = df if mask is None else df[mask]
    post = np.asarray(d.index >= SPLIT, dtype=float)
    X = sm.add_constant(post)
    res = sm.OLS(d["delta"].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": ml(len(d))})
    pre = d.loc[d.index < SPLIT, "delta"]
    pst = d.loc[d.index >= SPLIT, "delta"]
    _, mwp = mannwhitneyu(pre, pst, alternative="two-sided")
    return res.params[1], res.pvalues[1], mwp, len(d)


def annual_composite(df, months):
    d = df[df.index.month.isin(months)].copy()
    d["year"] = d.index.year
    ann = d.groupby("year")["delta"].mean()
    yrs = ann.index.values
    pre = ann[yrs < SPLIT.year].values
    pst = ann[yrs >= SPLIT.year].values
    t, p = ttest_ind(pre, pst, equal_var=False)
    return p, len(pre), len(pst)


def bh_fdr(pvals, alpha=0.05):
    p = np.asarray(pvals, float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    crit = (np.arange(1, n + 1) / n) * alpha
    passed = ranked <= crit
    kmax = np.where(passed)[0].max() + 1 if passed.any() else 0
    survive = np.zeros(n, bool)
    if kmax > 0:
        thr = ranked[kmax - 1]
        survive_sorted = ranked <= thr
        survive[order] = survive_sorted
    # BH-adjusted q-values (monotone)
    q = np.empty(n)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        val = ranked[i] * n / (i + 1)
        prev = min(prev, val)
        q[i] = prev
    qvals = np.empty(n)
    qvals[order] = q
    return survive, qvals


def run_matrix():
    ndvi = load_delta("ee-chart_ndvi.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean")
    lst_full = load_delta("ee-chart_lst_sensitivity.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean")
    lst_core = load_delta("ee-chart_lst.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean")
    et = load_delta("ee-chart_et.csv", "Sprawl_ET_mean", "Control_ET_mean")

    tests = []  # (metric, ROI, window, test, p)

    # NDVI
    _, ndvi_hac_p, _, n_nd = hac_did(ndvi)
    tests.append(("NDVI", "core", "full", "HAC OLS DiD", ndvi_hac_p))
    # Seasonal Mann-Kendall on monthly-resampled delta
    monthly = ndvi["delta"].resample("ME").mean().dropna()
    mkres = mk.seasonal_test(monthly.values, period=12)
    tests.append(("NDVI", "core", "full", "Seasonal Mann-Kendall", mkres.p))

    # LST full polygon (07)
    _, p, mwp, _ = hac_did(lst_full)
    tests.append(("LST", "full polygon", "full-year", "HAC OLS DiD", p))
    tests.append(("LST", "full polygon", "full-year", "Mann-Whitney U", mwp))
    jja = lst_full.index.month.isin([6, 7, 8])
    _, p, mwp, _ = hac_did(lst_full, jja)
    tests.append(("LST", "full polygon", "summer JJA", "HAC OLS DiD", p))
    tests.append(("LST", "full polygon", "summer JJA", "Mann-Whitney U", mwp))
    wp, _, _ = annual_composite(lst_full, [6, 7, 8])
    tests.append(("LST", "full polygon", "annual JJA composite", "Welch t", wp))

    # LST parking core (07b)
    _, p, mwp, _ = hac_did(lst_core)
    tests.append(("LST", "parking core", "full-year", "HAC OLS DiD", p))
    tests.append(("LST", "parking core", "full-year", "Mann-Whitney U", mwp))
    warm = lst_core.index.month.isin([4, 5, 6, 7, 8, 9])
    _, p, mwp, _ = hac_did(lst_core, warm)
    tests.append(("LST", "parking core", "warm Apr-Sep", "HAC OLS DiD", p))
    tests.append(("LST", "parking core", "warm Apr-Sep", "Mann-Whitney U", mwp))
    wp, _, _ = annual_composite(lst_core, [6, 7, 8])
    tests.append(("LST", "parking core", "annual JJA composite", "Welch t", wp))

    # ET
    _, p, mwp, _ = hac_did(et)
    tests.append(("ET", "500m", "full", "HAC OLS DiD", p))
    tests.append(("ET", "500m", "full", "Mann-Whitney U", mwp))

    pvals = [t[4] for t in tests]
    survive_all, q_all = bh_fdr(pvals)

    # primary family = HAC OLS DiD + Seasonal MK only (one primary test per ROI x window)
    prim_idx = [i for i, t in enumerate(tests) if t[3] in ("HAC OLS DiD", "Seasonal Mann-Kendall")]
    prim_p = [pvals[i] for i in prim_idx]
    surv_prim, q_prim = bh_fdr(prim_p)
    prim_survive = {prim_idx[j]: surv_prim[j] for j in range(len(prim_idx))}
    prim_q = {prim_idx[j]: q_prim[j] for j in range(len(prim_idx))}

    print("\n" + "=" * 98)
    print("(b) FULL p-VALUE MATRIX + Benjamini-Hochberg FDR (alpha=0.05)")
    print("=" * 98)
    print(f"{'metric':5s} {'ROI':13s} {'window':21s} {'test':22s} {'p':>10s} {'BH-q(all)':>10s} {'surv(all)':>9s}")
    print("-" * 98)
    for i, t in enumerate(tests):
        print(f"{t[0]:5s} {t[1]:13s} {t[2]:21s} {t[3]:22s} {t[4]:10.2e} {q_all[i]:10.2e} "
              f"{'YES' if survive_all[i] else 'no':>9s}")
    n_family = len(tests)
    print("-" * 98)
    print(f"FULL family: {int(survive_all.sum())}/{n_family} tests survive BH-FDR at alpha=0.05")

    print("\n  PRIMARY family only (HAC OLS DiD + Seasonal MK; excludes MW/Welch companions on same effect):")
    print(f"  {'metric':5s} {'ROI':13s} {'window':21s} {'p':>10s} {'BH-q(prim)':>11s} {'surv':>5s}")
    for i in prim_idx:
        t = tests[i]
        print(f"  {t[0]:5s} {t[1]:13s} {t[2]:21s} {pvals[i]:10.2e} {prim_q[i]:11.2e} "
              f"{'YES' if prim_survive[i] else 'no':>5s}")
    print(f"  PRIMARY family: {int(sum(prim_survive.values()))}/{len(prim_idx)} survive BH-FDR at alpha=0.05")
    return tests, survive_all, q_all, prim_idx, prim_survive, prim_q


def event_study_fig():
    metrics = [
        (load_delta("ee-chart_ndvi.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean"), "NDVI (core)", "#33CC66"),
        (load_delta("ee-chart_lst_sensitivity.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean"), "LST full polygon", "#FF8800"),
        (load_delta("ee-chart_lst.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean"), "LST parking core", "#FF4444"),
        (load_delta("ee-chart_et.csv", "Sprawl_ET_mean", "Control_ET_mean"), "ET", "#3399FF"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), dpi=180)
    for ax, (df, lab, c) in zip(axes.ravel(), metrics):
        d = df.copy()
        d["year"] = d.index.year
        ann = d.groupby("year")["delta"].agg(["mean", "count", "std"])
        ann["se"] = ann["std"] / np.sqrt(ann["count"])
        pre = ann[ann.index < SPLIT.year]
        ax.errorbar(ann.index, ann["mean"], yerr=1.96 * ann["se"], fmt="o-", color=c,
                    capsize=3, ms=5, lw=1.2)
        ax.axvline(SPLIT.year - 0.5, color="k", ls=":", lw=1.2, alpha=.6)
        ax.axhline(0, color="grey", lw=.8)
        # pre-trend line
        t0 = pre.index.min()
        xs = pre.index.values
        coef = np.polyfit(xs - t0, pre["mean"].values, 1)
        ax.plot(xs, np.polyval(coef, xs - t0), "--", color="black", alpha=.7, lw=1,
                label=f"pre-trend {coef[0]:+.3f}/yr")
        ax.set_title(lab, fontsize=11)
        ax.set_xlabel("year"); ax.set_ylabel(r"annual mean $\Delta$ (Impact-Control)")
        ax.legend(fontsize=8, loc="best")
        ax.grid(alpha=.2)
    fig.suptitle("Event-study annual DiD: pre-period parallel-trends check (split 2021-06-01) | 2026-06-15",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out = os.path.join(ROOT, "visualisations", "ParallelTrends_eventstudy_2026-06-15.png")
    fig.savefig(out, dpi=180, bbox_inches="tight")
    print(f"\nSAVED FIG: {out}")


if __name__ == "__main__":
    run_parallel()
    run_matrix()
    event_study_fig()
