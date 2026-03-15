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
echo "=================================================="
echo "Pipeline complete."
echo "=================================================="
echo ""
echo "Manual steps remaining:"
echo "  1. Run 04_gee_ndvi_pipeline.js in GEE Code Editor"
echo "     -> Save downloaded CSV as: data/raw_telemetry/ee-chart_ndvi.csv"
echo "  2. Run 06_gee_thermal_pipeline.js in GEE Code Editor"
echo "     -> Save downloaded CSV as: data/raw_telemetry/ee-chart_lst.csv"
echo "  3. Re-run this pipeline script or execute 07_plot_thermal_chart.py directly"
