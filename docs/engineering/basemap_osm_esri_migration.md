# Basemap Migration: CartoDB to OpenStreetMap & Esri

**Date**: 2026-10-30  
**Target**: `src/geolibre_frontend/index.html` (Authoritative generator: `runner/build_suitability_report.py`)  
**URL**: https://aura.getback2basics.net/index.html  

---

## 1. Context & Motivation
Previously, `index.html` used a single hardcoded CartoDB Voyager raster basemap (`https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png`).
To achieve cross-platform UI parity with the other map interfaces in AURA Siting Crafter (`map.html` and `docs/qa/geolibre_qa_inspect.html`), all CartoDB dependencies were removed and replaced with OpenStreetMap (OSM) and Esri tile layers along with an interactive Basemap Popover controller.

---

## 2. Basemap Tile Configurations

The map now offers the same 4 raster styles + 2 canvas modes as the companion GeoLibre WebGIS maps:

| Layer Key | Label | Tile Endpoint | Attribution |
| :--- | :--- | :--- | :--- |
| `osm-terrain` | ⛰️ OSM Terrain (Default) | `https://tile.opentopomap.org/{z}/{x}/{y}.png` | `&copy; OpenTopoMap &copy; OpenStreetMap` |
| `esri-imagery` | 🛰️ Esri World Imagery | `https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}` | `Tiles &copy; Esri, Maxar, Earthstar Geographics` |
| `osm-standard` | 🗺️ OpenStreetMap Standard | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` | `&copy; OpenStreetMap contributors` |
| `esri-topo` | 🗺️ Esri World Topo | `https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}` | `Tiles &copy; Esri` |
| `dark-canvas` | 🌑 No Basemap (Dark Canvas) | *None (Tile layer removed, background `#0a0f1d`)* | N/A |
| `white-canvas` | ⚪ No Basemap (White Canvas) | *None (Tile layer removed, background `#ffffff`)* | N/A |

---

## 3. UI Controls
- **Dropdown Popover**: Accessible via `🗺️ Basemap ▾` button directly in the National Siting Map header.
- **Style Selector**: Smoothly swaps active tile layer using Leaflet's `map.removeLayer()` / `map.addLayer()`.
- **Opacity Slider**: Real-time slider (0% to 100%, default 50%) adjusting `tileLayer.setOpacity()`.
- **Zero-Mock & Lint Gate Compliance**: All code complies with `tests/lint/test_no_mock_data.py` and passes the full lint test suite.

