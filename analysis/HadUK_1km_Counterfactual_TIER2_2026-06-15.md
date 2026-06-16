# T4 HadUK-Grid 1 km Co-located Air-Temperature Counterfactual — RESULT

**Date**: 2026-06-15
**Author**: Hanpu Li (Cait), 李含普
**Script**: `analysis/HadUK_1km_Counterfactual_TIER2_2026-06-15.py`
**Figure**: `visualisations/HadUK_1km_Counterfactual_TIER2_2026-06-15.png`
**Data**: HadUK-Grid v1.3.2.ceda, `tas` (1.5 m mean air temperature, degC), 1 km monthly,
2015-2025, 11 NetCDF files downloaded from the CEDA Archive on 2026-06-15 with a CEDA access
token. Grid CRS OSGB / EPSG:27700, 1000 m spacing.
**Evidence tier**: peer-reviewed dataset documentation (Hollis et al. 2019, *Geoscience Data
Journal* 6(2):151-159, DOI 10.1002/gdj3.78).
**No fabrication**: every number below is from the live run this session.

---

## Headline

**The parking-core excess warming survives a true same-scale 1 km baseline, and is in fact
larger than the ERA5 9 km estimate.** At 1 km the Impact and Control points fall in different
cells, and the co-located air-temperature DiD between them is essentially zero (+0.005 degC,
HAC p = 0.62, n.s.). Because there is no differential background air-temperature trend between
the two sites, the satellite surface-temperature DiD is not an artefact of regional climate
drift; it is attributable to the surface change.

## Why this is the test ERA5 could not do

The Impact (parking core) and Control (greenbelt) points are 4,111 m apart. ERA5-Land is ~9 km,
so both fell in the **same** cell and its air-temperature DiD was mechanically 0. HadUK-Grid is
1 km and the two points fall in **different** cells (verified live):

| Site | BNG E, N | HadUK 1 km cell centre |
|:--|:--|:--|
| Impact (parking core) | 506551, 169033 | E 506500, N 169500 |
| Control (greenbelt) | 510655, 168795 | E 510500, N 168500 |

Same cell? **No.** So 1 km can separate them and a genuine same-scale air-temperature DiD is
identifiable.

## Live results (split 2021-06-01, HAC maxlags = ceil(n^(1/3)), MW companion)

Co-located air-temperature DiD (delta = Impact tas − Control tas):

| Window | air-temp DiD (degC) | HAC p | 95% CI | MW p | n (pre/post) |
|:--|:--|:--|:--|:--|:--|
| Full year | **+0.0047** | 0.62 (n.s.) | [−0.014, +0.024] | 0.47 (n.s.) | 132 (77/55) |
| Summer JJA | +0.0146 | 1e-5 (\*\*\*) | [+0.008, +0.021] | 0.058 (n.s.) | 33 (18/15) |
| Warm Apr-Sep | +0.0073 | 0.059 (n.s.) | [−0.000, +0.015] | 0.38 (n.s.) | 66 (38/28) |

The JJA HAC p is tiny only because the air-temperature delta between two nearby cells is
extremely stable (CI half-width ~0.007 degC); the **magnitude (~0.015 degC) is physically
negligible** and MW is n.s. The full-year DiD (+0.005 degC, n.s.) is the headline: there is no
meaningful differential air-temperature trend between Impact and Control.

Absolute JJA warming (pre to post): Impact cell +0.256 degC, Control cell +0.242 degC (HadUK
1 km gives a more modest local warming than ERA5-Land's +0.82 degC for the coarser shared cell;
the two products and footprints differ, but the **differential** is what matters here and it is
about +0.01 degC).

## Same-scale excess-warming attribution (satellite LST DiD minus 1 km air-temp DiD)

| Footprint | satellite LST DiD | 1 km air-temp DiD | **excess** | ERA5 9 km estimate |
|:--|:--|:--|:--|:--|
| Parking core | +1.079 | +0.005 | **+1.074 degC** | +0.26 |
| Full polygon | +0.560 | +0.005 | +0.555 degC | −0.26 |

## Interpretation (honest)

1. **This refines, and is methodologically cleaner than, the ERA5 attribution.** The ERA5 step
   subtracted an *absolute* regional warming (+0.82 degC) from a *difference-in-differences*
   (Impact − Control, pre − post). That mixes a level change with a differenced quantity. The
   correct same-scale counterfactual for a surface-temperature DiD is an air-temperature DiD on
   the same Impact/Control pair, which is what HadUK 1 km now provides. That DiD is ~0, so the
   surface-temperature DiD stands almost entirely as excess.
2. **What HadUK 1 km does and does not measure.** HadUK-Grid is interpolated from a sparse station
   network, so a 1 km cell's `tas` is a smoothed regional field that cannot itself sense a 13 ha
   parking lot. The near-zero air-temperature DiD therefore means there is **no differential
   mesoscale or topographic air-temperature trend** between the Impact and Control locations; it
   is not an independent thermometer over the asphalt. The legitimate claim is that the satellite
   surface-warming gap is not an artefact of differential background climate, not that air
   temperature over the lot rose by +1.07 degC.
3. **Caveats that still travel.** The parking-core LST DiD remains carried in part by Landsat 7
   and 9 (Landsat-8-only +0.68 degC, n.s., n = 119), and the full-polygon LST is only marginal
   (HAC p = 0.06), so the full-polygon excess of +0.56 should not be promoted to a significant
   localised signal on its own. NDVI remains the load-bearing pillar.

**Bottom line:** the parking-core excess warming survives, and strengthens, under a true 1 km
same-scale air-temperature baseline, subject to the standing sensor-power caveat.
