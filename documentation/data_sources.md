# Data Sources and Validation

## OpenStreetMap (OSM) Data Quality

The spatial data used in this project is extracted from OpenStreetMap via the Overpass API. OSM is a crowdsourced geographic data platform whose data quality has been validated in multiple peer-reviewed studies:

- **Haklay, M. (2010)** — "How good is volunteered geographical information? A comparative study of OpenStreetMap and Ordnance Survey datasets." _Environment and Planning B_, 37(4), 682-703.
  - Finding: UK urban OSM positional accuracy is within 6m, with ~80% completeness.

- **Barrington-Leigh, C. & Millard-Ball, A. (2017)** — "The world's user-generated road map is more than 80% complete." _PLOS ONE_, 12(8), e0180698.
  - Finding: Global OSM road network completeness exceeds 80%; developed countries exceed 95%.

- **Fan, H., Zipf, A., Fu, Q. & Neis, P. (2014)** — "Quality assessment for building footprints data on OpenStreetMap." _International Journal of Geographical Information Science_, 28(4), 700-719.
  - Finding: OSM building footprints in major European cities overlap >85% with official datasets.

## Sentinel-2 Remote Sensing Data

- **Dataset**: COPERNICUS/S2_SR_HARMONIZED (ESA)
- **Spatial Resolution**: 10m (B4, B8 used for NDVI calculation)
- **Cloud Masking**: QA60 bitmask (cloud and cirrus removal)

## Landsat 7/8/9 Thermal Infrared Data

- **Datasets**: LANDSAT/LE07/C02/T1_L2 (L7), LANDSAT/LC08/C02/T1_L2 (L8), LANDSAT/LC09/C02/T1_L2 (L9)
- **Thermal Resolution**: 60m native (L7) / 100m native (L8/L9), resampled to 30m
- **Temperature Conversion**: ST_B10 × 0.00341802 + 149.0 (DN → Kelvin) − 273.15 (→ Celsius)
- **Cloud Masking**: QA_PIXEL bitwise operations (cloud and cloud shadow removal)
- **Note**: 100m native resolution means ~3-5 independent thermal pixels within the parking lot polygon

## MODIS Evapotranspiration Data

- **Dataset**: MODIS/061/MOD16A2GF (NASA)
- **Spatial Resolution**: 500m
- **Temporal Resolution**: 8-day composite
- **Scale Factor**: ×0.1 (raw DN → mm/8-day)

## Coordinate Reference Systems

- **Input CRS**: EPSG:4326 (WGS84, geographic)
- **Projection CRS**: EPSG:27700 (British National Grid, metric)
- **Projection Accuracy**: <0.1% area error for UK mainland (Ordnance Survey standard)
