"""
ET_2019_sensitivity_2026-06-15.py
2019 drought-year sensitivity analysis for the ET BACI/DiD.
Three specifications on ee-chart_et.csv, matching the mean-shift OLS +
Newey-West HAC methodology of scripts/11_plot_evapotranspiration.py:

  (a) baseline               : delta ~ const + Post
  (b) control for drought    : delta ~ const + Post + Drought2019
  (c) drop calendar-year 2019: delta ~ const + Post   (2019 rows removed)

delta = Sprawl_ET_mean - Control_ET_mean  (Impact - Control)
Split point CONSTRUCTION_DATE = 2021-06-01 (identical to script 11).
HAC bandwidth maxlags = ceil(n^(1/3)) (Andrews 1991), identical to script 11.
MW = Mann-Whitney U on pre vs post deltas (non-parametric companion).

No fabrication: every number below is printed from the live regression.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import mannwhitneyu
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "data", "raw_telemetry", "ee-chart_et.csv")
CONSTRUCTION_DATE = pd.Timestamp("2021-06-01")
FIG = os.path.join(ROOT, "visualisations", "ET_2019_sensitivity_2026-06-15.png")


def hac_maxlags(n):
    return int(np.ceil(n ** (1 / 3)))


def fit_hac(y, X):
    n = len(y)
    res = sm.OLS(y.values, X).fit(cov_type="HAC", cov_kwds={"maxlags": hac_maxlags(n)})
    return res


def load():
    df = pd.read_csv(CSV)
    df["t"] = pd.to_datetime(df["system:time_start"])
    df = df.sort_values("t").set_index("t")
    df = df[["Sprawl_ET_mean", "Control_ET_mean"]].dropna()
    df["delta"] = df["Sprawl_ET_mean"] - df["Control_ET_mean"]
    df["Post"] = (df.index >= CONSTRUCTION_DATE).astype(int)
    df["Drought2019"] = (df.index.year == 2019).astype(int)
    return df


def spec_a(df):
    X = sm.add_constant(df["Post"].values.astype(float))
    res = fit_hac(df["delta"], X)
    pre = df.loc[df["Post"] == 0, "delta"]
    post = df.loc[df["Post"] == 1, "delta"]
    _, mw = mannwhitneyu(pre, post, alternative="two-sided")
    return dict(beta=res.params[1], p=res.pvalues[1],
               ci=res.conf_int()[1], mw=mw, n=len(df),
               n_pre=len(pre), n_post=len(post),
               mw_pre=len(pre), mw_post=len(post), mw_desc="pre(all) vs post(all)")


def spec_b(df):
    X = sm.add_constant(np.column_stack([df["Post"].values, df["Drought2019"].values]).astype(float))
    res = fit_hac(df["delta"], X)
    # MW companion: removing 2019's leverage <=> compare pre-excl-2019 vs post
    pre = df.loc[(df["Post"] == 0) & (df["Drought2019"] == 0), "delta"]
    post = df.loc[df["Post"] == 1, "delta"]
    _, mw = mannwhitneyu(pre, post, alternative="two-sided")
    return dict(beta=res.params[1], p=res.pvalues[1],
               ci=res.conf_int()[1], mw=mw, n=len(df),
               drought_beta=res.params[2], drought_p=res.pvalues[2],
               mw_pre=len(pre), mw_post=len(post),
               mw_desc="pre(excl 2019) vs post(all)")


def spec_c(df):
    d = df[df["Drought2019"] == 0].copy()
    X = sm.add_constant(d["Post"].values.astype(float))
    res = fit_hac(d["delta"], X)
    pre = d.loc[d["Post"] == 0, "delta"]
    post = d.loc[d["Post"] == 1, "delta"]
    _, mw = mannwhitneyu(pre, post, alternative="two-sided")
    return dict(beta=res.params[1], p=res.pvalues[1],
               ci=res.conf_int()[1], mw=mw, n=len(d),
               n_pre=len(pre), n_post=len(post),
               mw_pre=len(pre), mw_post=len(post), mw_desc="pre(excl 2019) vs post(all)")


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "n.s."


def main():
    df = load()
    a, b, c = spec_a(df), spec_b(df), spec_c(df)

    print("=== ET 2019 drought sensitivity | split=2021-06-01 | delta=Impact-Control ===")
    print(f"Total valid 8-day obs n={len(df)} | 2019 obs={int(df['Drought2019'].sum())} (all in pre)\n")

    print("(a) baseline  delta ~ const + Post")
    print(f"    Post beta = {a['beta']:+.4f} mm/8-day | HAC p={a['p']:.4f} ({stars(a['p'])}) "
          f"| 95% CI [{a['ci'][0]:+.3f},{a['ci'][1]:+.3f}] | MW p={a['mw']:.4f} | "
          f"n={a['n']} (pre {a['n_pre']}/post {a['n_post']})\n")

    print("(b) control   delta ~ const + Post + Drought2019")
    print(f"    Post beta = {b['beta']:+.4f} mm/8-day | HAC p={b['p']:.4f} ({stars(b['p'])}) "
          f"| 95% CI [{b['ci'][0]:+.3f},{b['ci'][1]:+.3f}] | MW p={b['mw']:.4f} ({b['mw_desc']}) | n={b['n']}")
    print(f"    Drought2019 beta = {b['drought_beta']:+.4f} | HAC p={b['drought_p']:.4f} ({stars(b['drought_p'])})\n")

    print("(c) drop 2019 delta ~ const + Post  (calendar 2019 removed)")
    print(f"    Post beta = {c['beta']:+.4f} mm/8-day | HAC p={c['p']:.4f} ({stars(c['p'])}) "
          f"| 95% CI [{c['ci'][0]:+.3f},{c['ci'][1]:+.3f}] | MW p={c['mw']:.4f} | "
          f"n={c['n']} (pre {c['n_pre']}/post {c['n_post']})\n")

    # ---- sensitivity figure ----
    specs = ["(a) baseline", "(b) +Drought2019\ncovariate", "(c) drop 2019"]
    betas = [a["beta"], b["beta"], c["beta"]]
    los = [a["ci"][0], b["ci"][0], c["ci"][0]]
    his = [a["ci"][1], b["ci"][1], c["ci"][1]]
    ps = [a["p"], b["p"], c["p"]]
    err_lo = [betas[i] - los[i] for i in range(3)]
    err_hi = [his[i] - betas[i] for i in range(3)]

    fig, ax = plt.subplots(figsize=(8, 5), dpi=200)
    x = np.arange(3)
    colors = ["#888888", "#FF8800", "#3399FF"]
    ax.errorbar(x, betas, yerr=[err_lo, err_hi], fmt="o", ms=10, capsize=6,
                lw=2, ecolor="#444444", mfc="none")
    for i in range(3):
        ax.plot(x[i], betas[i], "o", ms=11, color=colors[i])
        ax.annotate(f"{betas[i]:+.3f}\nHAC p={ps[i]:.3f}\n{stars(ps[i])}",
                    (x[i], betas[i]), textcoords="offset points",
                    xytext=(14, 0), va="center", fontsize=9)
    ax.axhline(0, color="red", ls="--", lw=1, alpha=.7)
    ax.set_xticks(x)
    ax.set_xticklabels(specs)
    ax.set_ylabel(r"DiD Post coefficient ($\Delta$ET mm/8-day, Impact$-$Control)")
    ax.set_title("ET DiD: 2019 drought-year sensitivity (2026-06-15)\nMODIS MOD16A2GF | split 2021-06-01 | HAC + 95% CI")
    ax.set_xlim(-0.5, 2.9)
    ax.grid(axis="y", ls="--", alpha=.3)
    fig.tight_layout()
    fig.savefig(FIG, dpi=200, bbox_inches="tight")
    print(f"SAVED FIG: {FIG}")


if __name__ == "__main__":
    main()
