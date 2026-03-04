OSM_AUDIT_2025: Spatial Audit of Virtual Production Infrastructure

Project Context

This repository contains the spatial audit project developed by Hanpu Li for the English Language and Study Skills Presentation module, completed as part of the Pre-Masters programme at Queen Mary University of London in March 2026.

Overview

The project examines the physical infrastructure required to support virtual production in the United Kingdom screen industries, focusing on the expansion of Shepperton Studios. While virtual production is often described in industry literature as a low-carbon alternative to traditional filming, this research quantifies the associated land conversion and energy demand. The methodology integrates OpenStreetMap spatial projection, Critical Discourse Analysis of municipal planning dossiers, and Time-Series Remote Sensing via Google Earth Engine to assess spatial reorganisation at the metropolitan periphery.

Repository Structure

The repository is organised into four primary directories. The scripts directory contains the analytical codebase, including the Overpass query language script for raw OpenStreetMap data extraction, Python scripts for WGS84 to EPSG:27700 spatial projection and data standardisation, a Google Earth Engine script for longitudinal Normalised Difference Vegetation Index analysis, and a Python script for structural trend visualisation.

The data directory stores the raw spatial extracts, Copernicus Sentinel-2 satellite telemetry, and processed datasets. The visualisations directory holds the output maps and charts concerning logistical area expansion and energy infrastructure. The documentation directory contains the quantitative data extraction logs from municipal planning records and the presentation transcript.

Methodological Transparency and Reproducibility

To ensure methodological transparency and reproducibility, the entire analytical workflow is open source. Spatial area metrics are calculated using the British National Grid projection to maintain high spatial accuracy. The remote sensing analysis applies a rolling annual mean to Copernicus Sentinel-2 surface reflectance data, filtering seasonal variation to measure sustained changes in biomass. Researchers may replicate the findings by executing the provided scripts in their numbered sequence within the analytical pipeline.

License

This project is released under the MIT License for academic research purposes.
