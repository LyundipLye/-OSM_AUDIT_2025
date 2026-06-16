# T7 Non-VP Comparator Case — Candidate Selection Memo

**Date**: 2026-06-15  
**Author**: Hanpu Li (Cait), 李含普  
**Purpose**: Identify 2–3 non-studio green-belt release sites of comparable footprint (~30–50 ha) in the Surrey/Spelthorne/Runnymede area, permitted ~2018–2024, for biophysical comparison with Shepperton VP.

---

## Selection Criteria

1. **Green-belt release**: site must have been on designated Metropolitan Green Belt land
2. **Similar footprint**: ~20–50 ha total development area
3. **Similar era**: outline permission or construction 2017–2024
4. **Non-studio**: logistics (B8), data centre, housing, or mixed-use — NOT film/TV
5. **Same region**: Surrey / Spelthorne / Runnymede / Elmbridge (shared climate, soils, geology)
6. **Verifiable**: planning application reference must be obtainable from public records

---

## Candidate 1: Longcross Garden Village (LEAD CANDIDATE)

| Field | Detail |
|:--|:--|
| **Location** | Longcross, Chertsey, Surrey KT16 |
| **Borough** | Runnymede |
| **Coordinates** | approx. −0.565, 51.384 |
| **Size** | ~79 ha total site; ~47 ha for residential/mixed-use phases |
| **Land use** | Former DERA/QinetiQ defence site; green belt |
| **Permission** | Runnymede BC ref. RU.17/1749 (outline), approved 2019 |
| **Construction** | Phased from 2020; first homes occupied 2022 |
| **End use** | ~1,700 residential dwellings + local centre + school |
| **Evidence tier** | Planning ref = official public record (Runnymede planning portal) |
| **Fit** | ✅ Excellent: similar era, same region (~8 km from Shepperton), green-belt release, non-studio, housing not VP |
| **Distance from Shepperton** | ~8 km SW |

**Source**: Runnymede Borough Council planning register, application RU.17/1749.  
**Evidence tier**: Official local authority record (Tier 2: official dataset documentation).

> [!IMPORTANT]  
> Longcross is the strongest candidate: large-scale green-belt release in the same borough cluster, permitted and built in the same window, entirely housing — tests whether the biophysical signature is generic to any green-belt hardening vs specific to VP.

---

## Candidate 2: Brooklands Business Park / Mercedes-Benz World expansion

| Field | Detail |
|:--|:--|
| **Location** | Brooklands, Weybridge, Surrey KT13 |
| **Borough** | Elmbridge |
| **Coordinates** | approx. −0.465, 51.350 |
| **Size** | ~30 ha (Brooklands Business Park area) |
| **Land use** | Mixed brownfield/greenfield; heritage motor circuit |
| **Permission** | Multiple phased consents; Elmbridge BC refs various |
| **End use** | Commercial/office park, retail, automotive heritage |
| **Fit** | ⚠️ Moderate: partly brownfield (pre-existing hardstanding), mixed-use, less clean greenfield→impervious conversion |
| **Distance from Shepperton** | ~7 km SE |

**Source**: Elmbridge Borough Council planning register.  
**Evidence tier**: Official local authority record.

**Weakness**: Brooklands is partly brownfield (former airfield/racecourse), so the greenfield-to-impervious conversion signal would be diluted. Less clean comparison than Longcross.

---

## Candidate 3: Heathrow Western Logistics Hub area

| Field | Detail |
|:--|:--|
| **Location** | Stanwell / Bedfont, near Heathrow |
| **Borough** | Spelthorne / Hounslow border |
| **Coordinates** | approx. −0.475, 51.455 |
| **Size** | ~20–35 ha (various logistics/warehouse schemes) |
| **Land use** | Green-belt fringe near Heathrow |
| **Permission** | Various B8 logistics consents 2018–2023 |
| **End use** | Warehousing / distribution centres |
| **Fit** | ⚠️ Moderate: fragmented (multiple smaller schemes, not one large consent); green-belt status varies parcel-by-parcel |
| **Distance from Shepperton** | ~5 km N |

**Source**: Spelthorne / Hounslow planning portals.  
**Evidence tier**: Official local authority records.

**Weakness**: Fragmented — no single ≥30 ha consent. Would need to aggregate multiple schemes, weakening the comparison.

---

## Recommendation

**Longcross Garden Village (RU.17/1749)** is the clear first choice:
- Clean greenfield→impervious conversion (~47 ha active development)
- Same region and era (permitted 2019, built 2020–2023)
- Single large consent (not fragmented)
- Housing, not studio — directly tests Limitation 6
- Green-belt designated land
- ~8 km from Shepperton (close enough for same climate, far enough for independence)

### Logic of the comparison

If Longcross shows the **same** NDVI/LST/impervious signature as Shepperton → confirms the biophysical layer is **generic to any green-belt hardening**, and the VP-specific critique must rest entirely on **discourse and institutional evidence** (the decarbonisation narrative + S106/governance structure). This **strengthens** the two-layer argument by making it precise.

If Longcross shows a **different** signature → the VP development has physically distinct characteristics worth investigating (e.g., different impervious fraction, different thermal mass).

---

## GEE Extraction Polygon (for sign-off)

Approximate Longcross development footprint (to be refined):
```
[-0.5710, 51.3800], [-0.5710, 51.3880],
[-0.5580, 51.3880], [-0.5580, 51.3800]
```
(~1.2 km × 0.9 km rectangle enclosing the main residential development area)

Control zone for Longcross: stable green belt ~2 km away  
Proposed: [-0.545, 51.370], buffer 200m

---

## ⏸️ PAUSING FOR SIGN-OFF

Please confirm:
1. Longcross Garden Village as the primary comparator?
2. Polygon coordinates acceptable, or refine?
3. Proceed with GEE extraction (same NDVI/LST pipeline as Shepperton)?
