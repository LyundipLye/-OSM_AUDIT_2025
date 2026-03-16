#!/bin/bash
# ==============================================================================
# OSM_AUDIT_2025: Automated Pipeline Runner
# 按顺序执行本地 Python 分析管线
# 
# 前置条件:
#   1. pip install -r requirements.txt
#   2. GEE 脚本 (04, 06) 需要在 GEE Code Editor 中手动执行
#      并将 CSV 导出到 data/raw_telemetry/
#   3. OSM 数据已通过 01_osm_extraction.ql（Overpass Turbo）下载到 data/raw_spatial/
# ==============================================================================

set -e  # 出错即停

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON="${PROJECT_ROOT}/../bin/python"

echo "=================================================="
echo "OSM_AUDIT_2025 Pipeline"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

echo ""
echo "[Step 1/3] Spatial Projection & Area Calculation..."
$PYTHON "$SCRIPT_DIR/02_spatial_projection.py"

echo ""
echo "[Step 2/3] Kepler.gl Data Generation..."
$PYTHON "$SCRIPT_DIR/03_kepler_formatter.py"

echo ""
echo "[Step 3/3] NDVI Trend Chart..."
$PYTHON "$SCRIPT_DIR/05_plot_ndvi_chart.py"

echo ""
echo "[Step 4/7] LST Thermal Chart..."
if [ -f "$PROJECT_ROOT/data/raw_telemetry/ee-chart_lst.csv" ]; then
    $PYTHON "$SCRIPT_DIR/07_plot_thermal_chart.py"
else
    echo "  -> Skip: 'data/raw_telemetry/ee-chart_lst.csv' not found. Run GEE script 06 first."
fi

echo ""
echo "[Step 5/7] LST Sensitivity Chart (Option A)..."
if [ -f "$PROJECT_ROOT/data/raw_telemetry/ee-chart_lst_sensitivity.csv" ]; then
    $PYTHON "$SCRIPT_DIR/07b_plot_thermal_sensitivity.py"
else
    echo "  -> Skip: 'data/raw_telemetry/ee-chart_lst_sensitivity.csv' not found. Run GEE script 06b first."
fi

echo ""
echo "[Step 6/7] Spatial Transect Decay Chart..."
if [ -f "$PROJECT_ROOT/data/raw_telemetry/ee-chart_decay.csv" ]; then
    $PYTHON "$SCRIPT_DIR/09_plot_transect_decay.py"
else
    echo "  -> Skip: 'data/raw_telemetry/ee-chart_decay.csv' not found. Run GEE script 08 first."
fi

echo ""
echo "[Step 7/7] Evapotranspiration Collapse Chart..."
if [ -f "$PROJECT_ROOT/data/raw_telemetry/ee-chart_et.csv" ]; then
    $PYTHON "$SCRIPT_DIR/11_plot_evapotranspiration.py"
else
    echo "  -> Skip: 'data/raw_telemetry/ee-chart_et.csv' not found. Run GEE script 10 first."
fi

echo ""
echo "=================================================="
echo "Pipeline complete."
echo "=================================================="
echo ""
echo "Manual steps remaining in GEE Code Editor:"
echo "  1. Run 04_gee_ndvi_pipeline.js          -> Save to: data/raw_telemetry/ee-chart_ndvi.csv"
echo "  2. Run 06_gee_thermal_pipeline.js       -> Save to: data/raw_telemetry/ee-chart_lst.csv"
echo "  3. Run 06b_gee_thermal_sensitivity.js   -> Save to: data/raw_telemetry/ee-chart_lst_sensitivity.csv"
echo "  4. Run 08_gee_transect_decay.js         -> Save to: data/raw_telemetry/ee-chart_decay.csv"
echo "  5. Run 10_gee_evapotranspiration.js     -> Save to: data/raw_telemetry/ee-chart_et.csv"
echo "  Then re-run this script to generate all charts."
