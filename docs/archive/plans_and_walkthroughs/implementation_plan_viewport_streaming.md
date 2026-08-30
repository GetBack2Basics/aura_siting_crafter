# Implementation Plan — Viewport BBOX Streaming, Zoom LOD Scaling, Point Clustering & UI Refinement (v2)

## Goal Description
Enhance the AURA Siting Crafter GeoLibre WebGIS application with dynamic **Viewport Bounding Box (BBOX) spatial streaming**, **Zoom-level Level of Detail (LOD) filtering**, **MapLibre Point Clustering symbology**, interactive layer analytics charts with dynamic chart-type toggling, unified basemap opacity control, realistic compute credit telemetry, and national dataset parity confirmation.

---

## 1. National Level Data Parity Confirmation
All national-level datasets used in the Multi-Criteria Decision Analysis (MCDA) report (`runner/national_suitability_report.html`) and Wherobots Cloud lakehouse (`wherobots://fgsdb/aura_siting` / `s3://wherobots-user-storage/aura_siting/`) are **100% identical and mapped 1:1 in GeoLibre**:
- **Candidate Hubs**: All 16 Multi-Criteria Decision Analysis (MCDA) scored candidate parcels across 8 Australian States & Territories (NSW, QLD, VIC, WA, ACT, NT, SA, TAS) with identical Lot/Plan, Area (ha), Slope (%), Grid Proximity, Recycled Water Proximity, Sensitive Receptor Buffers, and Pumped Hydro Capacity (MWh).
- **Thematic Infrastructure Layers**: All 18 authoritative portal layers covering Energy Grid ($\ge 132\text{kV}$), BoM Surface Hydrography & Recycled WWTW, ACARA National Schools, NHSD National Healthcare, BioNet Biodiversity/KHIB, and Heavy Freight Rail corridors.

---

## 2. Proposed Technical Changes

### A. Viewport BBOX Spatial Streaming & Zoom-Level LOD Filtering
- **Backend (`src/geolibre_proxy/main.py`)**:
  - Update `GET /api/data/{layer_id}` to accept optional query parameters:
    - `bbox: Optional[str] = Query(None)` (format: `minx,miny,maxx,maxy` in WGS84)
    - `zoom: Optional[float] = Query(None)`
  - When `bbox` is supplied, pass the spatial envelope to ArcGIS REST MapServer (`geometry={xmin,ymin,xmax,ymax}&geometryType=esriGeometryEnvelope&spatialRel=esriSpatialRelIntersects&inSR=4326&outSR=4326`).
  - Implement Zoom-Level Level of Detail (LOD) filtering:
    - **Zoomed Out ($z < 8$)**: Filter for major/backbone infrastructure only:
      - Energy Grid: Transmission lines with `voltage >= 330kV` or `voltage IS NULL` (major interconnector trunk lines).
      - Candidates: Top tier candidate hubs ($S_{\text{suitability}} \ge 0.90$).
      - Transport: Main freight corridors.
    - **Mid Zoom ($8 \le z < 12$)**: Filter for regional assets:
      - Energy Grid: Lines and substations with `voltage >= 132kV`.
      - Water: Regional treatment plants and major supply canals.
      - Social Receptors: High schools and secondary campuses.
    - **Zoomed In ($z \ge 12$)**: Load all local features within current viewport:
      - All distribution feeds, local canals, primary schools, medical clinics, and local cadastre envelopes.
- **Frontend (`src/geolibre_frontend/index.html`)**:
  - Implement debounced viewport listener (`map.on('moveend')` with 300ms debounce).
  - On pan/zoom, query active visible layers with `getBounds()` and current `getZoom()`.
  - Dynamically update MapLibre GeoJSON sources and table rows to reflect **only features present in the current active viewport**.

---

### B. MapLibre Point Clustering Symbology
- Enable native MapLibre point clustering for all point layers (National Candidates, Water Plants, Schools, Healthcare Directory):
  ```javascript
  map.addSource(srcId, {
    type: 'geojson',
    data: data,
    cluster: true,
    clusterMaxZoom: 14,
    clusterRadius: 50
  });
  ```
- Add cluster bubble layers (`circle-color` scaled by point count: `<10` green, `10-50` blue, `>50` purple) and cluster count labels (`symbol` layer with `point_count_abbreviated`).
- Add unclustered individual point layers with custom color styling.
- On cluster click, smoothly zoom into the cluster extent (`map.getSource(srcId).getClusterExpansionZoom()`).

---

### C. Startup Layer Visibility
- Set default startup state so that **ONLY** `National Cadastre & Siting Candidates` is enabled/checked (`checked = true`).
- All other 9 thematic layers default to **unchecked** (`checked = false`, `visibility: none`) to minimize initial network load and keep the initial map clean.

---

### D. Basemap Selection & Universal Opacity Slider
- **Dropdown Options**:
  1. `🗺️ OSM Terrain` (Default)
  2. `🛰️ Esri World Imagery`
  3. `🌐 OpenStreetMap Standard`
  4. `🌑 No Basemap (Dark Canvas)`
  5. `⚪ No Basemap (White Canvas)` (Placed as the last option).
- Remove static percentage labels from the basemap dropdown text.
- Add a universal **Basemap Opacity slider** in the top navigation bar (default: `50%`) that dynamically controls raster opacity across all basemap styles.

---

### E. Header & Controls UI Polish
- **Cost Telemetry Badge**:
  - Replace verbose header text with a clean, compact badge: **`☁️ Compute: $0.00 | 300.00 Credits`**.
  - Add native HTML `title` tooltip with full cloud telemetry details:
    `Google Cloud Serverless Footprint: Cloud Run Idle (0 active containers) | Active Compute Cost: $0.00 / hr (Note: Does not account for fixed monthly platform plan fees) | Scale-to-Zero Enabled`.
- **Remove Top Version Tag**:
  - Remove `v2.0.9 | 202608300450` from the top header brand (kept in the footer).
- **Sidebar Action Icons**:
  - Change Attribute Table icon from chart (`📊`) to **Table icon** (`⊞` or SVG grid icon).
  - Add **Analytics Chart icon** (`📊`) next to each layer that triggers a modal visualising layer statistics.

---

### F. Layer Analytics Chart Modal & Dynamic Chart-Type Switching
- When the user clicks the Chart icon (`📊`) next to any layer, open an interactive Analytics Modal with a **Chart-Type Selector** (Bar Chart, Histogram, Donut/Pie Chart, Line/Scatter).
- **Default Chart Configurations per Layer**:
  1. **National Candidates**:
     - *Default*: Histogram of Suitability Scores ($S_{\text{mce}}$ distribution across 0.80 – 1.00).
     - *Toggle Options*: Bar Chart (Hectares per Site), Scatter Chart (Power Distance vs Water Distance).
  2. **Energy Grid & Substations**:
     - *Default*: Bar Chart of Voltage ratings (500kV, 330kV, 275kV, 132kV, 66kV).
     - *Toggle Options*: Donut Chart (Operational Status distribution), Line Chart (Transmission Corridor Lengths).
  3. **Water & Cooling Loops**:
     - *Default*: Bar Chart of Water Asset Types (Supply Canals, WWTW, Storage Tanks).
     - *Toggle Options*: Histogram (Capacity / Buffer Distances).
  4. **Social & Sensitive Receptors (Schools & Healthcare)**:
     - *Default*: Donut / Bar Chart of Facility Categories (Primary, Secondary, Hospital, Emergency, Community Clinic).
     - *Toggle Options*: Histogram of Setback Buffer Distances.
  5. **Biodiversity & Hazards**:
     - *Default*: Bar Chart of Hazard Severity & BioNet Categories (KHIB, HEV, APZ Category 1).

---

## Verification Plan

### Automated Tests
- Run lint suite: `pytest tests/lint/ -v` (ensure all tests pass, 0 secret leaks).

### Manual Verification
1. Open [`https://storage.googleapis.com/aura-siting-crafter-geolibre-app/index.html`](https://storage.googleapis.com/aura-siting-crafter-geolibre-app/index.html).
2. Verify top bar shows `☁️ Compute: $0.00 | 300.00 Credits` with hover details noting plan fee exclusion.
3. Verify only "National Cadastre & Siting Candidates" is checked on startup and points cluster with count bubbles.
4. Verify Basemap dropdown has White Canvas last, and the top basemap opacity slider changes transparency smoothly.
5. Zoom in/out and pan across Australia to verify viewport BBOX streaming and LOD filtering for active layers.
6. Click the Table icon (`⊞`) to open the attribute table for visible features.
7. Click the Chart icon (`📊`) to view the interactive data distribution modal, and toggle chart types using the dropdown.
