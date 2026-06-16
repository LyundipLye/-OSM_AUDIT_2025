"""
SpecCurve_2026-06-15.py
Specification-curve / multiverse analysis over the locally-variable
researcher degrees of freedom, for each headline biophysical DiD.

WHY (second-order improvement):
  A single headline DiD coefficient hides how much the result depends on
  arbitrary analyst choices. A specification curve (Simonsohn, Simmons &
  Nelson 2020) runs the SAME estimand under every reasonable combination of
  defensible choices and shows the whole distribution of estimates, so a
  reader can see whether the sign and significance are an artefact of one
  lucky specification or hold across the multiverse.

DEGREES OF FREEDOM SWEPT (only the locally-variable ones; ROI/file fixed):
  1. BACI split date : monthly grid 2021-02-01 .. 2021-12-01 (11 levels).
  2. Season / month window : full-year, growing Mar-Oct, warm Apr-Sep,
     summer JJA (4 levels).
  3. HAC bandwidth (Newey-West maxlags) : Andrews ceil(n^1/3); Newey-West
     rule-of-thumb ceil(4*(n/100)^(2/9)); 2x Andrews; fixed 6 (4 levels).
  => up to 11 x 4 x 4 = 176 specifications per metric.

ESTIMAND (fixed, per project convention):
  delta = Impact - Control ; Post = index >= split ;
  DiD = OLS mean-shift coefficient on Post, HAC SE.
  Two-sided significance at alpha = 0.05.

REPORTED PER METRIC:
  estimate distribution (median / IQR / min / max), sign-consistency with the
  headline 2021-06-01 / full-year spec, and the share of specifications that
  are significant. Figure = classic spec curve (sorted estimates + 95% CI +
  significance shading on top; choice dot-matrix below).

ROI -> file mapping (filenames inverted vs role, per README). No fabrication:
  every estimate is a live regression on the archived CSVs.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw_telemetry")
VIS = os.path.join(ROOT, "visualisations")

METRICS = [
    ("NDVI_core",        "NDVI core (FDR survivor)",        "ee-chart_ndvi.csv",            "Sprawl_Zone_Core_mean", "Control_Zone_mean", "#33CC66"),
    ("LST_parking_core", "LST parking core (FDR survivor)", "ee-chart_lst.csv",             "Sprawl_Zone_Core_mean", "Control_Zone_mean", "#FF4444"),
    ("LST_full_polygon", "LST full polygon (primary)",      "ee-chart_lst_sensitivity.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean", "#FF8800"),
    ("ET_500m",          "ET (500m)",                       "ee-chart_et.csv",              "Sprawl_ET_mean",        "Control_ET_mean",   "#3399FF"),
]

SPLITS = [pd.Timestamp(2021, m, 1) for m in range(2, 13)]   # 2021-02 .. 2021-12
WINDOWS = {
    "full-year":      list(range(1, 13)),
    "grow Mar-Oct":   [3, 4, 5, 6, 7, 8, 9, 10],
    "warm Apr-Sep":   [4, 5, 6, 7, 8, 9],
    "summer JJA":     [6, 7, 8],
}
HEADLINE_SPLIT = pd.Timestamp("2021-06-01")
HEADLINE_WIN = "full-year"


def andrews(n):
    return int(np.ceil(n ** (1 / 3)))


def newey_rot(n):
    return int(np.ceil(4 * (n / 100.0) ** (2.0 / 9.0)))


def bandwidths(n):
    return {
        "Andrews n^1/3":  andrews(n),
        "NW rule-of-thumb": newey_rot(n),
        "2x Andrews":     2 * andrews(n),
        "fixed 6":        6,
    }


def load_delta(fname, impact, control):
    df = pd.read_csv(os.path.join(RAW, fname))
    df["t"] = pd.to_datetime(df["system:time_start"])
    df = df.sort_values("t").set_index("t")
    df = df[[impact, control]].dropna()
    df["delta"] = df[impact] - df[control]
    return df


def did(df, split, months, maxlags):
    d = df[df.index.month.isin(months)]
    if len(d) < 12:
        return None
    post = np.asarray(d.index >= split, dtype=float)
    if post.sum() < 4 or (len(post) - post.sum()) < 4:
        return None
    X = sm.add_constant(post)
    ml = max(1, min(maxlags, len(d) - 2))
    res = sm.OLS(d["delta"].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": ml})
    return res.params[1], res.pvalues[1], res.conf_int()[1], len(d)


def run_metric(fname, impact, control):
    df = load_delta(fname, impact, control)
    specs = []
    for split in SPLITS:
        for wname, months in WINDOWS.items():
            n_full = len(df[df.index.month.isin(months)])
            for bname, ml in bandwidths(n_full).items():
                r = did(df, split, months, ml)
                if r is None:
                    continue
                beta, p, ci, n = r
                specs.append(dict(split=split, window=wname, bw=bname,
                                  beta=beta, p=p, lo=ci[0], hi=ci[1], n=n))
    return pd.DataFrame(specs)


def summarise(name, label, sc):
    head = sc[(sc["split"] == HEADLINE_SPLIT) & (sc["window"] == HEADLINE_WIN)]
    head_sign = np.sign(head["beta"].median()) if len(head) else np.sign(sc["beta"].median())
    sign_consistent = (np.sign(sc["beta"]) == head_sign).mean() * 100
    pct_sig = (sc["p"] < 0.05).mean() * 100
    pct_sig_signed = ((sc["p"] < 0.05) & (np.sign(sc["beta"]) == head_sign)).mean() * 100
    print(f"\n### {label}   [{name}]   {len(sc)} specifications")
    print(f"    beta: median {sc['beta'].median():+.4f} | IQR [{sc['beta'].quantile(.25):+.4f},"
          f"{sc['beta'].quantile(.75):+.4f}] | min {sc['beta'].min():+.4f} | max {sc['beta'].max():+.4f}")
    print(f"    headline-sign = {'+' if head_sign > 0 else '-'} | "
          f"sign-consistent with headline: {sign_consistent:.1f}% of specs")
    print(f"    significant (p<0.05): {pct_sig:.1f}% of specs | "
          f"significant AND headline-signed: {pct_sig_signed:.1f}%")
    # median p by window
    for w in WINDOWS:
        sub = sc[sc["window"] == w]
        if len(sub):
            print(f"      - {w:14s}: median beta {sub['beta'].median():+.4f}, "
                  f"median p {sub['p'].median():.3f}, %sig {100*(sub['p']<0.05).mean():.0f}")
    return dict(sign_consistent=sign_consistent, pct_sig=pct_sig,
                pct_sig_signed=pct_sig_signed, head_sign=head_sign)


def plot_spec_curve(name, label, color, sc):
    sc = sc.sort_values("beta").reset_index(drop=True)
    x = np.arange(len(sc))
    sig = sc["p"] < 0.05

    fig = plt.figure(figsize=(12, 8.5), dpi=160)
    gs = GridSpec(2, 1, height_ratios=[2.2, 1.6], hspace=0.06)
    ax = fig.add_subplot(gs[0])
    # CI band
    ax.vlines(x, sc["lo"], sc["hi"], color="#cccccc", lw=0.8, zorder=1)
    ax.scatter(x[~sig], sc["beta"][~sig], s=12, c="#999999", zorder=3, label="n.s. (p>=0.05)")
    ax.scatter(x[sig], sc["beta"][sig], s=14, c=color, zorder=4, label="sig (p<0.05)")
    ax.axhline(0, color="red", ls="--", lw=1, alpha=.7)
    ax.set_ylabel(r"DiD Post coefficient ($\Delta$ Impact-Control)")
    ax.set_title(f"Specification curve — {label}\n"
                 f"{len(sc)} specs = split(2021-02..12) x window(4) x HAC bw(4) | "
                 f"{100*sig.mean():.0f}% significant | 2026-06-15", fontsize=11)
    ax.legend(fontsize=8, loc="best")
    ax.grid(axis="y", alpha=.2)
    ax.set_xlim(-1, len(sc))

    # choice dot-matrix
    ax2 = fig.add_subplot(gs[1], sharex=ax)
    rows = ([("split " + s.strftime("%Y-%m")) for s in SPLITS]
            + ["win " + w for w in WINDOWS]
            + ["bw " + b for b in bandwidths(100)])
    row_idx = {r: i for i, r in enumerate(rows)}
    for j in range(len(sc)):
        srow = sc.iloc[j]
        keys = ["split " + srow["split"].strftime("%Y-%m"),
                "win " + srow["window"], "bw " + srow["bw"]]
        col = color if srow["p"] < 0.05 else "#999999"
        for k in keys:
            ax2.scatter(j, row_idx[k], s=6, c=col, marker="s")
    ax2.set_yticks(range(len(rows)))
    ax2.set_yticklabels(rows, fontsize=7)
    ax2.set_xlabel("specification (sorted by estimate)")
    ax2.invert_yaxis()
    ax2.grid(axis="x", alpha=.15)
    out = os.path.join(VIS, f"SpecCurve_{name}_2026-06-15.png")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"    SAVED FIG: {out}")


def main():
    print("=" * 92)
    print("SPECIFICATION-CURVE / MULTIVERSE  | estimand: HAC DiD Post coef, delta=Impact-Control")
    print("DoF swept: split date (11) x season window (4) x HAC bandwidth (4)")
    print("=" * 92)
    for name, label, fname, impact, control, color in METRICS:
        sc = run_metric(fname, impact, control)
        summarise(name, label, sc)
        plot_spec_curve(name, label, color, sc)


if __name__ == "__main__":
    main()
