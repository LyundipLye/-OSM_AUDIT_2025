# Consolidation and Verification Pass — Shepperton Forensic Spatial Audit

**Date**: 2026-06-15
**Author**: Hanpu Li (Cait), 李含普
**Operator**: Claude Code (working environment with the venv and archived CSVs available, so all
load-bearing numbers were re-run live this session; no transcription of expected values).
**GEE project**: `stone-cathode-465519-a4`

---

## Conclusion first

1. **Parking-core provenance is sound. The +1.08°C is NOT circular.** The `Sprawl_Zone_Core`
   boundary was defined from the EIA parking footprint and the OSM `amenity=parking` geometry,
   independently of the LST data, and is shared with the NDVI metric. A live geometric check
   found 79% of the hardcoded LST core polygon overlaps the independently extracted OSM parking
   footprint, with its centroid inside that footprint. Two cosmetic residuals only (see §1).
2. **NDVI remains the single load-bearing pillar** (−0.365, re-verified live; survives FDR,
   synthetic control, spec-curve, placebo, in-time placebo). Everything else is corroboration.
3. **The Tier-2 suite is now folded into README and AUDIT honestly**, with the Landsat-8-only
   +0.68°C (n.s.) caveat travelling with every +1.08°C mention, the parking core reframed as a
   surface-cover-stratified Local Climate Zone result, ET as principled-weak, and the comparator
   carrying its n=1 / residential-versus-industrial caveat.
4. **T3 (HadUK 1 km) and T2/T5 (ECOSTRESS night LST) are data-blocked, not analytical gaps.**
   Both have exact, ready-to-run request specs. T3's only blocker is a configured CEDA credential
   (the account already exists; the AI must not handle the password).

---

## 1. Parking-core provenance verdict (highest priority)

**VERDICT: land-use-derived, independent of LST. Not circular.** Full write-up with exact
file/line evidence in `documentation/parking_core_provenance_2026-06-15.md`.

- The polygon is hardcoded in `scripts/06_gee_thermal_pipeline.js:14-20` (LST, the +1.08 result),
  with the same parking footprint sampled in `scripts/04_gee_ndvi_pipeline.js:14-15` (NDVI) and
  enlarged in `scripts/06b_gee_thermal_sensitivity.js:14-24` (full polygon).
- The selection criterion (`documentation/sprawl_zone_selection.md:9-12`) is the EIA-documented
  parking conversion plus optical land-cover change, never a temperature criterion. The thermal
  band (`ST_B10`/`ST_B6`) never entered the boundary definition.
- **Live geometric check (this session)** against the independent OSM layer
  `data/raw_spatial/export_shepperton.geojson` (21 `amenity=parking` polygons): the 2.14 ha LST
  core polygon overlaps the OSM parking footprint by **1.685 ha (79%)**, its centroid sits **0.0 m
  inside** that footprint, and the NDVI sampling point is also inside it. A boundary that serves
  both the thermal and the (Sentinel-2) NDVI metric, and that lands on the independently extracted
  OSM parking polygon, cannot have been drawn from the temperature field.
- **Residuals (cosmetic, not validity defects):** (a) reword the one sentence in
  `sprawl_zone_selection.md:12` that names "Landsat imagery" so it cannot be read as drawing the
  boundary from temperature; (b) optionally ingest the polygon vertices from the geojson rather
  than hardcoding them, for full reproducibility.

---

## 2. What was folded into README and AUDIT

README §4 now carries a marked "Third-order corroboration suite (Tier-2, added 2026-06-15)" block
plus inline caveats; `documentation/AUDIT_2026-06-12.md` gained a dated section D. Specifically:

- **(a) Parking-core LST as a Local Climate Zone / surface-cover-stratified analysis** (Stewart and
  Oke, 2012, BAMS, now in the bibliography), reported alongside the n.s. full polygon, with the
  **Landsat-8-only +0.68°C (n.s., n=119) caveat attached to every +1.08°C mention** (README lines
  for §2.C, §3 sensitivity, and §3 regional-baseline).
- **(b) ET as principled-weak**: reference-ET normalisation (ETa/ET₀, FAO-56) absorbs the 2019
  drought and leaves the DiD at +0.005 (HAC p=0.18, n.s.).
- **(c) Comparator with the honest n=1 caveat**: Longcross NDVI −0.013 / LST +0.41 (both n.s.)
  supports "impact scales with imperviousness", not "VP-specific"; Limitation 6 explicitly stands
  at the virtual-production level.
- **(d) Multi-df pre-trend Wald rejection = likely early-construction leakage** making the 2021-06
  split conservative. This was already consolidated in README §4 (event-study bullet) before this
  pass; confirmed and left in place.
- Synthetic control (NDVI −0.3525, LST +0.428) and the ERA5 co-located counterfactual (excess
  +0.26 core / −0.26 full polygon) added, with the 9 km same-cell scale caveat and a pointer to the
  pending 1 km test. NDVI kept as the load-bearing pillar.

---

## 3. T3 HadUK-Grid 1 km — COMPLETED (Cait supplied a CEDA token; run live 2026-06-15)

Cait generated a CEDA access token, so the 11 HadUK-Grid `tas` 1 km monthly files (2015-2025)
were downloaded to `data/raw_telemetry/haduk_1km_2026-06-15/` and the co-located air-temperature
DiD was run live (`analysis/HadUK_1km_Counterfactual_TIER2_2026-06-15.{py,md}`).

- Impact and Control fall in **different** 1 km cells (E506500/N169500 vs E510500/N168500),
  4,111 m apart, so the air-temperature DiD is identifiable (unlike the ERA5 9 km same cell).
- **Co-located air-temperature DiD (full year) = +0.005 °C (HAC p = 0.62, n.s.).** There is no
  meaningful differential background air-temperature trend between the two sites.
- **Same-scale excess: parking core +1.07 °C, full polygon +0.56 °C.** The parking-core excess
  warming **survives, and is larger than, the ERA5 9 km estimate (+0.26)**, because the ERA5 step
  had subtracted an absolute regional warming from a difference-in-differences; the proper
  same-scale counterfactual (an air-temp DiD on the same pair) is ~0.
- Honest bound: HadUK-Grid is station-interpolated, so the near-zero air-temp DiD shows the
  surface-warming gap is not an artefact of differential climate, not that air temperature over
  the 13 ha lot rose by +1.07 °C. The Landsat-8-only n.s. caveat and the marginal full-polygon
  significance still apply.
- README §4 Tier-2 block updated with a dedicated "True 1 km same-scale air-temperature baseline"
  bullet. Token was stored in `~/.ceda_token` (chmod 600); **Cait should revoke/regenerate it**
  since it appeared in the chat transcript.

---

## 4. ECOSTRESS night LST — blocked on NASA Earthdata, request emitted

No `data/raw_telemetry/ecostress_night_lst.csv` present. Ran
`analysis/ECOSTRESS_Night_TIER2_2026-06-15.py` this session; it printed the exact AppEEARS request
and stopped (no fabrication): product **ECO_L2T_LSTE.002**, layer SDS_LST, Impact
(-0.469366, 51.410315) and Control (-0.410459, 51.407395), 2018-07-01 to 2026-03-15, night
overpasses, CSV output. Once the CSV exists the script runs the day-vs-night BACI/DiD with the
repo's standard conventions.

---

## 5. Consistency and anti-fabrication sweep

### 5a. Live re-verification of every headline number (this session, archived CSVs)

| Metric | README value | Live re-run this session | Match |
|:--|:--|:--|:--|
| NDVI core DiD (full year) | −0.365 | **−0.3653** (HAC p<1e-4, MW p=6.8e-52) | yes |
| LST parking core (full year) | +1.08 | **+1.0788** (HAC p=0.0034, MW p=1.2e-4) | yes |
| LST parking core (Apr-Sep) | +1.54 | **+1.5426** (HAC p=0.0018) | yes |
| LST full polygon (full year) | +0.56 | **+0.5602** (HAC p=0.061 n.s., MW p=0.041) | yes |
| ET raw DiD | −0.08 | **−0.0815** (HAC p=0.45 n.s.) | yes |
| SCM NDVI / LST gap | −0.3525 / +0.428 | **−0.3525 / +0.4283** (post-minus-pre of saved gaps) | yes |
| Longcross NDVI / LST (own 2020-01 split) | −0.013 / +0.41 | **−0.0130 / +0.4098** (both n.s.) | yes |

The Longcross figures initially appeared to disagree until I matched the comparator's own
construction split (2020-01-01, not 2021-06-01); reconciled exactly. GEE-derived Tier-2 numbers
(ERA5 +0.82 local warming, L8-only +0.68 at n=119, normalised ET +0.005, SCM permutation p-values)
were NOT recomputed this session because they require live GEE re-extraction; they are attributed to
the documented 2026-06-15 Tier-2 live runs and labelled as such in README, not presented as fresh.

### 5b. Genuine inconsistencies found, with fixes

| # | Inconsistency | Where | Status / fix |
|:--|:--|:--|:--|
| 1 | `parking_spaces: 2300` (and "2,300" description); also `greenbelt_loss_ha: 13.05`, `development_footprint_ha: 14.12`, `construction_start: '2019-06'` | `scripts/12_impervious_surface_analysis.py:48` etc. | Contradicts EIA log (2,595 + 250 overflow) and the 39 ha / 2021-06 used everywhere else. Already logged in `_RIGOROUS_AUDIT §3.1`; re-flagged in AUDIT D-4. Not propagated into any README figure. **Fix (Cait's, EIA facts are hers to own): align script-12 `EIA_DATA` to `eia_data_extraction_log.md`.** Not edited by me per the no-overwrite rule. |
| 2 | Two non-nesting impervious totals: 16.91 ha "Shepperton + Longcross combined" vs 17.43 ha "Shepperton alone" | README lines 161 and 179 | A combined figure cannot be smaller than its Shepperton-only subset. I re-verified **17.43 ha = Shepperton-only OSM impervious union** live this session. They come from different scripts (02 vs 12) with different category sets. **Fix: reconcile the scope labels.** Flagged in AUDIT D-4. |
| 3 | Hollis et al. 2019 cited as "Int. J. Climatol." | `documentation/haduk_grid_T4_source_2026-06-15.md:10` | Canonical HadUK-Grid paper is *Geoscience Data Journal* 6(2):151-159, DOI 10.1002/gdj3.78. README bibliography uses the correct record. **Fix: correct the journal in that doc** (flagged there and here). |

### 5c. Stale tokens checked — correctly quarantined, NO repo-claim contradictions

- **+5°C**, **365-day rolling smoothing**, **£6,150 ecological buyout**, **85-95% per OSM wiki**,
  **"USGS Landsat 8" only** appear ONLY inside defect logs (`AUDIT_2026-06-12.md` D1/D2/D4) and
  deck-versus-repo discrepancy notes (`_CURRENT_STATE_SUMMARY`, `_RIGOROUS_AUDIT`). They describe
  what the OLD slide deck still shows, not current repo claims. The repo's README and AUDIT assert
  the corrected, controlled values. The slide deck (pptx) is out of scope and was not touched.
- **NDVI embedded chart PNG** still shows the retired legend ("365D Rolling", single-zone
  "Permanent Loss"); the text was corrected but the PNG was not regenerated (old PNG purged from
  iCloud, per `_RIGOROUS_AUDIT §184`). This is a regenerate-the-figure task (`scripts/05` from the
  archived CSV), not a text contradiction. Listed under remaining work.
- **"Ye" author misrender**: none found anywhere in the repo. Author renders as Hanpu Li (Cait) /
  李含普 throughout.
- **Em-dashes in my edits**: none. README and AUDIT em-dash counts were unchanged (24 and 38) after
  my additions; all new clauses use minus signs, hyphens, semicolons and parentheses.

### 5d. Final headline-claims table

| Claim | Current value | Verification status | Caveat that must travel with it |
|:--|:--|:--|:--|
| NDVI collapse | −0.365 DiD | Re-run live; FDR q<0.01, SCM −0.3525, spec 100%, placebo, in-time 0 | Load-bearing pillar. None material. |
| Parking-core LST warming | +1.08°C (full yr), +1.54 (Apr-Sep) | Re-run live, HAC sig. | **L8-only +0.68°C n.s. (n=119)**; SCM +0.428 (p=0.35); LCZ-stratified, not boundary-from-heat |
| Full-polygon LST | +0.56°C | Re-run live, HAC p=0.061 (n.s.) | Does not exceed regional/co-located baseline; not an independent signal |
| ET suppression | −0.08 raw / +0.005 normalised | raw re-run live; normalised from Tier-2 GEE run | Principled-weak, directional only, not a pillar |
| Co-located excess warming (HadUK 1 km, primary) | core **+1.07 °C** / full +0.56 °C | **Run live this session**; air-temp DiD +0.005 °C (HAC p=0.62, n.s.), so the surface DiD stands as excess | Parking-core excess **survives same-scale 1 km baseline**; HadUK station-interpolated so it shows "not a differential-climate artefact", not "+1.07 °C of air warming over the lot"; L8-only and marginal full-polygon caveats still apply |
| Co-located excess warming (ERA5 9 km, superseded) | core +0.26 / full −0.26 °C | Tier-2 GEE run; LST DiDs re-verified live | Mixed an absolute regional warming into a DiD, and 9 km could not separate Impact/Control; kept for transparency, superseded by the HadUK 1 km row above |
| Non-VP comparator | NDVI −0.013 / LST +0.41 (n.s.) | Re-run live at 2020-01 split | n=1; supports "scales with imperviousness", not VP-specific |
| Parking-core provenance | land-use-defined, non-circular | Live geometric check, 79% OSM overlap | Reword 1 sentence; optionally ingest geojson |
| S106 / GVA / 39 ha / 79 trees / 2,595 spaces | £36,150 / £322.7M yr, £392M build / 39 ha / 79 / 2,595 | Internal arithmetic checked; primary values are Cait's to own | Script-12 hardcodes conflicting 2,300/13.05 (item 5b-1) |

---

## 6. What genuinely remains before this goes to a supervisor

1. **Reword `sprawl_zone_selection.md:12`** to remove the "Landsat imagery ... land-cover change"
   wording that could read as boundary-from-temperature (5 minutes; closes the only soft edge on
   the defensibility hinge).
2. **Align `scripts/12` `EIA_DATA`** to the EIA extraction log (2,595 spaces, etc.), or add a one-
   line provenance note. Cait owns the EIA numbers, so I left the file unedited (item 5b-1).
3. **Reconcile the two impervious totals** (16.91 combined vs 17.43 Shepperton-only) with explicit
   scope labels (item 5b-2).
4. **Correct the Hollis 2019 journal** in `haduk_grid_T4_source_2026-06-15.md` (item 5b-3).
5. **Regenerate the NDVI chart PNG** from `scripts/05` so the embedded figure legend matches the
   corrected method text (no more "365D Rolling").
6. **T3 (HadUK 1 km) — DONE this session** (token supplied). Parking-core excess survives the true
   same-scale baseline (+1.07 °C; air-temp DiD +0.005, n.s.). Revoke the CEDA token now that it has
   been used. See §3.
7. **Run T2 (ECOSTRESS night LST)** once the AppEEARS CSV is downloaded: tests whether the daytime
   parking-core warming has a nocturnal UHI counterpart, the mechanism the daytime-only Landsat
   transect cannot reach.
8. Optional hardening: ingest the parking-core polygon vertices directly from the geojson rather
   than hardcoding them, for full provenance reproducibility.

Nothing in this pass overturned a headline. NDVI is the pillar; the parking-core warming is a real
but power-limited, surface-cover-stratified signal that must always carry its L8-only n.s. caveat;
full-polygon LST and ET are non-significant; the comparator says the signature scales with
imperviousness rather than being virtual-production-specific. The two genuinely informative upgrades
left (1 km air temperature, night LST) are blocked on free external accounts, not on method.
