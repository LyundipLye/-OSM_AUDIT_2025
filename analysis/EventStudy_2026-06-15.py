"""
EventStudy_2026-06-15.py
Dynamic / event-study Difference-in-Differences for each BACI pipeline.

WHY (second-order improvement over the single-Post dummy):
  The headline DiD collapses the post-treatment period into one mean-shift
  coefficient. That cannot show *when* the effect opens, nor whether the
  pre-period leads are flat (the parallel-trends identification assumption).
  This script replaces the single Post dummy with a full set of event-time
  leads + lags relative to the construction split, so we can check that:
    (i)  pre-period lead coefficients are ~0 (parallel trends, cross-checked
         against ParallelTrends_FDR_2026-06-15.py); and
    (ii) the effect "opens" at / after the construction split, not before.

METHOD / PROJECT CONVENTIONS (identical to ParallelTrends_FDR / Split_Robustness):
  delta = Impact - Control.
  Split CONSTRUCTION_DATE = 2021-06-01.
  Event time measured in HALF-YEAR (182.625-day) bins relative to the split.
  Reference (omitted, coefficient fixed at 0) = the last pre-split half-year,
  event-bin index -1, so every plotted coefficient is a contrast vs the
  immediate pre-construction baseline.
  HAC (Newey-West) covariance, maxlags = ceil(n^(1/3)) (Andrews 1991), on the
  FULL pooled event-time regression.
  Bins with < MIN_OBS observations are dropped (and reported) to avoid a
  near-singular design; this only trims the sparse calendar extremes.
  Joint pre-trend test: HAC Wald test that ALL surviving lead coefficients
  (event-bin <= -2) are simultaneously 0. Caveat (Roth 2022): a low-power
  pre-test is corroboration, not an exemption.

ROI -> file mapping (filenames are inverted vs role, per README):
  NDVI core (FDR survivor) -> ee-chart_ndvi.csv          (Sprawl_Zone_Core_mean - Control_Zone_mean)
  LST parking core (survivor)-> ee-chart_lst.csv         (Sprawl_Zone_Core_mean - Control_Zone_mean)
  LST full polygon (primary)-> ee-chart_lst_sensitivity.csv (Sprawl_Zone_Core_mean - Control_Zone_mean)
  ET                       -> ee-chart_et.csv            (Sprawl_ET_mean - Control_ET_mean)

No fabrication: every number is printed from the live regression on the
archived CSVs. Run with the project venv (audit_env/bin/python); reproduces
the documented Split_Robustness numbers bit-for-bit.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw_telemetry")
SPLIT = pd.Timestamp("2021-06-01")
BIN_DAYS = 182.625          # half-year event bins
MIN_OBS = 5                 # drop event bins with fewer obs than this
FIG = os.path.join(ROOT, "visualisations", "EventStudy_2026-06-15.png")

METRICS = [
    ("NDVI core (FDR survivor)",       "ee-chart_ndvi.csv",            "Sprawl_Zone_Core_mean", "Control_Zone_mean", "#33CC66"),
    ("LST parking core (FDR survivor)","ee-chart_lst.csv",             "Sprawl_Zone_Core_mean", "Control_Zone_mean", "#FF4444"),
    ("LST full polygon (primary)",     "ee-chart_lst_sensitivity.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean", "#FF8800"),
    ("ET (500m)",                      "ee-chart_et.csv",              "Sprawl_ET_mean",        "Control_ET_mean",   "#3399FF"),
]


def ml(n):
    return int(np.ceil(n ** (1 / 3)))


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "n.s."


def load_delta(fname, impact, control):
    df = pd.read_csv(os.path.join(RAW, fname))
    df["t"] = pd.to_datetime(df["system:time_start"])
    df = df.sort_values("t").set_index("t")
    df = df[[impact, control]].dropna()
    df["delta"] = df[impact] - df[control]
    return df


def event_bins(df):
    rel_days = (df.index - SPLIT).days.values.astype(float)
    # bin index: 0 = first half-year on/after split; -1 = last half-year before split
    b = np.floor(rel_days / BIN_DAYS).astype(int)
    return b


def event_study(df, label):
    d = df.copy()
    d["ebin"] = event_bins(d)
    counts = d["ebin"].value_counts().sort_index()
    keep = counts[counts >= MIN_OBS].index
    dropped = counts[counts < MIN_OBS]
    d = d[d["ebin"].isin(keep)].copy()

    ref = -1  # last pre-split half-year = omitted baseline
    if ref not in set(d["ebin"]):
        # fall back to the largest pre-split bin available
        pre_bins = sorted([b for b in keep if b < 0])
        ref = pre_bins[-1] if pre_bins else sorted(keep)[0]

    bins = sorted(b for b in d["ebin"].unique() if b != ref)
    # design matrix: const + dummy per non-reference bin
    X = np.column_stack([(d["ebin"].values == b).astype(float) for b in bins])
    X = sm.add_constant(X)
    y = d["delta"].values
    res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": ml(len(y))})

    coefs = res.params[1:]
    pvals = res.pvalues[1:]
    ci = res.conf_int()[1:]
    name_idx = {b: i for i, b in enumerate(bins)}

    # joint pre-trend Wald test: all lead bins (<= -2) == 0
    leads = [b for b in bins if b <= -2]
    pretrend_p = np.nan
    if leads:
        R = np.zeros((len(leads), X.shape[1]))
        for r, b in enumerate(leads):
            R[r, 1 + name_idx[b]] = 1.0
        wt = res.wald_test(R, scalar=True)
        pretrend_p = float(wt.pvalue)

    # first post bin (>=0) opening test
    open_b = min((b for b in bins if b >= 0), default=None)
    open_info = None
    if open_b is not None:
        j = name_idx[open_b]
        open_info = (open_b, coefs[j], pvals[j], ci[j])

    rows = []
    rows.append(dict(ebin=ref, beta=0.0, p=np.nan, lo=np.nan, hi=np.nan,
                     n=int((d["ebin"] == ref).sum()), role="REF"))
    for b in bins:
        j = name_idx[b]
        rows.append(dict(ebin=b, beta=coefs[j], p=pvals[j], lo=ci[j][0], hi=ci[j][1],
                         n=int((d["ebin"] == b).sum()),
                         role="lead" if b <= -2 else ("REF" if b == -1 else "lag")))
    tab = pd.DataFrame(rows).sort_values("ebin").reset_index(drop=True)
    return dict(label=label, tab=tab, ref=ref, pretrend_p=pretrend_p,
                open=open_info, n=len(y), dropped=dropped)


def ebin_to_year(b):
    # left edge of the half-year bin as a calendar date, for readable x-axis
    return SPLIT + pd.Timedelta(days=b * BIN_DAYS)


def main():
    print("=" * 92)
    print("EVENT-STUDY DiD  | half-year bins | ref = last pre-split half-year (ebin -1)")
    print(f"split = {SPLIT.date()} | delta = Impact - Control | HAC maxlags = ceil(n^1/3)")
    print("=" * 92)

    results = []
    for label, fname, impact, control, _ in METRICS:
        df = load_delta(fname, impact, control)
        r = event_study(df, label)
        results.append(r)
        print(f"\n### {label}   [{fname}]   n={r['n']}  ref bin={r['ref']}")
        if len(r["dropped"]):
            dd = ", ".join(f"{int(b)}:{int(c)}" for b, c in r["dropped"].items())
            print(f"    dropped sparse bins (<{MIN_OBS} obs): {dd}")
        print(f"    {'ebin':>5s} {'window (left edge)':>18s} {'role':>5s} {'n':>4s} "
              f"{'beta':>9s} {'95% CI':>20s} {'p':>9s}")
        for _, row in r["tab"].iterrows():
            edge = ebin_to_year(row["ebin"]).date()
            if row["role"] == "REF":
                print(f"    {int(row['ebin']):5d} {str(edge):>18s} {'REF':>5s} {int(row['n']):4d} "
                      f"{0.0:9.4f} {'(baseline=0)':>20s} {'-':>9s}")
            else:
                ci = f"[{row['lo']:+.3f},{row['hi']:+.3f}]"
                print(f"    {int(row['ebin']):5d} {str(edge):>18s} {row['role']:>5s} {int(row['n']):4d} "
                      f"{row['beta']:+9.4f} {ci:>20s} {row['p']:9.2e} {stars(row['p'])}")
        if not np.isnan(r["pretrend_p"]):
            verdict = "PASS (leads jointly n.s.)" if r["pretrend_p"] >= .05 else "FLAG (leads jointly sig.)"
            print(f"    >> joint pre-trend (all leads ebin<=-2 = 0): HAC Wald p={r['pretrend_p']:.4f} -> {verdict}")
        else:
            print("    >> joint pre-trend: not enough surviving lead bins for a joint test")
        if r["open"] is not None:
            ob, obeta, op, oci = r["open"]
            print(f"    >> opening bin ebin={ob} ({ebin_to_year(ob).date()}): "
                  f"beta={obeta:+.4f} CI[{oci[0]:+.3f},{oci[1]:+.3f}] HAC p={op:.2e} ({stars(op)})")

    # ---------------- figure ----------------
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5), dpi=170)
    for ax, r, (label, _, _, _, c) in zip(axes.ravel(), results, METRICS):
        tab = r["tab"]
        x = [ebin_to_year(b) for b in tab["ebin"]]
        beta = tab["beta"].values
        lo = tab["lo"].values
        hi = tab["hi"].values
        yerr_lo = beta - lo
        yerr_hi = hi - beta
        # reference point has no CI
        mask_ci = ~np.isnan(lo)
        ax.errorbar(np.array(x)[mask_ci], beta[mask_ci],
                    yerr=[yerr_lo[mask_ci], yerr_hi[mask_ci]],
                    fmt="o", color=c, capsize=3, ms=5, lw=1.1, ecolor="#555555")
        # reference marker
        ax.plot(np.array(x)[~mask_ci], beta[~mask_ci], "s", color="black", ms=7,
                label="reference (ebin -1)")
        ax.axvline(SPLIT, color="k", ls=":", lw=1.3, alpha=.7)
        ax.axhline(0, color="grey", lw=.8)
        ax.set_title(label, fontsize=11)
        ax.set_xlabel("event time (half-year bin, left edge)")
        ax.set_ylabel(r"event-time $\beta$ ($\Delta$ vs pre-split baseline)")
        sub = (f"pre-trend Wald p={r['pretrend_p']:.3f}" if not np.isnan(r["pretrend_p"])
               else "pre-trend: n/a")
        if r["open"] is not None:
            sub += f" | open p={r['open'][2]:.1e}"
        ax.text(0.02, 0.04, sub, transform=ax.transAxes, fontsize=8.5,
                bbox=dict(boxstyle="round", fc="white", ec="grey", alpha=.8))
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(alpha=.2)
    fig.suptitle("Event-study dynamic DiD: leads should be ~0, effect should open at the split "
                 f"(dotted = {SPLIT.date()}) | 2026-06-15", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(FIG, dpi=170, bbox_inches="tight")
    print(f"\nSAVED FIG: {FIG}")


if __name__ == "__main__":
    main()
