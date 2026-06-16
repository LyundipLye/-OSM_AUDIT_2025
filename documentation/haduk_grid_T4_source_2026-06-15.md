# HadUK-Grid 1 km source for T4 (verified on CEDA, 2026-06-15)

**Dataset:** HadUK-Grid Gridded Climate Observations on a 1 km grid over the UK,
**v1.3.2.ceda (1836–2025)**. Met Office; Hollis, McCarthy, Kendon, Legg.
Licence: **Open Government Licence — Permitted Use: Any** (CEDA login required; a free
registered account suffices — already obtained). DOI of the dataset series:
10.5285/bbca3267dc7d4219af484976734c9527 (that DOI points to v1.1.0.0; cite the v1.3.2.ceda
record for the data actually used — confirm its own citation string on the catalogue page).
Evidence tier: **official Met Office dataset documentation (peer-reviewed methodology,
Hollis et al. 2019, Int. J. Climatol.)** — NOT a preprint, NOT Wikipedia.

**Variable / resolution / cadence:** `tas` (mean 1.5 m air temperature), **1 km**, **monthly**.

**Archive directory (browsable, logged-in):**
`https://data.ceda.ac.uk/badc/ukmo-hadobs/data/insitu/MOHC/HadOBS/HadUK-Grid/v1.3.2.ceda/1km/tas/mon/v20260512/`

**File naming:** one NetCDF per calendar year, ~39.5 MB each:
`tas_hadukgrid_uk_1km_mon_YYYY01-YYYY12.nc` (national 1 km grid; OSGB / British National Grid,
EPSG:27700; variable `tas`, dims projection_y_coordinate × projection_x_coordinate × time).
Coverage confirmed through **2025** (`...202501-202512.nc` present).

**Files needed for the BACI window (2015–2025) — 11 files, ~435 MB total:**
```
for Y in 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025; do
  tas_hadukgrid_uk_1km_mon_${Y}01-${Y}12.nc
done
```

**Download:** CEDA archive HTTPS requires authentication. Two options (do this in Claude Code /
terminal, NOT by pasting a password into any agent):
- Preferred: create a **CEDA access token** (CEDA account → "My Account" → access token) and
  `wget --header="Authorization: Bearer <TOKEN>" <url>` — or use the `ceda-download` / `pooch`
  helper.
- Or a `~/.netrc` with `machine data.ceda.ac.uk login <user> password <pw>` then
  `wget --auth-no-challenge`. (Set up the credential yourself; the AI must not handle your CEDA
  password in plaintext.)

**Processing (Claude Code, xarray):**
1. Identify Impact (Shepperton sprawl-core centroid) and Control (the BACI control polygon
   centroid) lon/lat from `data/raw_spatial/` (e.g. `export_shepperton.geojson` + the control
   polygon used in the GEE scripts). Reproject those centroids to EPSG:27700.
2. `xr.open_mfdataset(...)`, select the nearest 1 km grid cell to each centroid (`.sel(method="nearest")`).
3. Confirm the Impact and Control centroids fall in **different** 1 km cells (they should — the
   donors sit >2.9 km away; the BACI control is several km from Shepperton). If they share a cell,
   say so honestly — it would mean even 1 km cannot separate them.
4. Build the monthly `tas` series for Impact and Control 2015–2025, compute the air-temperature
   DiD (delta = Impact − Control; Post = time ≥ 2021-06-01; HAC maxlags = ceil(n^(1/3)); MW
   companion) — same conventions as the rest of the repo.
5. Re-state the parking-core excess-warming attribution against this **true same-scale 1 km**
   baseline (replacing the ERA5-Land 9 km baseline, which could not separate Impact/Control).
   Report whether the +0.26 °C parking-core excess survives.

Output: `analysis/HadUK_1km_Counterfactual_TIER2_<date>.{py,md}` + a dated figure. New files only;
do not overwrite. No fabrication — every number from the live xarray computation.
