# Multi-site widening — PINEWOOD reconnaissance (RESULT, 2026-06-16)

**Script:** `analysis/MultiSite_Pinewood_Recon_TIER2_2026-06-16.py` ·
**Fig:** `visualisations/MultiSite_Pinewood_Recon_2026-06-16.png` ·
**Data:** `data/raw_telemetry/pinewood_recon_ndvi_2026-06-16.csv`.
Landsat 8/9 summer NDVI 2014–2025 over the OSM Pinewood Studios AOI (relation 13016756).

## Question
Before running a Pinewood BACI for the multi-site "studio-sprawl as a class" argument
(`_PHD_SEED_FRAMING_2026-06-16.md` §4): is there a greenbelt→built conversion at Pinewood, how big,
and **when** — because if its expansion predates the Shepperton 2021-06 split, that split is wrong for
Pinewood and would manufacture a misleading null.

## Result — Pinewood is NOT a clean post-2021 BACI case
- Data-derived vegetation-loss footprint in the AOI: **10.12 ha**, centroid 51.5528, −0.5292 (east of
  the studio core — consistent with the "Pinewood East" expansion side).
- **But the change does NOT behave like a permanent impervious conversion:**
  - The largest Impact NDVI drop is **into 2015 (−0.26)**, then it **partially recovers** (NDVI 0.46→0.55→0.64
    by 2017, hovering 0.55–0.68 thereafter). A built studio surface does not re-green — so this is a
    transient 2015 disturbance / since-landscaped works (or a thin 2015 summer Landsat composite), not a
    Shepperton-style permanent sealed core.
  - The Impact−Control NDVI delta is **roughly flat at −0.10 to −0.15 across 2016–2025**, with **no
    post-2021 divergence** (the Shepperton split line is irrelevant here).
- Implied construction window from the data: **~2014–2015**, i.e. firmly **before** 2021-06.

## Decision
1. **Do not run a 2021-split BACI on Pinewood** — it would yield a misleading ~null. Confirmed the §4
   timing concern with data.
2. Pinewood's PSDF / Pinewood East expansion is either pre-2014, within the already-built footprint, or
   landscaped such that 30 m Landsat sees no fresh greenbelt loss in 2014–2025. Either way it **does not
   contribute a clean recent greenbelt-conversion case** to the multi-site class.
3. **Recommended clean second film-studio comparator: Sky Studios Elstree** (Herts, ~51.66, −0.30) —
   built on greenbelt 2020–2022, opened Dec 2022, i.e. a genuine **post-2021** conversion that the
   Shepperton split fits. Run the same NDVI + ECOSTRESS-day pipeline there next.

## Method honesty
- AOI anchored on the **exogenous OSM studio boundary**, not a guessed polygon. The loss footprint is
  **data-derived** (NDVI change), reported with centroid + area provenance — used only to *date/size* the
  change (reconnaissance). A confirmatory BACI would anchor Impact on the OSM/planning construction
  boundary to avoid outcome-selection.
- Reconnaissance only: 30 m Landsat, summer composites, point/stable-mask sampling. Not a final DiD.
- Net value: this **prevented a misleading Pinewood null from entering the audit** and redirected the
  multi-site effort to a comparator (Sky Elstree) whose timing actually matches — exactly the
  methodological discipline the PhD framing leans on.
