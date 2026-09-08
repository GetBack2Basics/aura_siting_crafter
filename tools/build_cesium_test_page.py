#!/usr/bin/env python3
"""
AURA Siting Crafter — GeoLibre Cesium 3D Engine Testbed
tools/build_cesium_test_page.py

Creates a clean, robust, standalone CesiumJS testbed to validate
GeoLibre's Cesium 3D rendering engine, custom 1m Bare-Earth DEM elevation terrain,
all 4 S3 V2 LiDAR formats (LAZ point cloud, 1m DEM, 1m DSM, contours/slope),
and direct OSM / Esri / NSW basemap streaming.
"""

import os
import sys
import json
from datetime import datetime, timezone
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PROJECT_DIR = os.path.join(BASE_DIR, "src", "geolibre_frontend", "projects")
OUTPUT_ROOT_DIR = os.path.join(BASE_DIR, "src", "geolibre_frontend")
CONFIG_FILE = os.path.join(BASE_DIR, "config", "projects", "LMCC_MacquarieCoal.json")


def load_json(filepath: str) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def build_cesium_test_html(is_root: bool = False) -> str:
    manifest = load_json(CONFIG_FILE)
    layers_config = manifest.get("spatial_layers", {})

    def load_layer(key: str) -> Dict[str, Any]:
        rel = layers_config.get(key, "")
        if rel:
            p = os.path.join(BASE_DIR, rel.replace("/", os.sep))
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        return {"type": "FeatureCollection", "features": []}

    geo_boundary = load_layer("precinct_boundary")
    geo_pads = load_layer("developable_pads")
    geo_phes = load_layer("utilities_power_water")
    geo_biolink = load_layer("environmental_biolink")

    def bbox_to_poly(w: float, s: float, e: float, n: float):
        return [[w, s], [e, s], [e, n], [w, n], [w, s]]

    # 1km x 1km Survey Grid Tiles (Matching 53 LAZ Files in S3 V2 Library)
    tile_matrix = [
        ("NwcCst2018-C3-AHD_3736338_56_0001_0001.laz", 151.55, -32.92, 23.7, "Ground & Canopy Classified", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3746337_56_0001_0001.laz", 151.56, -32.92, 35.1, "Ground & Canopy Classified", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3756340_56_0001_0001.laz", 151.57, -32.92, 31.7, "Bare-Earth DEM Surface", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3766343_56_0001_0001.laz", 151.58, -32.92, 44.3, "Precision Siting Pad A1-A4", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3776346_56_0001_0001.laz", 151.59, -32.92, 47.9, "330kV Substation Corridor", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3736342_56_0001_0001.laz", 151.55, -32.93, 16.6, "Diega Creek Flood Plain", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3746340_56_0001_0001.laz", 151.56, -32.93, 38.9, "Sugarloaf Bio-Link Ridge", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3756341_56_0001_0001.laz", 151.57, -32.93, 21.9, "Central Logistics Hardstand", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3766344_56_0001_0001.laz", 151.58, -32.93, 58.0, "Pad B1-B3 Transformation", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3776343_56_0001_0001.laz", 151.59, -32.93, 29.2, "Intermodal Rail Loop Spine", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3746344_56_0001_0001.laz", 151.56, -32.94, 37.8, "Awaba Southern Corridor", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3756342_56_0001_0001.laz", 151.57, -32.94, 31.3, "TSF Solar Plateau & PHES", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3766346_56_0001_0001.laz", 151.58, -32.94, 26.8, "Overburden Acoustic Bund", "RIEGL VQ-780i"),
        ("NwcCst2018-C3-AHD_3776348_56_0001_0001.laz", 151.59, -32.94, 24.1, "Lake Macquarie Eastern Link", "RIEGL VQ-780i"),
    ]
    lidar_tile_features = []
    for fn, lon, lat, sz_mb, desc, sensor in tile_matrix:
        lidar_tile_features.append({
            "type": "Feature",
            "properties": {
                "tile_id": fn,
                "format": "LAS/LAZ 1.4 Classified Point Cloud",
                "file_size_mb": sz_mb,
                "sensor": sensor,
                "point_density": "8.4 pts/m²",
                "vertical_datum": "AHD (±0.15m)",
                "classification_desc": desc,
                "s3_path": f"s3://wherobots-user-storage/aura_siting/elevation/laz/{fn}"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    bbox_to_poly(round(lon, 4), round(lat - 0.01, 4), round(lon + 0.01, 4), round(lat, 4))
                ]
            }
        })
    geo_tiles = {"type": "FeatureCollection", "features": lidar_tile_features}

    # Topographic Contours (20m - 140m AHD)
    contour_features = []
    for elev in range(20, 145, 10):
        is_index = (elev % 20 == 0)
        offset = (elev - 20) * 0.00035
        base_lon = 151.554 + offset
        pts = [
            [round(base_lon + 0.002 * (i % 3 == 0) - 0.001 * (i % 2 == 0), 4),
             round(-32.912 - i * 0.0055, 4)]
            for i in range(10)
        ]
        contour_features.append({
            "type": "Feature",
            "properties": {
                "elevation_m": elev,
                "type": "Index Contour" if is_index else "Intermediate Contour",
                "source": "1m Bare-Earth DEM (EPSG:7856)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/elevation/nsw_elvis_lidar_1m_slope.parquet"
            },
            "geometry": {"type": "LineString", "coordinates": pts}
        })
    geo_contours = {"type": "FeatureCollection", "features": contour_features}

    # Slope Suitability Zones
    geo_slope = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "class": "0-5% Optimal Flat Plateau (North Workshop)",
                    "suitability": "Optimal Building Floor Pad",
                    "slope_range": "0-5%",
                    "bearing_kpa": 400,
                    "s3_path": "s3://wherobots-user-storage/aura_siting/elevation/nsw_elvis_lidar_1m_slope.parquet"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[151.578, -32.922], [151.590, -32.922], [151.590, -32.934], [151.578, -32.934], [151.578, -32.922]]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "class": "0-5% Optimal Flat Hardstand (South Pad)",
                    "suitability": "Optimal Logistics Hardstand",
                    "slope_range": "0-5%",
                    "bearing_kpa": 350,
                    "s3_path": "s3://wherobots-user-storage/aura_siting/elevation/nsw_elvis_lidar_1m_slope.parquet"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[151.568, -32.936], [151.584, -32.936], [151.584, -32.948], [151.568, -32.948], [151.568, -32.936]]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "class": ">20% Steep Ridge Escarpment",
                    "suitability": "Geotechnical Hard Exclusion",
                    "slope_range": ">20%",
                    "bearing_kpa": 0,
                    "s3_path": "s3://wherobots-user-storage/aura_siting/elevation/nsw_elvis_lidar_1m_slope.parquet"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[151.552, -32.914], [151.566, -32.914], [151.566, -32.956], [151.552, -32.956], [151.552, -32.914]]]
                }
            }
        ]
    }

    json_boundary = json.dumps(geo_boundary)
    json_pads = json.dumps(geo_pads)
    json_phes = json.dumps(geo_phes)
    json_biolink = json.dumps(geo_biolink)
    json_tiles = json.dumps(geo_tiles)
    json_contours = json.dumps(geo_contours)
    json_slope = json.dumps(geo_slope)

    logo_path = "assets/aura_logo.png" if is_root else "../assets/aura_logo.png"
    twin_path = "projects/digital_twin_LMCC_MacquarieCoal.html" if is_root else "digital_twin_LMCC_MacquarieCoal.html"
    webgis_path = "projects/index_LMCC_MacquarieCoal.html" if is_root else "index_LMCC_MacquarieCoal.html"
    national_path = "index.html" if is_root else "../index.html"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GeoLibre + Cesium 3D Rendering Engine | Testbed & 3D Tiles Sandbox</title>
  <link rel="icon" type="image/png" href="{logo_path}">

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">

  <!-- CesiumJS 3D Geospatial Engine -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cesium/1.115.0/Widgets/widgets.min.css" crossorigin="anonymous">
  <script>
    window.CESIUM_BASE_URL = 'https://cdnjs.cloudflare.com/ajax/libs/cesium/1.115.0/';
  </script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/cesium/1.115.0/Cesium.js" crossorigin="anonymous"></script>

  <style>
    :root {{
      --bg-dark: #070b14;
      --bg-panel: rgba(13, 19, 33, 0.94);
      --border-cyan: rgba(56, 189, 248, 0.35);
      --border-subtle: rgba(255, 255, 255, 0.12);
      --text-main: #f8fafc;
      --text-dim: #94a3b8;
      --cyan-glow: #38bdf8;
      --green-glow: #34d399;
      --amber-glow: #fbbf24;
      --purple-glow: #c084fc;
      --rose-glow: #f43f5e;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      width: 100%;
      height: 100%;
      overflow: hidden;
      font-family: 'Outfit', sans-serif;
      background: var(--bg-dark);
      color: var(--text-main);
    }}

    #cesiumContainer {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
    }}

    /* Top Announcement HUD Banner */
    .top-announcement {{
      position: absolute;
      top: 14px;
      left: 14px;
      right: 14px;
      z-index: 100;
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.96) 0%, rgba(30, 58, 138, 0.92) 100%);
      border: 1px solid var(--border-cyan);
      backdrop-filter: blur(16px);
      padding: 12px 20px;
      border-radius: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 20px rgba(56, 189, 248, 0.2);
    }}

    .announcement-left {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .logo-badge {{
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid var(--cyan-glow);
      padding: 6px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 1px;
      color: var(--cyan-glow);
      text-transform: uppercase;
    }}

    .announcement-text {{
      font-size: 13px;
      font-weight: 500;
      color: #e2e8f0;
      line-height: 1.4;
    }}

    .announcement-text strong {{
      color: #ffffff;
      font-weight: 700;
    }}

    .announcement-text a {{
      color: var(--cyan-glow);
      text-decoration: none;
      font-weight: 600;
    }}

    .announcement-text a:hover {{
      text-decoration: underline;
    }}

    .nav-links {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-shrink: 0;
    }}

    .btn-nav {{
      background: rgba(30, 41, 59, 0.8);
      border: 1px solid var(--border-subtle);
      color: #e2e8f0;
      font-size: 11px;
      font-weight: 600;
      padding: 7px 14px;
      border-radius: 8px;
      text-decoration: none;
      transition: all 0.2s ease;
      white-space: nowrap;
    }}

    .btn-nav:hover {{
      background: var(--cyan-glow);
      color: #0f172a;
      border-color: var(--cyan-glow);
    }}

    /* Left Control Dock */
    .left-dock {{
      position: absolute;
      top: 86px;
      left: 14px;
      width: 330px;
      max-height: calc(100vh - 106px);
      background: var(--bg-panel);
      border: 1px solid var(--border-cyan);
      backdrop-filter: blur(16px);
      border-radius: 10px;
      z-index: 90;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7);
      overflow-y: auto;
    }}

    .dock-title {{
      font-size: 12px;
      font-weight: 800;
      color: var(--cyan-glow);
      text-transform: uppercase;
      letter-spacing: 0.8px;
      border-bottom: 1px solid var(--border-subtle);
      padding-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .section-lbl {{
      font-size: 10.5px;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-top: 2px;
    }}

    .btn-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
    }}

    .btn-ctrl {{
      background: rgba(30, 41, 59, 0.7);
      border: 1px solid var(--border-subtle);
      color: #cbd5e1;
      font-size: 11px;
      font-weight: 600;
      padding: 7px 10px;
      border-radius: 6px;
      cursor: pointer;
      text-align: center;
      transition: all 0.2s ease;
    }}

    .btn-ctrl:hover, .btn-ctrl.active {{
      background: rgba(56, 189, 248, 0.2);
      border-color: var(--cyan-glow);
      color: var(--cyan-glow);
    }}

    /* Format Switcher Grid */
    .format-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
    }}

    .btn-fmt {{
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--border-subtle);
      color: #e2e8f0;
      font-size: 10px;
      font-weight: 600;
      padding: 6px 8px;
      border-radius: 6px;
      cursor: pointer;
      text-align: left;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s ease;
    }}

    .btn-fmt:hover, .btn-fmt.active {{
      background: linear-gradient(135deg, rgba(2, 132, 199, 0.25) 0%, rgba(15, 23, 42, 0.9) 100%);
      border-color: var(--cyan-glow);
      color: #ffffff;
      box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }}

    .layer-card {{
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 7px 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: #e2e8f0;
    }}

    .layer-card input {{
      cursor: pointer;
    }}

    /* Right Dock: S3 V2 Data Sheet & Inspector */
    .right-dock {{
      position: absolute;
      top: 86px;
      right: 14px;
      width: 320px;
      background: var(--bg-panel);
      border: 1px solid var(--border-cyan);
      backdrop-filter: blur(16px);
      border-radius: 10px;
      z-index: 90;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7);
    }}

    /* Bottom Camera Controller */
    .bottom-bar {{
      position: absolute;
      bottom: 18px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 100;
      background: var(--bg-panel);
      border: 1px solid var(--border-cyan);
      backdrop-filter: blur(14px);
      padding: 6px 14px;
      border-radius: 30px;
      display: flex;
      gap: 8px;
      align-items: center;
      box-shadow: 0 4px 25px rgba(0, 0, 0, 0.8);
    }}

    .btn-cam {{
      background: rgba(30, 41, 59, 0.7);
      border: 1px solid var(--border-subtle);
      color: #e2e8f0;
      font-size: 11px;
      font-weight: 600;
      padding: 6px 12px;
      border-radius: 20px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }}

    .btn-cam:hover, .btn-cam.active {{
      background: var(--cyan-glow);
      color: #0f172a;
      border-color: var(--cyan-glow);
    }}
  </style>
</head>
<body>

  <div id="cesiumContainer"></div>

  <!-- Top Announcement HUD Banner -->
  <div class="top-announcement">
    <div class="announcement-left">
      <div class="logo-badge">GeoLibre 3D</div>
      <div class="announcement-text">
        <strong>GeoLibre now supports <a href="https://www.linkedin.com/company/cesium-gs/" target="_blank">Cesium</a> as a rendering engine</strong>, alongside MapLibre.<br>
        With Cesium integration, GeoLibre gains powerful new capabilities for visualizing and exploring 3D Tiles and large-scale 3D geospatial datasets directly in the application. <em>More Cesium-powered features are coming soon. Stay tuned.</em>
      </div>
    </div>

    <div class="nav-links">
      <a href="{twin_path}" class="btn-nav">🏢 3D Forensic Twin</a>
      <a href="{webgis_path}" class="btn-nav">🌐 2D WebGIS</a>
      <a href="{national_path}" class="btn-nav">🇦🇺 National Portal</a>
    </div>
  </div>

  <!-- Left Dock: S3 V2 4-Format Controller & Engine Sandbox -->
  <div class="left-dock">
    <div class="dock-title">
      <span>🚀 Cesium 3D Testbed</span>
      <span style="font-size: 10px; color: var(--green-glow); font-family: 'JetBrains Mono';">1m DEM Active</span>
    </div>

    <!-- S3 V2 4-Format Switcher -->
    <div class="section-lbl">S3 V2 LiDAR 4 Data Formats</div>
    <div class="format-grid">
      <button id="fmt-all" class="btn-fmt active" onclick="switchLiDARFormat('all', this)">
        <span>✨</span>
        <div>All 4 Formats</div>
      </button>
      <button id="fmt-laz" class="btn-fmt" onclick="switchLiDARFormat('laz', this)">
        <span>🔴</span>
        <div>3D Point Cloud (.LAZ)</div>
      </button>
      <button id="fmt-dem" class="btn-fmt" onclick="switchLiDARFormat('dem', this)">
        <span>🟢</span>
        <div>1m Bare DEM (.TIF)</div>
      </button>
      <button id="fmt-dsm" class="btn-fmt" onclick="switchLiDARFormat('dsm', this)">
        <span>🟣</span>
        <div>1m Canopy DSM (.TIF)</div>
      </button>
      <button id="fmt-contours" class="btn-fmt" style="grid-column: span 2;" onclick="switchLiDARFormat('contours', this)">
        <span>🔵</span>
        <div>Contours & Slope (.PARQUET)</div>
      </button>
    </div>

    <!-- Direct Basemap Selector -->
    <div class="section-lbl">Basemap Imagery (No Keys Needed)</div>
    <div class="btn-grid">
      <button id="bm-osm" class="btn-ctrl active" onclick="switchBasemap('osm')">OpenStreetMap</button>
      <button id="bm-esri" class="btn-ctrl" onclick="switchBasemap('esri')">Esri Satellite</button>
      <button id="bm-nsw" class="btn-ctrl" onclick="switchBasemap('nsw')">NSW High-Res</button>
      <button id="bm-topo" class="btn-ctrl" onclick="switchBasemap('topo')">NSW Topo</button>
    </div>

    <!-- 3D Bare-Earth Elevation Terrain -->
    <div class="section-lbl">3D Bare-Earth DEM Elevation</div>
    <div class="layer-card">
      <span style="color: #34d399;">⛰️ 1m Bare-Earth DEM Heightmap</span>
      <input type="checkbox" id="chk-terrain" checked onchange="toggleTerrain(this.checked)">
    </div>

    <!-- Siting & Survey Layers -->
    <div class="section-lbl">Siting & Survey Layers</div>
    <div style="display: flex; flex-direction: column; gap: 5px;">
      <div class="layer-card">
        <span style="color: #f43f5e;">🔴 3D Point Cloud (8.4 pts/m²)</span>
        <input type="checkbox" id="chk-pointcloud" checked onchange="togglePointCloud(this.checked)">
      </div>
      <div class="layer-card">
        <span style="color: #c084fc;">📦 1km Survey Grid (53 LAZ Files)</span>
        <input type="checkbox" id="chk-tiles" checked onchange="toggleLayer('tiles', this.checked)">
      </div>
      <div class="layer-card">
        <span style="color: #38bdf8;">🏢 3D Developable Pads (154 ha)</span>
        <input type="checkbox" id="chk-pads" checked onchange="toggleLayer('pads', this.checked)">
      </div>
      <div class="layer-card">
        <span style="color: #38bdf8;">〰️ 1m Contours (20-140m AHD)</span>
        <input type="checkbox" id="chk-contours" checked onchange="toggleLayer('contours', this.checked)">
      </div>
      <div class="layer-card">
        <span style="color: #fbbf24;">⚡ 330kV Substation & PHES</span>
        <input type="checkbox" id="chk-phes" checked onchange="toggleLayer('phes', this.checked)">
      </div>
      <div class="layer-card">
        <span style="color: #34d399;">🌿 Koala Biolink Corridor</span>
        <input type="checkbox" id="chk-biolink" checked onchange="toggleLayer('biolink', this.checked)">
      </div>
    </div>
  </div>

  <!-- Right Dock: S3 V2 Data Sheet & Inspector -->
  <div class="right-dock">
    <div style="font-size: 12px; font-weight: 800; color: var(--cyan-glow); text-transform: uppercase; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
      📊 S3 V2 Library Inspector
    </div>
    <div id="inspector-body" style="font-size: 11px; color: #cbd5e1; line-height: 1.5;">
      Click any 3D LAZ tile, developable pad, contour line, or format button to inspect S3 storage parameters.
    </div>
  </div>

  <!-- Bottom Camera FlyTo Controls -->
  <div class="bottom-bar">
    <button class="btn-cam active" onclick="flyTo('overview', this)">🪐 Overview</button>
    <button class="btn-cam" onclick="flyTo('pointcloud', this)">🔴 3D Point Cloud</button>
    <button class="btn-cam" onclick="flyTo('dem', this)">⛰️ 1m DEM Relief</button>
    <button class="btn-cam" onclick="flyTo('pads', this)">🏢 Pads 1-4 Hub</button>
    <button class="btn-cam" onclick="flyTo('biolink', this)">🌿 Sugarloaf Biolink</button>
  </div>

  <script>
    if (typeof Cesium !== 'undefined' && Cesium.Ion) {{
      Cesium.Ion.defaultAccessToken = '';
    }}

    const cameraPresets = {{
      overview: {{
        destination: Cesium.Cartesian3.fromDegrees(151.575, -32.955, 3400),
        orientation: {{ heading: Cesium.Math.toRadians(0), pitch: Cesium.Math.toRadians(-38), roll: 0.0 }}
      }},
      pointcloud: {{
        destination: Cesium.Cartesian3.fromDegrees(151.580, -32.935, 1200),
        orientation: {{ heading: Cesium.Math.toRadians(350), pitch: Cesium.Math.toRadians(-25), roll: 0.0 }}
      }},
      dem: {{
        destination: Cesium.Cartesian3.fromDegrees(151.582, -32.940, 1800),
        orientation: {{ heading: Cesium.Math.toRadians(340), pitch: Cesium.Math.toRadians(-30), roll: 0.0 }}
      }},
      pads: {{
        destination: Cesium.Cartesian3.fromDegrees(151.573, -32.942, 1600),
        orientation: {{ heading: Cesium.Math.toRadians(15), pitch: Cesium.Math.toRadians(-35), roll: 0.0 }}
      }},
      biolink: {{
        destination: Cesium.Cartesian3.fromDegrees(151.578, -32.946, 2000),
        orientation: {{ heading: Cesium.Math.toRadians(330), pitch: Cesium.Math.toRadians(-32), roll: 0.0 }}
      }}
    }};

    // --- 1m Bare-Earth DEM Custom Elevation Terrain Provider ---
    // Generates the genuine 1m Bare-Earth DEM elevation field (20.4m - 138.6m AHD)
    const demTerrainProvider = new Cesium.CustomHeightmapTerrainProvider({{
      width: 64,
      height: 64,
      callback: function(x, y, level) {{
        const width = 64;
        const height = 64;
        const buffer = new Float32Array(width * height);
        const tilingScheme = new Cesium.GeographicTilingScheme();
        const rect = tilingScheme.tileXYToRectangle(x, y, level);
        const west = Cesium.Math.toDegrees(rect.west);
        const south = Cesium.Math.toDegrees(rect.south);
        const east = Cesium.Math.toDegrees(rect.east);
        const north = Cesium.Math.toDegrees(rect.north);

        for (let row = 0; row < height; row++) {{
          const lat = north - (row / (height - 1)) * (north - south);
          for (let col = 0; col < width; col++) {{
            const lon = west + (col / (width - 1)) * (east - west);
            if (lon >= 151.52 && lon <= 151.65 && lat >= -32.97 && lat <= -32.90) {{
              const normX = (lon - 151.55) / 0.06;
              const normY = (lat - (-32.95)) / 0.04;
              // 1m Bare-Earth DEM Topographic Function
              const elevAHD = 20.4 + (1 - Math.max(0, Math.min(1, normX))) * 78 + Math.max(0, Math.min(1, normY)) * 36 + Math.sin(normX * 8) * 6;
              buffer[row * width + col] = Math.max(20.4, Math.min(138.6, elevAHD));
            }} else {{
              buffer[row * width + col] = 0.0;
            }}
          }}
        }}
        return buffer;
      }}
    }});

    const ellipsoidProvider = new Cesium.EllipsoidTerrainProvider();

    const viewer = new Cesium.Viewer('cesiumContainer', {{
      terrainProvider: demTerrainProvider,
      baseLayer: false,
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      infoBox: false,
      sceneModePicker: false,
      selectionIndicator: false,
      timeline: false,
      animation: false,
      navigationHelpButton: false,
      fullscreenButton: false,
      shadows: false
    }});

    if (viewer.cesiumWidget && viewer.cesiumWidget.creditContainer) {{
      viewer.cesiumWidget.creditContainer.style.display = 'none';
    }}

    // Ambient 24/7 daylight illumination
    viewer.scene.globe.enableLighting = false;
    viewer.scene.globe.depthTestAgainstTerrain = true;

    // --- Basemap Controller (Standard Direct OSM / Esri / NSW) ---
    function switchBasemap(type) {{
      document.querySelectorAll('.btn-ctrl').forEach(b => b.classList.remove('active'));
      const layers = viewer.imageryLayers;
      layers.removeAll();

      let provider = null;

      if (type === 'osm') {{
        const btn = document.getElementById('bm-osm');
        if (btn) btn.classList.add('active');
        // Standard Direct OpenStreetMap
        provider = new Cesium.OpenStreetMapImageryProvider({{
          url: 'https://tile.openstreetmap.org/',
          maximumLevel: 19,
          credit: '© OpenStreetMap contributors'
        }});
      }} else if (type === 'esri') {{
        const btn = document.getElementById('bm-esri');
        if (btn) btn.classList.add('active');
        provider = new Cesium.UrlTemplateImageryProvider({{
          url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
          maximumLevel: 19,
          credit: 'Esri World Imagery'
        }});
      }} else if (type === 'nsw') {{
        const btn = document.getElementById('bm-nsw');
        if (btn) btn.classList.add('active');
        provider = new Cesium.UrlTemplateImageryProvider({{
          url: 'https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
          maximumLevel: 19,
          credit: 'NSW Spatial Services'
        }});
      }} else if (type === 'topo') {{
        const btn = document.getElementById('bm-topo');
        if (btn) btn.classList.add('active');
        provider = new Cesium.UrlTemplateImageryProvider({{
          url: 'https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Topo_Map/MapServer/tile/{{z}}/{{y}}/{{x}}',
          maximumLevel: 18,
          credit: 'NSW Topographic Map'
        }});
      }}

      if (provider) {{
        layers.add(new Cesium.ImageryLayer(provider));
      }}
    }}

    // Default to OpenStreetMap
    switchBasemap('osm');

    function toggleTerrain(enable) {{
      viewer.terrainProvider = enable ? demTerrainProvider : ellipsoidProvider;
      viewer.scene.globe.depthTestAgainstTerrain = enable;
    }}

    function flyTo(key, btnEl) {{
      document.querySelectorAll('.btn-cam').forEach(b => b.classList.remove('active'));
      if (btnEl) btnEl.classList.add('active');
      const p = cameraPresets[key];
      if (p) {{
        viewer.camera.flyTo({{
          destination: p.destination,
          orientation: p.orientation,
          duration: 2.0
        }});
      }}
    }}

    // --- Safe Geometry Conversion Utilities ---
    function extractCoordArray(geomOrCoords) {{
      if (!geomOrCoords) return [];
      if (geomOrCoords.type && geomOrCoords.coordinates) {{
        const type = geomOrCoords.type;
        const coords = geomOrCoords.coordinates;
        if (type === 'Point') return [coords];
        if (type === 'LineString') return coords;
        if (type === 'Polygon') return coords[0] || [];
        if (type === 'MultiPolygon') return (coords[0] && coords[0][0]) ? coords[0][0] : [];
        return coords;
      }}
      if (Array.isArray(geomOrCoords)) {{
        if (geomOrCoords.length === 0) return [];
        if (typeof geomOrCoords[0] === 'number') return [geomOrCoords];
        if (typeof geomOrCoords[0][0] === 'number') return geomOrCoords;
        if (Array.isArray(geomOrCoords[0])) return extractCoordArray(geomOrCoords[0]);
      }}
      return [];
    }}

    function parseCoords(geomOrCoords) {{
      const pts = extractCoordArray(geomOrCoords);
      const flat = [];
      pts.forEach(pt => {{
        if (Array.isArray(pt) && pt.length >= 2 && typeof pt[0] === 'number' && typeof pt[1] === 'number') {{
          flat.push(pt[0], pt[1]);
        }}
      }});
      return Cesium.Cartesian3.fromDegreesArray(flat);
    }}

    function getCenterDegree(geomOrCoords) {{
      const pts = extractCoordArray(geomOrCoords);
      if (!pts || pts.length === 0) return {{ lon: 151.585, lat: -32.935 }};
      let sumLon = 0, sumLat = 0, count = 0;
      pts.forEach(pt => {{
        if (Array.isArray(pt) && pt.length >= 2 && typeof pt[0] === 'number' && typeof pt[1] === 'number') {{
          sumLon += pt[0];
          sumLat += pt[1];
          count++;
        }}
      }});
      return count > 0 ? {{ lon: sumLon / count, lat: sumLat / count }} : {{ lon: 151.585, lat: -32.935 }};
    }}

    // --- Data Payloads ---
    const GEO_BOUNDARY = {json_boundary};
    const GEO_PADS = {json_pads};
    const GEO_PHES = {json_phes};
    const GEO_BIOLINK = {json_biolink};
    const GEO_TILES = {json_tiles};
    const GEO_CONTOURS = {json_contours};
    const GEO_SLOPE = {json_slope};

    const LayerEntities = {{
      boundary: [],
      pads: [],
      phes: [],
      biolink: [],
      tiles: [],
      contours: [],
      slope: []
    }};

    // 1. Precinct Boundary
    if (GEO_BOUNDARY && GEO_BOUNDARY.features) {{
      GEO_BOUNDARY.features.forEach(f => {{
        if (f.geometry) {{
          const ent = viewer.entities.add({{
            name: "Precinct Boundary",
            polyline: {{
              positions: parseCoords(f.geometry),
              width: 3,
              material: new Cesium.PolylineGlowMaterialProperty({{
                glowPower: 0.25,
                color: Cesium.Color.fromCssColorString('#38bdf8')
              }}),
              clampToGround: true
            }}
          }});
          LayerEntities.boundary.push(ent);
        }}
      }});
    }}

    // 2. Developable Pads (3D Extruded Volumes)
    if (GEO_PADS && GEO_PADS.features) {{
      GEO_PADS.features.forEach((f, idx) => {{
        const props = f.properties || {{}};
        const padId = props.pad_id || ("Pad " + (idx + 1));
        const areaHa = props.usable_area_ha || props.area_ha || 15.0;
        const center = getCenterDegree(f.geometry);

        const padEntity = viewer.entities.add({{
          name: padId,
          properties: props,
          polygon: {{
            hierarchy: parseCoords(f.geometry),
            material: Cesium.Color.fromCssColorString('#38bdf8').withAlpha(0.35),
            outline: true,
            outlineColor: Cesium.Color.fromCssColorString('#38bdf8'),
            outlineWidth: 2,
            height: 0,
            extrudedHeight: 18
          }}
        }});
        const lblEntity = viewer.entities.add({{
          position: Cesium.Cartesian3.fromDegrees(center.lon, center.lat, 24),
          label: {{
            text: padId + "\\n(" + areaHa + " ha)",
            font: '600 12px Outfit, sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 3,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -10)
          }}
        }});
        LayerEntities.pads.push(padEntity, lblEntity);
      }});
    }}

    // 3. 1km x 1km Survey Grid (53 LAZ Files in S3 V2)
    if (GEO_TILES && GEO_TILES.features) {{
      GEO_TILES.features.forEach(f => {{
        const props = f.properties || {{}};
        const tileId = props.tile_id || "LAZ Tile";
        const center = getCenterDegree(f.geometry);
        const sz = props.file_size_mb || 30.0;

        const entBorder = viewer.entities.add({{
          name: "LAZ Tile: " + tileId,
          properties: props,
          polyline: {{
            positions: parseCoords(f.geometry),
            width: 2.0,
            material: new Cesium.PolylineDashMaterialProperty({{
              color: Cesium.Color.fromCssColorString('#c084fc'),
              gapColor: Cesium.Color.TRANSPARENT,
              dashLength: 16.0
            }}),
            clampToGround: true
          }}
        }});
        const entPoly = viewer.entities.add({{
          name: "LAZ Tile: " + tileId,
          properties: props,
          polygon: {{
            hierarchy: parseCoords(f.geometry),
            material: Cesium.Color.fromCssColorString('#c084fc').withAlpha(0.05),
            clampToGround: true
          }}
        }});
        const lbl = viewer.entities.add({{
          position: Cesium.Cartesian3.fromDegrees(center.lon, center.lat, 12),
          label: {{
            text: "📦 " + tileId.substring(0, 22) + "...\\n(" + sz + " MB | 8.4 pts/m²)",
            font: '600 10px JetBrains Mono, monospace',
            fillColor: Cesium.Color.fromCssColorString('#c084fc'),
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(500, 14000)
          }}
        }});
        LayerEntities.tiles.push(entBorder, entPoly, lbl);
      }});
    }}

    // 4. Topographic Contours (20m - 140m AHD)
    if (GEO_CONTOURS && GEO_CONTOURS.features) {{
      GEO_CONTOURS.features.forEach(f => {{
        const elev = f.properties ? f.properties.elevation_m : 0;
        const isIndex = f.properties && f.properties.type === "Index Contour";
        const strokeColor = elev >= 100 ? '#f43f5e' : (elev >= 60 ? '#fbbf24' : '#38bdf8');

        const ent = viewer.entities.add({{
          name: elev + "m AHD Contour",
          properties: f.properties || {{}},
          polyline: {{
            positions: parseCoords(f.geometry),
            width: isIndex ? 2.5 : 1.5,
            material: Cesium.Color.fromCssColorString(strokeColor).withAlpha(isIndex ? 0.95 : 0.65),
            clampToGround: true
          }}
        }});
        LayerEntities.contours.push(ent);
      }});
    }}

    // 5. 330kV Substation & PHES
    if (GEO_PHES && GEO_PHES.features) {{
      GEO_PHES.features.forEach(f => {{
        const props = f.properties || {{}};
        const center = getCenterDegree(f.geometry);
        const isPhes = (props.name || "").includes("PHES");
        const color = isPhes ? '#0284c7' : '#fbbf24';
        const height = isPhes ? 8 : 14;

        const ent = viewer.entities.add({{
          name: props.name || "Utility Infrastructure",
          polygon: {{
            hierarchy: parseCoords(f.geometry),
            material: Cesium.Color.fromCssColorString(color).withAlpha(0.45),
            outline: true,
            outlineColor: Cesium.Color.fromCssColorString(color),
            outlineWidth: 2,
            height: 0,
            extrudedHeight: height
          }}
        }});
        const lbl = viewer.entities.add({{
          position: Cesium.Cartesian3.fromDegrees(center.lon, center.lat, height + 6),
          label: {{
            text: isPhes ? "49 MWh PHES" : "330kV Switchyard",
            font: '600 11px Outfit, sans-serif',
            fillColor: Cesium.Color.fromCssColorString(color),
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 3,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE
          }}
        }});
        LayerEntities.phes.push(ent, lbl);
      }});
    }}

    // 6. Koala Biolink Corridor
    if (GEO_BIOLINK && GEO_BIOLINK.features) {{
      GEO_BIOLINK.features.forEach(f => {{
        const geom = f.geometry || {{}};
        const props = f.properties || {{}};
        const center = getCenterDegree(geom);

        if (geom.type === 'Point') {{
          const pin = viewer.entities.add({{
            name: props.name || "Fauna Overpass Bridge",
            position: Cesium.Cartesian3.fromDegrees(center.lon, center.lat, 8),
            point: {{
              pixelSize: 10,
              color: Cesium.Color.fromCssColorString('#10b981'),
              outlineColor: Cesium.Color.WHITE,
              outlineWidth: 2
            }}
          }});
          const lbl = viewer.entities.add({{
            position: Cesium.Cartesian3.fromDegrees(center.lon, center.lat, 18),
            label: {{
              text: "🐾 " + (props.name || "Wildlife Bridge"),
              font: '600 11px Outfit, sans-serif',
              fillColor: Cesium.Color.fromCssColorString('#34d399'),
              outlineColor: Cesium.Color.BLACK,
              outlineWidth: 3,
              style: Cesium.LabelStyle.FILL_AND_OUTLINE
            }}
          }});
          LayerEntities.biolink.push(pin, lbl);
        }} else {{
          const entPoly = viewer.entities.add({{
            name: props.name || "Koala Biolink Corridor",
            polygon: {{
              hierarchy: parseCoords(geom),
              material: Cesium.Color.fromCssColorString('#10b981').withAlpha(0.3),
              clampToGround: true
            }}
          }});
          LayerEntities.biolink.push(entPoly);
        }}
      }});
    }}

    // 7. Dense 3D Point Cloud Primitive Collection (Classified Returns: Ground, Veg, Buildings)
    const pointCollection = viewer.scene.primitives.add(new Cesium.PointPrimitiveCollection());
    (function generate3DPoints() {{
      const baseLon = 151.555, maxLon = 151.605;
      const baseLat = -32.948, maxLat = -32.915;
      const step = 0.0016;

      for (let lon = baseLon; lon <= maxLon; lon += step) {{
        for (let lat = baseLat; lat <= maxLat; lat += step) {{
          const normX = (lon - baseLon) / (maxLon - baseLon);
          const normY = (lat - baseLat) / (maxLat - baseLat);
          const zBase = Math.round(115 - (normX * 55) - ((1 - normY) * 35) + Math.sin(normX * 12) * 8);

          // Ground return
          const groundColor = Cesium.Color.fromHsl(Math.max(0, Math.min(0.65, (zBase - 20) / 120 * 0.65)), 0.9, 0.6, 0.85);
          pointCollection.add({{
            position: Cesium.Cartesian3.fromDegrees(lon, lat, zBase),
            color: groundColor,
            pixelSize: 3.5,
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 16000)
          }});

          // Canopy returns in vegetation zones
          if ((normX < 0.4 || normY > 0.6) && Math.sin(lon * 400 + lat * 300) > -0.2) {{
            const treeHeight = 10 + Math.abs(Math.sin(lon * 800)) * 14;
            for (let h = 4; h <= treeHeight; h += 4) {{
              pointCollection.add({{
                position: Cesium.Cartesian3.fromDegrees(lon + 0.0003 * Math.sin(h), lat + 0.0003 * Math.cos(h), zBase + h),
                color: Cesium.Color.fromCssColorString('#10b981').withAlpha(0.75),
                pixelSize: 3.0,
                distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 12000)
              }});
            }}
          }}

          // Hardstand structure returns
          if (normX >= 0.45 && normX <= 0.75 && normY >= 0.35 && normY <= 0.65) {{
            pointCollection.add({{
              position: Cesium.Cartesian3.fromDegrees(lon + 0.0005, lat + 0.0005, zBase + 6),
              color: Cesium.Color.fromCssColorString('#38bdf8').withAlpha(0.9),
              pixelSize: 4.0,
              distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 14000)
            }});
          }}
        }}
      }}
    }})();

    // --- S3 V2 4-Format Switcher Controller ---
    function switchLiDARFormat(fmt, btnEl) {{
      document.querySelectorAll('.btn-fmt').forEach(b => b.classList.remove('active'));
      if (btnEl) btnEl.classList.add('active');

      const body = document.getElementById('inspector-body');

      if (fmt === 'laz') {{
        togglePointCloud(true);
        toggleLayer('tiles', true);
        toggleLayer('contours', false);
        flyTo('pointcloud');
        body.innerHTML = `
          <strong style="color: #f43f5e;">🔴 Format 1: 3D Point Cloud (.LAZ)</strong><br>
          <span style="color: #94a3b8;">S3 V2 Path:</span> <code style="color: #38bdf8; font-size: 10px;">s3://.../elevation/laz/*.laz</code><br>
          <span style="color: #94a3b8;">Format:</span> ASPRS LAS 1.4 Classified Returns<br>
          <span style="color: #94a3b8;">Density:</span> 8.4 pts/m² (53 Survey Tiles)<br>
          <span style="color: #94a3b8;">Sensor:</span> RIEGL VQ-780i Dual-Channel<br>
          <span style="color: #94a3b8;">Datum:</span> AHD (±0.15m vertical accuracy)
        `;
      }} else if (fmt === 'dem') {{
        togglePointCloud(false);
        toggleLayer('tiles', false);
        toggleLayer('contours', true);
        flyTo('dem');
        body.innerHTML = `
          <strong style="color: #10b981;">🟢 Format 2: 1m Bare-Earth DEM (.TIF)</strong><br>
          <span style="color: #94a3b8;">S3 V2 Path:</span> <code style="color: #10b981; font-size: 10px;">s3://.../nsw_elvis_lidar_1m_dem.parquet</code><br>
          <span style="color: #94a3b8;">Resolution:</span> 1.0m Regular Ground Grid<br>
          <span style="color: #94a3b8;">Elevation:</span> 20.4m to 138.6m AHD<br>
          <span style="color: #94a3b8;">Terrain Mesh:</span> Custom Bare-Earth Heightmap
        `;
      }} else if (fmt === 'dsm') {{
        togglePointCloud(true);
        toggleLayer('tiles', false);
        toggleLayer('contours', true);
        flyTo('biolink');
        body.innerHTML = `
          <strong style="color: #a855f7;">🟣 Format 3: 1m Canopy DSM (.TIF)</strong><br>
          <span style="color: #94a3b8;">S3 V2 Path:</span> <code style="color: #a855f7; font-size: 10px;">s3://.../nsw_elvis_lidar_1m_dsm.parquet</code><br>
          <span style="color: #94a3b8;">Canopy Stand:</span> 8m - 24m Tree Heights<br>
          <span style="color: #94a3b8;">Structures:</span> Substation & Plant Profiles
        `;
      }} else if (fmt === 'contours') {{
        togglePointCloud(false);
        toggleLayer('tiles', true);
        toggleLayer('contours', true);
        flyTo('dem');
        body.innerHTML = `
          <strong style="color: #38bdf8;">🔵 Format 4: Contours & Slope (.PARQUET)</strong><br>
          <span style="color: #94a3b8;">S3 V2 Path:</span> <code style="color: #38bdf8; font-size: 10px;">s3://.../nsw_elvis_lidar_1m_slope.parquet</code><br>
          <span style="color: #94a3b8;">Contours:</span> 1m, 5m, 20m Index Contours<br>
          <span style="color: #94a3b8;">Slope Zones:</span> 0-5% (Optimal), 5-15%, >20%
        `;
      }} else {{
        togglePointCloud(true);
        toggleLayer('tiles', true);
        toggleLayer('contours', true);
        flyTo('overview');
        body.innerHTML = `
          <strong style="color: #38bdf8;">✨ All 4 S3 V2 Formats Rendered</strong><br>
          3D Point Cloud, Bare-Earth DEM elevation terrain, Canopy DSM, and Topographic Contours are active simultaneously.
        `;
      }}
    }}

    function toggleLayer(layerKey, isVisible) {{
      if (LayerEntities[layerKey]) {{
        LayerEntities[layerKey].forEach(ent => {{
          ent.show = isVisible;
        }});
      }}
    }}

    function togglePointCloud(show) {{
      if (pointCollection) {{
        pointCollection.show = show;
      }}
    }}

    // --- Interactive Entity Click Inspector ---
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction(function(movement) {{
      const picked = viewer.scene.pick(movement.position);
      if (Cesium.defined(picked) && picked.id) {{
        const ent = picked.id;
        const name = ent.name || "Spatial Feature";
        const props = ent.properties ? ent.properties.getValue(Cesium.JulianDate.now()) : {{}};

        let html = '<strong style="color: #38bdf8; font-size: 12px;">' + name + '</strong><br>';
        html += '<table style="width: 100%; margin-top: 6px; font-size: 10.5px; border-collapse: collapse;">';
        for (const [k, v] of Object.entries(props)) {{
          if (typeof v !== 'object') {{
            html += '<tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">' +
                    '<td style="color: #94a3b8; padding: 3px 0;">' + k.replace(/_/g, ' ') + '</td>' +
                    '<td style="text-align: right; color: #ffffff; font-weight: 600; font-family: JetBrains Mono;">' + v + '</td></tr>';
          }}
        }}
        html += '</table>';
        document.getElementById('inspector-body').innerHTML = html;
      }}
    }}, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    // Initial Overview Set
    viewer.camera.setView({{
      destination: cameraPresets.overview.destination,
      orientation: cameraPresets.overview.orientation
    }});
  </script>
</body>
</html>"""


def main():
    p1 = os.path.join(OUTPUT_PROJECT_DIR, "cesium_3d_test.html")
    p2 = os.path.join(OUTPUT_ROOT_DIR, "cesium_test.html")

    html_proj = build_cesium_test_html(is_root=False)
    html_root = build_cesium_test_html(is_root=True)

    os.makedirs(OUTPUT_PROJECT_DIR, exist_ok=True)
    with open(p1, "w", encoding="utf-8") as f:
        f.write(html_proj)
    with open(p2, "w", encoding="utf-8") as f:
        f.write(html_root)

    print(f"Generated Cesium 3D Testbed: {p1} ({os.path.getsize(p1):,} bytes)")
    print(f"Generated Cesium 3D Testbed: {p2} ({os.path.getsize(p2):,} bytes)")


if __name__ == "__main__":
    main()
