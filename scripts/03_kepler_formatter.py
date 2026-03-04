import json
import csv
import os
from shapely.geometry import shape

def extract_features_for_kepler(file_path, sector_name):
    """
    Extracts geographical features from GeoJSON and formats them for Kepler.gl.
    Identifies Power Nodes and centroids of Logistical Sprawl (Parking).
    """
    features_list = []
    
    if not os.path.exists(file_path):
        print(f"[WARNING] File not found: {file_path}")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"[ERROR] Failed to decode JSON from {file_path}")
            return []
        
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        geom = feature.get('geometry', {})
        
        if not geom:
            continue

        # 1. Extract Power Infrastructure Nodes (Point data)
        if 'power' in props and geom['type'] == 'Point':
            lon, lat = geom['coordinates']
            features_list.append({
                'sector': sector_name,
                'audit_type': 'Energy_Displacement',
                'category': props.get('power', 'infrastructure'),
                'latitude': lat,
                'longitude': lon,
                'intensity': 1.0  # Used for heatmap weight
            })
            
        # 2. Extract Logistical Sprawl (Polygon Centroids for Heatmap weighting)
        if props.get('amenity') == 'parking' and geom['type'] in ['Polygon', 'MultiPolygon']:
            # Calculate the geometric centre of the parking lot
            s = shape(geom)
            centroid = s.centroid
            features_list.append({
                'sector': sector_name,
                'audit_type': 'Logistical_Sprawl',
                'category': 'asphalt_surface',
                'latitude': centroid.y,
                'longitude': centroid.x,
                'intensity': s.area / 1000  # Weight the heatmap by the size of the parking lot
            })
            
    return features_list

if __name__ == "__main__":
    # Ensure the directory exists
    os.makedirs('geographic', exist_ok=True)

    # Process both studio sectors
    shepperton_data = extract_features_for_kepler('geographic/raw/export_shepperton.geojson', 'Shepperton')
    longcross_data = extract_features_for_kepler('geographic/raw/export_longcross.geojson', 'Longcross')

    all_data = shepperton_data + longcross_data

    # Define output path
    output_file = 'geographic/kepler_gl_visualisation.csv'

    # Write to CSV with clear headers for Kepler.gl auto-detection
    fieldnames = ['sector', 'audit_type', 'category', 'latitude', 'longitude', 'intensity']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"--- KEPLER DATA GENERATION COMPLETE ---")
    print(f"Total entries processed: {len(all_data)}")
    print(f"File saved to: {output_file}")
    print("ACTION: Drag this file into kepler.gl/demo and use 'audit_type' for colour filtering.")