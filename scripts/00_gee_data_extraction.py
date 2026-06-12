#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_gee_data_extraction.py
Automated GEE Data Extraction — Replaces Manual Code Editor Workflow

Extracts all 5 satellite datasets via the Python ee API:
  1. NDVI (Sentinel-2)
  2. LST Primary (Landsat 7+8+9, Full VP polygon)
  3. LST Sensitivity (Landsat 7+8+9, Parking-lot polygon)
  4. Transect Decay (Landsat 7+8+9, concentric rings)
  5. Evapotranspiration (MODIS MOD16A2GF)

Usage:
  python 00_gee_data_extraction.py --project YOUR_GEE_PROJECT_ID
  python 00_gee_data_extraction.py --project YOUR_GEE_PROJECT_ID --force
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
import ee

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry')

# ==============================================================================
# Shared Geometry Definitions
# ==============================================================================
CONSTRUCTION_DATE = '2021-06-01'

# Parking-lot polygon (5 vertices, ~3 Landsat thermal pixels)
PARKING_LOT_COORDS = [
    [-0.4676848515978538, 51.40882742185046],
    [-0.4669123754015647, 51.409429716784295],
    [-0.46926006378714025, 51.41065315692719],
    [-0.4703222185570377, 51.40986350085904],
    [-0.4676848515978538, 51.40882742185046]
]

# Full VP development polygon (9 vertices, ~1 km², ~50 thermal pixels)
VP_POLYGON_COORDS = [
    [-0.4758927487043363, 51.41217153384681],
    [-0.47417613493480504, 51.409200313379166],
    [-0.4710862301496488, 51.40735324117383],
    [-0.47027083860912144, 51.405479323562865],
    [-0.4644343517927152, 51.40454233596011],
    [-0.45975657927074254, 51.40778155441695],
    [-0.4637047909406644, 51.40791540148267],
    [-0.4710862301496488, 51.412225067579875],
    [-0.4758927487043363, 51.41217153384681]
]

# Control Zone (stable greenbelt, ~2 km from Shepperton)
CONTROL_POINT = [-0.4104592619093905, 51.40739479750269]

END_DATE = '2026-03-15'


def init_ee(project_id):
    """Authenticate and initialise Earth Engine."""
    try:
        ee.Initialize(project=project_id)
        print(f"[OK] Earth Engine initialised (project: {project_id})")
    except Exception:
        print("[AUTH] Authenticating with Earth Engine...")
        ee.Authenticate()
        ee.Initialize(project=project_id)
        print(f"[OK] Earth Engine authenticated and initialised (project: {project_id})")


def fc_to_dataframe(fc, properties):
    """Convert an ee.FeatureCollection to a pandas DataFrame."""
    info = fc.getInfo()
    rows = []
    for feat in info['features']:
        props = feat['properties']
        row = {}
        for p in properties:
            row[p] = props.get(p)
        rows.append(row)
    return pd.DataFrame(rows)


# ==============================================================================
# 1. NDVI Extraction (Sentinel-2)
# ==============================================================================
def extract_ndvi(output_path):
    """Replaces 04_gee_ndvi_pipeline.js"""
    print("\n[1/5] Extracting NDVI (Sentinel-2)...")
    
    sprawl = ee.Geometry.Point([-0.469366, 51.410315]).buffer(100)
    control = ee.Geometry.Point(CONTROL_POINT).buffer(100)
    analysis = ee.Geometry.Point([-0.4640, 51.4065]).buffer(1000)
    
    s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
          .filterBounds(analysis)
          .filterDate('2018-01-01', END_DATE)
          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))
    
    def mask_s2(image):
        qa = image.select('QA60')
        mask_qa = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
        scl = image.select('SCL')
        mask_scl = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
        return image.updateMask(mask_qa.And(mask_scl)).divide(10000)
    
    ndvi_col = s2.map(lambda img: (
        mask_s2(img)
        .normalizedDifference(['B8', 'B4']).rename('NDVI')
        .copyProperties(img, ['system:time_start'])
    ))
    
    rois = ee.FeatureCollection([
        ee.Feature(sprawl, {'label': 'Sprawl_Zone_Core'}),
        ee.Feature(control, {'label': 'Control_Zone'})
    ])
    
    def extract_stats(image):
        stats = image.reduceRegions(
            collection=rois,
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
            scale=10
        )
        sp = ee.Feature(stats.filter(ee.Filter.eq('label', 'Sprawl_Zone_Core')).first())
        ct = ee.Feature(stats.filter(ee.Filter.eq('label', 'Control_Zone')).first())
        return ee.Feature(None, {
            'Sprawl_Zone_Core_mean': sp.get('mean'),
            'Sprawl_Zone_Core_std': sp.get('stdDev'),
            'Control_Zone_mean': ct.get('mean'),
            'Control_Zone_std': ct.get('stdDev'),
            'system:time_start': image.get('system:time_start')
        })
    
    ts = ndvi_col.map(extract_stats)
    df = fc_to_dataframe(ts, [
        'system:time_start', 'Sprawl_Zone_Core_mean', 'Sprawl_Zone_Core_std',
        'Control_Zone_mean', 'Control_Zone_std'
    ])
    df['system:time_start'] = pd.to_datetime(df['system:time_start'], unit='ms')
    df = df.sort_values('system:time_start')
    df.to_csv(output_path, index=False)
    print(f"  -> Saved {len(df)} observations to {output_path}")


# ==============================================================================
# 2. LST Primary (Full VP Polygon, ~50 thermal pixels)
# ==============================================================================
def _build_lst_collection(bounds, start_date, end_date):
    """Build triple-satellite LST collection (shared by primary + sensitivity)."""
    
    def prep_l7(image):
        qa = image.select('QA_PIXEL')
        mask = (qa.bitwiseAnd(1 << 1).eq(0)
                .And(qa.bitwiseAnd(1 << 3).eq(0))
                .And(qa.bitwiseAnd(1 << 4).eq(0))
                .And(qa.bitwiseAnd(1 << 5).eq(0)))
        lst = image.select('ST_B6').multiply(0.00341802).add(149.0).subtract(273.15).rename('LST_Celsius')
        return image.addBands(lst).updateMask(mask).copyProperties(image, ['system:time_start']).set('satellite', 'L7')
    
    def prep_l89(image):
        qa = image.select('QA_PIXEL')
        mask = (qa.bitwiseAnd(1 << 1).eq(0)
                .And(qa.bitwiseAnd(1 << 3).eq(0))
                .And(qa.bitwiseAnd(1 << 4).eq(0))
                .And(qa.bitwiseAnd(1 << 5).eq(0)))
        lst = image.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15).rename('LST_Celsius')
        return image.addBands(lst).updateMask(mask).copyProperties(image, ['system:time_start']).set('satellite', 'L89')
    
    l7 = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2').filterBounds(bounds).filterDate(start_date, end_date).map(prep_l7)
    l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').filterBounds(bounds).filterDate(start_date, end_date).map(prep_l89)
    l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2').filterBounds(bounds).filterDate(start_date, end_date).map(prep_l89)
    
    return l7.merge(l8).merge(l9).select(['LST_Celsius']).sort('system:time_start')


def _extract_lst_timeseries(lst_col, sprawl_geom, control_geom, output_path, label):
    """Extract paired BACI time series for given impact/control zones."""
    
    def extract_stats(image):
        lst = image.select('LST_Celsius')
        sp_mean = lst.reduceRegion(reducer=ee.Reducer.mean(), geometry=sprawl_geom, scale=30, bestEffort=True)
        sp_std = lst.reduceRegion(reducer=ee.Reducer.stdDev(), geometry=sprawl_geom, scale=30, bestEffort=True)
        ct_mean = lst.reduceRegion(reducer=ee.Reducer.mean(), geometry=control_geom, scale=30, bestEffort=True)
        ct_std = lst.reduceRegion(reducer=ee.Reducer.stdDev(), geometry=control_geom, scale=30, bestEffort=True)
        return ee.Feature(None, {
            'Sprawl_Zone_Core_mean': sp_mean.get('LST_Celsius'),
            'Sprawl_Zone_Core_std': sp_std.get('LST_Celsius'),
            'Control_Zone_mean': ct_mean.get('LST_Celsius'),
            'Control_Zone_std': ct_std.get('LST_Celsius'),
            'system:time_start': image.get('system:time_start')
        })
    
    ts = lst_col.map(extract_stats)
    df = fc_to_dataframe(ts, [
        'system:time_start', 'Sprawl_Zone_Core_mean', 'Sprawl_Zone_Core_std',
        'Control_Zone_mean', 'Control_Zone_std'
    ])
    df['system:time_start'] = pd.to_datetime(df['system:time_start'], unit='ms')
    df = df.sort_values('system:time_start')
    df.to_csv(output_path, index=False)
    print(f"  -> [{label}] Saved {len(df)} observations to {output_path}")


def extract_lst_primary(output_path):
    """Replaces 06b_gee_thermal_sensitivity.js (now primary: full VP polygon)."""
    print("\n[2/5] Extracting LST Primary (Full VP Polygon)...")
    
    sprawl = ee.Geometry.Polygon([VP_POLYGON_COORDS])
    control = ee.Geometry.Point(CONTROL_POINT).buffer(150)
    bounds = ee.Geometry.Rectangle([-0.48, 51.40, -0.40, 51.42])
    
    lst_col = _build_lst_collection(bounds, '2015-01-01', END_DATE)
    print(f"  -> Total scenes: {lst_col.size().getInfo()}")
    _extract_lst_timeseries(lst_col, sprawl, control, output_path, "Primary VP")


def extract_lst_sensitivity(output_path):
    """Replaces 06_gee_thermal_pipeline.js (now sensitivity: parking lot)."""
    print("\n[3/5] Extracting LST Sensitivity (Parking-Lot Sub-Polygon)...")
    
    sprawl = ee.Geometry.Polygon([PARKING_LOT_COORDS])
    control = ee.Geometry.Point(CONTROL_POINT).buffer(150)
    bounds = ee.Geometry.Rectangle([-0.48, 51.40, -0.40, 51.42])
    
    lst_col = _build_lst_collection(bounds, '2015-01-01', END_DATE)
    _extract_lst_timeseries(lst_col, sprawl, control, output_path, "Sensitivity ParkingLot")


# ==============================================================================
# 4. Transect Decay
# ==============================================================================
def extract_transect(output_path):
    """Replaces 08_gee_transect_decay.js"""
    print("\n[4/5] Extracting Spatial Transect Decay...")
    
    sprawl = ee.Geometry.Polygon([PARKING_LOT_COORDS])
    bounds = ee.Geometry.Rectangle([-0.49, 51.39, -0.45, 51.43])
    max_distance = 800
    step_size = 50
    
    lst_col = _build_lst_collection(bounds, '2015-01-01', END_DATE)
    
    summer_pre = (lst_col.select('LST_Celsius')
                  .filter(ee.Filter.calendarRange(6, 8, 'month'))
                  .filterDate('2018-01-01', '2021-01-01').mean())
    summer_post = (lst_col.select('LST_Celsius')
                   .filter(ee.Filter.calendarRange(6, 8, 'month'))
                   .filterDate('2023-01-01', '2026-01-01').mean())
    
    composite = ee.Image([
        summer_pre.rename('Pre_LST_mean'),
        summer_post.rename('Post_LST_mean')
    ])
    
    # Build concentric rings
    zones = []
    # Core = impact zone itself
    zones.append(ee.Feature(sprawl, {'Distance_m': 0}))
    
    for d in range(0, max_distance - step_size + 1, step_size):
        inner = sprawl.buffer(max(d, 0.1))
        outer = sprawl.buffer(d + step_size)
        ring = outer.difference(inner)
        zones.append(ee.Feature(ring, {'Distance_m': d + step_size / 2}))
    
    transect_fc = ee.FeatureCollection(zones)
    
    def extract_decay(feature):
        stats = composite.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=feature.geometry(),
            scale=30,
            bestEffort=True
        )
        return feature.set({
            'Pre_LST_mean': stats.get('Pre_LST_mean'),
            'Post_LST_mean': stats.get('Post_LST_mean')
        })
    
    decay_data = transect_fc.map(extract_decay)
    df = fc_to_dataframe(decay_data, ['Distance_m', 'Pre_LST_mean', 'Post_LST_mean'])
    df = df.sort_values('Distance_m')
    df.to_csv(output_path, index=False)
    print(f"  -> Saved {len(df)} rings to {output_path}")


# ==============================================================================
# 5. Evapotranspiration (MODIS)
# ==============================================================================
def extract_et(output_path):
    """Replaces 10_gee_evapotranspiration.js"""
    print("\n[5/5] Extracting Evapotranspiration (MODIS MOD16A2GF)...")
    
    sprawl = ee.Geometry.Polygon([VP_POLYGON_COORDS])
    control = ee.Geometry.Point(CONTROL_POINT).buffer(500)
    
    modis_et = (ee.ImageCollection('MODIS/061/MOD16A2GF')
                .filterDate('2015-01-01', END_DATE)
                .select('ET'))
    
    def prep_et(image):
        return image.select('ET').multiply(0.1).rename('ET_mm_8day').copyProperties(image, ['system:time_start'])
    
    et_col = modis_et.map(prep_et)
    
    def extract_stats(image):
        sp = image.reduceRegion(reducer=ee.Reducer.mean(), geometry=sprawl, scale=500, bestEffort=True)
        ct = image.reduceRegion(reducer=ee.Reducer.mean(), geometry=control, scale=500, bestEffort=True)
        return ee.Feature(None, {
            'Sprawl_ET_mean': sp.get('ET_mm_8day'),
            'Control_ET_mean': ct.get('ET_mm_8day'),
            'system:time_start': image.get('system:time_start')
        })
    
    ts = et_col.map(extract_stats)
    df = fc_to_dataframe(ts, ['system:time_start', 'Sprawl_ET_mean', 'Control_ET_mean'])
    df['system:time_start'] = pd.to_datetime(df['system:time_start'], unit='ms')
    df = df.sort_values('system:time_start')
    df.to_csv(output_path, index=False)
    print(f"  -> Saved {len(df)} observations to {output_path}")


# ==============================================================================
# Main
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description='OSM_AUDIT_2025: Automated GEE Data Extraction',
        epilog='Replaces manual GEE Code Editor workflow. '
               'First run requires ee.Authenticate() via browser.'
    )
    parser.add_argument('--project', required=True,
                        help='GEE Cloud Project ID (e.g. "ee-myproject")')
    parser.add_argument('--force', action='store_true',
                        help='Force re-extraction even if CSVs already exist')
    parser.add_argument('--only', choices=['ndvi', 'lst-primary', 'lst-sensitivity', 'transect', 'et'],
                        help='Extract only a specific dataset')
    args = parser.parse_args()
    
    init_ee(args.project)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    tasks = {
        'ndvi': ('ee-chart_ndvi.csv', extract_ndvi),
        'lst-primary': ('ee-chart_lst_sensitivity.csv', extract_lst_primary),
        'lst-sensitivity': ('ee-chart_lst.csv', extract_lst_sensitivity),
        'transect': ('ee-chart_decay.csv', extract_transect),
        'et': ('ee-chart_et.csv', extract_et),
    }
    
    if args.only:
        tasks = {args.only: tasks[args.only]}
    
    for name, (filename, func) in tasks.items():
        path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(path) and not args.force:
            print(f"\n[SKIP] {filename} already exists. Use --force to re-extract.")
            continue
        try:
            func(path)
        except Exception as e:
            print(f"\n[ERROR] {name} extraction failed: {e}")
            print("  Continuing with remaining extractions...")
            continue
    
    print("\n" + "=" * 60)
    print("GEE extraction complete.")
    print("=" * 60)


if __name__ == '__main__':
    main()
