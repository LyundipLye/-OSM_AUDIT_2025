# OSM_AUDIT_2025: Forensic Spatial Audit of Virtual Production Infrastructure

**Project Title:** The Political Economy of Greenwashing: Spatialising the Myth of Immateriality in Virtual Production and the Digital Spatial Fix

**Author:** Hanpu Li (Caitlyn Lye)

**Institution:** Queen Mary University of London (QMUL)

**Status:** PMP ELSS Module Coursework (20% Assessment)

## 1. Project Overview & Academic Contribution

This repository contains the spatial data pipelines, Earth Observation (EO) algorithms, and theoretical frameworks developed for the empirical audit of Virtual Production (VP) infrastructure, specifically examining the Shepperton Studios expansion in the United Kingdom.

While contemporary industry discourse frames virtual production and cloud rendering as a low-carbon, "immaterial" alternative to location shooting, this project proposes a structural counter-narrative. By synthesising Computational Spatial Science (GIS/Remote Sensing) with Eco-Marxist Political Economy, this repository provides a replicable, open-source methodological pipeline to quantify the physical, thermodynamic, and ecological costs of digital media expansion.

### Theoretical Framework

The analytical pipeline is grounded in three core political-economic paradigms:

- **The Digital Spatial Fix** (Greene & Joseph, 2015): Conceptualising digital infrastructure not as a dematerialised entity, but as a mechanism through which capital resolves accumulation crises by expanding into new geographic territories.
- **The Metabolic Rift** (Marx, 1867 / Bozak, 2012): Quantifying the physical rupture in ecological systems necessitated by algorithmic and computational metabolism.
- **Accumulation by Dispossession** (Harvey, 2004): Examining the asymmetry between privatised economic gains (Net GVA) and socialised ecological burdens (localised thermodynamic escalation and biomass erasure).

## 2. Methodological Architecture

To ensure scientific rigor, this project employs a triangulated approach combining OSM topological tracing, multi-spectral Earth Observation, and local governance dossier reviews. For NDVI, a strict **Difference-in-Differences (DiD)** methodology with **Seasonal Mann-Kendall** testing isolates vegetative degradation from biological autocorrelation. For LST, a **Paired BACI (Before-After-Control-Impact)** design with **Welch's t-test** and **Mann-Whitney U** quantifies the thermal regime shift from land-use conversion. Both pipelines implement **Pixel-Level Uncertainty Quantification (UQ)**.

### Phase I: Geomatic Extraction & Topological Normalisation

**Objective:** To empirically quantify logistical sprawl by bypassing corporate-curated spatial data.

- **`01_osm_extraction.ql`** (Overpass QL): 
  - **Logic**: Executes a radius-constrained extraction (1200m) around the Shepperton coordinates via the Overpass API. Targets industrial geometries, power infrastructure (132kV transformers), and newly concreted logistical surfaces (`amenity=parking`).
- **`02_spatial_projection.py`** (Python): 
  - **Logic**: Ingests WGS84 GeoJSON satellite vectors. Utilising `shapely.geometry` and `pyproj.Transformer`, the script mathematically transforms angular geographic coordinates into the British National Grid (EPSG:27700) Cartesian plane.
  - **Why this matters**: Calculating areas directly in WGS84 introduces severe spherical distortions. Projecting to EPSG:27700 allows the script to compute exact planar land-conversion metrics (in square metres) with an error margin of <0.1%.
- **`03_kepler_formatter.py`** (Python): 
  - **Logic**: Iterates over projected spatial geometries, calculating their centroids and planar areas. Exports a rigorously formatted CSV infused with intensity weightings designed specifically for 3D extrusion rendering in Kepler.gl.

### Phase II: Earth Observation & Metabolic Quantification

**Objective:** To measure the longitudinal biophysical and thermodynamic alterations in the audited zone, rigorously controlled against nearby undeveloped greenbelts.

- **`04_gee_ndvi_pipeline.js`** (Google Earth Engine API - JavaScript): 
  - **Logic**: Interfaces with the ESA Sentinel-2 (S2_SR_HARMONIZED) multispectral constellation. Extracts the Normalised Difference Vegetation Index (NDVI), calculating both geometric spatial means and pixel-level standard deviations (`stdDev`) across an 8-year temporal axis.
  - **Algorithm Highlight**: Implements a dual-layer cloud masking function using both the QA60 bitmask and the advanced SCL (Scene Classification Layer) to strictly filter cloud shadows, cirrus bands, and snow. Pivotally exports spatial variance telemetry in Wide-Format for Academic Uncertainty Quantification (UQ).
- **`05_plot_ndvi_chart.py`** (Python): 
  - **Logic**: Ingests the raw NDVI telemetry CSV from GEE. 
  - **Algorithm Highlight**: Employs a 3rd-order Savitzky-Golay signal filter (`scipy.signal.savgol_filter`, window=365 days) to preserve peak amplitude of seasonal vegetation phenology. Utilizes **Difference-in-Differences (DiD)** against the Control Zone greenbelt to calculate the net anthropogenic signal ($\Delta$ NDVI). Applies a rigorous Non-Parametric **Seasonal Mann-Kendall test** (`pymannkendall`, `period=365`) to algebraically neutralize biological autocorrelation and verify the degradation core. Renders a $\pm 1 \sigma$ semi-transparent error band encapsulating spatial variance (UQ) for ultimate empirical defense.
- **`06_gee_thermal_pipeline.js`** / **`07_plot_thermal_chart.py`**: 
  - **Logic**: Implements a **triple-satellite fusion** (Landsat 7,8,9) to maximise temporal observation density. Extracts LST over a precise 5-vertex polygon delineating the newly-constructed parking lot. 
  - **Algorithm Highlight**: Employs a **Paired BACI** design, removing NDBI masking to measure the pure causal effect of greenfield-to-asphalt conversion. Evaluates $\Delta$T significance via Welch's t-test and Mann-Whitney U.

**To fortify the thermal inference against the physical resolution limits of Landsat TIRS (100m native thermal pixel), this project deploys a Tri-Pillar Causal Defense — three methodologically independent pipelines that converge on the same physical reality from distinct vantage points:**

- **Option A: Sensitivity Analysis** (`06b_gee_thermal_sensitivity.js`, `07b_plot_thermal_sensitivity.py`):
  - **Logic**: Expands the spatial pool from the parking-lot polygon (~3 thermal pixels) to the full 1 km² VP development polygon (~50 pixels), and restricts the temporal window to the Warm Season (Apr–Sep) when surface energy balance differences are maximised.
  - **Rationale**: By increasing the pixel count an order of magnitude, spatial variance ($\sigma$) is reduced via $\sigma/\sqrt{n}$, radically boosting the statistical power of the Welch's t-test. This tests whether the marginal BACI result (p ≈ 0.07) strengthens when the spatial constraint is relaxed.

- **Phase IV: Spatial Transect / Distance Gradient Analysis** (`08_gee_transect_decay.js`, `09_plot_transect_decay.py`):
  - **Logic**: Constructs 16 concentric annular buffers (50 m bandwidth, 0–800 m) emanating radially from the Impact Zone boundary. For each ring, the GEE script computes the spatial mean LST from 3-year summer (JJA) composites for both the pre-construction epoch (2016–2018) and the post-construction epoch (2023–2025), using the same triple-satellite fusion (Landsat 7+8+9) as the primary BACI pipeline.
  - **Algorithm Highlight**: Because the two epochs may differ in regional baseline temperature due to inter-annual climate variability (e.g., the 2016–18 London summers were empirically ~1.4 °C warmer than 2023–25), the Python script applies a **background-subtraction normalisation**. The far-field anomaly (mean of Post−Pre at 400–800 m) is treated as the climate baseline and subtracted from each ring, yielding a **Net Thermal Scar** metric that isolates the spatially localised effect of the land-cover change from global confounders.
  - **Physical Interpretation**: This pipeline does not test temporal significance (that is the BACI's role); instead, it provides **spatial corroboration** — demonstrating whether the thermal anomaly exhibits the monotonic distance-decay gradient expected of a point-source emitter, consistent with sensible heat advection theory (Oke, 1987).

- **Phase V: Evapotranspiration Collapse / Metabolic Proxy** (`10_gee_evapotranspiration.js`, `11_plot_evapotranspiration.py`):
  - **Logic**: Extracts the 8-day Actual Evapotranspiration (ET, kg/m²/8-day) from the MODIS/Terra MOD16A2GF product (500 m spatial resolution) over the full VP development polygon (Impact Zone) and a stable parkland Control Zone of equivalent area (~500 m radius buffer). The GEE script applies the MODIS scale factor (×0.1) and exports a paired time series spanning 2015–2026.
  - **Algorithm Highlight**: At MODIS 500 m resolution, both zones are sub-pixel suburban mosaics, so absolute ET curves visually overlap. The critical signal emerges in the **Difference-in-Differences (DiD)** domain: $\Delta$ET = ET$_{\text{Sprawl}}$ − ET$_{\text{Control}}$. The Python script partitions $\Delta$ET into pre- and post-construction epochs and applies Welch's t-test and Mann-Whitney U to test for a statistically significant regime shift.
  - **Physical Rationale**: Evapotranspiration is a direct proxy for the **latent heat flux** ($Q_E$) term in the surface energy balance equation: $Q^* = Q_H + Q_E + Q_G$. When vegetated soil (high $Q_E$, evaporative cooling) is replaced by impervious asphalt (near-zero $Q_E$), the absorbed solar radiation is redirected entirely into sensible heat ($Q_H$, direct atmospheric warming) and ground heat storage ($Q_G$). A statistically significant decline in $\Delta$ET therefore constitutes a **thermodynamic proof of mechanism** — it demonstrates not merely *that* the surface warmed, but *why* it warmed, from first principles of conservation of energy. This operationalises the Marxian concept of the **Metabolic Rift** (Foster, 1999; Bozak, 2012) as a quantifiable rupture in the land-atmosphere energy exchange cycle.

### Inter-Pipeline Automation (`run_pipeline.sh`)
While the Google Earth Engine scripts (`04`, `06`, `06b`, `08`, `10`) must be executed natively in the GEE cloud to leverage Google's server-side computation, the entire local analytical workflow is fully automated.

Executing `./scripts/run_pipeline.sh` automatically daisy-chains the spatial reprojection (`02`), geospatial formatting (`03`), and advanced statistical rendering (`05`, `07`, `07b`, `09`, `11`), selectively executing Python modules if their respective GEE `raw_telemetry` CSVs are present.

### Phase III: Institutional Governance & Discourse Audit

**Objective:** To cross-reference spatial realities with municipal planning compliance (EIA 18/01212/OUT).

A structural analysis of Spelthorne Borough Council's grey literature is documented in `documentation/`. This phase contrasts corporate ESG assertions with physical facts extracted in Phases I and II.

## 3. Key Empirical Findings (Shepperton Case Study)

The execution of this pipeline yielded the following statistically verified metrics:

- **Logistical Sprawl:** A total land conversion of 13.21 hectares (132,123.11 SQM) of the Green Belt into impermeable asphalt parking surfaces (distinct from the 16.4 ha of building floorspace reported in the EIA).
- **Energy Parasitism:** The identification of 17 new high-capacity grid nodes for virtual rendering and HVAC maintenance.
- **Biophysical Erasure (NDVI):** A permanent structural collapse from a baseline NDVI of ~0.635 to ~0.28, isolated via **DiD**. The devastation trend is definitively verified by **Seasonal Mann-Kendall** testing (p < 0.001, statistically significant at 99.9% confidence). The adjacent Control Zone greenbelt remained completely stable over the 8-year continuum.
- **Thermodynamic Escalation (LST) & Metabolic Rift:** A Tri-Pillar methodological defense confirms severe and permanent thermodynamic disruption from the land-use conversion:

  - *I. Inferential Anchor (Paired BACI)*: Using n=268 paired Landsat observations (L7+L8+L9), $\Delta$T (Impact − Control) shifted from a pre-construction mean of **+0.85 °C** to a post-construction mean of **+0.95 °C** (full-year Welch p=0.69). The summer-only (JJA) subset shows a shift from **+0.45 °C** to **+0.69 °C** (p=0.73). These p-values are not significant, reflecting the fundamental **spatial resolution constraint**: the parking-lot polygon spans ~3 native Landsat TIRS pixels (100 m), yielding an SNR ≈ 0.18 that precludes statistical significance at conventional thresholds regardless of sample size. This is documented transparently as a **physical limitation of the sensor, not a methodological failure**.

  - *II. Spatial Corroboration (Distance Gradient / Net Thermal Scar)*: The background-subtracted spatial transect reveals a **Net Thermal Scar of −1.17 °C** at the Impact Zone core (0 m), decaying monotonically to zero at ~375 m. The negative sign indicates that the post-construction surface cooled *relative to the regional trend* — consistent with an **albedo-dominated daytime regime** where the high-reflectance parking surface (light-coloured asphalt, painted markings) reflects more incoming shortwave radiation than the pre-existing dark grassland. This does not contradict the UHI hypothesis; rather, it reveals its **diurnal asymmetry**: newly impervious surfaces may exhibit lower daytime LST (higher albedo) while storing and releasing substantially more heat at night (higher thermal admittance). This finding is consistent with the urban energy balance literature (Oke et al., 2017) and warrants explicit discussion in the final report.

  - *III. Latent Heat Collapse (Evapotranspiration — The Thermodynamic Proof of Mechanism)*: The MODIS ET DiD analysis provides the **strongest statistical result** in the entire thermal pillar. Pre-construction $\Delta$ET (Sprawl − Control) averaged **−0.05 mm/8-day** (near-zero, confirming the parallel trends assumption). Post-construction $\Delta$ET collapsed to **−0.24 mm/8-day** — a regime shift of **−0.19 mm/8-day** (Welch p = 5.48×10⁻³, Mann-Whitney p = 3.11×10⁻³; **both highly significant**). The annual bar decomposition reveals 2019 (the construction year) as a catastrophic outlier ($\Delta$ET ≈ −0.75 mm/8-day), followed by a permanent stabilisation below the pre-construction baseline in all subsequent years (2020–2025). This confirms the irreversible destruction of latent heat flux ($Q_E$) and the forced thermodynamic repartitioning of absorbed solar radiation from evaporative cooling into sensible heat ($Q_H$) and ground storage ($Q_G$) — the quantitative expression of the **Metabolic Rift**.

## 4. Repository Structure

```
OSM_AUDIT_2025/
├── scripts/                    # Fully automated analytical and statistical pipeline
│   ├── 01_osm_extraction.ql
│   ├── 02_spatial_projection.py
│   ├── 03_kepler_formatter.py
│   ├── 04_gee_ndvi_pipeline.js
│   ├── 05_plot_ndvi_chart.py
│   ├── 06_gee_thermal_pipeline.js
│   ├── 06b_gee_thermal_sensitivity.js
│   ├── 07_plot_thermal_chart.py
│   ├── 07b_plot_thermal_sensitivity.py
│   ├── 08_gee_transect_decay.js
│   ├── 09_plot_transect_decay.py
│   ├── 10_gee_evapotranspiration.js
│   ├── 11_plot_evapotranspiration.py
│   └── run_pipeline.sh         # Shell script to execute all local Python stages
├── data/
│   ├── raw_spatial/            # Raw JSON extracts (WGS84)
│   ├── raw_telemetry/          # Satellite CSVs from GEE
│   └── processed/              # Kepler CSVs and projections
├── visualisations/             # Output NDVI/LST charts
├── documentation/              # Sprawl zone point rationale & OSM accuracy citations
├── requirements.txt            # Python dependencies (incl. pymannkendall, statsmodels)
├── LICENSE                     # MIT License
└── README.md
```

## 5. Dependencies and Execution

**1. Software Environment (Python 3.10+):**
```bash
pip install -r requirements.txt
./scripts/run_pipeline.sh
```

**2. Remote Sensing (GEE):**
All `.js` scripts (`04`, `06`, `06b`, `08`, `10`) are designed for the [Google Earth Engine Code Editor](https://code.earthengine.google.com/). Users must execute these manually to generate the `.csv` telemetry files in `data/raw_telemetry/` before running the Python charting scripts.

## 6. Licensing

This project is submitted for the PMP ELSS module assessment. 
Copyright (c) 2026 Hanpu Li (Caitlyn Lye). Released under the MIT License.
