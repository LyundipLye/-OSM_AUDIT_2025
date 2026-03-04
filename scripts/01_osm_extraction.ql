[out:json][timeout:30];
/*
  OSM_AUDIT_2025: Infrastructure Extraction Query
  Target Area: Shepperton Studios (51.4065, -0.4640) & Longcross Studios (51.3830, -0.5930)
  Radius: 1200m (Based on EIA primary receptor zones)
*/

(
  // Audit 1: Shepperton Sector
  nwr["building"~"industrial|commercial"](around:1200, 51.4065, -0.4640);
  nwr["power"](around:1200, 51.4065, -0.4640);
  nwr["amenity"="parking"](around:1200, 51.4065, -0.4640);

  // Audit 2: Longcross Sector
  nwr["building"~"industrial|commercial"](around:1200, 51.3830, -0.5930);
  nwr["power"](around:1200, 51.3830, -0.5930);
  nwr["amenity"="parking"](around:1200, 51.3830, -0.5930);
);

// Output geometry for spatial projection
out geom;