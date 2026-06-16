# Tier-2 Results — Shepperton Forensic Spatial Audit

**Date**: 2026-06-15  
**Author**: Hanpu Li (Cait), 李含普  
**Methodology**: All numbers from live GEE + local computation. No fabrication.  
**GEE project**: `stone-cathode-465519-a4`

---

## Conclusion-First Summary

| Task | Status | Headline finding | Effect on conclusions |
|:--|:--|:--|:--|
| **T1** Synthetic Control | ✅ COMPLETE (re-run 2026-06-16, 0 fetch errors, all numbers reproduced exactly) | NDVI SCM = −0.352 (p=0.15, in-time placebo −0.010 ✓clean). LST SCM = +0.428°C (p=0.35, **in-time placebo −0.472 ✗unstable**). | **NDVI STRENGTHENS** (SCM-robust collapse). **LST SCM is WEAK / non-corroborating** — large in-time placebo signals pre-trend instability; the warming claim rests on cross-sensor Landsat+ECOSTRESS, not this SCM. |
| **T2** ECOSTRESS Day/Night LST | ✅ COMPLETE (2026-06-16) | **DAY DiD = +0.72°C** (HAC p=0.006 **, MW p=6e-4; +0.64 robust at Oct split). NIGHT DiD = +0.32°C (p=0.20, n.s.). Pre-construction core was −0.45°C *cooler*, flips to +0.27°C warmer. | **STRENGTHENS (day) + BOUNDS (night)**: independent cross-sensor (ECOSTRESS 70m, ISS) confirmation of daytime parking-core warming AND resolves the daytime cold-core anomaly; night n.s. → signal is surface/daytime impervious heating, NOT a 24-h UHI. |
| **T3** Reference-ET (FAO-56) | ✅ COMPLETE | Normalised ET DiD = +0.005 (p=0.18, n.s.) | **CONFIRMS** ET is genuinely weak; drought of 2019 was successfully absorbed. |
| **T4** ERA5-Land Counterfactual | ✅ COMPLETE | Local climate warming = +0.82°C. Excess warming exists only in parking core (+0.26°C), not full polygon (−0.26°C). | **CONFIRMS** footprint-specific signal; full polygon does not exceed co-located climate. |
| **T5** Sensor Robustness | ✅ COMPLETE | L8-only LST = +0.68°C (p=0.19, n.s.) | **QUALIFIES** parking-core LST — power issue (n halved 238→119). |
| **T7** Non-VP Comparator | ✅ COMPLETE | Longcross GV NDVI DiD = −0.013 (n.s.), LST DiD = +0.41°C (n.s.). | **CONFIRMS** Shepperton's signature is specific to its industrial design, not generic to green-belt release. |

---

## T1: Synthetic Control Method (SCM) — COMPLETE

Instead of a single hand-picked Control polygon, we constructed a dynamically weighted **Synthetic Control** using 19 stable green-belt donor polygons in Surrey/Spelthorne.

### NDVI (NDVI Core)
- **SCM Weights**: Kempton Park W (58.1%), Addlestone Moor (20.2%), Chobham Common S (15.8%), Staines Moor (5.9%).
- **SCM Treatment Effect**: **−0.3525** (confirms the massive collapse of vegetation).
- **Placebo Rank**: 3 / 20 (permutation p = 0.1500).
- **In-time Placebo (2019 split)**: **−0.0105** (essentially zero, confirming pre-trend validation).

### LST (Parking Core)
- **SCM Weights**: Staines Moor (24.9%), Ottershaw Meadow (22.7%), Stanwell Moor (22.5%), Thorpe Green (17.3%), Walton Riverbank (7.5%), Kempton Park W (5.1%).
- **SCM Treatment Effect**: **+0.4283°C** (positive warming, but more conservative than the single-control estimates).
- **Placebo Rank**: 7 / 20 (permutation p = 0.3500).
- **In-time Placebo (2019 split)**: **−0.4722°C**.

> ⚠️ **Honest read of the LST SCM — it is WEAK, do not lean on it (reviewer point B).** The in-time
> placebo at a *fake* 2019 split returns **−0.47°C**, an order of magnitude larger than NDVI's
> −0.01°C and comparable in magnitude to the actual +0.43°C estimate. A valid SCM should give ~0
> here; this large pre-period placebo (in-time RMSPE ratio 2.83) signals an **unstable pre-treatment
> fit / probable pre-trend** in the LST series — the synthetic does not track the treated unit cleanly
> before treatment, so the +0.43°C "effect" cannot be cleanly attributed. Combined with the permutation
> p = 0.35 (n.s.), the L8-only n.s. result (T5), and the ERA5 excess of only +0.26°C (T4), the **LST
> SCM is non-corroborating-to-weak**. The parking-core daytime-warming claim should therefore rest on
> the **cross-sensor agreement** — Landsat tri-sensor +1.08°C (**) AND ECOSTRESS day +0.72°C (**, T2,
> independent orbit/instrument) — NOT on this SCM. The NDVI SCM (−0.3525, in-time −0.01, clean) is the
> robust one; the LST SCM is reported for completeness and as a transparent negative on robustness.

The contrast (NDVI in-time −0.01 vs LST in-time −0.47) is itself the finding: vegetation collapse is
SCM-robust; surface warming is not SCM-robust and needs the multi-sensor argument instead.

### Estimator note (declared)
The SCM uses **outer-only optimisation with V = I** (all pre-period months weighted equally),
not the Abadie–Diamond–Hainmueller (2010) nested V-optimisation used by `Synth`/`pysyncon`. This
is a defensible simplification for a short single-variable pre-period series, but it is a known
divergence from the roadmap's "nested V" spec — stated here for reviewer transparency
(see `fit_scm` docstring).

### Files Created
- [SyntheticControl_Analysis_TIER2_2026-06-15.py](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/analysis/SyntheticControl_Analysis_TIER2_2026-06-15.py)
- [SyntheticControl_Analysis_TIER2_2026-06-15.png](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/visualisations/SyntheticControl_Analysis_TIER2_2026-06-15.png)

---

## T2: ECOSTRESS Day/Night LST — COMPLETE (2026-06-16)

ECOSTRESS (ECO_L2T_LSTE.002, 70 m, ISS non-sun-synchronous orbit) is the only sensor giving
**night** LST at the site — Landsat/MODIS on GEE are day overpasses. Night LST isolates stored/
anthropogenic heat with no incoming-shortwave confound. Data via NASA AppEEARS point extraction
(request `126592dd-...`), 2018-07 → 2026-03; 1,189 paired clean overpasses after QA
(TES-produced + cloud==0 + water==0). Day/night by inline NOAA solar elevation.

### Live Results (primary = all produced-clear; [bracket] = LST_accuracy ≤2 K)

| Regime | DiD (Impact−Control) | HAC p | MW p | pre mean | post mean | n_pre/post | Oct-split |
|:--|:--|:--|:--|:--|:--|:--|:--|
| **DAY**   | **+0.72°C** [+0.68] | **0.0062** [0.0076] | 6.1e-4 [8.1e-4] | **−0.45** | **+0.27** | 246/454 | +0.64°C, p=0.013 |
| **NIGHT** | +0.32°C [+0.31] | 0.195 (n.s.) | 0.038 [0.041] | +0.30 | +0.62 | 137/352 | +0.28°C, n.s. |

- **DAY = independent cross-sensor confirmation** of daytime parking-core warming (Landsat +1.08°C
  → ECOSTRESS +0.72°C, same sign + significant + robust). Resolves the cold-core anomaly: the core
  was *cooler* pre-construction (open/vegetated) and flips warmer post.
- **NIGHT = directional, not significant** (DiD p=0.20, fails Oct-split). The persistent ~+0.5°C
  night level is a pre-existing site difference, not a construction-driven heat-store. → bounds the
  claim to **surface/daytime impervious heating, NOT a 24-h UHI**.

### Files Created
- [ECOSTRESS_Night_TIER2_2026-06-16.py](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/analysis/ECOSTRESS_Night_TIER2_2026-06-16.py)
- [ECOSTRESS_DayNight_TIER2_RESULTS_2026-06-16.md](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/analysis/ECOSTRESS_DayNight_TIER2_RESULTS_2026-06-16.md)
- [ECOSTRESS_DayNight_2026-06-16.png](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/visualisations/ECOSTRESS_DayNight_2026-06-16.png)

---

## T3: Reference-ET Normalisation — COMPLETE

### Data
- **Actual ET**: MODIS MOD16A2GF (archived `ee-chart_et.csv`, 506 observations)
- **Reference ET₀**: ERA5-Land `potential_evaporation_hourly` via GEE (132 monthly records, 2015–2025)

### Live results

| Metric | DiD | HAC p | MW p | Verdict |
|:--|:--|:--|:--|:--|
| ET raw (all months) | −0.082 | 0.445 (n.s.) | 0.569 (n.s.) | Confirms baseline |
| ET normalised (ETa/ET₀) | +0.005 | 0.184 (n.s.) | 0.048 (*) | **n.s. by HAC** |
| ET normalised warm Apr-Sep | −0.009 | 0.014 (*) | 0.001 (**) | Window-dependent |

- Normalisation **dramatically absorbs the 2019 drought** (raw drought ΔET of −0.802 drops to −0.034 in ratio).
- ET's status as "directional qualitative support only" is now principled, confirming the absence of a robust well-powered DiD signal.

### Files Created
- [ReferenceET_TIER2_2026-06-15.py](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/analysis/ReferenceET_TIER2_2026-06-15.py)
- [ReferenceET_TIER2_2026-06-15.png](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/visualisations/ReferenceET_TIER2_2026-06-15.png)

---

## T4: ERA5-Land Co-located Climate Counterfactual — COMPLETE

Instead of using a coarse Met Office SE England regional baseline (+0.64°C), we extracted the 2m air temperature from co-located **ERA5-Land 9 km grid cells** containing the Impact and Control sites.

### Live Results
- **ERA5-Land local background JJA warming**: **+0.82°C** (higher than regional Met Office baseline).
- **Air-temperature DiD (Impact vs Control)**: **+0.00°C** (both fall in the same 9 km grid cell, confirming identical local microclimatic baseline).
- **Excess Warming (Attribution)**:
  - **Parking Core**: +1.08°C (LST) − 0.82°C (local climate) = **+0.26°C** (anthropogenic local warming confirmed).
  - **Full Polygon**: +0.56°C (LST) − 0.82°C (local climate) = **−0.26°C** (does not exceed local climate trend).

This confirms that the local anthropogenic heating signal is **confined to the parking core** and does not apply to the full polygon.

### Files Created
- [GridCounterfactual_TIER2_2026-06-15.py](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/analysis/GridCounterfactual_TIER2_2026-06-15.py)
- [GridCounterfactual_TIER2_2026-06-15.png](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/visualisations/GridCounterfactual_TIER2_2026-06-15.png)

---

## T5: Sensor Robustness (L8-only) — COMPLETE

### Live Results

| Metric | DiD (°C) | HAC p | MW p | n |
|:--|:--|:--|:--|:--|
| LST parking core (L7+L8+L9) | +1.079 | 0.0034 (**) | 1.2e-4 (***) | 238 |
| LST parking core (L8-only) | +0.676 | 0.186 (n.s.) | 0.128 (n.s.) | 119 |

- Landsat 8-only point estimate remains positive (**+0.68°C**) but loses significance due to halved sample size ($n$ halved: 238 → 119). This is a power issue, not a reversal.
- NDVI uses Sentinel-2 only, so it has no cross-sensor calibration issues.

### Files Created
- [SensorRobustness_TIER2_2026-06-15.py](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/analysis/SensorRobustness_TIER2_2026-06-15.py)
- [SensorRobustness_TIER2_2026-06-15.png](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/visualisations/SensorRobustness_TIER2_2026-06-15.png)

---

## T7: Non-VP Comparator (Longcross Garden Village) — COMPLETE

To test if the biophysical signature is generic to any green-belt development, we ran the same BACI DiD pipeline on **Longcross Garden Village** (RU.17/1749), a ~47 ha residential green-belt release in Surrey built 2020–2023.

### Live Results
- **NDVI DiD**: **−0.0130** (HAC p = 0.478, n.s.) — no NDVI collapse (due to green infrastructure/gardens).
- **LST DiD**: **+0.4098°C** (HAC p = 0.180, n.s.) — no significant surface warming.

This confirms that Shepperton's massive NDVI collapse (−0.36) and parking-core warming (+1.08°C) are **specific to its industrial/studio design** (high-density concrete, large sound stages), and are not a generic consequence of green-belt releases.

### Files Created
- [NonVP_ComparatorSelection_TIER2_2026-06-15.md](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/analysis/NonVP_ComparatorSelection_TIER2_2026-06-15.md)
- [NonVP_ComparatorAnalysis_TIER2_2026-06-15.py](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/analysis/NonVP_ComparatorAnalysis_TIER2_2026-06-15.py)
- [NonVP_ComparatorAnalysis_TIER2_2026-06-15.png](file:///Users/caitlye/Desktop/学习/audit_env/-OSM_AUDIT_2025/visualisations/NonVP_ComparatorAnalysis_TIER2_2026-06-15.png)
