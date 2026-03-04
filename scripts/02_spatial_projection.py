# -*- coding: utf-8 -*-
"""
OSM_AUDIT_2025: Spatial Projection and Quantification Utility
Converts raw WGS84 GeoJSON data into physical metrics using the British National Grid.
"""

import json
import os
from shapely.geometry import shape
import pyproj
from shapely.ops import transform

# Define Coordinate Reference Systems
# WGS84 (Global Degrees) -> EPSG:27700 (British National Grid in Metres)
WGS84 = "epsg:4326"
BNG = "epsg:27700"
projector = pyproj.Transformer.from_crs(WGS84, BNG, always_xy=True).transform

def run_spatial_audit(file_path):
    """
    Executes a quantitative audit of spatial data.
    Returns: (total_parking_area, power_node_count)
    """
    if not os.path.exists(file_path):
        print(f"[ERROR] Source file missing: {file_path}")
        return 0.0, 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid JSON format in {file_path}")
            return 0.0, 0
            
    parking_area = 0.0
    power_nodes = 0
    
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        geom = feature.get('geometry', {})
        
        if not geom:
            continue
            
        # 1. Audit Power Infrastructure Nodes
        if 'power' in props and props['power'] is not None:
            power_nodes += 1
            
        # 2. Quantify Logistical Sprawl (Parking Polygons)
        if props.get('amenity') == 'parking' and geom.get('type') in ['Polygon', 'MultiPolygon']:
            # Project geometry to BNG for accurate area calculation
            s = shape(geom)
            s_projected = transform(projector, s)
            parking_area += s_projected.area
            
    return parking_area, power_nodes

if __name__ == "__main__":
    print("--- INITIATING EMPIRICAL SPATIAL AUDIT (OSM_AUDIT_2025) ---")
    
    # Audit Paths (Align with Repository Architecture)
    shep_path = 'geographic/raw/export_shepperton.geojson'
    long_path = 'geographic/raw/export_longcross.geojson'
    
    # Execute calculations
    shep_area, shep_pwr = run_spatial_audit(shep_path)
    long_area, long_pwr = run_spatial_audit(long_path)
    
    total_area = shep_area + long_area
    total_hectares = total_area / 10000
    
    # Detailed Console Output
    print(f"SHEPPERTON_SECTOR: {shep_area:,.2f} SQM | Nodes: {shep_pwr}")
    print(f"LONGCROSS_SECTOR:  {long_area:,.2f} SQM | Nodes: {long_pwr}")
    print("-" * 50)
    print(f"AGGREGATE LOGISTICAL SPRAWL: {total_area:,.2f} SQM")
    print(f"TOTAL LAND CONVERSION:      {total_hectares:,.4f} Hectares")
    print(f"TOTAL POWER ANCHORS:        {shep_pwr + long_pwr}")
    print("--- AUDIT COMPLETE: DATA READY FOR VISUALISATION ---")