OSM_AUDIT_2025: Forensic Spatial Audit of Virtual Production Infrastructure

Project Title: The Political Economy of Greenwashing: Spatialising the Myth of Immateriality in Virtual Production and the Digital Spatial Fix

Author: Hanpu Li

Institution: Queen Mary University of London (QMUL)

Status: Open-Source Methodology / Proof-of-Concept for Doctoral Research Application

1. Project Overview & Academic Contribution

This repository contains the spatial data pipelines, Earth Observation (EO) algorithms, and theoretical frameworks developed for the empirical audit of Virtual Production (VP) infrastructure, specifically examining the Shepperton Studios expansion in the United Kingdom.

While contemporary industry discourse frames virtual production and cloud rendering as a low-carbon, "immaterial" alternative to location shooting, this project proposes a structural counter-narrative. By synthesising Computational Spatial Science (GIS/Remote Sensing) with Eco-Marxist Political Economy, this repository provides a replicable, open-source methodological pipeline to quantify the physical, thermodynamic, and ecological costs of digital media expansion.

Theoretical Framework

The analytical pipeline is grounded in three core political-economic paradigms:

The Digital Spatial Fix (Greene & Joseph, 2015): Conceptualising digital infrastructure not as a dematerialised entity, but as a mechanism through which capital resolves accumulation crises by expanding into new geographic territories.

The Metabolic Rift (Marx, 1867 / Bozak, 2012): Quantifying the physical rupture in ecological systems necessitated by algorithmic and computational metabolism.

Accumulation by Dispossession (Harvey, 2004): Examining the asymmetry between privatised economic gains (Net GVA) and socialised ecological burdens (localised thermodynamic escalation and biomass erasure).

2. Methodological Architecture

The repository is structured around a multi-scalar audit pipeline, transitioning from macro-level infrastructural sprawl to micro-level biophysical changes. The exact logic and function of the core scripts are documented below.

Phase I: Geomatic Extraction & Topological Normalisation

Objective: To empirically quantify logistical sprawl bypassing corporate-curated spatial data.

01_osm_extraction.ql (Overpass QL): Executes a radius-constrained extraction (1200m) around the Shepperton and Longcross coordinates via the Overpass API. The query specifically targets industrial geometries, power infrastructure (high-voltage nodes), and impermeable logistical surfaces (amenity=parking).

02_spatial_projection.py (Python): Ingests raw WGS84 GeoJSON datasets. Utilising geopandas and pyproj, the script re-projects angular global coordinates into the British National Grid (EPSG:27700). This cartographic transformation is critical for calculating exact planar areas (square metres) with an error margin of <0.1%, ensuring the empirical validity of land-conversion metrics.

Phase II: Earth Observation & Metabolic Quantification

Objective: To measure the longitudinal biophysical and thermodynamic alterations in the audited zone.

04_gee_ndvi_pipeline.js (Google Earth Engine API): Interfaces with the ESA Sentinel-2 (S2_SR_HARMONIZED) multispectral satellite constellation. The algorithm applies a QA60 bitwise cloud-masking function to remove atmospheric interference. By calculating the Normalised Difference Vegetation Index (NDVI) over an 8-year temporal axis, it measures the spatiotemporal collapse of local biomass.

05_plot_ndvi_chart.py (Python): Processes the GEE time-series data. It applies a 365-day rolling mean algorithm using pandas to eliminate seasonal meteorological noise, thereby isolating the structural trajectory of ecological degradation.

06_gee_thermal_audit.js (Google Earth Engine API): Utilises the USGS Landsat 8 (TIRS) sensor to conduct a thermodynamic audit. The script tracks Land Surface Temperature (LST) anomalies over a decade. A dropna() filtering mechanism is applied to purge cloud-induced null artefacts, followed by a linear regression model to identify the structural thermal escalation caused by high-density server rendering and asphalt heat retention.

Phase III: Institutional Governance & Discourse Audit

Objective: To cross-reference spatial realities with municipal planning compliance and economic rationalisation.

07_cda_institutional_audit.md (Retrieval-Augmented CDA):
A structural analysis of Spelthorne Borough Council’s grey literature, planning dossiers (e.g., 18/01212/OUT), and Environmental Impact Assessments (EIA). This phase contrasts the discursive euphemisms ("biodiversity improvements") with the physical realities extracted in Phases I and II. Note: This section forms the empirical basis for the accompanying unpublished report on institutional interconnectivity and strategic governance.

3. Key Empirical Findings (Shepperton Case Study)

The execution of this pipeline yielded the following verified metrics:

Logistical Sprawl: A total land conversion of 13.2123 hectares (132,123.11 SQM) of the Metropolitan Green Belt into impermeable infrastructural surfaces.

Energy Parasitism: The identification of 17 new high-capacity (132kV) grid nodes, resulting in a regulated base energy demand of 5.4 GWh/year for virtual engine rendering and infrastructural maintenance.

Biophysical Erasure: A structural NDVI collapse from a baseline of ~0.635 to ~0.28, correlating directly with the arboricultural removal of 79 mature trees.

Thermodynamic Escalation: A net structural increase in Land Surface Temperature (LST) of +5°C within the immediate sprawl zone (2015–2025).

Asymmetric Value Extraction: The spatial audit identified a severe imbalance in institutional governance: a £392,000,000 annual Gross Value Added (GVA) was sanctioned against a minimal Section 106 ecological compensation buyout of £6,150 (a ratio of 0.0015%).

4. Repository Structure

OSM_AUDIT_2025/
├── data_raw/                  # Raw spatial vectors (WGS84 GeoJSON)
├── data_processed/            # Projected vectors (EPSG:27700) & cleaned CSVs
├── scripts_spatial/           # Python processing stack (Projection & Centroid extraction)
├── scripts_remote_sensing/    # GEE JavaScript algorithms (NDVI & LST tracking)
├── visualisations/            # Output regression charts and Kepler.gl configuration files
├── institutional_archives/    # Extracted municipal tables (S106, Arboricultural impacts)
├── LICENSE                    # MIT License
└── README.md                  # Documentation


5. Dependencies and Reproducibility

To ensure rigorous academic reproducibility, the methodology relies exclusively on open-source libraries and publicly accessible telemetry.

Python Stack (3.9+):

pip install pandas numpy matplotlib geopandas shapely pyproj


Remote Sensing Execution:
The .js files located in /scripts_remote_sensing are designed for native execution within the Google Earth Engine (GEE) Code Editor. Users require an authenticated Google Cloud Project (GCP) environment.

6. Citation and Licensing

Researchers and academic institutions are encouraged to clone, audit, and scale this pipeline for longitudinal spatial studies.

Suggested Citation:

Li, H. (2026). OSM_AUDIT_2025: Forensic Spatial Audit of Virtual Production Infrastructure [Source Code and Data Repository]. GitHub.

(For inquiries regarding the extended institutional governance dossier or potential Master's or PhD collaborative frameworks, please refer to the corresponding academic contact channels).
