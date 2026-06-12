# Impact Zone and Control Zone Selection

## Impact Zone Coordinates

**Coordinates**: `[-0.469366, 51.410315]`

This coordinate corresponds to the newly-constructed parking lot complex south of the Shepperton Studios expansion area (Zone C in the EIA planning documents), located south of Studios Road and southwest of the main studio complex.

Selection rationale:
1. This area was greenfield/agricultural land before 2018, converted to impervious asphalt surface during 2020–2023
2. Directly corresponds to the new parking capacity (2,595 spaces) documented in the EIA (18/01212/OUT)
3. Sentinel-2 and Landsat imagery visually confirms this area experienced the most significant land-cover change

## Sensitivity Check

Audit results are not dependent on the selection of a single coordinate. Four offset sampling points (~100–200m in each cardinal direction) are used:

| Point | Coordinates | Purpose |
|-------|-------------|---------|
| Impact_Core | [-0.469366, 51.410315] | Primary audit point |
| Impact_North | [-0.469366, 51.411500] | ~130m north offset |
| Impact_South | [-0.469366, 51.409100] | ~130m south offset |
| Impact_East | [-0.467000, 51.410315] | ~160m east offset |
| Control | [-0.4105, 51.4074] | Control zone (stable greenbelt) |

## Control Zone Selection

**Coordinates**: `[-0.4105, 51.4074]`

- Located ~3km northeast of Shepperton, north bank of the Thames, on stable greenbelt
- No major development projects recorded in the observation period
- Similar latitude/elevation to the Impact Zone, reducing topographic confounders
- Within the same Sentinel-2 / Landsat swath path, ensuring consistent sensor conditions

## Area Metric Clarification

| Metric | Value | Source |
|--------|-------|--------|
| Parking polygon area | 13.2 ha | OSM spatial audit (`02_spatial_projection.py`) |
| New building floorspace | 16.4 ha (164,000 sqm) | EIA 18/01212/OUT |
| Total greenbelt loss | 39 ha | Spelthorne Borough Council |
| Deduplicated impervious surface (all categories) | 16.91 ha | OSM spatial audit (Shepperton + Longcross combined) |

The parking polygon area is a measure of logistical impervious surface coverage and should not be conflated with total development floorspace or total greenbelt loss.
