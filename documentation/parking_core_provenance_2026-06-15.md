# Parking-core boundary provenance — defensibility check (2026-06-15)

**Question:** is the "parking core" / `Sprawl_Zone_Core` (LST sensitivity) polygon defined from
the LAND-USE / planning footprint (independent of the temperature data), or was it drawn from the
LST raster (which would be circular)?

**Verdict: DEFENSIBLE. The boundary is land-use / planning-defined, not temperature-defined.**

## Evidence (from the repo, verbatim)
- `scripts/00_gee_data_extraction.py` line 34–35: `PARKING_LOT_COORDS` = a fixed 5-vertex polygon,
  commented "Parking-lot polygon (5 vertices, ~3 Landsat thermal pixels)". The LST "sensitivity"
  extraction (`_extract_lst_sensitivity`) reduces over `ee.Geometry.Polygon([PARKING_LOT_COORDS])`.
  The polygon vertices are hard-coded geometry, not derived from any temperature field.
- `documentation/sprawl_zone_selection.md` selection rationale for the impact/parking zone:
  1. "greenfield/agricultural land before 2018, converted to impervious asphalt surface during
     2020–2023" (treatment-side, land cover);
  2. "Directly corresponds to the new parking capacity (2,595 spaces) documented in the EIA
     (18/01212/OUT)" — **anchored to a primary planning document (the Environmental Impact
     Assessment for the consented scheme)**;
  3. "Sentinel-2 and Landsat imagery visually confirms this area experienced the most significant
     land-cover change."

## Assessment
- Selection is on the **treatment** (the development / impervious conversion, anchored to the EIA
  Zone-C car park, 2,595 spaces), **not on the outcome (LST)**. Selecting the analysis zone by
  treatment intensity is standard and non-circular.
- This is the standard, defensible move in surface-temperature / urban-heat work: a
  surface-cover-stratified / Local Climate Zone analysis (Stewart & Oke 2012, *BAMS*), reported
  ALONGSIDE the full polygon (which is n.s.), with multiple-comparison (FDR) control.

## Honest caveats to state in the write-up
1. Rationale point 3 ("most significant land-cover change") is **treatment-side corroboration**, not
   outcome selection — frame it that way so no reader mistakes it for selecting-on-the-hot-pixels.
2. The boundary is a **hand-digitised 5-vertex polygon matched to the EIA car-park footprint**, not
   an objective impervious-surface classification mask. The rigorous upgrade is to derive the zone
   from the impervious classification (`scripts/12`, 17.43 ha) rather than manual digitising; the
   conclusion should not hinge on the exact hand-drawn vertices (the spec-curve already shows the
   parking-core effect holds across 89.8% of specifications, which mitigates this).
3. Pair every parking-core +1.08 °C with the **L8-only +0.68 °C (n.s.)** sensor caveat and the
   ERA5/HadUK same-scale attribution (+0.26 °C excess), so the claim is "consistent with the
   impervious-surface heating mechanism", not "a proven hotspot".

**Bottom line for a viva:** the zone is planning-defined and the analysis is a legitimate
LCZ/surface-stratified design; the defensible framing is mechanism-consistent localised heating,
reported with the full-polygon null and the sensor/power caveats — not an isolated significant
subgroup pulled from the data.
