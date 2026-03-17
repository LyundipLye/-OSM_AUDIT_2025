[out:json][timeout:30][date:"2026-03-03T00:00:00Z"];
/*
  OSM_AUDIT_2025: Infrastructure Extraction Query
  Target Area: Shepperton Studios (51.4065, -0.4640) & Longcross Studios (51.3830, -0.5930)
  Radius: 1200m (Based on EIA primary receptor zones)
  
  Tag coverage expanded to capture all impervious surface categories:
  - Buildings: industrial, commercial
  - Power infrastructure: substations, transformers, lines
  - Parking surfaces: amenity=parking
  - Industrial/commercial landuse polygons
  - Service roads with paved/asphalt surfaces
  - Industrial works and construction areas
*/

(
  // Audit 1: Shepperton Sector
  nwr["building"~"industrial|commercial"](around:1200, 51.4065, -0.4640);
  nwr["power"](around:1200, 51.4065, -0.4640);
  nwr["amenity"="parking"](around:1200, 51.4065, -0.4640);
  nwr["landuse"~"industrial|commercial|construction"](around:1200, 51.4065, -0.4640);
  way["highway"="service"]["surface"~"asphalt|paved|concrete"](around:1200, 51.4065, -0.4640);
  nwr["man_made"="works"](around:1200, 51.4065, -0.4640);

  // Audit 2: Longcross Sector
  nwr["building"~"industrial|commercial"](around:1200, 51.3830, -0.5930);
  nwr["power"](around:1200, 51.3830, -0.5930);
  nwr["amenity"="parking"](around:1200, 51.3830, -0.5930);
  nwr["landuse"~"industrial|commercial|construction"](around:1200, 51.3830, -0.5930);
  way["highway"="service"]["surface"~"asphalt|paved|concrete"](around:1200, 51.3830, -0.5930);
  nwr["man_made"="works"](around:1200, 51.3830, -0.5930);
);

// Output geometry for spatial projection
out geom;