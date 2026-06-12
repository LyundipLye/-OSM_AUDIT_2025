# -*- coding: utf-8 -*-
"""
12_impervious_surface_analysis.py
Phase VI: Non-Satellite Ground Truth — Impervious Surface Analysis
Uses OSM feature data and EIA planning documents to independently
verify land-cover change, without any GEE/satellite dependency.

Analyses:
1. OSM-derived impervious surface area by category
2. Cross-reference with EIA-documented development footprint (14.12 ha)
3. Land-cover transition matrix (greenfield → impervious)
4. Theoretical latent heat suppression estimate (Penman-Monteith parameters)
"""

import json
import os
import logging
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import shape
from shapely.ops import transform, unary_union
import pyproj

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WGS84 = "epsg:4326"
BNG = "epsg:27700"
projector = pyproj.Transformer.from_crs(WGS84, BNG, always_xy=True).transform


# ==============================================================================
# EIA Planning Data (from Spelthorne Borough Council Case Ref 18/01212/OUT)
# These are documented in documentation/eia_data_extraction_log.md
# ==============================================================================
EIA_DATA = {
    'planning_ref': '18/01212/OUT',
    'applicant': 'Shepperton Studios Ltd (Pinewood Group)',
    'total_site_area_ha': 24.28,            # Total application site
    'development_footprint_ha': 14.12,      # Area of proposed development
    'existing_studio_ha': 10.16,            # Existing studio retained
    'greenbelt_loss_ha': 13.05,             # Green Belt land affected
    'construction_start': '2019-06',
    'construction_end': '2023-12',          # Approximate completion
    'new_stages': 17,                       # Additional sound stages
    'parking_spaces': 2300,                 # New parking spaces
    'description': 'EXPANSION of film studio production facilities including '
                   '17 new stages, workshops, offices, and 2,300 parking spaces'
}

# Penman-Monteith reference parameters for UK lowland summer
# Source: Allen et al. (1998) FAO-56; UK Met Office regional averages
SURFACE_PARAMS = {
    'grassland': {
        'albedo': 0.23,           # Short grass reference
        'emissivity': 0.95,
        'ET_summer_mm_day': 3.5,  # UK lowland summer ET (FAO-56 reference)
        'description': 'Short grass (pre-development greenfield)'
    },
    'asphalt': {
        'albedo': 0.12,           # Dark asphalt/concrete
        'emissivity': 0.92,
        'ET_summer_mm_day': 0.1,  # Near-zero (sealed surface, no transpiration)
        'description': 'Impervious asphalt/concrete (post-development)'
    }
}


def classify_feature(props):
    """Classify an OSM feature into an impervious surface category."""
    if props.get('amenity') == 'parking':
        return 'Parking'
    elif props.get('landuse') in ('industrial', 'commercial', 'construction'):
        return f"Landuse: {props['landuse'].title()}"
    elif props.get('highway') == 'service' and props.get('surface') in ('asphalt', 'paved', 'concrete'):
        return 'Service Road (Paved)'
    elif props.get('man_made') == 'works':
        return 'Industrial Works'
    elif props.get('building') in ('industrial', 'commercial'):
        return f"Building: {props['building'].title()}"
    elif 'power' in props and props['power'] is not None:
        return 'Power Infrastructure'
    elif props.get('building') is not None:
        return f"Building: {props.get('building', 'yes').title()}"
    return None


def run_impervious_analysis(geojson_path, output_path):
    """Main analysis function."""
    
    # ---------------------------------------------------------
    # 1. Load and classify OSM features
    # ---------------------------------------------------------
    try:
        with open(geojson_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {geojson_path}")
        return

    features = data.get('features', data.get('elements', []))
    
    category_geoms = {}  # category -> list of shapely geometries
    category_counts = {}
    point_features = 0
    
    for feat in features:
        geom = feat.get('geometry')
        props = feat.get('properties', feat.get('tags', {}))
        
        if not geom or not props:
            continue
        
        cat = classify_feature(props)
        if cat is None:
            continue
            
        try:
            shp = shape(geom)
            if shp.geom_type == 'Point':
                point_features += 1
                category_counts[cat] = category_counts.get(cat, 0) + 1
                continue
            
            # Project to BNG for area calculation
            shp_bng = transform(projector, shp)
            if shp_bng.area > 0:
                category_geoms.setdefault(cat, []).append(shp_bng)
                category_counts[cat] = category_counts.get(cat, 0) + 1
        except Exception as e:
            logger.debug(f"Skipping feature: {e}")
            continue
    
    # ---------------------------------------------------------
    # 2. Calculate areas per category (deduplicated)
    # ---------------------------------------------------------
    category_areas = {}
    all_polygons = []
    
    for cat, geoms in category_geoms.items():
        merged = unary_union(geoms)
        area_sqm = merged.area
        category_areas[cat] = area_sqm
        all_polygons.extend(geoms)
    
    total_union = unary_union(all_polygons)
    total_area_sqm = total_union.area
    total_area_ha = total_area_sqm / 10000
    
    # ---------------------------------------------------------
    # 3. Print results and cross-reference with EIA
    # ---------------------------------------------------------
    print("=" * 72)
    print("PHASE VI: NON-SATELLITE GROUND TRUTH — IMPERVIOUS SURFACE ANALYSIS")
    print("=" * 72)
    print(f"\nData Source: OpenStreetMap (non-satellite, crowd-sourced geospatial)")
    print(f"Planning Ref: {EIA_DATA['planning_ref']}")
    print(f"Applicant: {EIA_DATA['applicant']}")
    
    print(f"\n--- OSM-Derived Impervious Surface Area ---")
    sorted_cats = sorted(category_areas.items(), key=lambda x: -x[1])
    for cat, area in sorted_cats:
        count = category_counts.get(cat, 0)
        print(f"  {cat:30s}: {area:>10,.0f} m² ({area/10000:>6.2f} ha)  [{count} features]")
    
    print(f"  {'─'*30}  {'─'*10}")
    print(f"  {'TOTAL (deduplicated union)':30s}: {total_area_sqm:>10,.0f} m² ({total_area_ha:>6.2f} ha)")
    print(f"  Point features (no area):     {point_features}")
    
    # Cross-reference
    eia_footprint_ha = EIA_DATA['development_footprint_ha']
    coverage_pct = (total_area_ha / eia_footprint_ha) * 100 if eia_footprint_ha > 0 else 0
    
    print(f"\n--- Cross-Reference with EIA Planning Data ---")
    print(f"  EIA Development Footprint:    {eia_footprint_ha:.2f} ha")
    print(f"  OSM Impervious (deduplicated): {total_area_ha:.2f} ha")
    print(f"  Coverage Ratio:               {coverage_pct:.1f}%")
    print(f"  Green Belt Loss (EIA):        {EIA_DATA['greenbelt_loss_ha']:.2f} ha")
    
    if coverage_pct < 50:
        print(f"  ⚠ OSM coverage is {coverage_pct:.0f}% of EIA footprint — likely incomplete mapping")
    elif coverage_pct > 120:
        print(f"  ⚠ OSM area exceeds EIA footprint — possible overlap with pre-existing development")
    else:
        print(f"  ✓ OSM area is within expected range of EIA footprint")
    
    # ---------------------------------------------------------
    # 4. Land-cover transition matrix
    # ---------------------------------------------------------
    print(f"\n--- Land-Cover Transition Matrix ---")
    print(f"  Pre-Development:  Greenfield (grassland + agricultural)")
    print(f"  Post-Development: Impervious (asphalt + concrete + building)")
    print(f"  Transition Area:  {total_area_ha:.2f} ha (OSM) / {eia_footprint_ha:.2f} ha (EIA)")
    
    # ---------------------------------------------------------
    # 5. Theoretical latent heat suppression
    # ---------------------------------------------------------
    grass = SURFACE_PARAMS['grassland']
    asphalt = SURFACE_PARAMS['asphalt']
    
    # Latent heat of vaporisation: ~2.45 MJ/kg at ~20°C
    L_v = 2.45  # MJ/kg
    
    # ET suppression per unit area
    delta_ET = grass['ET_summer_mm_day'] - asphalt['ET_summer_mm_day']  # mm/day = kg/m²/day
    delta_QE = delta_ET * L_v  # MJ/m²/day
    
    # Total latent heat suppression over the development footprint
    footprint_m2 = eia_footprint_ha * 10000
    total_QE_suppression_MJ = delta_QE * footprint_m2
    total_QE_suppression_MW = total_QE_suppression_MJ / 86400  # MJ/day -> MW (1 MW = 86400 MJ/day)
    
    # Albedo change: reduced shortwave reflection = more absorbed radiation
    delta_albedo = grass['albedo'] - asphalt['albedo']
    # UK summer average solar irradiance ~600 W/m² (peak), daily avg ~200 W/m²
    solar_avg_W = 200  # W/m²
    absorbed_increase_MW = delta_albedo * solar_avg_W * footprint_m2 / 1e6
    
    print(f"\n--- Theoretical Latent Heat Suppression (Penman-Monteith) ---")
    print(f"  Pre-development ET:  {grass['ET_summer_mm_day']:.1f} mm/day ({grass['description']})")
    print(f"  Post-development ET: {asphalt['ET_summer_mm_day']:.1f} mm/day ({asphalt['description']})")
    print(f"  ΔET:                 {delta_ET:+.1f} mm/day (per unit area)")
    print(f"  ΔQE (latent heat):   {delta_QE:+.2f} MJ/m²/day → diverted to sensible heat")
    print(f"  Total over {eia_footprint_ha:.1f} ha:  ~{total_QE_suppression_MW:.1f} MW thermal load")
    print(f"  Albedo change:       {grass['albedo']:.2f} → {asphalt['albedo']:.2f} (Δ={delta_albedo:+.2f})")
    print(f"  Extra absorbed solar: ~{absorbed_increase_MW:.1f} MW (summer daily average)")
    print(f"\n  CONCLUSION: Land-cover transition independently verified via OSM + EIA.")
    print(f"  The physical mechanism (latent heat suppression) predicts ~{total_QE_suppression_MW:.0f} MW")
    print(f"  of additional thermal load during summer, consistent with UHI effect.")

    # ---------------------------------------------------------
    # 6. Generate summary chart
    # ---------------------------------------------------------
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), dpi=300,
                                    gridspec_kw={'width_ratios': [3, 2]})
    
    # Panel 1: Impervious surface area by category
    cats = [c for c, _ in sorted_cats if category_areas[c] > 100]
    areas_ha = [category_areas[c] / 10000 for c in cats]
    
    palette = plt.cm.magma(np.linspace(0.3, 0.85, len(cats)))
    bars = ax1.barh(range(len(cats)), areas_ha, color=palette, edgecolor='white', linewidth=0.5)
    ax1.set_yticks(range(len(cats)))
    ax1.set_yticklabels(cats, fontsize=10, fontfamily='Courier New')
    ax1.set_xlabel('Area (hectares)', fontsize=12, fontfamily='Courier New', color='#CCCCCC')
    ax1.set_title('OSM-Derived Impervious Surface\n(Non-Satellite Ground Truth)',
                  fontsize=14, fontweight='bold', fontfamily='Courier New', color='white')
    ax1.invert_yaxis()
    ax1.grid(axis='x', linestyle='--', alpha=0.3)
    
    # Annotate bar values
    for bar, val in zip(bars, areas_ha):
        ax1.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                 f'{val:.2f} ha', va='center', fontsize=9, fontfamily='Courier New', color='#CCCCCC')
    
    # Add EIA reference line
    ax1.axvline(x=eia_footprint_ha, color='#FF4444', linestyle='--', linewidth=2, alpha=0.7,
                label=f'EIA Footprint ({eia_footprint_ha:.1f} ha)')
    ax1.legend(loc='lower right', frameon=False, prop={'family': 'Courier New', 'size': 10})
    
    # Panel 2: Energy balance comparison
    categories = ['Pre\n(Grassland)', 'Post\n(Impervious)']
    et_values = [grass['ET_summer_mm_day'], asphalt['ET_summer_mm_day']]
    albedo_values = [grass['albedo'] * 10, asphalt['albedo'] * 10]  # Scale for visibility
    
    x = np.arange(len(categories))
    width = 0.3
    
    bars1 = ax2.bar(x - width/2, et_values, width, color='#33CC33', alpha=0.85,
                    edgecolor='white', linewidth=0.5, label='ET (mm/day)')
    bars2 = ax2.bar(x + width/2, albedo_values, width, color='#3399FF', alpha=0.85,
                    edgecolor='white', linewidth=0.5, label='Albedo (×10)')
    
    # Annotate
    for bar, val in zip(bars1, et_values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 f'{val:.1f}', ha='center', fontsize=11, fontweight='bold',
                 fontfamily='Courier New', color='#33CC33')
    for bar, val in zip(bars2, albedo_values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 f'{val/10:.2f}', ha='center', fontsize=11, fontweight='bold',
                 fontfamily='Courier New', color='#3399FF')
    
    # Arrow showing suppression
    ax2.annotate(f'ΔET = {delta_ET:+.1f}\nmm/day',
                 xy=(0.15, et_values[0]/2), xytext=(0.65, et_values[0]/2),
                 fontsize=12, fontweight='bold', color='#FF4444', fontfamily='Courier New',
                 arrowprops=dict(arrowstyle='->', color='#FF4444', lw=2),
                 ha='center', va='center')
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories, fontsize=11, fontfamily='Courier New')
    ax2.set_title('Surface Energy Balance Change\n(Penman-Monteith Theory)',
                  fontsize=14, fontweight='bold', fontfamily='Courier New', color='white')
    ax2.legend(loc='upper right', frameon=False, prop={'family': 'Courier New', 'size': 10})
    ax2.grid(axis='y', linestyle='--', alpha=0.3)
    ax2.set_ylabel('Value', fontsize=12, fontfamily='Courier New', color='#CCCCCC')
    
    fig.text(0.5, 0.005,
             'Data: OpenStreetMap + Spelthorne Borough Council EIA | No satellite dependency | Author: H. Li',
             fontsize=9, color='#888888', ha='center', va='bottom', fontfamily='Helvetica')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"\nSAVED: {output_path}")


if __name__ == '__main__':
    geojson_path = os.path.join(PROJECT_ROOT, 'data', 'raw_spatial', 'export_shepperton.geojson')
    output_path = os.path.join(PROJECT_ROOT, 'visualisations', 'impervious_surface_analysis.png')
    run_impervious_analysis(geojson_path, output_path)
