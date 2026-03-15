# OSM_AUDIT_2025: Forensic Spatial Audit of Virtual Production Infrastructure

**Project Title:** The Political Economy of Greenwashing: Spatialising the Myth of Immateriality in Virtual Production and the Digital Spatial Fix

**Author:** Hanpu Li

**Institution:** Queen Mary University of London (QMUL)

**Status:** Open-Source Methodology / Proof-of-Concept for Doctoral Research Application

## 1. Project Overview & Academic Contribution

This repository contains the spatial data pipelines, Earth Observation (EO) algorithms, and theoretical frameworks developed for the empirical audit of Virtual Production (VP) infrastructure, specifically examining the Shepperton Studios expansion in the United Kingdom.

While contemporary industry discourse frames virtual production and cloud rendering as a low-carbon, "immaterial" alternative to location shooting, this project proposes a structural counter-narrative. By synthesising Computational Spatial Science (GIS/Remote Sensing) with Eco-Marxist Political Economy, this repository provides a replicable, open-source methodological pipeline to quantify the physical, thermodynamic, and ecological costs of digital media expansion.

### Theoretical Framework

The analytical pipeline is grounded in three core political-economic paradigms:

- **The Digital Spatial Fix** (Greene & Joseph, 2015): Conceptualising digital infrastructure not as a dematerialised entity, but as a mechanism through which capital resolves accumulation crises by expanding into new geographic territories.
- **The Metabolic Rift** (Marx, 1867 / Bozak, 2012): Quantifying the physical rupture in ecological systems necessitated by algorithmic and computational metabolism.
- **Accumulation by Dispossession** (Harvey, 2004): Examining the asymmetry between privatised economic gains (Net GVA) and socialised ecological burdens (localised thermodynamic escalation and biomass erasure).

## 2. Methodological Architecture

The repository is structured around a multi-scalar audit pipeline, transitioning from macro-level infrastructural sprawl to micro-level biophysical changes. The exact logic and function of the core scripts are documented below.

### Phase I: Geomatic Extraction & Topological Normalisation

**Objective:** To empirically quantify logistical sprawl by bypassing corporate-curated spatial data.

- **`01_osm_extraction.ql`** (Overpass QL): Executes a radius-constrained extraction (1200m) around the Shepperton and Longcross coordinates via the Overpass API. The query specifically targets industrial geometries, power infrastructure (high-voltage nodes), and impermeable logistical surfaces (`amenity=parking`).

- **`02_spatial_projection.py`** (Python): Ingests raw WGS84 GeoJSON datasets. Utilising `shapely` and `pyproj`, the script re-projects angular global coordinates into the British National Grid (EPSG:27700). This cartographic transformation is critical for calculating exact planar areas (square metres) with an error margin of <0.1%, ensuring the empirical validity of land-conversion metrics.

- **`03_kepler_formatter.py`** (Python): Extracts geographical features from GeoJSON and formats them for Kepler.gl visualisation. Parking polygon areas are projected to EPSG:27700 before calculation to produce accurate square-metre intensity values for heatmap weighting.

### Phase II: Earth Observation & Metabolic Quantification

**Objective:** To measure the longitudinal biophysical and thermodynamic alterations in the audited zone.

- **`04_gee_ndvi_pipeline.js`** (Google Earth Engine API): Interfaces with the ESA Sentinel-2 (S2_SR_HARMONIZED) multispectral satellite constellation. The algorithm applies a QA60 bitwise cloud-masking function to remove atmospheric interference. By calculating the Normalised Difference Vegetation Index (NDVI) over an 8-year temporal axis, it measures the spatiotemporal collapse of local biomass.

- **`05_plot_ndvi_chart.py`** (Python): Processes the GEE time-series CSV data. It applies a 365-day rolling mean algorithm using `pandas` to eliminate seasonal meteorological noise, thereby isolating the structural trajectory of ecological degradation.

- **`06_gee_thermal_pipeline.js`** (Google Earth Engine API): Interfaces with the USGS Landsat 8 Collection 2 (TIRS) thermal infrared sensor. The algorithm applies QA_PIXEL bitwise cloud-masking, converts raw thermal DN to Land Surface Temperature (LST) in Celsius, and constructs a relative Urban Heat Island (UHI) anomaly map comparing pre-construction (2017) and post-construction (2024) summer composites to isolate the net thermodynamic scar.

- **`07_plot_thermal_chart.py`** (Python): Processes the LST CSV data exported from the GEE thermal audit. Applies a 365-day rolling mean and linear regression model to visualise the structural thermal escalation trend.

### Phase III: Institutional Governance & Discourse Audit

**Objective:** To cross-reference spatial realities with municipal planning compliance and economic rationalisation.

A structural analysis of Spelthorne Borough Council's grey literature, planning dossiers (e.g., 18/01212/OUT), and Environmental Impact Assessments (EIA) is documented in the `documentation/` directory. This phase contrasts the discursive euphemisms ("biodiversity improvements") with the physical realities extracted in Phases I and II.

## 3. Key Empirical Findings (Shepperton Case Study)

The execution of this pipeline yielded the following verified metrics:

- **Logistical Sprawl:** A total land conversion of 13.2123 hectares (132,123.11 SQM) of the Metropolitan Green Belt into impermeable infrastructural surfaces.
- **Energy Parasitism:** The identification of 17 new high-capacity (132kV) grid nodes, resulting in a regulated base energy demand of 5.4 GWh/year for virtual engine rendering and infrastructural maintenance.
- **Biophysical Erasure:** A structural NDVI collapse from a baseline of ~0.635 to ~0.28, correlating directly with the arboricultural removal of 79 mature trees.
- **Thermodynamic Escalation:** A net structural increase in Land Surface Temperature (LST) of +5°C within the immediate sprawl zone (2015–2025).
- **Asymmetric Value Extraction:** The spatial audit identified a severe imbalance in institutional governance: a £392,000,000 annual Gross Value Added (GVA) was sanctioned against a minimal Section 106 ecological compensation buyout of £6,150 (a ratio of 0.0015%).

## 4. Repository Structure

```
OSM_AUDIT_2025/
├── scripts/                    # Analytical pipeline (numbered sequentially)
│   ├── 01_osm_extraction.ql    #   Overpass QL data extraction query
│   ├── 02_spatial_projection.py#   WGS84 → EPSG:27700 projection & area calculation
│   ├── 03_kepler_formatter.py  #   Kepler.gl CSV generation with projected areas
│   ├── 04_gee_ndvi_pipeline.js #   GEE Sentinel-2 NDVI time-series (run in GEE Code Editor)
│   ├── 05_plot_ndvi_chart.py   #   NDVI structural trend visualisation
│   ├── 06_gee_thermal_pipeline.js# GEE Landsat 8 LST audit (run in GEE Code Editor)
│   └── 07_plot_thermal_chart.py#   LST trend visualisation (local Python)
├── data/
│   ├── raw_spatial/            #   Raw GeoJSON vectors (WGS84)
│   ├── raw_telemetry/          #   Satellite telemetry CSVs from GEE
│   └── processed/              #   Projected & cleaned output files
├── visualisations/             # Output charts and Kepler.gl map exports
├── documentation/              # EIA data extraction logs
├── Forensic_Audit_Shepperton/  # Forensic audit report (PDF)
├── requirements.txt            # Python dependencies
├── LICENSE                     # MIT License
└── README.md
```

## 5. Dependencies and Reproducibility

To ensure rigorous academic reproducibility, the methodology relies exclusively on open-source libraries and publicly accessible telemetry.

**Python (3.10+):**

```bash
pip install -r requirements.txt
```

**Remote Sensing Execution:**

The GEE scripts (`scripts/04_gee_ndvi_pipeline.js` and `scripts/06_gee_thermal_pipeline.js`) are designed for native execution within the [Google Earth Engine Code Editor](https://code.earthengine.google.com/). Users require an authenticated Google Cloud Project (GCP) environment.

## 6. Citation and Licensing

Researchers and academic institutions are encouraged to clone, audit, and scale this pipeline for longitudinal spatial studies.

**Suggested Citation:**

> Li, H. (2026). *OSM_AUDIT_2025: Forensic Spatial Audit of Virtual Production Infrastructure* [Source Code and Data Repository]. GitHub.

For inquiries regarding the extended institutional governance dossier or potential Master's or PhD collaborative frameworks, please refer to the corresponding academic contact channels.
