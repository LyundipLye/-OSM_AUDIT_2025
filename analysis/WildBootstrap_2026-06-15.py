"""
WildBootstrap_2026-06-15.py
Wild bootstrap-t for the small-sample ANNUAL-COMPOSITE DiD.

WHY (second-order improvement):
  The annual JJA composites (07c) collapse the time series to ~6 pre / ~5 post
  annual means and test the regime shift with a Welch t-test. With n that small,
  the t-distribution reference is unreliable. The wild bootstrap (Wu 1986;
  Cameron, Gelbach & Miller 2008; MacKinnon & Webb 2017) imposes the null,
  resamples residuals with Rademacher (+/-1) weights, and builds the reference
  distribution of the t-statistic empirically. It is the standard small-sample
  fix and is reported here ALONGSIDE the naive Welch/OLS t, not as a replacement.

METHOD:
  Composite: for each metric, take the chosen month window, average delta within
  each calendar year -> one annual mean per year. Regress annual_delta ~ const + Post,
  Post = (year >= split_year). Statistic of interest = beta_Post.
  Restricted wild bootstrap-t (WCR, recommended by MacKinnon & Webb 2017):
    1. Fit restricted model under H0: beta_Post = 0 (regress on const only).
    2. For b in 1..B: y* = fitted_restricted + Rademacher_b * resid_restricted ;
       refit unrestricted; t*_b = beta1*_b / se(beta1*_b)  [HC1 SE].
    3. p = mean( |t*_b| >= |t_obs| ) , t_obs from the unrestricted fit.
  B = 9999. delta = Impact - Control ; split year = 2021 (CONSTRUCTION_DATE 2021-06-01).
  Each annual mean is its own cluster (annual aggregation removes within-year
  autocorrelation), so observation-level wild bootstrap = wild-cluster bootstrap here.

No fabrication: bootstrap p-values are computed live; seed fixed for reproducibility.
"""
import os
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw_telemetry")
SPLIT_YEAR = 2021
B = 9999
SEED = 20260615

CASES = [
    # label, file, impact, control, months, window-name
    ("NDVI core",        "ee-chart_ndvi.csv",            "Sprawl_Zone_Core_mean", "Control_Zone_mean", list(range(1, 13)), "full-year"),
    ("LST parking core", "ee-chart_lst.csv",             "Sprawl_Zone_Core_mean", "Control_Zone_mean", [6, 7, 8],          "summer JJA"),
    ("LST parking core", "ee-chart_lst.csv",             "Sprawl_Zone_Core_mean", "Control_Zone_mean", [4, 5, 6, 7, 8, 9], "warm Apr-Sep"),
    ("LST full polygon", "ee-chart_lst_sensitivity.csv", "Sprawl_Zone_Core_mean", "Control_Zone_mean", [6, 7, 8],          "summer JJA"),
    ("ET 500m",          "ee-chart_et.csv",              "Sprawl_ET_mean",        "Control_ET_mean",   [6, 7, 8],          "summer JJA"),
    ("ET 500m",          "ee-chart_et.csv",              "Sprawl_ET_mean",        "Control_ET_mean",   [4, 5, 6, 7, 8, 9], "warm Apr-Sep"),
]


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "n.s."


def load_delta(fname, impact, control):
    df = pd.read_csv(os.path.join(RAW, fname))
    df["t"] = pd.to_datetime(df["system:time_start"])
    df = df.sort_values("t").set_index("t")
    df = df[[impact, control]].dropna()
    df["delta"] = df[impact] - df[control]
    return df


def annual_composite(df, months):
    d = df[df.index.month.isin(months)].copy()
    d["year"] = d.index.year
    ann = d.groupby("year")["delta"].mean()
    return ann


def ols_beta_t(y, post):
    """Unrestricted OLS y ~ const + post; return beta1 and HC1 t-stat."""
    X = np.column_stack([np.ones_like(post), post])
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta
    n, k = X.shape
    # HC1 heteroskedasticity-robust covariance
    meat = (X * (resid ** 2)[:, None]).T @ X
    cov = XtX_inv @ meat @ XtX_inv * (n / (n - k))
    se1 = np.sqrt(cov[1, 1])
    return beta[1], beta[1] / se1, se1


def wild_bootstrap(ann, B=B, seed=SEED):
    yrs = ann.index.values
    y = ann.values.astype(float)
    post = (yrs >= SPLIT_YEAR).astype(float)
    n_pre = int((post == 0).sum())
    n_post = int((post == 1).sum())
    beta_obs, t_obs, se_obs = ols_beta_t(y, post)

    # restricted fit under H0: beta1 = 0  -> y ~ const only
    mu = y.mean()
    resid_r = y - mu
    fitted_r = np.full_like(y, mu)

    rng = np.random.default_rng(seed)
    count = 0
    t_star = np.empty(B)
    for b in range(B):
        v = rng.choice([-1.0, 1.0], size=len(y))   # Rademacher
        y_star = fitted_r + v * resid_r
        _, t_b, _ = ols_beta_t(y_star, post)
        t_star[b] = t_b
        if abs(t_b) >= abs(t_obs):
            count += 1
    p_boot = (count + 1) / (B + 1)   # MacKinnon (2015) finite-sample correction

    # naive Welch t for comparison
    pre = y[post == 0]
    pst = y[post == 1]
    _, p_welch = ttest_ind(pre, pst, equal_var=False)
    return dict(beta=beta_obs, t=t_obs, se=se_obs, n_pre=n_pre, n_post=n_post,
                p_boot=p_boot, p_welch=p_welch)


def main():
    print("=" * 92)
    print(f"WILD BOOTSTRAP-t (Rademacher, B={B}, restricted/WCR) on ANNUAL composites")
    print(f"split year = {SPLIT_YEAR} | delta = Impact - Control | seed = {SEED}")
    print("=" * 92)
    print(f"{'metric':18s} {'window':13s} {'n_pre/post':>10s} {'beta':>9s} {'t_obs':>7s} "
          f"{'Welch p':>9s} {'wild p':>9s} {'verdict':>8s}")
    print("-" * 92)
    for label, fname, impact, control, months, wname in CASES:
        df = load_delta(fname, impact, control)
        ann = annual_composite(df, months)
        r = wild_bootstrap(ann)
        print(f"{label:18s} {wname:13s} {str(r['n_pre'])+'/'+str(r['n_post']):>10s} "
              f"{r['beta']:+9.4f} {r['t']:+7.2f} {r['p_welch']:9.3f} "
              f"{r['p_boot']:9.4f} {stars(r['p_boot']):>8s}")
    print("-" * 92)
    print("Note: wild p is the small-sample-honest reference. Where wild p > Welch p the")
    print("naive t over-stated significance; where wild p < Welch p the t was conservative.")
    print("Annual composites rest on very few clusters (<=6 pre / <=5 post); even the wild")
    print("bootstrap cannot manufacture power from ~11 points -- it only corrects the reference.")


if __name__ == "__main__":
    main()
