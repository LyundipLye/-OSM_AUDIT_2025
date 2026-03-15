# -*- coding: utf-8 -*-
"""
02_spatial_projection.py
WGS84 GeoJSON -> EPSG:27700 面积计算 & 电力节点统计
"""

import json
import os
import logging
from datetime import datetime
from shapely.geometry import shape
import pyproj
from shapely.ops import transform

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WGS84 = "epsg:4326"
BNG = "epsg:27700"
projector = pyproj.Transformer.from_crs(WGS84, BNG, always_xy=True).transform

def run_spatial_audit(file_path):
    """返回 (停车场总面积 sqm, 电力节点数)"""
    if not os.path.exists(file_path):
        logger.error("Source file missing: %s", file_path)
        return 0.0, 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            logger.error("Invalid JSON: %s", file_path)
            return 0.0, 0

    # 记录数据提取元信息
    timestamp = data.get('osm3s', {}).get('timestamp_osm_base', 'unknown')
    logger.info("OSM data timestamp: %s | File: %s", timestamp, os.path.basename(file_path))

    parking_area = 0.0
    power_nodes = 0
    
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        geom = feature.get('geometry', {})
        
        if not geom:
            continue

        if 'power' in props and props['power'] is not None:
            power_nodes += 1

        if props.get('amenity') == 'parking' and geom.get('type') in ['Polygon', 'MultiPolygon']:
            s = shape(geom)
            s_projected = transform(projector, s)
            parking_area += s_projected.area
            
    return parking_area, power_nodes

if __name__ == "__main__":
    logger.info("Audit executed: %s", datetime.now().strftime('%Y-%m-%d %H:%M'))

    shep_path = os.path.join(PROJECT_ROOT, 'data', 'raw_spatial', 'export_shepperton.geojson')
    long_path = os.path.join(PROJECT_ROOT, 'data', 'raw_spatial', 'export_longcross.geojson')
    
    shep_area, shep_pwr = run_spatial_audit(shep_path)
    long_area, long_pwr = run_spatial_audit(long_path)
    
    total_area = shep_area + long_area
    total_hectares = total_area / 10000
    
    logger.info("SHEPPERTON: %,.2f SQM | Nodes: %d", shep_area, shep_pwr)
    logger.info("LONGCROSS:  %,.2f SQM | Nodes: %d", long_area, long_pwr)
    logger.info("-" * 50)
    logger.info("TOTAL SPRAWL:      %,.2f SQM", total_area)
    logger.info("LAND CONVERSION:   %,.4f Hectares", total_hectares)
    logger.info("POWER NODES:       %d", shep_pwr + long_pwr)
    logger.info("NOTE: parking-only metric (amenity=parking). "
                "EIA total floorspace = 164,000 sqm / green belt loss = 39 ha.")