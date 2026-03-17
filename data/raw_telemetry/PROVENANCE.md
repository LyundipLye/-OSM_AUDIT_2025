# Data Provenance: `raw_telemetry/`

All CSV files in this directory were exported from Google Earth Engine (GEE) via the Code Editor's chart-download functionality. They represent the raw satellite-derived time series used by the Python plotting and statistical scripts.

## CSV Manifest

| Filename | GEE Script | Satellite Source | Export Date | Temporal Range |
|:---------|:-----------|:-----------------|:------------|:---------------|
| `ee-chart_ndvi.csv` | `04_gee_ndvi_pipeline.js` | ESA Sentinel-2 (S2_SR_HARMONIZED) | 2026-03-03 | 2018-01 to 2026-03 |
| `ee-chart_lst.csv` | `06_gee_thermal_pipeline.js` | USGS Landsat 7+8+9 (C2 T1 L2) | 2026-03-03 | 2015-01 to 2026-03 |
| `ee-chart_decay.csv` | `08_gee_transect_decay.js` | USGS Landsat 7+8+9 (C2 T1 L2) | 2026-03-03 | Summer composites: 2016–2018 vs 2023–2025 |
| `ee-chart_et.csv` | `10_gee_evapotranspiration.js` | NASA MODIS MOD16A2GF | 2026-03-03 | 2015-01 to 2026-03 |

## Reproducibility Notes

- **GEE scripts must be executed manually** in the [GEE Code Editor](https://code.earthengine.google.com/). CSVs are downloaded via the chart pop-out menu.
- GEE script public links are provided in the README for independent verification.
- The CSVs archived here represent the data snapshot used for all results reported in the README and presentation materials.
- Re-running GEE scripts on a later date may produce slightly different results due to updated satellite collections or reprocessed imagery.
