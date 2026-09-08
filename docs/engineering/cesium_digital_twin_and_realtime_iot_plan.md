# Implementation Plan: CesiumJS 3D Digital Twin, Interactive Label Controls, ELVIS LiDAR & Real-Time IoT Integration

## Goal
1. **Switch 3D Digital Twin Engine**: Replace MapLibre GL with **CesiumJS** in `src/geolibre_frontend/projects/digital_twin_LMCC_MacquarieCoal.html` and `tools/build_geolibre_digital_twin.py` to deliver a true 3D geospatial digital twin with true 3D extruded facilities, terrain drapes, lighting/shadow simulation, and camera flight paths.
2. **Layer Label Management**: Provide per-layer and global controls to close, minimize, collapse, or altitude-filter on-map labels and billboards so users can inspect clean 3D geometry without label clutter.
3. **Real-Time IoT Sensor Feeds**: Integrate Lake Macquarie City Council's genuine real-time open data APIs directly into the Digital Twin (Decentlab environmental sensors and ATM41 all-in-one weather stations) with dynamic HUD telemetry.
4. **ELVIS High-Resolution LiDAR Ingestion Plan**: Document and architect the ingestion pipeline for the 2.11 GB ELVIS LiDAR dataset (`DATA_2374296.zip`) for millimeter-accurate 1m DEM terrain mesh and cut/fill volumetric earthwork modeling.

---

## Technical Architecture

### 1. CesiumJS 3D Engine Migration
- **CDN Assets**: Loaded via `https://cdn.jsdelivr.net/npm/cesium@1.115.0/Build/Cesium/Cesium.js` and `Widgets/widgets.css`.
- **Imagery & Terrain**: Esri World Imagery / OpenStreetMap + ArcGIS World Elevation / Cesium Terrain.
- **3D Features**:
  - 10 Net Developable Pads with extruded heights (12m - 18m) and neon perimeter glow.
  - 330kV Transgrid Switchyard with substation gantry heights (10m) and 49 MWh PHES reservoir with translucent water polygon.
  - Mine Subsidence Zones (G1-G3) with color-coded risk envelopes.
  - Acoustic Overburden Bunds (8m height) and Koala Biolink Corridor.
  - Diega Creek 1% AEP flood corridor.

### 2. Label Visibility & Minimization Mechanics
- **Per-Layer Controls**: Checkboxes to toggle labels independently from layer geometries (`Show/Hide Labels`).
- **Global Label Control**: One-click floating toggle (`🏷️ Toggle All Labels`) to instantly declutter the 3D scene.
- **Distance Scaling / Occlusion**: `Cesium.DistanceDisplayCondition` configured so labels only render within optimal camera ranges (e.g. 0 to 7,500m) and do not overlap at high altitudes.

### 3. Lake Macquarie Real-Time IoT Ingestion
- **ATM41 Weather Stations**: Queries `https://data.lakemac.com.au/api/explore/v2.1/catalog/datasets/weather-station-atm41-realtime/records?limit=20` for temperature, atmospheric pressure, wind speed, solar radiation, and lightning distance.
- **Decentlab Sensors**: Queries `https://data.lakemac.com.au/api/explore/v2.1/catalog/datasets/council-decentlab-realtime/records?limit=20` for microclimate temperature and humidity.
- **HUD telemetry card** displaying live live sensor feeds with timestamp and device ID.

### 4. ELVIS LiDAR Pipeline (1m DEM & Point Clouds)
- **Source**: `https://elvis-downloads.s3.amazonaws.com/DATA_2374296.zip` (2.11 GB).
- **Processing**: Convert LAS/LAZ to 3D Tiles (`py3dtiles`) for CesiumJS point cloud streaming, and GeoTIFFs to Cloud-Optimized GeoTIFFs (COGs) for Apache Sedona slope analysis.

---

## Verification Strategy
1. Unit and lint test suite (`pytest tests/lint/ -v` and `pytest -v`).
2. Browser verification of CesiumJS rendering, 3D extrusions, label toggles, and real-time sensor popups.
3. Deployment to GCS and live endpoint check.
