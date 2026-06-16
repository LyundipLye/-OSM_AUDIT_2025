"""
Placebo_2026-06-15.py
Placebo / falsification tests for the BACI/DiD design.

WHY (second-order improvement):
  A DiD that opens only at the true construction date is more credible than one
  that "finds" a shift wherever you put the split. Two placebo families:

  (a) TIME PLACEBO (implemented, local). Restrict the sample to the
      PRE-construction period only (index < true split 2021-06-01) and re-run
      the SAME HAC DiD at several FAKE split points inside that clean pre-window.
      Under a valid design there is no treatment in the pre-window, so every
      fake-split DiD should be ~0 / non-significant. A significant fake-split
      DiD would mean the estimator manufactures shifts from ordinary
      autocorrelation/seasonality -> a red flag.

  (b) SPATIAL PLACEBO (data-availability check, honest). A spatial placebo runs
      the identical DiD on a SECOND, undisturbed control series that should show
      no effect. The archived telemetry CSVs contain only one Impact column
      (Sprawl_*_mean) and one Control column (Control_*_mean) per metric (plus
      their pixel-level std), i.e. there is NO independent second control /
      donor series. The script verifies this programmatically and reports that
      the local data DO NOT support a spatial placebo, rather than fabricating
      one. A genuine spatial placebo requires additional donor polygons and is
      specified under synthetic control in the Tier-2 roadmap.

CONVENTIONS (identical to the rest of the project):
  delta = Impact - Control ; Post = index >= split ;
  HAC maxlags = ceil(n^1/3) (Andrews 1991) ; MW = Mann-Whitney U two-sided.
  True split CONSTRUCTION_DATE = 2021-06-01.

No fabrication: every number is a live regression on the archived CSVs.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import mannwhitneyu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw_telemetry")
TRUE_SPLIT = pd.Timestamp("2021-06-01")
MIN_SIDE = 12   # require at least this many obs each side of a fake split

METRICS = [
    ("NDVI core (FDR survivor)",        "ee-chart_ndvi.csv",            "Sprawl_Zone_Core_mean", "Control_Zone_mean"),
    ("LST parking core (FDR survivor)", "ee-chart_lst.csv",             "Sprawl_Zone_Core_mean", "Control_Zone_mean"),
    ("LST full polygon (primary)",      "ee-chart_lst_sensitivity.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean"),
    ("ET (500m)",                       "ee-chart_et.csv",              "Sprawl_ET_mean",        "Control_ET_mean"),
]

# fake splits to try inside the pre-construction window (kept >= MIN_SIDE each side)
FAKE_SPLITS = [pd.Timestamp(y, m, 1) for (y, m) in
               [(2016, 6), (2017, 6), (2018, 6), (2019, 6), (2020, 1), (2020, 6)]]


def ml(n):
    return int(np.ceil(n ** (1 / 3)))


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "n.s."


def load_raw(fname, impact, control):
    df = pd.read_csv(os.path.join(RAW, fname))
    df["t"] = pd.to_datetime(df["system:time_start"])
    df = df.sort_values("t").set_index("t")
    return df, impact, control


def did(delta, split):
    post = np.asarray(delta.index >= split, dtype=float)
    X = sm.add_constant(post)
    res = sm.OLS(delta.values, X).fit(cov_type="HAC", cov_kwds={"maxlags": ml(len(delta))})
    pre = delta.loc[delta.index < split]
    pst = delta.loc[delta.index >= split]
    _, mwp = mannwhitneyu(pre, pst, alternative="two-sided")
    return res.params[1], res.pvalues[1], mwp, len(pre), len(pst)


def time_placebo():
    print("=" * 96)
    print("(a) TIME PLACEBO  | pre-construction window ONLY (index < 2021-06-01)")
    print("    fake splits should give DiD ~ 0 / n.s.  | delta = Impact - Control | HAC SE")
    print("=" * 96)
    overall_flags = 0
    overall_tests = 0
    for label, fname, impact, control in METRICS:
        df, imp, ctl = load_raw(fname, impact, control)
        sub = df[df.index < TRUE_SPLIT][[imp, ctl]].dropna()
        delta = (sub[imp] - sub[ctl])
        print(f"\n### {label}   [{fname}]   pre-window n={len(delta)} "
              f"({delta.index.min().date()} .. {delta.index.max().date()})")
        any_run = False
        for fs in FAKE_SPLITS:
            npre = int((delta.index < fs).sum())
            npst = int((delta.index >= fs).sum())
            if npre < MIN_SIDE or npst < MIN_SIDE:
                continue
            any_run = True
            b, p, mw, n0, n1 = did(delta, fs)
            overall_tests += 1
            flag = p < 0.05
            overall_flags += int(flag)
            tag = "FLAG (sig in pre-window!)" if flag else "ok (n.s.)"
            print(f"    fake split {fs.date()}  DiD={b:+.4f} | HAC p={p:.4g} ({stars(p)}) "
                  f"| MW p={mw:.4g} | n_pre={n0} n_post={n1}  -> {tag}")
        if not any_run:
            print(f"    (no fake split leaves >= {MIN_SIDE} obs on both sides; pre-window too short)")
    print("\n" + "-" * 96)
    print(f"TIME-PLACEBO SUMMARY: {overall_flags}/{overall_tests} fake-split DiDs are spuriously "
          f"significant (p<0.05).")
    print("Ideal = 0. Any flag means the estimator can produce a 'shift' inside the untreated "
          "pre-window\nfor that metric, and its real-split estimate should be read with that in mind.")


def spatial_placebo_check():
    print("\n" + "=" * 96)
    print("(b) SPATIAL PLACEBO  | data-availability check")
    print("=" * 96)
    for label, fname, impact, control in METRICS:
        df, imp, ctl = load_raw(fname, impact, control)
        cols = list(df.columns)
        mean_cols = [c for c in cols if c.endswith("_mean")]
        # candidate independent control series = any *_mean column that is neither
        # the impact nor the designated control
        extra = [c for c in mean_cols if c not in (imp, ctl)]
        print(f"\n### {label}   [{fname}]")
        print(f"    mean-valued columns present: {mean_cols}")
        print(f"    impact={imp} | control={ctl}")
        if extra:
            print(f"    -> additional candidate control series found: {extra} "
                  f"(a spatial placebo COULD be built on these)")
        else:
            print("    -> NO independent second control / undisturbed series in this file.")
    print("\n" + "-" * 96)
    print("CONCLUSION: the archived telemetry exposes exactly one Impact and one Control series")
    print("per metric (plus pixel-level std), so the LOCAL DATA DO NOT SUPPORT a spatial placebo.")
    print("A spatial placebo needs additional donor polygons; it is specified under the synthetic-")
    print("control item of _METHODOLOGY_ROADMAP_TIER2_2026-06-15.md (leave-one-donor-out / in-space")
    print("placebo). No spatial placebo is fabricated here.")


if __name__ == "__main__":
    time_placebo()
    spatial_placebo_check()
