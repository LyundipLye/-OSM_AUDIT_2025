# T4 HadUK-Grid 1 km Air-Temperature DiD — execution note (complements `haduk_grid_T4_source_2026-06-15.md`)

**Date**: 2026-06-15
**Author**: Hanpu Li (Cait), 李含普
**Status**: DONE 2026-06-15. Cait supplied a CEDA access token; the 11 `tas` files were
downloaded and the analysis was run live. Result: co-located air-temperature DiD = +0.005 °C
(HAC p=0.62, n.s.); parking-core excess survives at +1.07 °C. Full write-up in
`analysis/HadUK_1km_Counterfactual_TIER2_2026-06-15.md`. The original request notes are retained
below for provenance. (Revoke the CEDA token; it entered the chat transcript.)

**Original status (now resolved)**: was BLOCKED in this environment on a configured CEDA credential, NOT on signup. The
authoritative dataset record, archive URL, file list and download protocol are already in
`documentation/haduk_grid_T4_source_2026-06-15.md` (HadUK-Grid v1.3.2.ceda, variable `tas`,
1 km, monthly). Per that doc's own security instruction, the AI must not handle the CEDA
password in plaintext, so Cait sets up the token or `~/.netrc` and runs the download; the
analysis below is then ready to run. This note adds the one thing that doc left open: the
live-computed 1 km grid cells.

## Why this upgrade matters (the ERA5 limitation it fixes)

The Tier-2 counterfactual used ERA5-Land at ~9 km. The Impact (parking core) and Control
(greenbelt) points are only **4,111 m apart** (computed this session), smaller than one
ERA5-Land cell, so both fall in the **same 9 km cell** and the air-temperature DiD is
mechanically **0.00°C**. HadUK-Grid is 1 km, and the two points fall in **different** 1 km
cells, so a same-scale air-temperature DiD is identifiable.

## Computed 1 km cells (this session, EPSG:27700) — resolves step 3 of the source doc

| Site | Lon, Lat | BNG E, N | HadUK 1 km cell (SW corner) |
|:--|:--|:--|:--|
| Impact (parking core) | -0.46937, 51.41031 | 506551, 169033 | E 506000, N 169000 |
| Control (greenbelt) | -0.41046, 51.40739 | 510654, 168795 | E 510000, N 168000 |

The cells differ (Impact E506/N169, Control E510/N168), so 1 km **can** separate Impact and
Control. Select with `.sel(projection_x_coordinate=..., projection_y_coordinate=..., method="nearest")`
near the cell centres (E 506500/N 169500 and E 510500/N 168500).

## Analysis ready to run once the NetCDF files are local

- delta = impact_tas − control_tas; split at 2021-06-01.
- HAC OLS DiD, maxlags = ceil(n^(1/3)); Mann-Whitney U companion; JJA and warm Apr-Sep windows.
- Re-derive excess warming: parking-core LST DiD (+1.08°C, with the L8-only +0.68°C n.s. caveat)
  minus the **1 km** air-temperature DiD, replacing the 9 km ERA5 baseline. Report whether the
  +0.26°C parking-core excess survives a same-scale 1 km baseline.
- Save outputs as `analysis/HadUK_1km_Counterfactual_TIER2_<date>.{py,md}` plus a dated figure.
  New files only. Every number from the live xarray computation, no fabrication.

## Citation note (flag for Cait)

The HadUK-Grid methodology paper is Hollis, D. et al. (2019), "HadUK-Grid: a new UK dataset of
gridded climate observations", *Geoscience Data Journal*, 6(2), 151-159, DOI 10.1002/gdj3.78
(peer-reviewed). `haduk_grid_T4_source_2026-06-15.md` cites this as "Int. J. Climatol.", which
appears to be the wrong journal; the README bibliography uses the Geoscience Data Journal record.
Confirm the exact citation string on the v1.3.2.ceda catalogue page before submission.
