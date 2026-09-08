#!/usr/bin/env python3
"""
AURA Siting Crafter — GeoLibre Cesium 3D Engine Testbed
tools/build_cesium_test_page.py

Creates a clean, robust, standalone CesiumJS test page to validate
GeoLibre's Cesium 3D rendering engine, 3D Tiles support, terrain streaming,
and large-scale geospatial datasets.
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

    json_boundary = json.dumps(geo_boundary)
    json_pads = json.dumps(geo_pads)
    json_phes = json.dumps(geo_phes)
    json_biolink = json.dumps(geo_biolink)

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
      width: 320px;
      max-height: calc(100vh - 106px);
      background: var(--bg-panel);
      border: 1px solid var(--border-cyan);
      backdrop-filter: blur(16px);
      border-radius: 10px;
      z-index: 90;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
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
      margin-top: 4px;
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

    .layer-card {{
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 8px 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11.5px;
      color: #e2e8f0;
    }}

    .layer-card input {{
      cursor: pointer;
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

  <!-- Left Dock: Engine & Layer Sandbox -->
  <div class="left-dock">
    <div class="dock-title">
      <span>🚀 Cesium 3D Testbed</span>
      <span style="font-size: 10px; color: var(--green-glow); font-family: 'JetBrains Mono';">v1.115.0</span>
    </div>

    <!-- Basemap Selector -->
    <div class="section-lbl">Basemap Imagery</div>
    <div class="btn-grid">
      <button id="bm-esri" class="btn-ctrl active" onclick="switchBasemap('esri')">Esri Satellite</button>
      <button id="bm-nsw" class="btn-ctrl" onclick="switchBasemap('nsw')">NSW High-Res</button>
      <button id="bm-topo" class="btn-ctrl" onclick="switchBasemap('topo')">NSW Topo</button>
      <button id="bm-osm" class="btn-ctrl" onclick="switchBasemap('osm')">OpenStreetMap</button>
    </div>

    <!-- 3D Terrain Switcher -->
    <div class="section-lbl">3D Elevation Terrain</div>
    <div class="layer-card">
      <span>WorldElevation3D Terrain</span>
      <input type="checkbox" id="chk-terrain" checked onchange="toggleTerrain(this.checked)">
    </div>

    <!-- Siting Test Layers -->
    <div class="section-lbl">Test Geospatial Layers</div>
    <div style="display: flex; flex-direction: column; gap: 6px;">
      <div class="layer-card">
        <span style="color: #38bdf8;">🏢 3D Developable Pads (154 ha)</span>
        <input type="checkbox" id="chk-pads" checked onchange="toggleLayer('pads', this.checked)">
      </div>
      <div class="layer-card">
        <span style="color: #fbbf24;">⚡ 330kV Substation & PHES</span>
        <input type="checkbox" id="chk-phes" checked onchange="toggleLayer('phes', this.checked)">
      </div>
      <div class="layer-card">
        <span style="color: #34d399;">🌿 Koala Biolink Corridor</span>
        <input type="checkbox" id="chk-biolink" checked onchange="toggleLayer('biolink', this.checked)">
      </div>
      <div class="layer-card">
        <span style="color: #38bdf8;">📐 Precinct Boundary</span>
        <input type="checkbox" id="chk-boundary" checked onchange="toggleLayer('boundary', this.checked)">
      </div>
    </div>

    <div style="font-size: 10px; color: var(--text-dim); line-height: 1.4; margin-top: 8px; border-top: 1px solid var(--border-subtle); padding-top: 8px;">
      Testbed sandbox for 3D Tiles streaming, LOD point clouds, and Cesium-powered GeoLibre extensions.
    </div>
  </div>

  <!-- Bottom Camera FlyTo Controls -->
  <div class="bottom-bar">
    <button class="btn-cam active" onclick="flyTo('overview', this)">🪐 Precinct Overview</button>
    <button class="btn-cam" onclick="flyTo('pads', this)">🏢 Developable Pads</button>
    <button class="btn-cam" onclick="flyTo('substation', this)">⚡ 330kV Substation</button>
    <button class="btn-cam" onclick="flyTo('biolink', this)">🌿 Sugarloaf Biolink</button>
  </div>

  <script>
    // Explicitly disable Ion tokens & tracking
    if (typeof Cesium !== 'undefined' && Cesium.Ion) {{
      Cesium.Ion.defaultAccessToken = '';
    }}

    const cameraPresets = {{
      overview: {{
        destination: Cesium.Cartesian3.fromDegrees(151.575, -32.955, 3800),
        orientation: {{
          heading: Cesium.Math.toRadians(0),
          pitch: Cesium.Math.toRadians(-42),
          roll: 0.0
        }}
      }},
      pads: {{
        destination: Cesium.Cartesian3.fromDegrees(151.573, -32.942, 1800),
        orientation: {{
          heading: Cesium.Math.toRadians(15),
          pitch: Cesium.Math.toRadians(-38),
          roll: 0.0
        }}
      }},
      substation: {{
        destination: Cesium.Cartesian3.fromDegrees(151.584, -32.932, 1400),
        orientation: {{
          heading: Cesium.Math.toRadians(350),
          pitch: Cesium.Math.toRadians(-35),
          roll: 0.0
        }}
      }},
      biolink: {{
        destination: Cesium.Cartesian3.fromDegrees(151.578, -32.946, 2200),
        orientation: {{
          heading: Cesium.Math.toRadians(330),
          pitch: Cesium.Math.toRadians(-35),
          roll: 0.0
        }}
      }}
    }};

    let terrainProvider = new Cesium.ArcGISTiledElevationTerrainProvider({{
      url: 'https://elevation3d.arcgis.com/arcgis/rest/services/WorldElevation3D/Terrain3D/ImageServer'
    }});
    let ellipsoidProvider = new Cesium.EllipsoidTerrainProvider();

    const viewer = new Cesium.Viewer('cesiumContainer', {{
      terrainProvider: terrainProvider,
      imageryProvider: new Cesium.UrlTemplateImageryProvider({{
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
        maximumLevel: 19
      }}),
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

    viewer.scene.globe.depthTestAgainstTerrain = true;
    viewer.scene.globe.enableLighting = true;

    // --- Basemap Controller ---
    function switchBasemap(type) {{
      document.querySelectorAll('.btn-ctrl').forEach(b => b.classList.remove('active'));
      const layers = viewer.imageryLayers;
      layers.removeAll();

      if (type === 'esri') {{
        const btn = document.getElementById('bm-esri');
        if (btn) btn.classList.add('active');
        layers.addImageryProvider(new Cesium.UrlTemplateImageryProvider({{
          url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
          maximumLevel: 19,
          credit: 'Esri World Imagery'
        }}));
      }} else if (type === 'nsw') {{
        const btn = document.getElementById('bm-nsw');
        if (btn) btn.classList.add('active');
        layers.addImageryProvider(new Cesium.UrlTemplateImageryProvider({{
          url: 'https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
          maximumLevel: 19,
          credit: 'NSW Spatial Services'
        }}));
      }} else if (type === 'topo') {{
        const btn = document.getElementById('bm-topo');
        if (btn) btn.classList.add('active');
        layers.addImageryProvider(new Cesium.UrlTemplateImageryProvider({{
          url: 'https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Topo_Map/MapServer/tile/{{z}}/{{y}}/{{x}}',
          maximumLevel: 18,
          credit: 'NSW Topographic Map'
        }}));
      }} else if (type === 'osm') {{
        const btn = document.getElementById('bm-osm');
        if (btn) btn.classList.add('active');
        layers.addImageryProvider(new Cesium.UrlTemplateImageryProvider({{
          url: 'https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}@2x.png',
          subdomains: ['a', 'b', 'c', 'd'],
          maximumLevel: 19,
          credit: 'OpenStreetMap contributors / CARTO'
        }}));
      }}
    }}

    function toggleTerrain(enable) {{
      viewer.terrainProvider = enable ? terrainProvider : ellipsoidProvider;
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

    // --- Geometry Conversion Utilities ---
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

    // --- Data Layers ---
    const GEO_BOUNDARY = {json_boundary};
    const GEO_PADS = {json_pads};
    const GEO_PHES = {json_phes};
    const GEO_BIOLINK = {json_biolink};

    const LayerEntities = {{
      boundary: [],
      pads: [],
      phes: [],
      biolink: []
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

    // 3. 330kV Substation & PHES
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

    // 4. Koala Biolink Corridor
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

    function toggleLayer(layerKey, isVisible) {{
      if (LayerEntities[layerKey]) {{
        LayerEntities[layerKey].forEach(ent => {{
          ent.show = isVisible;
        }});
      }}
    }}

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
