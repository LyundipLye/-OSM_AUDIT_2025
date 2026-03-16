# -*- coding: utf-8 -*-
"""
09_plot_transect_decay.py
Phase IV: Spatial Transect Analysis
Plots the Thermal Decay Curve (Distance Gradient) from the Impact Zone outwards.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.figure")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def render_decay_curve(csv_path, output_image_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {csv_path}")
        return

    required = ['Distance_m', 'Pre_LST_mean', 'Post_LST_mean']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[ERROR] CSV missing columns: {missing}")
        return

    # Sort and clean
    df = df.dropna(subset=['Distance_m', 'Pre_LST_mean', 'Post_LST_mean'])
    df = df.sort_values('Distance_m').reset_index(drop=True)
    
    dist = df['Distance_m'].values
    pre = df['Pre_LST_mean'].values
    post = df['Post_LST_mean'].values

    # ---------------------------------------------------------
    # 绘图逻辑
    # ---------------------------------------------------------
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 7), dpi=400)

    # 绘制基础衰减曲线
    ax.plot(dist, pre, color='#33CC33', linewidth=3, marker='o', markersize=6, 
            label='Pre-Construction (Summer 2016-2018)')
    ax.plot(dist, post, color='#FF4500', linewidth=3, marker='s', markersize=6,
            label='Post-Construction (Summer 2023-2025)')

    # 填充热力疤痕区域 (The Thermodynamic Scar)
    ax.fill_between(dist, pre, post, where=(post > pre), 
                    color='#FF4500', alpha=0.15, interpolate=True,
                    label='Advective Heat Spillover')

    # 添加 0m 边界参考线
    ax.axvline(x=0, color='#FFFFFF', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.text(5, max(max(pre), max(post)) * 0.99, 'Parking Lot Core', 
            fontsize=10, fontname='Courier New', color='#FFFFFF', rotation=90, va='top')

    # 核心样式
    ax.set_title('Spatial Transect (0-800m): Urban Heat Advection Decay',
                  fontsize=16, fontweight='bold', fontname='Courier New', color='white', pad=20)
    ax.set_xlabel('Distance from Impact Zone Boundary (meters)', fontsize=13, fontname='Courier New', color='#CCCCCC')
    ax.set_ylabel('Mean Summer LST (°C)', fontsize=13, fontname='Courier New', color='#FF8888')

    ax.legend(loc='upper right', frameon=True, facecolor='#111111', edgecolor='#444444', 
              prop={'family': 'Courier New', 'size': 11})
    
    ax.grid(True, color='#333333', linestyle=':', linewidth=1.5, alpha=0.6)
    ax.tick_params(axis='both', labelsize=11, colors='#AAAAAA')

    # 数据源和作者水印
    fig.text(0.98, 0.02,
             'Data: USGS Landsat 7+8+9 (100m) | Method: 50m Concentric Buffers | Author: H. Li',
             fontsize=9, color='#666666', ha='right', va='bottom', fontfamily='Helvetica')

    plt.tight_layout()
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"\\nSAVED TRANSECT: {output_image_path}")
    
    if os.environ.get('MPLBACKEND') != 'Agg':
        plt.show(block=False)

if __name__ == "__main__":
    input_csv = os.path.join(PROJECT_ROOT, 'data', 'raw_telemetry', 'ee-chart_decay.csv')
    output_png = os.path.join(PROJECT_ROOT, 'visualisations', 'spatial_transect_decay_chart.png')
    render_decay_curve(input_csv, output_png)
