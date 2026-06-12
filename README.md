# OSM_AUDIT_2025: Spatial Audit of Virtual Production Infrastructure

**Project Title:** The Material Footprint of Virtual Production: A Remote Sensing Assessment of Land-Cover Change and Biophysical Impacts at Shepperton Studios

**Author:** Hanpu Li (Caitlyn Lye)

**Institution:** Queen Mary University of London (QMUL)

**Status:** PMP ELSS Module Coursework (20% Assessment)

---

## 1. Project Overview & Academic Contribution

This repository contains the spatial data pipelines, Earth Observation (EO) algorithms, and analytical frameworks developed for a spatial audit of Virtual Production (VP) infrastructure, specifically examining the Shepperton Studios expansion (Planning Application: 18/01212/OUT) in the London Borough of Spelthorne, United Kingdom.

While contemporary industry discourse frames virtual production and cloud rendering as a low-carbon alternative to location shooting (Keeney, 2024), this project investigates the material and biophysical dimensions of that claim. By combining Computational Spatial Science (GIS/Remote Sensing) with political-economic analysis, this repository provides a replicable, open-source methodological pipeline to quantify the physical, thermodynamic, and ecological consequences of digital media infrastructure expansion — consequences that receive limited attention in corporate environmental disclosure (Maxwell and Miller, 2012).

### Theoretical Context

The analytical pipeline draws on three political-economic concepts used in the Discussion to interpret the biophysical findings:

- **The Digital Spatial Fix** (Greene & Joseph, 2015): Conceptualising digital infrastructure not as a dematerialised entity, but as a mechanism through which capital expands into new geographic territories. Virtual production's material footprint — soundstages, rendering farms, HVAC systems, and logistical surfaces — represents such a spatial expansion.
- **The Metabolic Rift** (Marx, 1867; Foster, 1999; Bozak, 2012): The conversion of vegetated greenbelt to impervious surface disrupts the land-atmosphere energy exchange cycle, forcing a thermodynamic repartitioning from latent heat (evaporative cooling) to sensible heat (atmospheric warming).
- **Accumulation by Dispossession** (Harvey, 2004): The S106 agreement for this development contains no explicit ecological compensation for the 39 ha greenbelt conversion. The total S106 financial obligation (£36,150) consists entirely of transport-related administrative fees — including a £6,150 Travel Plan Monitoring Fee, a £10,000 Parking Restriction Review, and a £20,000 Signage Strategy contribution (Spelthorne Borough Council, 2019) — while the development is projected to generate **£322.7 million in GVA per annum** once operational (Turley Economics, 2018, para 33 / Table 3.6 series), and a one-off **£392 million in GVA across the four-year construction period** (Turley Economics, 2018, Table 6.2). The ecological loss was not priced within the existing planning framework.

---

## 2. Methodological Architecture

**BACI threshold.** All before/after tests use a single fixed construction split, **`2021-06-01`**, applied identically across the NDVI, LST, and ET pipelines and to the Met Office regional baseline. This date is the mid-point of the documented impervious-conversion window: outline consent 18/01212/OUT was approved on **12 February 2019** (Spelthorne Borough Council Planning Committee), with the expansion **completed in March 2024** (Pinewood Group), giving a greenfield → asphalt build of roughly **2020–2023** (see `documentation/sprawl_zone_selection.md`). A mid-window split is the conservative choice for a phased conversion: it avoids assigning transitional years entirely to either epoch and biases the estimated shift *downward* rather than inflating it. (The spatial transect, `08`/`09`, instead contrasts clean pre- and post-windows — JJA 2016–2018 vs 2023–2025 — to sidestep the transition years altogether.)

This project employs a triangulated approach combining OSM topological tracing, multi-spectral Earth Observation (executed via the Google Earth Engine platform; Gorelick et al., 2017), and local governance dossier review. All three biophysical pipelines (NDVI, LST, ET) use **Mean-Shift OLS Regression with Newey-West HAC standard errors** as the primary significance test, addressing temporal autocorrelation inherent in Earth Observation time series. For NDVI, **Seasonal Mann-Kendall** testing (`period=12`, monthly resampling) provides a complementary trend test. For LST, a **Paired BACI (Before-After-Control-Impact)** design (Stewart-Oaten et al., 1986) with **Mann-Whitney U** serves as a non-parametric reference. For ET, the HAC OLS directly tests for a regime shift in latent heat flux.

### Phase I: Geomatic Extraction & Topological Normalisation

**Objective:** To empirically quantify impervious surface coverage by leveraging open-source Volunteered Geographic Information via the Overpass API (OpenStreetMap contributors, 2015).

- **`01_osm_extraction.ql`** (Overpass QL): 
  - **Logic**: Executes a radius-constrained extraction (1200 m) around the Shepperton coordinates (51.4065°N, 0.4640°W) and Longcross coordinates (51.3830°N, 0.5930°W) via the Overpass API, pinned to a fixed temporal snapshot (`[date:"2026-03-03"]`) for reproducibility. Targets multiple impervious surface categories: industrial/commercial buildings (`building=industrial|commercial`), power infrastructure (`power=*`), parking (`amenity=parking`), industrial/commercial/construction landuse polygons (`landuse=industrial|commercial|construction`), paved service roads (`highway=service` with `surface=asphalt|paved|concrete`), and industrial works (`man_made=works`). **Limitation:** Despite the expanded tag set, OSM coverage of private industrial sites remains incomplete; untagged hardstanding is not captured.
  - **Rationale**: This uses publicly accessible geographic data to quantify physical infrastructure without relying on proprietary corporate disclosures.

- **`02_spatial_projection.py`** (Python / `shapely`, `pyproj`): 
  - **Logic**: Ingests WGS84 GeoJSON vectors extracted from OSM. Classifies each feature into impervious surface categories (parking, industrial landuse, paved service roads, buildings) and projects to EPSG:27700 for accurate area calculation. Uses `shapely.ops.unary_union` to dissolve overlapping polygons and produce a **deduplicated total** impervious area.
  - **Rationale**: Calculating areas directly in WGS84 (a geographic, non-projected CRS) introduces spherical distortions at UK latitudes (~0.7% area error). Projecting to EPSG:27700, the UK's official planar coordinate system, achieves planar land-conversion metrics (in square metres) with an error margin of <0.1%. Deduplication prevents double-counting overlapping OSM geometries.

- **`03_kepler_formatter.py`** (Python / `shapely`, `pyproj`, `csv`): 
  - **Logic**: Iterates over all impervious surface categories from the expanded GeoJSON, calculating centroids and planar areas. Exports a formatted CSV with intensity weightings designed for 3D extrusion rendering in [Kepler.gl](https://kepler.gl/). Includes parking, industrial landuse, paved service roads, buildings, and power infrastructure.
  - **Output**: `data/processed/kepler_gl_visualisation.csv` — a georeferenced dataset for visual inspection of the spatial distribution and intensity of impervious surface coverage.

### Phase II: Earth Observation & Biophysical Quantification

**Objective:** To measure the longitudinal biophysical and thermodynamic changes in the audited zone, controlled against nearby undeveloped greenbelt.

**Data Sources:**
- **ESA Copernicus Sentinel-2** (S2_SR_HARMONIZED): 10 m multispectral imagery for vegetation dynamics (ESA, 2026).
- **USGS Landsat 7 ETM+ / Landsat 8 OLI-TIRS / Landsat 9 OLI-2-TIRS-2** (Collection 2, Tier 1, Level 2): 100 m thermal infrared for land-surface temperature (USGS, 2026).
- **NASA MODIS/Terra MOD16A2GF**: 500 m, 8-day composite Actual Evapotranspiration (Running et al., 2019).

**Cloud-Masking & Temporal Normalisation:**
- GEE `QA60` bitwise cloud-masking combined with Scene Classification Layer (SCL) filtering to remove cloud shadows, cirrus, and snow artefacts.
- `dropna()` filtering to remove cloud-induced null artefacts in thermal data.
- GEE exports raw per-overpass observations (no smoothing applied in extraction). All statistical testing is performed in the Python post-processing stage on either raw observations (HAC OLS, Welch's t-test) or monthly-resampled means (Seasonal Mann-Kendall).

#### A. NDVI Change Pipeline

- **`04_gee_ndvi_pipeline.js`** (Google Earth Engine API — JavaScript): 
  - **Logic**: Interfaces with the ESA Sentinel-2 (S2_SR_HARMONIZED) multispectral constellation. Extracts the Normalised Difference Vegetation Index (NDVI = [NIR − Red] / [NIR + Red]), calculating both geometric spatial means and pixel-level standard deviations (`stdDev`) across an 8-year temporal axis (2018–2026).
  - **Algorithm**: Implements a dual-layer cloud masking function using both the QA60 bitmask and the SCL (Scene Classification Layer) to filter cloud shadows, cirrus bands, and snow. Exports both spatial mean and pixel-level standard deviation (`stdDev`) in Wide-Format for spatial variance analysis.
  - **Source Code**: [GEE Public Link](https://code.earthengine.google.com/0cd023633ba069e4320a7a081bd65b62) (Li, 2026).

- **`05_plot_ndvi_chart.py`** (Python / `pandas`, `numpy`, `statsmodels`, `pymannkendall`, `matplotlib`): 
  - **Logic**: Ingests the raw NDVI telemetry CSV from GEE. 
  - **Algorithm**: Utilises **Difference-in-Differences (DiD)** against the Control Zone greenbelt to calculate the net anthropogenic signal ($\Delta$NDVI). The regime shift is tested via **Mean-Shift OLS Regression with Newey-West HAC standard errors** (matching the approach in the LST and ET pipelines) to account for temporal autocorrelation in the satellite time series. The primary trend test is a **Seasonal Mann-Kendall** (`pymannkendall`, `period=12`) applied to **monthly-resampled** $\Delta$NDVI — the standard approach in vegetation phenology literature, yielding 12 monthly "seasons" with ~8 observations each across 2018–2026.

#### B. LST / Thermodynamic Change Pipeline (Primary BACI)

> **LST input-file map (important).** The two LST telemetry files are named counter-intuitively relative to their analytical roles, so the mapping is stated explicitly here and in each script header:
>
> | Script | Role | Input CSV | Spatial extent |
> |:-------|:-----|:----------|:---------------|
> | `07` | **Primary** BACI | `ee-chart_lst_sensitivity.csv` | Full VP polygon (~50 thermal pixels) |
> | `07b` | **Sensitivity** check | `ee-chart_lst.csv` | Parking-lot sub-polygon (~3 thermal pixels) |
> | `07c` | Annual composite | both (full polygon + parking lot) | both |
>
> The filenames are retained for provenance continuity with the archived GEE exports; the roles are fixed by the input mapping above, not by the filename.

- **`07_plot_thermal_chart.py` / `07c_lst_annual_composite.py`**:
  - **Logic**: Implements a **triple-satellite fusion** (Landsat 7 ETM+ 60 m + Landsat 8 TIRS 100 m + Landsat 9 TIRS-2 100 m) to maximise temporal observation density across the 2015–2026 continuum. Extracts LST over the full 9-vertex VP development polygon (~1 km², ~50 thermal pixels) and a paired Control Zone.
  - **Annual Composite Algorithm**: Because per-overpass raw LST exhibits high variance ($\sigma \approx 2^\circ\mathrm{C}$), `07c` aggregates raw observations into **Annual Summer (JJA) Composites**, producing temporally independent observations that satisfy the i.i.d. assumption. Significance is evaluated via **Welch's t-test** combined with **Cohen's $d$ effect size** to measure practical significance irrespective of statistical power limitations.
  - **Raw BACI Algorithm**: `07` employs a standard Paired BACI design (Stewart-Oaten et al., 1986). The significance of the per-overpass $\Delta$T regime shift is evaluated using **Mean-Shift Regression with Newey-West HAC standard errors** to address temporal autocorrelation.

#### C. Robustness Checks

**To address the spatial resolution limits of Landsat TIRS (100 m native thermal pixel), this project deploys three methodologically independent robustness checks:**

- **Sensitivity Analysis — Core Impervious Polygon** (`07b_plot_thermal_sensitivity.py`):
  - **Direction of the test**: This check runs in the *opposite* direction to the primary analysis. The primary BACI (`07`) uses the full ~1 km² VP polygon (~50 thermal pixels) to maximise statistical power; `07b` deliberately *narrows* the ROI to the newly-constructed ~10.9 ha parking lot — at 100 m resolution only $\sim 3\text{--}4$ pure thermal pixels — to test whether the warming signal *localises to the impervious core* rather than being diffused across the mixed-cover polygon. The trade-off is intentional: narrowing the ROI sharpens the land-cover contrast but sacrifices power.
  - **Temporal window**: `07b` reports both a full-year BACI and a Warm-Season (Apr–Sep) BACI. The Apr–Sep window is deliberately wider than the primary summer analysis (Jun–Aug) so that the robustness check varies *both* the spatial ROI and the temporal window relative to the primary.
  - **Algorithm**: Same Mean-Shift OLS with Newey-West HAC standard errors as the primary BACI, plus Mann-Whitney U as a non-parametric reference; `07c` adds an annual-composite Welch t-test and Cohen's $d$ on the same parking-lot ROI.
  - **Results (re-verified 2026-06-12 against `ee-chart_lst.csv`, n = 238 valid overpasses):** full-year ΔT shift = **+1.08 °C** (HAC $p = 0.0034$, MW $p = 0.0001$); warm-season (Apr–Sep) shift = **+1.54 °C** (HAC $p = 0.0018$, MW $p = 0.0001$); annual JJA composite (`07c`) shift = **+2.03 °C** (Welch $p = 0.072$, n.s.; Cohen's $d = 1.37$, from 6 pre- / 5 post- annual means). These match §3. An earlier draft of this section quoted ≈ +0.57 °C / $d = 0.49$ / HAC $p = 0.12$; those figures were stale (the 0.57 was the *pre-period* mean, not the shift) and have been removed. The per-overpass HAC results are significant; only the small-$n$ annual composite is under-powered, which is why the thermodynamic claim is anchored on the per-overpass test and cross-pipeline convergence rather than on the composite alone.

- **Phase IV: Spatial Transect / Distance Gradient Analysis** (`08_gee_transect_decay.js`, `09_plot_transect_decay.py`):
  - **Logic**: Constructs 16 concentric annular buffers (50 m bandwidth, 0–800 m) emanating radially from the Impact Zone boundary. For each ring, the GEE script computes the spatial mean LST from 3-year summer (JJA) composites for both the pre-construction epoch (2016–2018) and the post-construction epoch (2023–2025), using the same triple-satellite fusion as the primary BACI pipeline.
  - **Algorithm — Background-Subtraction Normalisation**: Because the two epochs may differ in regional baseline temperature due to inter-annual climate variability, a direct comparison of absolute LST is confounded. The Python script applies a **background-subtraction normalisation**: the far-field anomaly (mean of [Post − Pre] at the 400–800 m reference annuli) is treated as the regional climate baseline and subtracted from each ring, yielding a **Net Thermal Anomaly** metric that isolates the spatially localised effect of the land-cover change from regional confounders.
  - **Physical Interpretation (and an honest negative result)**: In the archived data (`ee-chart_decay.csv`), every ring is *cooler* post-construction than pre-construction, and after background-subtraction the **core net anomaly is negative (≈ −1.5 °C relative to the 400–800 m far-field)**. The daytime transect therefore does **not** show a warm distance-decay scar; it shows a daytime *cool* core. This is the expected outcome for a high-albedo, dry asphalt surface under a ~10:30 Landsat overpass, where shortwave reflection dominates and stored heat has not yet re-radiated — exactly the albedo-dominated daytime regime noted in Limitation 8. The transect is retained as a transparent **boundary condition on the method**, not as corroboration of warming: a warm advective scar of the kind described by Oke (1987) is a *nocturnal* phenomenon and is undetectable with daytime-only sensors. Resolving it requires night-pass thermal data (ECOSTRESS, ASTER night), listed under Future Extensions. Reporting this negative result rather than omitting it is deliberate; it bounds what the daytime LST pipelines can and cannot establish. *Note on apparent tension with the BACI warming:* the parking-lot BACI reports daytime warming (+1.08 °C) while this transect shows a daytime cool core — these are not in conflict, because the BACI is a *temporal* Impact−Control contrast on fixed pixels (it captures the loss of the control's relative cooling over time), whereas the transect is a *spatial* core-vs-far-field contrast within single daytime composites (it captures asphalt's high daytime albedo relative to surrounding vegetation). Both are daytime measurements of different quantities.

- **Phase V: Evapotranspiration Change / Latent Heat Proxy** (`10_gee_evapotranspiration.js`, `11_plot_evapotranspiration.py`):
  - **Logic**: Extracts the 8-day Actual Evapotranspiration (ET, kg/m²/8-day) from the MODIS/Terra MOD16A2GF product (500 m spatial resolution) over the full VP development polygon (Impact Zone) and a stable parkland Control Zone of equivalent area (~500 m radius buffer). The GEE script applies the MODIS scale factor (×0.1) and exports a paired time series spanning 2015–2026.
  - **Algorithm**: At MODIS 500 m resolution, both zones are sub-pixel suburban mosaics, so absolute ET curves overlap. The critical signal emerges in the **Difference-in-Differences (DiD)** domain: $\Delta$ET = ET$_{\text{Impact}}$ − ET$_{\text{Control}}$. The Python script partitions $\Delta$ET into pre- and post-construction epochs and applies a **Mean-Shift OLS Regression with Newey-West HAC standard errors** to test for a statistically significant regime shift in latent heat flux. An annual bar decomposition visualises the year-by-year evolution of the DiD signal.
  - **Physical Rationale**: Evapotranspiration is a direct proxy for the **latent heat flux** ($Q_E$) term in the surface energy balance equation: $Q^* = Q_H + Q_E + Q_G$. When vegetated soil (high $Q_E$, evaporative cooling) is replaced by impervious asphalt (near-zero $Q_E$), the absorbed solar radiation is redirected into sensible heat ($Q_H$, atmospheric warming) and ground heat storage ($Q_G$). A statistically significant decline in $\Delta$ET therefore constitutes evidence for the physical mechanism underlying any surface warming — demonstrating not merely *that* the surface warmed, but *why* it warmed, from conservation of energy.

#### E. Non-Satellite Ground Truth Pipelines

- **Phase VI: Impervious Surface Analysis** (`12_impervious_surface_analysis.py`):
  - **Data Source**: OpenStreetMap (crowd-sourced geospatial) + Spelthorne Borough Council EIA (Case Ref 18/01212/OUT).
  - **Logic**: Classifies OSM features within the VP development footprint by impervious surface category (parking, buildings, service roads, industrial), projects to EPSG:27700, and computes deduplicated area via `shapely.unary_union`. Cross-references with EIA-documented 14.12 ha development footprint.
  - **Theoretical Validation**: Estimates latent heat suppression using Penman-Monteith reference parameters (Allen et al., 1998, FAO-56) for the grassland→asphalt transition, providing a physics-based prediction of the expected thermal response.
  - **No satellite or GEE dependency.**

- **Phase VII: Met Office Regional Temperature Baseline** (`13_metoffice_temperature_analysis.py`):
  - **Data Source**: UK Met Office HadUK-Grid 1 km station-interpolated areal series (England SE & Central S). Downloaded directly from the Met Office National Climate Information Centre.
  - **Logic**: Computes pre/post construction regional temperature anomaly and long-term warming trend (°C/decade). The key test: if satellite-observed ΔLST at Shepperton *exceeds* the regional climate baseline, the signal is local (anthropogenic); if ΔLST ≈ regional ΔT, the signal is climate-driven.
  - **No satellite or GEE dependency.**

### Inter-Pipeline Automation (`run_pipeline.sh`)

The satellite data extraction step can be executed either manually via the GEE Code Editor (`04`, `06`, `06b`, `08`, `10` .js scripts) or **automatically** via the Python `ee` API (`00_gee_data_extraction.py --project YOUR_PROJECT_ID`). The full local analytical pipeline (`run_pipeline.sh`) chains 10 steps:

1. Spatial reprojection (`02`) → 2. Kepler.gl formatting (`03`) → 3. NDVI analysis (`05`) → 4. LST Primary BACI (`07`) → 5. LST Sensitivity (`07b`) → 6. Spatial Transect (`09`) → 7. Evapotranspiration (`11`) → 8. **Non-GEE: OSM Impervious Surface (`12`)** → 9. **Non-GEE: Met Office Temperature (`13`)** → 10. Complete.

Steps 8 and 9 require **no satellite data or GEE access** and provide independent verification of the biophysical findings.

### Phase III: Institutional Governance & Discourse Review

**Objective:** To cross-reference spatial findings with municipal planning documents and institutional grey literature.

An analysis of the following institutional dossiers is documented in `documentation/`:

| Document | Source | Reference |
|:---------|:-------|:----------|
| Environmental Statement Vol. 1 (Main Text) | Spelthorne Borough Council | Planning App: 18/01212/OUT (2018) |
| Flood Risk Assessment | Hydrock Consultants Ltd | SPS-HYD-XX-XX-RP-D-5001 (2018) |
| Transport Assessment | i-Transport LLP | ITL14056-008D R (2018) |
| Arboricultural Implications Report (Parts 1 & 2) | SJA Trees | Drawing No: SJA TPP 18158-02 (2018) |
| Economic Impact Assessment | Turley Economics | Document Ref: PINR3003 (2018) |
| Heritage Statement | Turley Heritage | (2018) |
| Sustainability Assessment | Turley Sustainability | Document Ref: PINR3003 (2018) |
| Planning Committee Report & Minutes | Spelthorne Borough Council | 12 February 2019 |
| Capital Assurance Review | CIPFA | DLUHC (2023) |
| Business, Infrastructure & Growth Committee Agenda | Spelthorne Borough Council | 11 September 2025 |

This phase contrasts the EIA's projected economic benefits (£322.7M GVA per annum once operational, and £392M GVA over the four-year construction period; Turley Economics, 2018) with the observed ecological costs documented in Phases I and II, and examines the structure of the S106 agreement.

---

## 3. Key Empirical Findings (Shepperton Case Study)

The execution of this pipeline yielded the following metrics:

- **Impervious Surface Coverage:** A deduplicated total of **16.91 hectares** (169,100 m²) of OSM-tagged impervious surfaces within the 1200 m extraction radius (Shepperton and Longcross combined), comprising parking (13.21 ha), industrial landuse (3.70 ha), with overlap dissolved via `shapely.unary_union`. This figure is a **lower-bound estimate** as untagged hardstanding is not captured by OSM. It is distinct from the 16.4 ha of building floorspace reported in the EIA (Spelthorne Borough Council, 2018).

- **Power Infrastructure:** The identification of **17 `power=*`-tagged elements** (substations, transformers, power lines) within the 1200 m extraction radius. **Caveat:** OSM coverage of private industrial power infrastructure is known to be incomplete, and this count cannot distinguish pre-existing from newly-installed elements. The figure should be treated as an indicative lower bound, not a precise inventory of new capacity.

- **Arboricultural Impact:** Per the SJA Trees Arboricultural Implications Report (2018, summary table), the development requires the removal of **79 individual trees**, plus **18 tree groups removed in full and 4 groups removed in part** — a loss of carbon sequestration and canopy-level evapotranspiration capacity. (An earlier draft stated "95 trees (15 Cat B, 57 Cat C)"; that figure was unsupported and did not reconcile with the SJA summary table, and has been corrected.)

- **Biophysical Change (NDVI):** Two distinct quantities are reported and should not be conflated. (i) *Absolute* Impact-zone greenness declined from a pre-development level of **~0.635** to a post-development level of **~0.28** (a fall of ~0.36 in raw NDVI units). (ii) The *Difference-in-Differences* signal — the quantity actually tested in `05` — is the regime shift in ΔNDVI (Impact − Control), estimated at **−0.36** by HAC OLS regression (reported p = 2.9e-40) and confirmed in direction by the **Seasonal Mann-Kendall** test on monthly-resampled ΔNDVI (reported p < 0.001). The two figures nearly coincide only because the adjacent Control Zone remained stable across the window; with a stable control, the DiD shift collapses onto the raw Impact-zone decline. The very small HAC p-value should be read as evidence that the *direction* and *persistence* of the shift are robust to autocorrelation, not as a precision claim on the −0.36 point estimate (see Limitation 3).

- **Thermodynamic Change (LST):** *All LST figures below were re-computed from the archived telemetry on 2026-06-12 (BACI split 2021-06-01, Newey-West HAC, maxlags = ⌈n^(1/3)⌉).*
  - **Primary — full VP polygon (`07`, `ee-chart_lst_sensitivity.csv`, n = 269):** full-year ΔT shift = **+0.56 °C** (HAC $p = 0.061$, 95% CI [−0.03, +1.15]; MW $p = 0.041$); summer (JJA) shift = **+1.09 °C** (HAC $p = 0.067$, MW $p = 0.042$). The full-polygon shift is positive and non-parametrically significant but only **marginal under HAC**, exactly as Limitation 2 anticipates: the ~1 km² polygon retains substantial vegetation that dilutes the impervious signal. This is the honest headline result — a detectable but modest warming whose parametric significance is constrained by within-polygon heterogeneity, not a clean p < 0.05 effect.
  - **Sensitivity — impervious parking-lot core (`07b`, `ee-chart_lst.csv`, n = 238):** isolating the asphalt core sharpens the signal to a full-year shift of **+1.08 °C** (HAC $p = 0.0034$, MW $p = 0.0001$) and a warm-season (Apr–Sep) shift of **+1.54 °C** (HAC $p = 0.0018$, MW $p = 0.0001$). That narrowing the ROI to the land-cover change roughly doubles the effect and moves it firmly into significance is itself evidence that the warming is driven by the impervious conversion rather than by polygon-wide drift.
  - **Annual JJA composites (`07c`):** full polygon +1.28 °C (Welch $p = 0.19$, $d = 0.95$, n.s.); parking-lot core +2.03 °C (Welch $p = 0.072$, $d = 1.37$, n.s.). Both composites rest on only 11 annual means (6 pre / 5 post) and are under-powered; they are reported as practical-magnitude context, not as significance tests. (The +0.57 °C / $d = 0.49$ figures in an earlier §2.C draft were the full-polygon full-year shift mislabelled as the parking-lot result; corrected.)
  - **Annual Composite Validation:** To resolve per-overpass variance, the `07c` script aggregates the parking-lot data into Annual Summer Composites. This yields a point estimate of **+2.03 °C** with a large effect size (Cohen's $d = 1.37$) but **does not reach conventional significance (Welch $p = 0.071$, n.s.)**. The composite rests on only 11 annual means split across the BACI threshold (6 pre / 5 post), so both the p-value and the $d$ estimate carry wide uncertainty and low power; the large $d$ should be read as a *suggestive* practical-magnitude signal, not as confirmation. The significance that the project can defend for the thermodynamic claim comes from the convergent pattern across pipelines (sign-consistent warming in the impervious core, ET suppression, and the energy-balance prediction), not from this single underpowered test.

- **Evapotranspiration (Latent Heat Proxy):** The MODIS ET DiD analysis yields a regime shift of **−0.15 mm/8-day** (HAC $p=0.106$, MW $p=0.0022$). The annual bar decomposition reveals persistent stabilisation below the pre-construction baseline after 2020. This provides the physical mechanism (latent heat suppression) for the observed thermal effects.

- **Independent Regional Baseline (Met Office):** To contextualise local change against background climate variability, Phase VII compares the satellite LST against UK Met Office HadUK-Grid station-interpolated data. Using the same 2021 epoch split as the BACI design, the regional SE England summer mean shifted by **+0.37 °C**. The parking-lot annual-composite point estimate (+2.03 °C) is several times larger than this regional baseline, which is *consistent with* a localised impervious-surface heating contribution over and above regional drift. This comparison is indicative rather than conclusive: the +2.03 °C estimate is not itself statistically significant (Welch p = 0.071), the two series measure different physical quantities (satellite land-surface temperature vs. screen-level air temperature), and a formal test would require propagating the uncertainty of both estimates. The claim defended here is therefore directional — the local signal is unlikely to be wholly explained by regional warming — not a quantified attribution.

- **Independent Impervious Verification (OSM + EIA):** The Phase VI non-satellite pipeline verifies the land-cover transition using OpenStreetMap data, detecting **17.43 ha** of deduplicated impervious surface (123% of the EIA's 14.12 ha footprint). Applying Penman-Monteith surface parameters to this transition predicts ~13.6 MW of latent heat suppression, physically corroborating the satellite ET and LST observations.

- **S106 / Institutional Governance:** The S106 agreement for the Shepperton expansion (Spelthorne Borough Council, 2019) contains no explicit ecological compensation for the greenbelt conversion. The total S106 financial obligation is **£36,150**, consisting entirely of transport-related administrative fees. The EIA's regulated energy demand projection is **5.4 GWh/year** (Spelthorne Borough Council, 2018), which covers only fixed building services (heating, cooling, lighting) and excludes total operational energy.

---

## 4. Feasibility, Scalability & Limitations

### Feasibility
- **Uses open-source spatial data (OSM)**: The audit methodology leverages Volunteered Geographic Information via the Overpass API.
- **Compatible with existing EIA processes**: This framework interfaces with the statutory frameworks mandated by the Town and Country Planning (Environmental Impact Assessment) Regulations 2017.
- **Fully open-source**: No proprietary GIS software (ArcGIS, ERDAS) is required. The pipeline uses Google Earth Engine (free for academic use), Python, and open geospatial libraries.

### Scalability
Because the spatial projection utilises the standardised British National Grid (EPSG:27700), this pipeline is **applicable across the UK screen sector**. It can be deployed to quantify cumulative land-cover change across expanding studio clusters (Shepperton, Longcross, Leavesden; PwC, 2018). The interpretation of such changes through political-economic frameworks requires case-by-case supplementary economic and governance evidence.

### Methodological Limitations

The following limitations are inherent to the pipeline and should be considered when interpreting results:

1. **OSM Tag Coverage**: The expanded Overpass query captures multiple impervious surface categories, but industrial logistics surfaces (untagged hardstanding, loading bays) may not be tagged. The 16.91 ha figure is therefore a lower-bound estimate of total impervious surface coverage.

2. **Landsat TIRS Spatial Resolution**: The native 100 m thermal pixel means that 3–5 pixels cover the parking-lot polygon. The resulting signal-to-noise ratio is insufficient to achieve statistical significance in the primary BACI test, as documented in §3. The robustness checks (sensitivity analysis, spatial transect, ET proxy) provide additional evidence but do not fully resolve this constraint.

3. **Spatial Variance vs. Confidence Intervals**: The ±1σ error bands in NDVI and LST charts represent pixel-level spatial variance (within-ROI heterogeneity), not confidence intervals on the trend estimates. Conclusion-level uncertainty bounds (e.g., "NDVI decline = 0.355 ± X") are not provided; deriving them would require bootstrap or Monte Carlo uncertainty propagation.

4. **Temporal Extrapolation**: All trend statements are bounded by the observation window (2015/2018–2026). Statistical trend tests describe historical trajectories and cannot predict future states.

5. **OSM Snapshot Reproducibility**: The Overpass query is pinned to `[date:"2026-03-03"]`, but OSM is a living database. Running the query without the date parameter, or with a different date, may yield different geometries and counts.

6. **Theory–Evidence Boundary**: The biophysical data (NDVI, LST, ET) directly demonstrates the physical consequences of land-cover change. The interpretation of these changes through political-economic frameworks (Digital Spatial Fix, Metabolic Rift, Accumulation by Dispossession) requires supplementary economic, governance, and institutional evidence that is cited but not computationally derived by this pipeline. The same biophysical effects would be expected from any impervious surface conversion of equivalent scale, regardless of end use.

7. **Temporal Autocorrelation**: Earth Observation time-series violate the independent and identically distributed (i.i.d.) assumption required by standard t-tests. The ET and LST pipelines address this via Newey-West HAC standard errors; the NDVI pipeline uses the Seasonal Mann-Kendall test, which is designed for autocorrelated data.

8. **Daytime-Only Thermal Observations**: Landsat overpasses are daytime-only (~10:30 local time). The spatial transect's negative daytime anomaly at the parking lot reflects the albedo-dominated daytime regime. Nocturnal thermal release — the primary UHI mechanism (Oke et al., 2017) — cannot be assessed with the current dataset and requires nighttime thermal sensors (ECOSTRESS, ASTER night-pass).

### Future Extensions

| Dimension | Current Limit | Potential Extension |
|:----------|:-------------|:--------------------|
| **Geospatial** | OSM static snapshot | Real-time change detection via Sentinel-1 SAR |
| **Thermodynamic** | Daytime-only Landsat overpass | ECOSTRESS or night-pass for nocturnal UHI quantification |
| **Energy Attribution** | Macro-grid aggregate (5.4 GWh regulated demand) | HVAC & server cooling load regression modelling |
| **Discourse** | Manual governance document review | Automated NLP analysis of corporate ESG reports |
| **Transport** | 2018 EIA predictive models | Live Traffic API monitoring (TomTom/Google Maps) |

---

## 5. Repository Structure

```
OSM_AUDIT_2025/
├── scripts/                            # Analytical and statistical pipeline
│   ├── 01_osm_extraction.ql            # Overpass QL: OSM spatial extraction
│   ├── 02_spatial_projection.py        # WGS84 → EPSG:27700 reprojection & area calculation
│   ├── 03_kepler_formatter.py          # Kepler.gl geovisualisation CSV generator
│   ├── 04_gee_ndvi_pipeline.js         # GEE: Sentinel-2 NDVI time series extraction
│   ├── 05_plot_ndvi_chart.py           # DiD + Seasonal Mann-Kendall NDVI analysis
│   ├── 06_gee_thermal_pipeline.js      # GEE: Triple-satellite LST extraction (BACI)
│   ├── 06b_gee_thermal_sensitivity.js  # GEE: Sensitivity analysis (full polygon, warm season)
│   ├── 07_plot_thermal_chart.py        # Paired BACI statistical rendering
│   ├── 07b_plot_thermal_sensitivity.py # Sensitivity analysis rendering
│   ├── 08_gee_transect_decay.js        # GEE: Concentric buffer LST transect extraction
│   ├── 09_plot_transect_decay.py       # Net Thermal Anomaly (background-subtracted) analysis
│   ├── 10_gee_evapotranspiration.js    # GEE: MODIS ET time series extraction
│   ├── 11_plot_evapotranspiration.py   # ET DiD regime shift analysis
│   └── run_pipeline.sh                 # Shell orchestrator for all local Python stages
├── data/
│   ├── raw_spatial/                    # Raw GeoJSON extracts (WGS84)
│   ├── raw_telemetry/                  # Satellite time series CSVs from GEE
│   └── processed/                      # Kepler.gl CSVs and projected datasets
├── visualisations/                     # Output NDVI/LST/ET charts (PNG, 300 DPI)
├── Forensic_Audit_Shepperton/          # Presentation slides (PDF)
├── documentation/                      # Zone selection rationale, data sources, institutional dossiers
├── requirements.txt                    # Python dependencies (pymannkendall, statsmodels, scipy, etc.)
├── LICENSE                             # MIT License
└── README.md
```

---

## 6. Dependencies and Execution

### 6.1 Software Environment (Python 3.10+)
```bash
pip install -r requirements.txt
./scripts/run_pipeline.sh
```

### 6.2 Remote Sensing (Google Earth Engine)
All `.js` scripts (`04`, `06`, `06b`, `08`, `10`) are designed for the [Google Earth Engine Code Editor](https://code.earthengine.google.com/) (Gorelick et al., 2017). Users must execute these manually and export the resulting `.csv` telemetry files to `data/raw_telemetry/` before running the Python charting scripts. The pipeline script will automatically skip charting modules whose input CSVs are absent.

### 6.3 Transparency, Reproducibility & Replicability

| Item | Value |
|:-----|:------|
| **Repository** | [github.com/HanpuLi/-OSM_AUDIT_2025](https://github.com/HanpuLi/-OSM_AUDIT_2025) |
| **Data Extraction Date** | 3 March 2026 |
| **Spatial Projection** | British National Grid (EPSG:27700) |
| **OSM Pipeline** | Overpass API (OpenStreetMap contributors, 2015) |
| **Earth Observation** | GEE: ESA Sentinel-2 (S2_SR_HARMONIZED) + USGS Landsat 7/8/9 (C2 T1 L2) + NASA MODIS MOD16A2GF |
| **Local Processing** | Python (`pandas`, `numpy`, `scipy`, `matplotlib`, `pymannkendall`, `statsmodels`, `shapely`, `pyproj`) |

---

## 7. Selected Bibliography

### Academic Literature
- Bozak, N. (2012) *The Cinematic Footprint: Lights, Camera, Natural Resources*. Rutgers University Press.
- Formenti, C. (2024) 'The environmental footprint of animated realism', *NECSUS*, 13(1), pp. 221–241.
- Foster, J.B. (1999) 'Marx's Theory of Metabolic Rift', *American Journal of Sociology*, 105(2), pp. 366–405.
- Gorelick, N. et al. (2017) 'Google Earth Engine: Planetary-scale geospatial analysis for everyone', *Remote Sensing of Environment*, 202, pp. 18–27.
- Greene, D. and Joseph, D. (2015) 'The Digital Spatial Fix', *tripleC*, 13(2), pp. 223–247.
- Harvey, D. (2004) 'The "New" Imperialism: Accumulation by Dispossession', *Socialist Register*, 40, pp. 63–87.
- Keeney, D. (2024) *Virtual Production's Role in Carbon Reduction*. Future Observatory / AHRC.
- Maxwell, R. and Miller, T. (2012) *Greening the Media*. Oxford University Press.
- Oke, T.R. (1987) *Boundary Layer Climates*. 2nd edn. Routledge.
- Oke, T.R. et al. (2017) *Urban Climates*. Cambridge University Press.
- Running, S.W. et al. (2019) *MOD16A2GF MODIS/Terra Net Evapotranspiration Gap-Filled*. NASA LP DAAC.
- Stewart-Oaten, A. et al. (1986) 'Environmental impact assessment: "pseudoreplication" in time?', *Ecology*, 67(4), pp. 929–940.

### Institutional Dossiers
- albert, BFI and Arup (2020) *A Screen New Deal*. London: British Film Institute.
- CIPFA (2023) *Spelthorne Borough Council: Capital Assurance Review*. DLUHC.
- Hydrock Consultants (2018) *Flood Risk Assessment*. SPS-HYD-XX-XX-RP-D-5001.
- i-Transport LLP (2018) *Shepperton Studios Transport Assessment*. ITL14056-008D R.
- PwC (2018) *Review of the UK film and high-end TV production facility market*. London.
- SJA Trees (2018) *Arboricultural Implications Report — Parts 1 & 2*. Drawing No: SJA TPP 18158-02.
- Spelthorne Borough Council (2018) *Environmental Statement Volume 1*. Planning App: 18/01212/OUT.
- Spelthorne Borough Council (2019) *Planning Committee Report & Printed Minutes*, 12 February 2019.
- Turley Economics (2018) *Expanding Shepperton Studios: The Economic Impact*. PINR3003.

---

## 8. Licensing

This project is submitted for the PMP ELSS Module assessment at Queen Mary University of London.  
Copyright © 2026 Hanpu Li (Caitlyn Lye). Released under the MIT License.
