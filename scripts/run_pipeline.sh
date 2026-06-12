#!/bin/bash
# ==============================================================================
# OSM_AUDIT_2025: Automated Pipeline Runner
# Executes local Python analysis pipeline in sequence
# 
# Prerequisites:
#   1. pip install -r requirements.txt
#   2. GEE scripts (04, 06, 06b, 08, 10) must be run in the GEE Code Editor
#      and CSVs exported to data/raw_telemetry/
#   3. OSM data downloaded via 01_osm_extraction.ql (Overpass Turbo) to data/raw_spatial/
# ==============================================================================

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON="${PROJECT_ROOT}/../bin/python"

echo "=================================================="
echo "OSM_AUDIT_2025 Pipeline"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

echo ""
echo "[Step 1/10] Spatial Projection & Area Calculation..."
$PYTHON "$SCRIPT_DIR/02_spatial_projection.py"

echo ""
echo "[Step 2/10] Kepler.gl Data Generation..."
$PYTHON "$SCRIPT_DIR/03_kepler_formatter.py"

echo ""
echo "[Step 3/10] NDVI Trend Chart..."
$PYTHON "$SCRIPT_DIR/05_plot_ndvi_chart.py"

echo ""
echo "[Step 4/10] LST Primary BACI (Full VP Polygon)..."
if [ -f "$PROJECT_ROOT/data/raw_telemetry/ee-chart_lst_sensitivity.csv" ]; then
    $PYTHON "$SCRIPT_DIR/07_plot_thermal_chart.py"
else
    echo "  -> Skip: 'data/raw_telemetry/ee-chart_lst_sensitivity.csv' not found. Run GEE script 06b first."
fi

echo ""
echo "[Step 5/10] LST Sensitivity (Parking-Lot Sub-Polygon)..."
if [ -f "$PROJECT_ROOT/data/raw_telemetry/ee-chart_lst.csv" ]; then
    $PYTHON "$SCRIPT_DIR/07b_plot_thermal_sensitivity.py"
else
    echo "  -> Skip: 'data/raw_telemetry/ee-chart_lst.csv' not found. Run GEE script 06 first."
fi

echo ""
echo "[Step 6/10] Spatial Transect Decay Chart..."
if [ -f "$PROJECT_ROOT/data/raw_telemetry/ee-chart_decay.csv" ]; then
    $PYTHON "$SCRIPT_DIR/09_plot_transect_decay.py"
else
    echo "  -> Skip: 'data/raw_telemetry/ee-chart_decay.csv' not found."
fi

echo ""
echo "[Step 7/11] Annual Composite LST Analysis..."
if [ -f "$PROJECT_ROOT/data/raw_telemetry/ee-chart_lst_sensitivity.csv" ]; then
    $PYTHON "$SCRIPT_DIR/07c_lst_annual_composite.py"
else
    echo "  -> Skip: LST data not found."
fi

echo ""
echo "[Step 8/11] Evapotranspiration Chart..."
if [ -f "$PROJECT_ROOT/data/raw_telemetry/ee-chart_et.csv" ]; then
    $PYTHON "$SCRIPT_DIR/11_plot_evapotranspiration.py"
else
    echo "  -> Skip: 'data/raw_telemetry/ee-chart_et.csv' not found."
fi

echo ""
echo "[Step 9/11] Non-GEE: Impervious Surface Analysis (OSM + EIA)..."
$PYTHON "$SCRIPT_DIR/12_impervious_surface_analysis.py"

echo ""
echo "[Step 9/10] Non-GEE: Met Office Regional Temperature..."
$PYTHON "$SCRIPT_DIR/13_metoffice_temperature_analysis.py"

echo ""
echo "=================================================="
echo "Pipeline complete."
echo "=================================================="
echo ""
echo "To extract satellite data automatically (replaces manual GEE):"
echo "  $PYTHON scripts/00_gee_data_extraction.py --project YOUR_GEE_PROJECT_ID"
echo ""
echo "Or manually via GEE Code Editor:"
echo "  1. Run 04_gee_ndvi_pipeline.js          -> Save to: data/raw_telemetry/ee-chart_ndvi.csv"
echo "  2. Run 06_gee_thermal_pipeline.js       -> Save to: data/raw_telemetry/ee-chart_lst.csv"
echo "  3. Run 06b_gee_thermal_sensitivity.js   -> Save to: data/raw_telemetry/ee-chart_lst_sensitivity.csv"
echo "  4. Run 08_gee_transect_decay.js         -> Save to: data/raw_telemetry/ee-chart_decay.csv"
echo "  5. Run 10_gee_evapotranspiration.js     -> Save to: data/raw_telemetry/ee-chart_et.csv"
echo "  Then re-run this script to generate all charts."

