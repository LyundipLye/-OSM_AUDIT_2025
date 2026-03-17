# -*- coding: utf-8 -*-
"""
02_spatial_projection.py
WGS84 GeoJSON -> EPSG:27700 面积计算 & 电力节点统计
Expanded: Calculates area for ALL impervious surface categories,
not just amenity=parking. Uses shapely.unary_union to deduplicate
overlapping polygons.
"""

import json
import os
import logging
from datetime import datetime
from shapely.geometry import shape
from shapely.ops import transform, unary_union
import pyproj

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WGS84 = "epsg:4326"
BNG = "epsg:27700"
projector = pyproj.Transformer.from_crs(WGS84, BNG, always_xy=True).transform


def classify_feature(props):
    """Classify an OSM feature into an impervious surface category.
    Returns (category_name, is_polygon_area_feature, is_power_node)."""
    is_power = 'power' in props and props['power'] is not None
    
    if props.get('amenity') == 'parking':
        return 'parking', True, is_power
    elif props.get('landuse') in ('industrial', 'commercial', 'construction'):
        return f"landuse_{props['landuse']}", True, is_power
    elif props.get('highway') == 'service' and props.get('surface') in ('asphalt', 'paved', 'concrete'):
        return 'service_road_paved', True, is_power
    elif props.get('man_made') == 'works':
        return 'industrial_works', True, is_power
    elif props.get('building') in ('industrial', 'commercial'):
        return f"building_{props['building']}", True, is_power
    elif is_power:
        return 'power_infrastructure', False, True
    else:
        return None, False, False


def run_spatial_audit(file_path):
    """Returns (category_areas_dict, total_deduped_area_sqm, power_nodes_count)."""
    if not os.path.exists(file_path):
        logger.error("Source file missing: %s", file_path)
        return {}, 0.0, 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            logger.error("Invalid JSON: %s", file_path)
            return {}, 0.0, 0

    # 记录数据提取元信息
    timestamp = data.get('timestamp') or data.get('osm3s', {}).get('timestamp_osm_base', 'unknown')
    logger.info("OSM data timestamp: %s | File: %s", timestamp, os.path.basename(file_path))

    category_areas = {}      # category -> total area (sqm)
    category_geometries = {} # category -> list of projected shapely geometries
    all_geometries = []      # for deduplication via unary_union
    power_nodes = 0
    
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        geom = feature.get('geometry', {})
        
        if not geom:
            continue

        category, is_area_feature, is_power = classify_feature(props)
        
        if is_power:
            power_nodes += 1

        if is_area_feature and geom.get('type') in ['Polygon', 'MultiPolygon']:
            try:
                s = shape(geom)
                s_projected = transform(projector, s)
                area = s_projected.area
                
                # Per-category tracking (may double-count overlapping polygons)
                if category not in category_areas:
                    category_areas[category] = 0.0
                    category_geometries[category] = []
                category_areas[category] += area
                category_geometries[category].append(s_projected)
                
                # For global deduplication
                all_geometries.append(s_projected)
            except Exception as e:
                logger.warning("Skipping invalid geometry: %s", e)
                continue
            
    # Deduplicated total via unary_union (dissolves overlapping polygons)
    if all_geometries:
        merged = unary_union(all_geometries)
        total_deduped = merged.area
    else:
        total_deduped = 0.0
    
    return category_areas, total_deduped, power_nodes


if __name__ == "__main__":
    logger.info("Audit executed: %s", datetime.now().strftime('%Y-%m-%d %H:%M'))

    shep_path = os.path.join(PROJECT_ROOT, 'data', 'raw_spatial', 'export_shepperton.geojson')
    long_path = os.path.join(PROJECT_ROOT, 'data', 'raw_spatial', 'export_longcross.geojson')
    
    shep_cats, shep_area, shep_pwr = run_spatial_audit(shep_path)
    long_cats, long_area, long_pwr = run_spatial_audit(long_path)
    
    total_area = shep_area + long_area
    total_hectares = total_area / 10000
    
    logger.info("=" * 60)
    logger.info("SHEPPERTON (per-category, before deduplication):")
    for cat, area in sorted(shep_cats.items()):
        logger.info("  %-30s %12s SQM  (%6.2f ha)", cat, f"{area:,.2f}", area / 10000)
    logger.info("  SHEPPERTON DEDUPED TOTAL:    %12s SQM  (%6.2f ha)", f"{shep_area:,.2f}", shep_area / 10000)
    logger.info("  Power nodes:                 %d", shep_pwr)
    
    logger.info("-" * 60)
    logger.info("LONGCROSS (per-category, before deduplication):")
    for cat, area in sorted(long_cats.items()):
        logger.info("  %-30s %12s SQM  (%6.2f ha)", cat, f"{area:,.2f}", area / 10000)
    logger.info("  LONGCROSS DEDUPED TOTAL:     %12s SQM  (%6.2f ha)", f"{long_area:,.2f}", long_area / 10000)
    logger.info("  Power nodes:                 %d", long_pwr)
    
    logger.info("=" * 60)
    logger.info("COMBINED DEDUPED TOTAL:        %s SQM  (%.2f ha)", f"{total_area:,.2f}", total_hectares)
    logger.info("TOTAL POWER NODES:             %d", shep_pwr + long_pwr)
    logger.info("NOTE: Deduped total uses shapely.unary_union to dissolve overlapping polygons.")
    logger.info("NOTE: Includes parking, industrial/commercial landuse, paved service roads, buildings.")
    logger.info("NOTE: EIA total floorspace = 164,000 sqm / green belt loss = 39 ha.")