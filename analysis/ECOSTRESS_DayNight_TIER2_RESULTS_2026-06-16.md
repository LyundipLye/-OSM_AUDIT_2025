# T2 — ECOSTRESS day/night LST (LIVE RESULT, 2026-06-16)

**Script:** `analysis/ECOSTRESS_Night_TIER2_2026-06-16.py` (supersedes the data-blocked
06-15 stub). **Data:** NASA AppEEARS point extraction `ECO_L2T_LSTE.002`, request
`126592dd-1c43-4f82-83d1-d40279b5ddd3`, Impact 51.410315/-0.469366 + Control
51.407395/-0.410459, 2018-07-28 → 2026-03-31. **Figure:** `visualisations/ECOSTRESS_DayNight_2026-06-16.png`.

## Method
Per-overpass `delta = Impact − Control` (Impact & Control sampled at the *same* ISS overpass →
identical solar geometry, K==°C for a difference). QA per ECO_L2T_LSTE.002 User Guide v2: keep
TES-produced + cloud==0 (clear) + water==0 + LST not-NaN; tile-overlap duplicates averaged per
(Category, overpass). Day/night by inline NOAA solar elevation (night = sun < 0°; only ~9–10% of
overpasses fall within 6° of the terminator, so the split is clean). Canonical DiD:
`OLS delta ~ const + Post`, Post = t≥2021-06-01, Newey–West HAC maxlags=⌈n^(1/3)⌉; Mann–Whitney U
pre/post companion. 1,189 paired clean overpasses (489 night / 700 day).

## Result (primary = all produced-clear; sensitivity = LST_accuracy ≤2 K in brackets)

| Regime | DiD (Impact−Control) | HAC p | MW p | pre mean | post mean | n_pre/n_post | split 2021-10-01 |
|---|---|---|---|---|---|---|---|
| **DAY**   | **+0.72 °C** [+0.68] | **0.0062** [0.0076] | 6.1e-4 [8.1e-4] | **−0.45** | **+0.27** | 246/454 | +0.64 °C, p=0.013 |
| **NIGHT** | +0.32 °C [+0.31] | 0.195 (n.s.) [0.20] | 0.038 [0.041] | +0.30 | +0.62 | 137/352 | +0.28 °C, n.s. |

## Interpretation (honest)
1. **DAY is the find — and it is independent corroboration.** A *different sensor* (ECOSTRESS
   70 m, ISS) on a *different orbit* reproduces same-sign, significant daytime parking-core warming
   (+0.72 °C, robust to the Oct split). Smaller than the Landsat parking-core +1.08 °C but consistent
   in direction and significance — exactly what cross-sensor corroboration should look like.
2. **It resolves the daytime cold-core anomaly.** Pre-construction the core was *cooler* than Control
   (−0.45 °C: open/vegetated, higher evaporative cooling); post-construction it flips to +0.27 °C
   warmer. The DiD is the *flip*, not a pre-existing hotspot — strengthens the causal read.
3. **NIGHT: directional, not significant.** Impact is persistently ~+0.5 °C warmer at night across
   the whole record, but the *change* attributable to construction is n.s. under HAC (DiD +0.32 °C,
   p=0.20; MW marginal p=0.04, fails the Oct-split robustness). The warm night level is largely a
   pre-existing site difference, not a construction-driven heat-storage signal.
4. **Mechanism read:** the signal is **solar/surface-driven** (impervious surface heats under
   daytime insolation), **not** a deep thermal-mass UHI that would persist strongly at night. This is
   *honest and useful* — it says "impervious daytime heating", which is what the Landsat parking-core
   result and Stewart & Oke (2012) LCZ framing already claim. Do **not** over-state it as a 24-h UHI.

## Caveats to carry with every ECOSTRESS number
- ISS is **non-sun-synchronous**: "day"/"night" each pool varied overpass local times; the paired
  `delta` controls geometry within an overpass but pre/post overpass-time *distributions* may differ.
- Pre-period is short (ECOSTRESS from 2018-07; ~3 yr pre, n_pre day=246 / night=137).
- 70 m pixel at a point: parking-core point sits in a 70 m cell, coarser than the hand-digitised
  polygon used for Landsat — a point sample, not a polygon mean.
- Evidence tier: peer-reviewed (Fisher et al. 2020 WRR; Hook & Hulley 2022, DOI
  10.5067/ECOSTRESS/ECO_L2T_LSTE.002).

**One line:** ECOSTRESS gives the audit a second, independent, peer-reviewed sensor confirming
*daytime* parking-core warming and resolving the cold-core anomaly; the night channel is directional
but not significant, which correctly bounds the claim to surface/daytime heating rather than a
round-the-clock UHI.
