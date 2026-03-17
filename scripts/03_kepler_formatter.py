"""
03_kepler_formatter.py
从 GeoJSON 提取 Power Nodes + 全部不透水面要素，输出 Kepler.gl CSV
Expanded: Extracts parking, industrial landuse, paved service roads,
buildings, and power infrastructure — matching the expanded OSM query.
"""

import json
import csv
import os
from shapely.geometry import shape
from shapely.ops import transform
import pyproj

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WGS84 = "epsg:4326"
BNG = "epsg:27700"
projector = pyproj.Transformer.from_crs(WGS84, BNG, always_xy=True).transform


def _classify_for_kepler(props):
    """Return (audit_type, category) for Kepler.gl CSV, or None if not relevant."""
    if 'power' in props and props['power'] is not None:
        return 'Energy_Infrastructure', props.get('power', 'infrastructure')
    if props.get('amenity') == 'parking':
        return 'Logistical_Sprawl', 'parking'
    if props.get('landuse') in ('industrial', 'commercial', 'construction'):
        return 'Logistical_Sprawl', f"landuse_{props['landuse']}"
    if props.get('highway') == 'service' and props.get('surface') in ('asphalt', 'paved', 'concrete'):
        return 'Logistical_Sprawl', 'service_road_paved'
    if props.get('man_made') == 'works':
        return 'Logistical_Sprawl', 'industrial_works'
    if props.get('building') in ('industrial', 'commercial'):
        return 'Logistical_Sprawl', f"building_{props['building']}"
    return None, None


def extract_features_for_kepler(file_path, sector_name):
    """提取电力节点 (Point) 和不透水面质心 (Polygon centroid)，返回 dict 列表"""
    features_list = []
    
    if not os.path.exists(file_path):
        print(f"[WARNING] File not found: {file_path}")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid JSON: {file_path}")
            return []
        
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        geom = feature.get('geometry', {})
        
        if not geom:
            continue

        audit_type, category = _classify_for_kepler(props)
        if audit_type is None:
            continue

        lon, lat = None, None
        intensity = 50.0  # default for point features
        
        if geom['type'] == 'Point':
            lon, lat = geom['coordinates']
        elif geom['type'] in ['Polygon', 'MultiPolygon']:
            try:
                s = shape(geom)
                centroid = s.centroid
                lon, lat = centroid.x, centroid.y
                # For area features, use projected area as intensity
                s_projected = transform(projector, s)
                intensity = s_projected.area  # sqm
            except Exception:
                continue
        elif geom['type'] in ['LineString', 'MultiLineString']:
            # For service roads (lines), use midpoint
            coords = geom.get('coordinates', [])
            if coords:
                if geom['type'] == 'MultiLineString':
                    coords = coords[0]
                mid = len(coords) // 2
                lon, lat = coords[mid]
                
        if lon is not None and lat is not None:
            features_list.append({
                'sector': sector_name,
                'audit_type': audit_type,
                'category': category,
                'latitude': lat,
                'longitude': lon,
                'intensity': intensity
            })
            
    return features_list

if __name__ == "__main__":
    output_dir = os.path.join(PROJECT_ROOT, 'data', 'processed')
    os.makedirs(output_dir, exist_ok=True)

    shepperton_data = extract_features_for_kepler(
        os.path.join(PROJECT_ROOT, 'data', 'raw_spatial', 'export_shepperton.geojson'), 'Shepperton')
    longcross_data = extract_features_for_kepler(
        os.path.join(PROJECT_ROOT, 'data', 'raw_spatial', 'export_longcross.geojson'), 'Longcross')

    all_data = shepperton_data + longcross_data
    output_file = os.path.join(output_dir, 'kepler_gl_visualisation.csv')

    fieldnames = ['sector', 'audit_type', 'category', 'latitude', 'longitude', 'intensity']
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"Done. {len(all_data)} entries -> {output_file}")
    
    # Print summary by category
    from collections import Counter
    types = Counter(d['category'] for d in all_data)
    for cat, count in types.most_common():
        print(f"  {cat}: {count}")