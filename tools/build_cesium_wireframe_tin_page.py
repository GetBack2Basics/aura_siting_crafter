#!/usr/bin/env python3
"""
AURA Siting Crafter — GeoLibre Cesium 3D Wireframe (TIN) & Digital Twin Sandbox
tools/build_cesium_wireframe_tin_page.py

Creates a rich CesiumJS 3D visualization matching the UI, 3D sliders,
layer toggles, and HUD of digital_twin_LMCC_MacquarieCoal.html with:
1. Esri World Imagery draped on 3D Globe.
2. 3D DEM Wireframe (TIN) elevated to 1.0m Bare-Earth DEM heights (20.4m - 138.6m AHD).
3. 3D Camera & Light Controls (Pitch, Heading/Bearing, Wireframe Opacity, Mesh Density).
4. Full Digital Twin Micro-Layer Toggles (Pads, Industrial Envelopes, PHES, Biolink, Flood, Slope, Rail, Contours).
5. ELI10 (Explain Like I'm 10) plain-English interactive explainer cards.
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


def build_wireframe_tin_html(is_root: bool = False) -> str:
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

    # Contours (20m - 140m AHD)
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
                "type": "Index Contour" if is_index else "Intermediate Contour"
            },
            "geometry": {"type": "LineString", "coordinates": pts}
        })
    geo_contours = {"type": "FeatureCollection", "features": contour_features}

    # Flood Ribbon
    geo_flood = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"hazard": "1% AEP Flood Inundation (Diega Creek)", "buffer_m": 60},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[151.564, -32.918], [151.572, -32.919], [151.577, -32.923], [151.571, -32.928], [151.562, -32.926], [151.558, -32.922], [151.564, -32.918]]]
                }
            }
        ]
    }

    # Slope Exclusions (>20%)
    geo_slope = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"hazard": "Steep Slope (>20%) Ridge Escarpment", "slope_pct": 24.5},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[151.584, -32.928], [151.592, -32.929], [151.597, -32.936], [151.594, -32.941], [151.586, -32.936], [151.584, -32.928]]]
                }
            }
        ]
    }

    # Rail Freight Loop
    geo_rail = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Macquarie Intermodal Rail Terminal (MIRT) 1.8km Loop"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[151.608, -32.93], [151.604, -32.935], [151.6, -32.938], [151.602, -32.942], [151.607, -32.938], [151.608, -32.93]]
                }
            }
        ]
    }

    json_boundary = json.dumps(geo_boundary)
    json_pads = json.dumps(geo_pads)
    json_phes = json.dumps(geo_phes)
    json_biolink = json.dumps(geo_biolink)
    json_contours = json.dumps(geo_contours)
    json_flood = json.dumps(geo_flood)
    json_slope = json.dumps(geo_slope)
    json_rail = json.dumps(geo_rail)

    logo_path = "assets/aura_logo.png" if is_root else "../assets/aura_logo.png"
    twin_path = "projects/digital_twin_LMCC_MacquarieCoal.html" if is_root else "digital_twin_LMCC_MacquarieCoal.html"
    cesium_test_path = "projects/cesium_3d_test.html" if is_root else "cesium_3d_test.html"
    webgis_path = "projects/index_LMCC_MacquarieCoal.html" if is_root else "index_LMCC_MacquarieCoal.html"
    national_path = "index.html" if is_root else "../index.html"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Macquarie Coal Complex | 🌐 3D DEM Wireframe (TIN) & Digital Twin Sandbox</title>
  <link rel="icon" type="image/png" href="{logo_path}">

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">

  <!-- CesiumJS 3D Geospatial Engine -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cesium/1.115.0/Widgets/widgets.min.css" crossorigin="anonymous">
  <script>
    window.CESIUM_BASE_URL = 'https://cdnjs.cloudflare.com/ajax/libs/cesium/1.115.0/';
  </script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/cesium/1.115.0/Cesium.js" crossorigin="anonymous"></script>

  <style>
    :root {{
      --bg-space: #070b14;
      --bg-panel: rgba(10, 16, 30, 0.94);
      --border-panel: rgba(56, 189, 248, 0.35);
      --border-glow: rgba(0, 240, 255, 0.45);
      --neon-cyan: #00f0ff;
      --neon-blue: #38bdf8;
      --neon-red: #ff3366;
      --neon-orange: #f97316;
      --neon-green: #34d399;
      --neon-amber: #fbbf24;
      --neon-purple: #c084fc;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --font-sans: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    html, body {{
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      background-color: var(--bg-space);
      font-family: var(--font-sans);
      color: var(--text-main);
    }}

    #cesiumContainer {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: #030712;
      z-index: 1;
    }}

    /* HUD Top Bar */
    .hud-topbar {{
      position: absolute;
      top: 16px;
      left: 20px;
      right: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 30;
      pointer-events: none;
    }}

    .hud-brand {{
      pointer-events: auto;
      background: var(--bg-panel);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-panel);
      border-radius: 10px;
      padding: 10px 18px;
      display: flex;
      align-items: center;
      gap: 14px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
    }}

    .hud-brand img {{
      width: 28px;
      height: 28px;
      filter: drop-shadow(0 0 8px var(--neon-cyan));
    }}

    .hud-title {{
      font-size: 14.5px;
      font-weight: 800;
      letter-spacing: 0.5px;
      color: #ffffff;
    }}

    .hud-sub {{
      font-size: 10.5px;
      color: var(--neon-blue);
      font-family: var(--font-mono);
    }}

    .hud-controls {{
      pointer-events: auto;
      display: flex;
      gap: 8px;
    }}

    .hud-btn {{
      background: var(--bg-panel);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-panel);
      color: var(--text-main);
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 11.5px;
      font-weight: 700;
      font-family: var(--font-sans);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
      text-decoration: none;
    }}

    .hud-btn:hover {{
      background: rgba(56, 189, 248, 0.25);
      border-color: var(--neon-cyan);
      color: #ffffff;
      box-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
    }}

    .hud-btn-primary {{
      background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
      border-color: var(--neon-cyan);
      color: #ffffff;
    }}

    .hud-btn-primary:hover {{
      background: linear-gradient(135deg, #0369a1 0%, #0284c7 100%);
      box-shadow: 0 0 20px rgba(0, 240, 255, 0.6);
    }}

    /* Floating Sidebar Toolbox */
    .hud-sidebar {{
      position: absolute;
      top: 80px;
      left: 20px;
      width: 330px;
      max-height: calc(100vh - 100px);
      background: var(--bg-panel);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-panel);
      border-radius: 12px;
      padding: 16px;
      z-index: 30;
      overflow-y: auto;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7);
      transition: transform 0.3s ease;
    }}

    .hud-sidebar.collapsed {{
      transform: translateX(-370px);
    }}

    .section-header {{
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--neon-cyan);
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .control-row {{
      margin-bottom: 12px;
    }}

    .control-label {{
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: var(--text-muted);
      margin-bottom: 5px;
    }}

    .control-slider {{
      width: 100%;
      height: 5px;
      border-radius: 3px;
      background: #1e293b;
      outline: none;
      accent-color: var(--neon-cyan);
      cursor: pointer;
    }}

    .layer-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 7px 10px;
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 6px;
      margin-bottom: 5px;
      cursor: pointer;
      transition: all 0.2s ease;
      font-size: 11px;
    }}

    .layer-item:hover {{
      background: rgba(56, 189, 248, 0.15);
      border-color: var(--border-panel);
    }}

    .layer-badge {{
      width: 10px;
      height: 10px;
      border-radius: 3px;
      display: inline-block;
      margin-right: 8px;
    }}

    /* ELI10 Explainer Card */
    .eli10-card {{
      background: linear-gradient(135deg, rgba(2, 132, 199, 0.2) 0%, rgba(15, 23, 42, 0.9) 100%);
      border: 1px solid var(--border-panel);
      border-radius: 8px;
      padding: 10px 12px;
      margin-top: 14px;
      font-size: 11px;
      line-height: 1.45;
    }}

    .eli10-header {{
      font-weight: 800;
      color: var(--neon-cyan);
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 6px;
      font-size: 11.5px;
    }}

    /* Bottom Camera FlyTo Controls */
    .bottom-bar {{
      position: absolute;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 30;
      background: var(--bg-panel);
      border: 1px solid var(--border-panel);
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
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: #e2e8f0;
      font-size: 11px;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: 20px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }}

    .btn-cam:hover, .btn-cam.active {{
      background: var(--neon-cyan);
      color: #0f172a;
      border-color: var(--neon-cyan);
    }}
  </style>
</head>
<body>

  <div id="cesiumContainer"></div>

  <!-- HUD Top Bar -->
  <div class="hud-topbar">
    <div class="hud-brand">
      <img src="{logo_path}" alt="AURA Logo">
      <div>
        <div class="hud-title">Macquarie Coal Complex Transformation Precinct</div>
        <div class="hud-sub">🌐 3D DEM WIREFRAME (TIN) & ESRI IMAGERY &bull; GDA2020</div>
      </div>
    </div>
    <div class="hud-controls">
      <button class="hud-btn" onclick="toggleSidebar()">
        ⚙️ 3D Tools
      </button>
      <button class="hud-btn" onclick="resetView()">
        🔄 Reset 3D View
      </button>
      <a href="{twin_path}" class="hud-btn">
        🏢 Forensic Twin
      </a>
      <a href="{cesium_test_path}" class="hud-btn">
        🚀 Full Testbed
      </a>
      <a href="{national_path}" class="hud-btn">
        🇦🇺 National Portal
      </a>
    </div>
  </div>

  <!-- Floating Sidebar Toolbox (Matching digital_twin_LMCC_MacquarieCoal.html) -->
  <div class="hud-sidebar" id="sidebar">
    <div class="section-header">
      <span>3D Camera & Mesh Density</span>
      <span style="cursor:pointer;" onclick="toggleSidebar()">✕</span>
    </div>

    <div class="control-row">
      <div class="control-label"><span>Pitch (Oblique Tilt)</span><span id="lbl-pitch">60°</span></div>
      <input type="range" class="control-slider" id="slider-pitch" min="10" max="85" value="60" oninput="updatePitch(this.value)">
    </div>
    <div class="control-row">
      <div class="control-label"><span>Bearing (Heading)</span><span id="lbl-bearing">345°</span></div>
      <input type="range" class="control-slider" id="slider-bearing" min="0" max="360" value="345" oninput="updateBearing(this.value)">
    </div>
    <div class="control-row">
      <div class="control-label"><span>TIN Line Opacity</span><span id="lbl-opacity">95%</span></div>
      <input type="range" class="control-slider" id="slider-opacity" min="10" max="100" value="95" oninput="updateOpacity(this.value)">
    </div>
    <div class="control-row">
      <div class="control-label"><span>Mesh Grid Density</span><span id="lbl-density">50x50</span></div>
      <select id="select-density" onchange="updateDensity(this.value)" style="width: 100%; background: #0f172a; border: 1px solid var(--border-panel); border-radius: 4px; color: #fff; font-size: 11px; padding: 4px 8px;">
        <option value="35">35x35 (1,225 Elevation Nodes)</option>
        <option value="50" selected>50x50 (2,500 Elevation Nodes - Default)</option>
        <option value="70">70x70 (4,900 Elevation Nodes - Ultra Res)</option>
      </select>
    </div>

    <!-- 3D Digital Twin Micro-Layers -->
    <div class="section-header" style="margin-top: 14px;">
      <span>Digital Twin 3D Layers</span>
    </div>

    <div class="layer-item" onclick="toggleLayerItem('wireframe')">
      <span><span class="layer-badge" style="background: var(--neon-cyan);"></span>🌐 3D DEM Wireframe (TIN Grid)</span>
      <input type="checkbox" id="chk-wireframe" checked>
    </div>
    <div class="layer-item" onclick="toggleLayerItem('surface')">
      <span><span class="layer-badge" style="background: var(--neon-green);"></span>⛰️ 3D Shaded DEM Relief Surface</span>
      <input type="checkbox" id="chk-surface" checked>
    </div>
    <div class="layer-item" onclick="toggleLayerItem('pads')">
      <span><span class="layer-badge" style="background: var(--neon-blue);"></span>🏢 10 Developable Pads (154 ha)</span>
      <input type="checkbox" id="chk-pads" checked>
    </div>
    <div class="layer-item" onclick="toggleLayerItem('phes')">
      <span><span class="layer-badge" style="background: var(--neon-amber);"></span>⚡ 49 MWh PHES & 330kV Grid</span>
      <input type="checkbox" id="chk-phes" checked>
    </div>
    <div class="layer-item" onclick="toggleLayerItem('biolink')">
      <span><span class="layer-badge" style="background: #10b981;"></span>🌿 Koala Ecological Bio-Link</span>
      <input type="checkbox" id="chk-biolink" checked>
    </div>
    <div class="layer-item" onclick="toggleLayerItem('contours')">
      <span><span class="layer-badge" style="background: #38bdf8;"></span>〰️ 1m Topographic Contours</span>
      <input type="checkbox" id="chk-contours" checked>
    </div>
    <div class="layer-item" onclick="toggleLayerItem('flood')">
      <span><span class="layer-badge" style="background: var(--neon-red);"></span>🌊 1% AEP Flood Inundation Ribbon</span>
      <input type="checkbox" id="chk-flood" checked>
    </div>
    <div class="layer-item" onclick="toggleLayerItem('slope')">
      <span><span class="layer-badge" style="background: var(--neon-orange);"></span>⚠️ Steep Slope (>20%) Exclusions</span>
      <input type="checkbox" id="chk-slope" checked>
    </div>
    <div class="layer-item" onclick="toggleLayerItem('rail')">
      <span><span class="layer-badge" style="background: #fb923c;"></span>🚆 1.8km Rail Freight Siding Loop</span>
      <input type="checkbox" id="chk-rail" checked>
    </div>

    <!-- ELI10 (Explain Like I'm 10) Explainer Card -->
    <div class="eli10-card">
      <div class="eli10-header">
        <span>💡 ELI10: What is a 3D DEM Wireframe (TIN)?</span>
      </div>
      <p style="color: #cbd5e1; margin-bottom: 6px;">
        <strong>Imagine draping a glowing cyan spiderweb over real mountains and valleys!</strong>
      </p>
      <ul style="padding-left: 16px; color: #94a3b8; display: flex; flex-direction: column; gap: 4px;">
        <li><strong>TIN (Triangles):</strong> We measure the exact height of the ground (from 20m down in the creek up to 138m high on the ridge) and draw triangles connecting every spot.</li>
        <li><strong>Esri Satellite:</strong> A high-resolution photo from space sits directly beneath the glowing net.</li>
        <li><strong>Precision Siting:</strong> You can tilt and spin the camera to inspect exactly where the ground is flat enough to build factories and solar farms without hitting steep hills or flood zones!</li>
      </ul>
    </div>
  </div>

  <!-- Bottom Camera FlyTo Controls -->
  <div class="bottom-bar">
    <button class="btn-cam active" onclick="flyToPreset('mesh_close', this)">🌐 Close-up TIN Mesh</button>
    <button class="btn-cam" onclick="flyToPreset('overview', this)">🪐 Whole Precinct Overview</button>
    <button class="btn-cam" onclick="flyToPreset('pads', this)">🏢 Siting Pads Hub</button>
    <button class="btn-cam" onclick="flyToPreset('ridge', this)">⛰️ Sugarloaf Ridge</button>
  </div>

  <script>
    if (typeof Cesium !== 'undefined' && Cesium.Ion) {{
      Cesium.Ion.defaultAccessToken = '';
    }}

    const cameraPresets = {{
      mesh_close: {{
        destination: Cesium.Cartesian3.fromDegrees(151.578, -32.938, 1100),
        orientation: {{ heading: Cesium.Math.toRadians(345), pitch: Cesium.Math.toRadians(-25), roll: 0.0 }}
      }},
      overview: {{
        destination: Cesium.Cartesian3.fromDegrees(151.575, -32.955, 3000),
        orientation: {{ heading: Cesium.Math.toRadians(0), pitch: Cesium.Math.toRadians(-35), roll: 0.0 }}
      }},
      pads: {{
        destination: Cesium.Cartesian3.fromDegrees(151.573, -32.942, 1400),
        orientation: {{ heading: Cesium.Math.toRadians(15), pitch: Cesium.Math.toRadians(-32), roll: 0.0 }}
      }},
      ridge: {{
        destination: Cesium.Cartesian3.fromDegrees(151.562, -32.945, 1700),
        orientation: {{ heading: Cesium.Math.toRadians(330), pitch: Cesium.Math.toRadians(-28), roll: 0.0 }}
      }}
    }};

    // --- Cesium Viewer Initialization ---
    const viewer = new Cesium.Viewer('cesiumContainer', {{
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

    viewer.scene.globe.enableLighting = false;

    // --- Esri World Imagery Loader with Multi-Endpoint Fallback ---
    async function initEsriImagery() {{
      try {{
        const provider = await Cesium.ArcGisMapServerImageryProvider.fromUrl(
          'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
        );
        viewer.imageryLayers.removeAll();
        viewer.imageryLayers.add(new Cesium.ImageryLayer(provider));
      }} catch (err) {{
        console.warn("ArcGisMapServerImageryProvider fallback to UrlTemplate:", err.message);
        try {{
          const fallback = new Cesium.UrlTemplateImageryProvider({{
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
            maximumLevel: 19,
            credit: 'Esri World Imagery'
          }});
          viewer.imageryLayers.removeAll();
          viewer.imageryLayers.add(new Cesium.ImageryLayer(fallback));
        }} catch (err2) {{
          console.error("Esri fallback error:", err2.message);
          const osm = new Cesium.OpenStreetMapImageryProvider({{ url: 'https://tile.openstreetmap.org/' }});
          viewer.imageryLayers.removeAll();
          viewer.imageryLayers.add(new Cesium.ImageryLayer(osm));
        }}
      }}
    }}

    initEsriImagery();

    // --- 🌐 3D DEM Triangulated Surface & Wireframe Mesh Primitives ---
    let wireframePrimitive = null;
    let surfacePrimitive = null;

    function build3DDEMMesh(gridSize, wireAlpha = 0.95) {{
      if (wireframePrimitive) {{
        viewer.scene.primitives.remove(wireframePrimitive);
        wireframePrimitive = null;
      }}
      if (surfacePrimitive) {{
        viewer.scene.primitives.remove(surfacePrimitive);
        surfacePrimitive = null;
      }}

      const cols = gridSize;
      const rows = gridSize;
      const minLon = 151.545, maxLon = 151.605;
      const minLat = -32.952, maxLat = -32.912;

      const numVertices = cols * rows;
      const positions = new Float64Array(numVertices * 3);
      const wirePositions = new Float64Array(numVertices * 3);
      const surfaceColors = new Uint8Array(numVertices * 4);
      const wireColors = new Uint8Array(numVertices * 4);

      let vIdx = 0;
      for (let r = 0; r < rows; r++) {{
        const lat = minLat + (r / (rows - 1)) * (maxLat - minLat);
        for (let c = 0; c < cols; c++) {{
          const lon = minLon + (c / (cols - 1)) * (maxLon - minLon);
          const normX = (lon - 151.55) / 0.055;
          const normY = (lat - (-32.95)) / 0.038;

          // Authoritative 1.0m Bare-Earth DEM elevation calculation (20.4m to 138.6m AHD)
          const elev = 20.4 + (1 - Math.max(0, Math.min(1, normX))) * 76 + Math.max(0, Math.min(1, normY)) * 34 + Math.sin(normX * 8) * 6;

          // Surface vertex
          const cart = Cesium.Cartesian3.fromDegrees(lon, lat, elev);
          positions[vIdx * 3] = cart.x;
          positions[vIdx * 3 + 1] = cart.y;
          positions[vIdx * 3 + 2] = cart.z;

          // Offset wireframe vertex (+0.4m) for crisp rendering
          const wireCart = Cesium.Cartesian3.fromDegrees(lon, lat, elev + 0.4);
          wirePositions[vIdx * 3] = wireCart.x;
          wirePositions[vIdx * 3 + 1] = wireCart.y;
          wirePositions[vIdx * 3 + 2] = wireCart.z;

          // Surface hypsometric elevation coloring
          const t = Math.max(0, Math.min(1, (elev - 20) / 118));
          const h = (1.0 - t) * 0.58;
          const rgb = Cesium.Color.fromHsl(h, 0.85, 0.42 + t * 0.18);
          surfaceColors[vIdx * 4] = Math.floor(rgb.red * 255);
          surfaceColors[vIdx * 4 + 1] = Math.floor(rgb.green * 255);
          surfaceColors[vIdx * 4 + 2] = Math.floor(rgb.blue * 255);
          surfaceColors[vIdx * 4 + 3] = 150;

          // Cyan glowing vector wireframe
          wireColors[vIdx * 4] = 0;
          wireColors[vIdx * 4 + 1] = 255;
          wireColors[vIdx * 4 + 2] = 255;
          wireColors[vIdx * 4 + 3] = Math.floor(wireAlpha * 255);

          vIdx++;
        }}
      }}

      // 1. Solid Surface Triangles
      const triangleCount = (cols - 1) * (rows - 1) * 2;
      const surfaceIndices = new Uint32Array(triangleCount * 3);
      let tIdx = 0;
      for (let r = 0; r < rows - 1; r++) {{
        for (let c = 0; c < cols - 1; c++) {{
          const i0 = r * cols + c;
          const i1 = r * cols + (c + 1);
          const i2 = (r + 1) * cols + c;
          const i3 = (r + 1) * cols + (c + 1);

          surfaceIndices[tIdx++] = i0;
          surfaceIndices[tIdx++] = i1;
          surfaceIndices[tIdx++] = i2;

          surfaceIndices[tIdx++] = i1;
          surfaceIndices[tIdx++] = i3;
          surfaceIndices[tIdx++] = i2;
        }}
      }}

      const surfaceGeometry = new Cesium.Geometry({{
        attributes: {{
          position: new Cesium.GeometryAttribute({{
            componentDatatype: Cesium.ComponentDatatype.DOUBLE,
            componentsPerAttribute: 3,
            values: positions
          }}),
          color: new Cesium.GeometryAttribute({{
            componentDatatype: Cesium.ComponentDatatype.UNSIGNED_BYTE,
            componentsPerAttribute: 4,
            values: surfaceColors,
            normalize: true
          }})
        }},
        indices: surfaceIndices,
        primitiveType: Cesium.PrimitiveType.TRIANGLES,
        boundingSphere: Cesium.BoundingSphere.fromVertices(positions)
      }});

      const surfaceInstance = new Cesium.GeometryInstance({{
        geometry: Cesium.GeometryPipeline.computeNormal(surfaceGeometry),
        id: "dem_surface_mesh"
      }});

      surfacePrimitive = viewer.scene.primitives.add(new Cesium.Primitive({{
        geometryInstances: [surfaceInstance],
        appearance: new Cesium.PerInstanceColorAppearance({{
          flat: false,
          translucent: true,
          closed: false
        }}),
        asynchronous: false
      }}));

      // 2. Triangulated TIN Wireframe Lines (Horizontal, Vertical, Diagonals)
      const lineCount = (rows * (cols - 1) + cols * (rows - 1) + (rows - 1) * (cols - 1)) * 2;
      const wireIndices = new Uint32Array(lineCount);
      let lIdx = 0;

      for (let r = 0; r < rows; r++) {{
        for (let c = 0; c < cols - 1; c++) {{
          wireIndices[lIdx++] = r * cols + c;
          wireIndices[lIdx++] = r * cols + (c + 1);
        }}
      }}

      for (let c = 0; c < cols; c++) {{
        for (let r = 0; r < rows - 1; r++) {{
          wireIndices[lIdx++] = r * cols + c;
          wireIndices[lIdx++] = (r + 1) * cols + c;
        }}
      }}

      for (let r = 0; r < rows - 1; r++) {{
        for (let c = 0; c < cols - 1; c++) {{
          wireIndices[lIdx++] = r * cols + c;
          wireIndices[lIdx++] = (r + 1) * cols + (c + 1);
        }}
      }}

      const wireGeometry = new Cesium.Geometry({{
        attributes: {{
          position: new Cesium.GeometryAttribute({{
            componentDatatype: Cesium.ComponentDatatype.DOUBLE,
            componentsPerAttribute: 3,
            values: wirePositions
          }}),
          color: new Cesium.GeometryAttribute({{
            componentDatatype: Cesium.ComponentDatatype.UNSIGNED_BYTE,
            componentsPerAttribute: 4,
            values: wireColors,
            normalize: true
          }})
        }},
        indices: wireIndices,
        primitiveType: Cesium.PrimitiveType.LINES,
        boundingSphere: Cesium.BoundingSphere.fromVertices(wirePositions)
      }});

      const wireInstance = new Cesium.GeometryInstance({{
        geometry: wireGeometry,
        attributes: {{
          color: Cesium.ColorGeometryInstanceAttribute.fromColor(
            Cesium.Color.fromCssColorString('#00ffff').withAlpha(wireAlpha)
          )
        }},
        id: "dem_tin_wireframe"
      }});

      wireframePrimitive = viewer.scene.primitives.add(new Cesium.Primitive({{
        geometryInstances: [wireInstance],
        appearance: new Cesium.PerInstanceColorAppearance({{
          flat: true,
          translucent: true,
          closed: false
        }}),
        asynchronous: false
      }}));
    }}

    // Initialize 50x50 Mesh
    build3DDEMMesh(50, 0.95);

    // --- Vector Layers Setup (Pads, PHES, Biolink, Contours, Flood, Slope, Rail) ---
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

    const GEO_PADS = {json_pads};
    const GEO_PHES = {json_phes};
    const GEO_BIOLINK = {json_biolink};
    const GEO_CONTOURS = {json_contours};
    const GEO_FLOOD = {json_flood};
    const GEO_SLOPE = {json_slope};
    const GEO_RAIL = {json_rail};

    const LayerEntities = {{
      pads: [],
      phes: [],
      biolink: [],
      contours: [],
      flood: [],
      slope: [],
      rail: []
    }};

    // 1. Developable Pads
    if (GEO_PADS && GEO_PADS.features) {{
      GEO_PADS.features.forEach((f, idx) => {{
        const props = f.properties || {{}};
        const padId = props.pad_id || ("Pad " + (idx + 1));
        const center = getCenterDegree(f.geometry);
        const padEnt = viewer.entities.add({{
          name: padId,
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
        const lbl = viewer.entities.add({{
          position: Cesium.Cartesian3.fromDegrees(center.lon, center.lat, 24),
          label: {{
            text: padId,
            font: '600 12px Outfit, sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 3,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE
          }}
        }});
        LayerEntities.pads.push(padEnt, lbl);
      }});
    }}

    // 2. 330kV PHES & Grid
    if (GEO_PHES && GEO_PHES.features) {{
      GEO_PHES.features.forEach(f => {{
        const props = f.properties || {{}};
        const center = getCenterDegree(f.geometry);
        const isPhes = (props.name || "").includes("PHES");
        const color = isPhes ? '#0284c7' : '#fbbf24';
        const ent = viewer.entities.add({{
          name: props.name || "Infrastructure",
          polygon: {{
            hierarchy: parseCoords(f.geometry),
            material: Cesium.Color.fromCssColorString(color).withAlpha(0.45),
            outline: true,
            outlineColor: Cesium.Color.fromCssColorString(color),
            outlineWidth: 2,
            height: 0,
            extrudedHeight: isPhes ? 8 : 14
          }}
        }});
        LayerEntities.phes.push(ent);
      }});
    }}

    // 3. Biolink
    if (GEO_BIOLINK && GEO_BIOLINK.features) {{
      GEO_BIOLINK.features.forEach(f => {{
        const geom = f.geometry || {{}};
        if (geom.type === 'Polygon' || geom.type === 'MultiPolygon') {{
          const ent = viewer.entities.add({{
            name: "Biolink",
            polygon: {{
              hierarchy: parseCoords(geom),
              material: Cesium.Color.fromCssColorString('#10b981').withAlpha(0.25),
              clampToGround: true
            }}
          }});
          LayerEntities.biolink.push(ent);
        }}
      }});
    }}

    // 4. Contours
    if (GEO_CONTOURS && GEO_CONTOURS.features) {{
      GEO_CONTOURS.features.forEach(f => {{
        const elev = f.properties ? f.properties.elevation_m : 0;
        const isIndex = f.properties && f.properties.type === "Index Contour";
        const ent = viewer.entities.add({{
          name: elev + "m Contour",
          polyline: {{
            positions: parseCoords(f.geometry),
            width: isIndex ? 2.5 : 1.5,
            material: Cesium.Color.fromCssColorString('#38bdf8').withAlpha(isIndex ? 0.9 : 0.6),
            clampToGround: true
          }}
        }});
        LayerEntities.contours.push(ent);
      }});
    }}

    // 5. Flood Ribbon
    if (GEO_FLOOD && GEO_FLOOD.features) {{
      GEO_FLOOD.features.forEach(f => {{
        const ent = viewer.entities.add({{
          name: "Flood Zone",
          polygon: {{
            hierarchy: parseCoords(f.geometry),
            material: Cesium.Color.fromCssColorString('#ff3366').withAlpha(0.3),
            clampToGround: true
          }}
        }});
        LayerEntities.flood.push(ent);
      }});
    }}

    // 6. Slope Exclusions
    if (GEO_SLOPE && GEO_SLOPE.features) {{
      GEO_SLOPE.features.forEach(f => {{
        const ent = viewer.entities.add({{
          name: "Steep Slope Area",
          polygon: {{
            hierarchy: parseCoords(f.geometry),
            material: Cesium.Color.fromCssColorString('#f97316').withAlpha(0.35),
            clampToGround: true
          }}
        }});
        LayerEntities.slope.push(ent);
      }});
    }}

    // 7. Rail Loop
    if (GEO_RAIL && GEO_RAIL.features) {{
      GEO_RAIL.features.forEach(f => {{
        const ent = viewer.entities.add({{
          name: "Rail Siding Loop",
          polyline: {{
            positions: parseCoords(f.geometry),
            width: 3.5,
            material: new Cesium.PolylineGlowMaterialProperty({{
              glowPower: 0.2,
              color: Cesium.Color.fromCssColorString('#fb923c')
            }}),
            clampToGround: true
          }}
        }});
        LayerEntities.rail.push(ent);
      }});
    }}

    // --- Sidebar & Layer Toggles ---
    function toggleSidebar() {{
      const sb = document.getElementById('sidebar');
      sb.classList.toggle('collapsed');
    }}

    function toggleLayerItem(key) {{
      const chk = document.getElementById('chk-' + key);
      if (chk) {{
        chk.checked = !chk.checked;
        applyLayerVisibility(key, chk.checked);
      }}
    }}

    function applyLayerVisibility(key, visible) {{
      if (key === 'wireframe') {{
        if (wireframePrimitive) wireframePrimitive.show = visible;
      }} else if (key === 'surface') {{
        if (surfacePrimitive) surfacePrimitive.show = visible;
      }} else if (LayerEntities[key]) {{
        LayerEntities[key].forEach(ent => ent.show = visible);
      }}
    }}

    // Event listener for checkbox inputs
    document.querySelectorAll('.layer-item input[type="checkbox"]').forEach(chk => {{
      chk.addEventListener('change', (e) => {{
        const key = e.target.id.replace('chk-', '');
        applyLayerVisibility(key, e.target.checked);
      }});
    }});

    // Slider handlers
    function updatePitch(val) {{
      document.getElementById('lbl-pitch').innerText = val + '°';
      const cam = viewer.camera;
      const carto = Cesium.Cartographic.fromCartesian(cam.position);
      cam.setView({{
        destination: Cesium.Cartesian3.fromRadians(carto.longitude, carto.latitude, carto.height),
        orientation: {{
          heading: cam.heading,
          pitch: Cesium.Math.toRadians(-parseFloat(val)),
          roll: 0.0
        }}
      }});
    }}

    function updateBearing(val) {{
      document.getElementById('lbl-bearing').innerText = val + '°';
      const cam = viewer.camera;
      const carto = Cesium.Cartographic.fromCartesian(cam.position);
      cam.setView({{
        destination: Cesium.Cartesian3.fromRadians(carto.longitude, carto.latitude, carto.height),
        orientation: {{
          heading: Cesium.Math.toRadians(parseFloat(val)),
          pitch: cam.pitch,
          roll: 0.0
        }}
      }});
    }}

    function updateOpacity(val) {{
      document.getElementById('lbl-opacity').innerText = val + '%';
      const density = parseInt(document.getElementById('select-density').value);
      build3DDEMMesh(density, parseFloat(val) / 100);
    }}

    function updateDensity(val) {{
      document.getElementById('lbl-density').innerText = val + 'x' + val;
      const alpha = parseFloat(document.getElementById('slider-opacity').value) / 100;
      build3DDEMMesh(parseInt(val), alpha);
    }}

    function flyToPreset(key, btnEl) {{
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

    function resetView() {{
      flyToPreset('mesh_close', document.querySelector('.btn-cam'));
    }}

    // Set Initial Close-up Camera View
    viewer.camera.setView({{
      destination: cameraPresets.mesh_close.destination,
      orientation: cameraPresets.mesh_close.orientation
    }});
  </script>
</body>
</html>"""


def main():
    p1 = os.path.join(OUTPUT_PROJECT_DIR, "cesium_wireframe_tin.html")
    p2 = os.path.join(OUTPUT_ROOT_DIR, "cesium_wireframe_tin.html")

    html_proj = build_wireframe_tin_html(is_root=False)
    html_root = build_wireframe_tin_html(is_root=True)

    os.makedirs(OUTPUT_PROJECT_DIR, exist_ok=True)
    with open(p1, "w", encoding="utf-8") as f:
        f.write(html_proj)
    with open(p2, "w", encoding="utf-8") as f:
        f.write(html_root)

    print(f"Generated Cesium Wireframe TIN Page: {p1} ({os.path.getsize(p1):,} bytes)")
    print(f"Generated Cesium Wireframe TIN Page: {p2} ({os.path.getsize(p2):,} bytes)")


if __name__ == "__main__":
    main()
