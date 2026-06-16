# OSM_AUDIT_2025: Spatial Audit of Virtual Production Infrastructure

**Project Title:** The Material Footprint of Virtual Production: A Remote Sensing Assessment of Land-Cover Change and Biophysical Impacts at Shepperton Studios

**Author:** Hanpu Li (Caitlyn Lye)

**Institution:** Queen Mary University of London (QMUL)

**Status:** PMP ELSS Module Coursework (20% Assessment)

---

## 1. Project Overview & Argument

This repository contains the spatial data pipelines, Earth Observation (EO) algorithms, and analytical frameworks for a reproducible audit of the Shepperton Studios Virtual Production (VP) expansion (Planning Application 18/01212/OUT, London Borough of Spelthorne, United Kingdom). It combines Computational Spatial Science (GIS / Remote Sensing) with planning-archive and political-economic analysis.

The argument runs in five steps. The data and code in this repository complete the **first** of them and scope the remainder.

> **Scope statement.** This audit completes **Chapter 1**: it establishes, reproducibly, that the material footprint of the expansion is real, quantifiable, and — importantly — **not specific to virtual production**. Precisely *because* it is not specific, the argument's anchor moves from "virtual production is biophysically worse than other development" to "**low-carbon discourse licenses the ordinary physical cost of an impervious greenbelt development**." **Chapter 2** (discourse analysis of the consent file and the operator's sustainability claims) and **Chapter 3** (the political economy of land, ownership, and capital flow) are scoped here but not yet completed. Every "non-significant" result and the Longcross null below are therefore not failures but *correctly-bounded* Chapter-1 findings.

### 1.1 The claim

Contemporary industry discourse frames virtual production and cloud rendering as a low-carbon alternative to location shooting (Keeney, 2024; albert/BFI/Arup, 2020). Shepperton's green-belt release was consented within that framing. The first task of an audit is not to interpret the claim but to ask what was actually built on the ground — and whether the material record matches the rhetoric (Maxwell and Miller, 2012).

### 1.2 The material record — *the Digital Spatial Fix, made measurable*

Read through **the Digital Spatial Fix** (Greene & Joseph, 2015), digital media infrastructure is not a dematerialised entity but a mechanism through which capital expands into new geographic territory: soundstages, rendering farms, HVAC plant, and logistical hardstanding are that expansion in physical form. Where that expansion seals vegetated greenbelt, it also drives a **Metabolic Rift** (Marx, 1867; Foster, 1999; Bozak, 2012) in the land–atmosphere energy exchange, repartitioning absorbed radiation from latent heat (evaporative cooling) toward sensible heat (atmospheric warming).

The audit measures both. The load-bearing result is the **vegetation collapse**: a Difference-in-Differences NDVI shift of **−0.365 \*\*\*** that survives FDR control, a donor-weighted synthetic control, a 176-spec multiverse, a wild-cluster bootstrap, and a time-placebo. Daytime surface warming is then confirmed by **two independent satellites** — the Landsat parking-core BACI (**+1.08 °C**, HAC *p* = 0.003) and an independent ECOSTRESS re-extraction (**day +0.72 °C**, HAC *p* = 0.006). Greenbelt loss is ~39 ha. Full quantitative detail, and the honest bounds on each figure, are in §3 and §4.

### 1.3 The tell: the footprint is ordinary

Run the *same* pipeline on **Longcross Garden Village** — a residential green-belt release using the same planning mechanism, with no virtual-production component — and it shows the *same* generic signature scaled down with imperviousness (NDVI DiD −0.013 n.s., LST +0.41 °C n.s.). The Shepperton footprint is therefore **not** special to virtual production; it is what any impervious greenbelt conversion of that density looks like. This is the pivot of the whole project, not a weakness in it.

### 1.4 The asymmetry of extraction — *accumulation by dispossession*

If the physical harm is ordinary, the *institutional* record is where the development becomes legible as **accumulation by dispossession** (Harvey, 2004). The S106 agreement attached **no** ecological condition to a 39 ha greenbelt conversion:

> #### The asymmetry of extraction
> | What was taken / produced | Value | What was given back |
> |:--------------------------|:------|:--------------------|
> | Operational GVA (private, per annum) | **£322.7 M / yr** | — |
> | One-off construction-period GVA | £392 M | — |
> | Total S106 community obligation | **£36,150** | **entirely transport fees** |
> | Ecological / biodiversity contribution | — | **£0** |
> | Green-belt land converted | **39 ha** | **no ecological condition attached** |
> | Mature trees removed | 79+ individuals (plus 18 groups) | — |
>
> The £36,150 obligation consists entirely of transport-related administrative fees (a £6,150 Travel Plan Monitoring Fee, a £10,000 Parking Restriction Review, and a £20,000 Signage Strategy contribution; Spelthorne Borough Council, 2019). Gains are privatised at £322.7 M/yr (Turley Economics, 2018, para 33 / Table 3.6 series; construction-period GVA, Table 6.2); the ecological cost is socialised at a contracted price of **£0**. The remote sensing measures the *physical* erasure; this table measures the *institutional* one — and it is the cleaner evidence.

### 1.5 Therefore the discourse is the object

These steps converge on the project's actual object. If the material harm is generic (1.3) yet the development was consented as a low-carbon, "virtual", green substitute (1.1), then the **discourse** is doing the political work: it converts an ordinary greenbelt dispossession into a climate-virtuous one. The dissertation's object is the **gap between two registers** — the *discursive* (sustainable, virtual, green; what is claimed) and the *material* (greenbelt converted, surface warmed, ~5.4 GWh/yr regulated demand, £0 ecology; what is measured). This repository builds the measurement side of that gap as a reproducible, open-source method; the contribution is *"a reproducible method for auditing the material reality of 'sustainable' creative-industry infrastructure against its decarbonisation discourse."*

---

## 2. Methodological Architecture

**BACI threshold.** All before/after tests use a single fixed construction split, **`2021-06-01`**, applied identically across the NDVI, LST, and ET pipelines and to the Met Office regional baseline. This date is the mid-point of the documented impervious-conversion window: outline consent 18/01212/OUT was approved on **12 February 2019** (Spelthorne Borough Council Planning Committee), with the expansion **completed in March 2024** (Pinewood Group), giving a greenfield → asphalt build of roughly **2020–2023** (see `documentation/sprawl_zone_selection.md`). Dated primary/near-primary evidence now brackets this window (`documentation/construction_timeline_sources.md`): the geotechnical consultant (CGL) records pre-development ground investigation "during the height of the initial COVID-19 lockdown" (≈2020 Q2) and posts dated site photographs from **30 June 2021** and **8 December 2021**, with first stages opening from June 2023 and completion in March 2024 — placing `2021-06-01` squarely inside the active construction window. (Primary-source update, 2026-06-15, `documentation/construction_timeline_sources.md`: the Spelthorne Idox portal, read in a JavaScript-rendering browser, confirms that outline permission 18/01212/OUT is dated 4 July 2019 (council resolution 12 February 2019), that the Phase-1 reserved-matters approval 20/01108/RMA was issued 3 February 2021 so construction could not lawfully commence before that gate, and that the pre-commencement construction-management conditions 18/01212/DC20 were applied for on 13 October 2021; 2019 therefore sits firmly in the pre-period and the `2021-06-01` split falls after the legal gate and inside the active-works window. A reviewer could note that the construction-management conditions were not discharged until autumn 2021, so the split could plausibly move later; re-running the BACI at `2021-10-01` (`analysis/Split_Robustness_2026-06-15.py`) holds both load-bearing results, NDVI −0.346 ($p$ = 3.4e-26) and parking-core LST +0.84 °C (HAC $p$ = 0.032), attenuated but still significant, while full-polygon LST and ET stay non-significant at both splits. The southern parking-lot conversion month specifically still rests partly on imagery.) A mid-window split is the conservative choice for a phased conversion: it avoids assigning transitional years entirely to either epoch and biases the estimated shift *downward* rather than inflating it. (The spatial transect, `08`/`09`, instead contrasts clean pre- and post-windows — JJA 2016–2018 vs 2023–2025 — to sidestep the transition years altogether.)

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
  - **Results (re-verified 2026-06-12 against `ee-chart_lst.csv`, n = 238 valid overpasses):** full-year ΔT shift = **+1.08 °C** (HAC $p = 0.0034$, MW $p = 0.0001$); warm-season (Apr–Sep) shift = **+1.54 °C** (HAC $p = 0.0018$, MW $p = 0.0001$); annual JJA composite (`07c`) shift = **+2.03 °C** (Welch $p = 0.072$, n.s.; Cohen's $d = 1.37$, from 6 pre- / 5 post- annual means). These match §3. An earlier draft of this section quoted ≈ +0.57 °C / $d = 0.49$ / HAC $p = 0.12$; those figures were stale (the 0.57 was the *pre-period* mean, not the shift) and have been removed. The per-overpass HAC results are significant; only the small-$n$ annual composite is under-powered, which is why the thermodynamic claim is anchored on the per-overpass test and cross-pipeline convergence rather than on the composite alone. *(Sensor-robustness, added 2026-06-15: a Landsat-8-only re-extraction gives +0.68 °C, HAC $p = 0.19$, n.s. at n = 119; positive but underpowered once L7 and L9 are dropped. See §4 and `analysis/SensorRobustness_TIER2_2026-06-15.py`.)*

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

- **Impervious Surface Coverage:** A deduplicated total of **16.91 hectares** (169,100 m²) of OSM-tagged impervious surfaces within the 1200 m extraction radius (Shepperton and Longcross combined), comprising parking (13.21 ha) and industrial landuse (3.70 ha) only, with overlap dissolved via `shapely.unary_union`. This figure counts the parking and industrial-landuse categories alone and **excludes power infrastructure, buildings and paved service roads**; it is therefore not directly comparable with the Shepperton-only, power-inclusive 17.43 ha figure reported under Independent Impervious Verification below (the two use different category sets and different areas of interest, which is why the combined-site value here is smaller). This figure is a **lower-bound estimate** as untagged hardstanding is not captured by OSM. It is distinct from the 16.4 ha of building floorspace reported in the EIA (Spelthorne Borough Council, 2018).

- **Power Infrastructure:** The identification of **17 `power=*`-tagged elements** (substations, transformers, power lines) within the 1200 m extraction radius. **Caveat:** OSM coverage of private industrial power infrastructure is known to be incomplete, and this count cannot distinguish pre-existing from newly-installed elements. The figure should be treated as an indicative lower bound, not a precise inventory of new capacity.

- **Arboricultural Impact:** Per the SJA Trees Arboricultural Implications Report (2018, summary table), the development requires the removal of **79 individual trees**, plus **18 tree groups removed in full and 4 groups removed in part** — a loss of carbon sequestration and canopy-level evapotranspiration capacity. (An earlier draft stated "95 trees (15 Cat B, 57 Cat C)"; that figure was unsupported and did not reconcile with the SJA summary table, and has been corrected.)

- **Biophysical Change (NDVI):** Two distinct quantities are reported and should not be conflated. (i) *Absolute* Impact-zone greenness declined from a pre-development level of **~0.635** to a post-development level of **~0.28** (a fall of ~0.36 in raw NDVI units). (ii) The *Difference-in-Differences* signal — the quantity actually tested in `05` — is the regime shift in ΔNDVI (Impact − Control), estimated at **−0.36** by HAC OLS regression (reported p = 2.9e-40) and confirmed in direction by the **Seasonal Mann-Kendall** test on monthly-resampled ΔNDVI (reported p < 0.001). The two figures nearly coincide only because the adjacent Control Zone remained stable across the window; with a stable control, the DiD shift collapses onto the raw Impact-zone decline. The very small HAC p-value should be read as evidence that the *direction* and *persistence* of the shift are robust to autocorrelation, not as a precision claim on the −0.36 point estimate (see Limitation 3).

- **Thermodynamic Change (LST):** *All LST figures below were re-computed from the archived telemetry on 2026-06-12 (BACI split 2021-06-01, Newey-West HAC, maxlags = ⌈n^(1/3)⌉).*
  - **Primary — full VP polygon (`07`, `ee-chart_lst_sensitivity.csv`, n = 269):** full-year ΔT shift = **+0.56 °C** (HAC $p = 0.061$, 95% CI [−0.03, +1.15]; MW $p = 0.041$); summer (JJA) shift = **+1.09 °C** (HAC $p = 0.067$, MW $p = 0.042$). The full-polygon shift is positive and non-parametrically significant but only **marginal under HAC**, exactly as Limitation 2 anticipates: the ~1 km² polygon retains substantial vegetation that dilutes the impervious signal. This is the honest headline result — a detectable but modest warming whose parametric significance is constrained by within-polygon heterogeneity, not a clean p < 0.05 effect.
  - **Sensitivity — impervious parking-lot core (`07b`, `ee-chart_lst.csv`, n = 238):** isolating the asphalt core sharpens the signal to a full-year shift of **+1.08 °C** (HAC $p = 0.0034$, MW $p = 0.0001$) and a warm-season (Apr–Sep) shift of **+1.54 °C** (HAC $p = 0.0018$, MW $p = 0.0001$). That narrowing the ROI to the land-cover change roughly doubles the effect and moves it firmly into significance is itself evidence that the warming is driven by the impervious conversion rather than by polygon-wide drift. This sensitivity is best read as a **surface-cover-stratified contrast in the Local Climate Zone sense** (Stewart and Oke, 2012): the parking core is a paved LCZ-E inclusion inside a mixed-cover polygon, so stratifying to it isolates the impervious heating signal rather than redrawing a boundary around hot pixels. The boundary is verified to have been defined from the EIA and OSM parking footprint independently of the thermal data (`documentation/parking_core_provenance_2026-06-15.md`). *Sensor-robustness caveat (added 2026-06-15, `analysis/SensorRobustness_TIER2_2026-06-15.py`): restricting to Landsat 8 alone halves the sample to n = 119 and the parking-core shift falls to **+0.68 °C (HAC $p = 0.19$, n.s.)**; the point estimate stays positive, so this is a power loss from dropping the L7 and L9 scenes, not a sign reversal. Every +1.08 °C figure in this document should be read alongside this n.s. Landsat-8-only value.*
  - **Annual JJA composites (`07c`):** full polygon +1.28 °C (Welch $p = 0.19$, $d = 0.95$, n.s.); parking-lot core +2.03 °C (Welch $p = 0.072$, $d = 1.37$, n.s.). Both composites rest on only 11 annual means (6 pre / 5 post) and are under-powered; they are reported as practical-magnitude context, not as significance tests. (The +0.57 °C / $d = 0.49$ figures in an earlier §2.C draft were the full-polygon full-year shift mislabelled as the parking-lot result; corrected.)
  - **Annual Composite Validation:** To resolve per-overpass variance, the `07c` script aggregates the parking-lot data into Annual Summer Composites. This yields a point estimate of **+2.03 °C** with a large effect size (Cohen's $d = 1.37$) but **does not reach conventional significance (Welch $p = 0.071$, n.s.)**. The composite rests on only 11 annual means split across the BACI threshold (6 pre / 5 post), so both the p-value and the $d$ estimate carry wide uncertainty and low power; the large $d$ should be read as a *suggestive* practical-magnitude signal, not as confirmation. The significance that the project can defend for the thermodynamic claim comes from the convergent pattern across pipelines (sign-consistent warming in the impervious core, ET suppression, and the energy-balance prediction), not from this single underpowered test.
  - **Cross-sensor confirmation (ECOSTRESS):** An independent re-extraction on a *different* sensor and orbit — NASA ECOSTRESS `ECO_L2T_LSTE.002` (70 m, ISS, non-sun-synchronous; 1,189 paired clean overpasses, 700 day / 489 night) — reproduces the daytime warming: **day ΔT = +0.72 °C (HAC $p = 0.0062$, MW $p = 6.1\times10^{-4}$; robust to the Oct-split at +0.64 °C, $p = 0.013$)**, with the parking core flipping from −0.45 °C *cooler* than Control pre-construction to +0.27 °C *warmer* post-construction (the DiD is the flip, not a pre-existing hotspot). Smaller than the Landsat +1.08 °C but same-sign and significant — exactly what cross-sensor corroboration should look like. The **night** channel is directional but not significant (**+0.32 °C, HAC $p = 0.20$, n.s.**), which correctly bounds the claim to *solar/surface-driven daytime heating* rather than a round-the-clock thermal-mass UHI. (`analysis/ECOSTRESS_Night_TIER2_2026-06-16.py`; full result + caveats in `analysis/ECOSTRESS_DayNight_TIER2_RESULTS_2026-06-16.md`.)

- **Evapotranspiration (Latent Heat Proxy):** The MODIS ET DiD analysis yields a regime shift of **−0.08 mm/8-day** (HAC $p = 0.45$, MW $p = 0.57$, n.s.; pre $n = 295$, post $n = 211$). The post-construction annual ΔET values are sign-consistent and uniformly negative (−0.14 to −0.33 mm/8-day across 2021–2025), so the *direction* of latent-heat suppression matches the energy-balance prediction; but the difference-in-differences shift is **not statistically significant on the archived data**. The reason is that the pre-period mean is already negative (−0.13 mm/8-day), pulled down by the 2019 drought year (ΔET = −0.80, which falls in the pre epoch), and this compresses the estimated regime shift. ET is therefore retained as **qualitative, directional corroboration** of the latent-heat mechanism, *not* as a well-powered significant pillar of the thermodynamic claim. (2019-drought sensitivity, now run — `analysis/ET_2019_sensitivity_2026-06-15.md`: controlling for or dropping the 2019 drought year moves the DiD to −0.205 mm/8-day with HAC $p ≈ 0.049$, i.e. marginal significance that is **conditional on excluding a climate-anomaly year, bandwidth-sensitive (HAC $p$ ranges 0.05↔0.025), and not corroborated by the non-parametric Mann-Whitney test ($p = 0.20$)**; ET is therefore kept as qualitative/directional, not re-promoted to a significant pillar.) *Reference-ET normalisation (added 2026-06-15, `analysis/ReferenceET_TIER2_2026-06-15.py`): dividing actual ET by ERA5-Land reference ET₀ (FAO-56) to strip out the weather envelope shrinks the 2019 drought ΔET from −0.80 to about −0.03 and leaves the normalised DiD at **+0.005 (HAC $p = 0.18$, n.s.)**. This confirms the ET null is principled rather than an artefact of the drought year; ET stays directional corroboration, not a pillar.*

- **Independent Regional Baseline (Met Office):** To contextualise local change against background climate variability, Phase VII compares the satellite LST against UK Met Office HadUK-Grid station-interpolated data. Using the same 2021 epoch split as the BACI design, the regional SE England summer (JJA) mean shifted by **+0.64 °C** (annual mean +0.56 °C; long-term trend +0.32 °C/decade). This regional baseline is **larger than the full-polygon LST shift (+0.56 °C)**: the headline full-polygon warming therefore does **not** exceed regional climate drift, and cannot on its own be claimed as a localised anthropogenic signal. The case for a *local* impervious-surface contribution rests only on the parking-lot core, where the per-overpass full-year shift (+1.08 °C, HAC $p = 0.0034$; Landsat-8-only +0.68 °C, n.s., see §2.C and §4) and the annual JJA composite (+2.03 °C) sit above the +0.64 °C regional baseline. Even there the comparison is indicative rather than conclusive: the +2.03 °C composite is not itself statistically significant (Welch $p = 0.071$), the two series measure different physical quantities (satellite land-surface temperature vs. screen-level air temperature), and a formal test would require propagating the uncertainty of both estimates. The defensible claim is therefore narrow and directional: only the impervious core exceeds the regional baseline, and only suggestively, not a polygon-wide or quantified attribution.

- **Independent Impervious Verification (OSM + EIA):** The Phase VI non-satellite pipeline verifies the land-cover transition using OpenStreetMap data, detecting **17.43 ha** of deduplicated impervious surface for Shepperton alone — parking 10.94 ha + industrial landuse 3.70 ha + power infrastructure 2.79 ha (live `scripts/12` output), 123% of the EIA's 14.12 ha footprint. This Shepperton-only, power-inclusive total is a different metric from the 16.91 ha combined-site figure above (which counts only parking and industrial landuse across both Shepperton and Longcross); the two are not interchangeable. Applying Penman-Monteith surface parameters to this transition predicts ~13.6 MW of latent heat suppression, physically corroborating the satellite ET and LST observations.

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

6. **Theory–Evidence Boundary**: The biophysical data (NDVI, LST, ET) directly demonstrates the physical consequences of land-cover change. The interpretation of these changes through political-economic frameworks (Digital Spatial Fix, Metabolic Rift, Accumulation by Dispossession) requires supplementary economic, governance, and institutional evidence that is cited but not computationally derived by this pipeline. The same biophysical effects would be expected from any impervious surface conversion of equivalent scale, regardless of end use. *Empirical support (added 2026-06-15, `analysis/NonVP_ComparatorAnalysis_TIER2_2026-06-15.py`): a matched BACI on Longcross Garden Village, a residential green-belt release built 2020–2023 with its own construction split of 2020-01-01, returns NDVI DiD −0.013 (HAC $p = 0.48$, n.s.) and LST DiD +0.41 °C (HAC $p = 0.18$, n.s.), neither significant. This is consistent with the signature scaling with the degree of imperviousness (Shepperton's dense studio-and-parking build versus Longcross's lower-density garden-village layout) rather than being specific to virtual production. It is a single residential-versus-industrial pair (n = 1 comparator), so it supports the claim that impact scales with imperviousness, not a virtual-production-specific claim; this limitation therefore stands at the virtual-production level.*

7. **Temporal Autocorrelation**: Earth Observation time-series violate the independent and identically distributed (i.i.d.) assumption required by standard t-tests. The ET and LST pipelines address this via Newey-West HAC standard errors; the NDVI pipeline uses the Seasonal Mann-Kendall test, which is designed for autocorrelated data. *Identification and multiple-comparison robustness (added 2026-06-15, `analysis/ParallelTrends_FDR_2026-06-15.md`):* pre-period parallel-trends tests pass for all four pipelines (pre-trend slopes n.s., HAC $p ≥ 0.11$; the full-polygon LST slope $-0.13$/yr, $p = 0.11$, is the weakest and is flagged per Roth 2022); and under Benjamini-Hochberg FDR control across the full reported test matrix, the **NDVI and parking-core LST results remain significant ($q < 0.01$), while the marginal full-polygon LST and the n.s. ET do not survive** — exactly the collapse the corrected headline already anticipates.

*Second-order robustness suite (added 2026-06-15; four local-only tests, all numbers from live runs on the archived CSVs):*

- **Event-study / dynamic DiD** (`analysis/EventStudy_2026-06-15.py`): in half-year event time, the **parking-core LST effect opens exactly at the construction split** (ebin 0 = 2021-06: **+2.02 °C, HAC $p = 0.0043$**), and the **NDVI** post-split lags deepen monotonically and remain significant (ebin 5: $-0.30$, $p < 0.001$); the full-polygon LST and ET show no opening at the split (consistent with their marginal/null status). *Honest caveat:* the flexible joint pre-trend Wald test rejects flat leads for all four pipelines ($p < 0.001$), unlike the single-slope pre-trend test above — most plausibly early-works leakage (CGL ground investigation from ~2020 Q2; site photos dated 30 Jun / 8 Dec 2021) contaminating the late-pre baseline, which would make the 2021-06-01 split *conservative*. Both pre-trend readings are now reported rather than only the one that passes.
- **Specification curve / multiverse** (`analysis/SpecCurve_2026-06-15.py`, 176 specs each = split date × season window × HAC bandwidth): **NDVI core is 100% sign-consistent and 100% significant; parking-core LST is 100% sign-consistent (positive) and 89.8% significant**; full-polygon LST is sign-consistent but only 31.8% significant; **ET is 100% sign-consistent (negative) but only 25% significant, with significance confined entirely to the warm Apr–Sep window** — direct evidence that the two FDR survivors are spec-robust while ET's significance is window-dependent.
- **Wild-cluster bootstrap** (`analysis/WildBootstrap_2026-06-15.py`, Rademacher, $B = 9999$, restricted WCR): on the small-$n$ annual composites, **NDVI core $p = 0.004$ (\*\*)** and the **parking-core warm-season composite $p = 0.032$ (\*)** survive; the **parking-core JJA composite $p = 0.070$ (n.s.)** confirms — rather than contradicts — the README's Welch $p = 0.071$, and ET stays n.s. The bootstrap corrects the small-sample reference; it does not manufacture power from ~11 annual points.
- **Placebo** (`analysis/Placebo_2026-06-15.py`): time-placebo on the pre-construction window gives **0/6 spurious significant fake-split DiDs for the parking core** (cleanest falsification support) and 0/6 on HAC for ET; NDVI shows 2/6 minor flags whose magnitudes ($\pm0.12$) are ~⅓ of the true effect ($-0.365$) and one of opposite sign (the same late-pre leakage signal as the event-study). The **spatial placebo is honestly reported as unsupported by the local data** — each CSV carries only one Impact and one Control series — and is deferred to the synthetic-control in-space permutation in `_METHODOLOGY_ROADMAP_TIER2_2026-06-15.md`.

None of the four overturns a headline: the two FDR-surviving conclusions (NDVI core, parking-core LST) are hardened, and the full-polygon/ET caveats are confirmed. The one genuinely new tension is the flexible-event-study pre-trend flag, now disclosed. The companion `.md` for each script records the full measured output.

*Third-order corroboration suite (Tier-2, added 2026-06-15; the load-bearing DiDs were re-verified against the archived CSVs on 2026-06-15, and the synthetic-control, ERA5, sensor and reference-ET numbers come from the live Tier-2 runs logged in `analysis/_TIER2_RESULTS_2026-06-15.md`):*

- **Synthetic control** (`analysis/SyntheticControl_Analysis_TIER2_2026-06-15.py`): replacing the single hand-picked Control with a donor-weighted synthetic control built from 19 stable Surrey/Spelthorne green-belt polygons reproduces both headlines. The NDVI treatment effect is **−0.3525** (in-space placebo rank 3/20, permutation $p = 0.15$; in-time 2019 placebo −0.0105, essentially zero before construction), and the parking-core LST effect is **+0.428 °C** (rank 7/20, permutation $p = 0.35$), more conservative than the single-control +1.08 °C. NDVI survives the donor swap decisively; the LST effect keeps its sign and magnitude but is not significant under the permutation, consistent with its power-limited status.
- **Co-located climate counterfactual** (`analysis/GridCounterfactual_TIER2_2026-06-15.py`, ERA5-Land 9 km): local background JJA air-temperature warming over the site is **+0.82 °C**. Netting this off the satellite LST DiDs gives an excess (anthropogenic local) warming of **+0.26 °C in the parking core** (+1.08 − 0.82) but **−0.26 °C for the full polygon** (+0.56 − 0.82): the excess heating is confined to the impervious core, and the full polygon does not exceed its own co-located climate trend. *Scale caveat:* the Impact and Control points lie only 4.1 km apart and fall in the same ERA5-Land 9 km cell, so the air-temperature DiD is mechanically zero and this is a single-baseline subtraction, not a same-scale DiD.
- **True 1 km same-scale air-temperature baseline** (`analysis/HadUK_1km_Counterfactual_TIER2_2026-06-15.py`, HadUK-Grid v1.3.2.ceda `tas`, run 2026-06-15): at 1 km the Impact and Control points fall in **different** cells (E506500/N169500 vs E510500/N168500), so a genuine co-located air-temperature DiD is identifiable. That DiD is **+0.005 °C (HAC $p = 0.62$, n.s.)** over the full year, i.e. there is no meaningful differential background air-temperature trend between the two sites. Netting it off the satellite LST DiDs leaves a same-scale excess of **+1.07 °C in the parking core** and +0.56 °C for the full polygon. This refines and is cleaner than the ERA5 step, which subtracted an absolute regional warming from a difference-in-differences; the correct counterfactual for a surface-temperature DiD is an air-temperature DiD on the same pair, and it is essentially zero. *Honest bounds:* HadUK-Grid is station-interpolated, so a 1 km cell cannot itself sense the 13 ha lot; the result shows the surface-warming gap is not an artefact of differential climate, not that air temperature over the asphalt rose by +1.07 °C. The standing Landsat-8-only n.s. caveat and the marginal full-polygon significance still apply, and NDVI remains the load-bearing pillar. Full write-up: `analysis/HadUK_1km_Counterfactual_TIER2_2026-06-15.md`.
- **Sensor robustness** (`analysis/SensorRobustness_TIER2_2026-06-15.py`): the parking-core LST result is carried in part by Landsat 7 and 9; a Landsat-8-only re-extraction gives **+0.68 °C (HAC $p = 0.19$, n.s.)** at n = 119 against n = 238 for the triple-sensor merge. Positive but underpowered, a sample-size effect, not a reversal. NDVI uses Sentinel-2 only and has no cross-sensor exposure.
- **Independent-sensor day/night LST** (`analysis/ECOSTRESS_Night_TIER2_2026-06-16.py`, NASA ECOSTRESS `ECO_L2T_LSTE.002`, 70 m, ISS): a fully independent sensor and orbit confirms the daytime parking-core warming at **+0.72 °C (HAC $p = 0.0062$)** — same sign, significant, robust to the October split — and resolves the daytime cold-core anomaly (the core flips from −0.45 °C cooler pre-construction to +0.27 °C warmer post). The **night** DiD is **+0.32 °C (HAC $p = 0.20$, n.s.)**: directional but not significant, which bounds the signal to solar/surface-driven daytime heating rather than a deep-thermal-mass nocturnal UHI. This replaces the previously data-blocked night-LST extension with a measured result and is the strongest single piece of cross-sensor corroboration in the suite. Carry-with caveats: ISS overpass-time distributions differ pre/post, the pre-period is short (~3 yr), and the 70 m point sample is coarser than the hand-digitised Landsat polygon (`analysis/ECOSTRESS_DayNight_TIER2_RESULTS_2026-06-16.md`).
- **Reference-ET normalisation** (`analysis/ReferenceET_TIER2_2026-06-15.py`): normalising actual ET by ERA5-Land reference ET₀ absorbs the 2019 drought (drought ΔET −0.80 to about −0.03) and leaves the DiD at **+0.005 (HAC $p = 0.18$, n.s.)**, confirming the ET null is principled rather than drought-driven.
- **Non-virtual-production comparator** (`analysis/NonVP_ComparatorAnalysis_TIER2_2026-06-15.py`): Longcross Garden Village (residential green-belt release, built 2020–2023, own split 2020-01-01) shows NDVI DiD **−0.013** (HAC $p = 0.48$, n.s.) and LST DiD **+0.41 °C** (HAC $p = 0.18$, n.s.), neither significant. This supports the signature scaling with imperviousness rather than being specific to virtual production, but it is a single comparator (residential versus industrial), so it does not on its own license a virtual-production-specific claim (see Limitation 6).

Taken together, Tier-2 hardens NDVI as the load-bearing pillar (it survives the synthetic control and an in-time placebo), reframes the parking-core warming as a real but power-limited, surface-cover-stratified (Local Climate Zone) signal that should always travel with its Landsat-8-only n.s. caveat, and confirms the full-polygon LST and ET as non-significant. The true 1 km air-temperature baseline has now been run (HadUK-Grid, above): it strengthens rather than overturns the parking-core result. The previously outstanding upgrade — night-time and cross-sensor LST — has now also been run via ECOSTRESS (above): it confirms the daytime warming on an independent sensor and bounds the signal to daytime/surface heating, leaving no major analytical gap at the material-footprint (Chapter-1) level. The remaining work is structural and discursive (Chapters 2–3), not a further sensor.

8. **Daytime-Only Landsat / the nocturnal channel**: Landsat overpasses are daytime-only (~10:30 local time), and the spatial transect's negative daytime anomaly at the parking lot reflects the albedo-dominated daytime regime. Nocturnal thermal release — the primary UHI mechanism (Oke et al., 2017) — is invisible to Landsat. This is now *partly* addressed: the ECOSTRESS re-extraction (§4, Tier-2) supplies a night channel and finds the night DiD **non-significant (+0.32 °C, HAC $p = 0.20$)**, which bounds the confirmed signal to solar/surface-driven daytime heating rather than a deep-thermal-mass nocturnal UHI. A fuller nocturnal characterisation (longer night record, ASTER night-pass) remains a future extension.

### Future Extensions

| Dimension | Current Limit | Potential Extension |
|:----------|:-------------|:--------------------|
| **Geospatial** | OSM static snapshot | Real-time change detection via Sentinel-1 SAR |
| **Thermodynamic** | ECOSTRESS night channel n.s. on a short (~3 yr) pre-record | Longer night record + ASTER night-pass to fully characterise nocturnal release |
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
- Fisher, J.B. et al. (2020) 'ECOSTRESS: NASA's next-generation mission to measure evapotranspiration from the International Space Station', *Water Resources Research*, 56(4), e2019WR026058. (Cited 2026-06-15 for the night-LST extension.)
- Hollis, D. et al. (2019) 'HadUK-Grid: a new UK dataset of gridded climate observations', *Geoscience Data Journal*, 6(2), pp. 151–159. (Cited 2026-06-15 for the planned 1 km air-temperature baseline.)
- Stewart, I.D. and Oke, T.R. (2012) 'Local Climate Zones for urban temperature studies', *Bulletin of the American Meteorological Society*, 93(12), pp. 1879–1900. (Cited 2026-06-15 for the surface-cover-stratified framing of the parking core.)

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
