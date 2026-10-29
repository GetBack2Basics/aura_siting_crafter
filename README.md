# AURA Siting Crafter (Australian Urban & Regional AI Siting Crafter)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Dockerized](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](Dockerfile)
[![Live Platform](https://img.shields.io/badge/Live_WebGIS-aura.getback2basics.net-0ea5e9.svg)](https://aura.getback2basics.net)

**AURA Siting Crafter** is an open-source, cloud-native spatial data engineering and Multi-Criteria Decision Analysis (MCDA) framework for regional and national infrastructure siting (Data Centers, Clean Energy, Renewable Hydrogen, and Advanced Manufacturing Hubs across Australia).

It pairs heavy cloud-native upstream batch ETL on **Wherobots Cloud / Apache Sedona** and **Google Cloud Platform (GCP)** with zero-cost client-side compute (**DuckDB-WASM, MapLibre GL, Leaflet, Deck.gl, Cesium, and Potree**) for instant interactive scenario modeling in any standard web browser.

---

## Live Deployments & WebGIS Suite

The platform is deployed live on Google Cloud Platform:

| Web Interface | Endpoint / URL | Purpose |
| :--- | :--- | :--- |
| **National Siting Report** | [https://aura.getback2basics.net/index.html](https://aura.getback2basics.net/index.html) | Canonical suitability report, ABS meshblock rankings, power grid overlays, and real-time What-If scenario sandbox. |
| **GeoLibre WebGIS Engine** | [https://aura.getback2basics.net/map.html](https://aura.getback2basics.net/map.html) | Fullscreen MapLibre GL viewer with national cadastral vector overlays, jurisdiction extents, and spatial filtering. |
| **Data QA & Source Inspector** | [https://aura.getback2basics.net/data_qa.html](https://aura.getback2basics.net/data_qa.html) | Cross-page spatial data lineage audit and live inspector across 16 authoritative state & national portals. |
| **3D Digital Twin & COPC LiDAR** | [https://aura.getback2basics.net/projects/copc_3d_viewer.html](https://aura.getback2basics.net/projects/copc_3d_viewer.html) | WebGL & Potree 3D point cloud streaming for high-precision terrain and site engineering analysis. |
| **Spatial AI API Gateway** | [https://aura.getback2basics.net/api/docs](https://aura.getback2basics.net/api/docs) | FastAPI OpenAPI documentation for Natural Language to DuckDB Spatial SQL proxy on GCP Cloud Run. |

---

## Key Features

1. **Decoupled Asymmetric Compute Model**:
   - **Upstream Lakehouse Batch ETL**: Heavy geometric processing (coordinate transforms, multi-ring topological buffering, `ST_Difference` masks) runs on Wherobots Cloud (Apache Sedona & Iceberg) for ~$0.69 USD per national run across 15.91M geometries.
   - **Serving & AI Proxy**: Cloud Run container proxy and GCS bucket hosting in Sydney (`australia-southeast1`) at <$0.50 USD / month.
   - **Downstream Interactive Consumption**: 100% offloaded to client hardware using in-browser DuckDB-WASM and JavaScript at **$0.00 incremental server compute cost**.

2. **Open & Authoritative Basemap Suite**:
   - Zero commercial/proprietary basemap locks (CartoDB removed).
   - Instant live toggling and opacity blending (0–100%) across:
     - ⛰️ **OSM Terrain**: OpenTopoMap (`tile.opentopomap.org`)
     - 🛰️ **Esri World Imagery**: Maxar / Earthstar Geographics high-resolution imagery
     - 🗺️ **OpenStreetMap Standard**: Global crowdsourced street and boundary map
     - 🗺️ **Esri World Topo**: Shaded relief and administrative boundaries
     - 🌑 **Dark Canvas** & ⚪ **White Canvas**: High-contrast vector styling modes

3. **Strict Zero-Mock Data Standard**:
   - Zero sample coordinates, fallback counts, or synthetic geometries.
   - All layers load dynamically from live statutory endpoints, verified GeoParquet/GeoJSON pipelines, or `config/dataset_manifest_v2.json`.
   - Validated continuously via automated AST lint scans (`pytest tests/lint/test_no_mock_data.py -v`).

4. **Conversational Natural Language to Spatial AI**:
   - Integrated with Gemini 2.5 Flash on Vertex AI / Google Cloud to translate plain English queries into executable DuckDB Spatial SQL and client-side bounding box animations.

---

## Architecture Overview

```
                          ┌────────────────────────────┐
                          │    National & State APIs   │
                          │  (Geoscape, GA, SEED, Open)│
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                          ┌────────────────────────────┐
                          │  Wherobots / Apache Sedona │
                          │     Spatial ETL Engine     │
                          │ (src/Ingestion/spatial_ingest.py)
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                          ┌────────────────────────────┐
                          │  Apache Iceberg / Havasu   │
                          │   wherobots://fgsdb/...    │
                          └─────────────┬──────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
       ┌─────────────────────────┐             ┌─────────────────────────┐
       │   Spatial MCDA Engine   │             │   GeoLibre Cloud Run    │
       │ (src/Analysis/national_ │             │  Spatial AI Proxy (GCP) │
       │ suitability_analysis.py)│             │ (src/geolibre_proxy/)   │
       └─────────────────────────┘             └────────────┬────────────┘
                                                            │
                                            ┌───────────────┴───────────────┐
                                            ▼                               ▼
                               ┌─────────────────────────┐     ┌─────────────────────────┐
                               │  Interactive Dashboards │     │   In-Browser Compute    │
                               │   (GeoLibre WebGIS /    │     │   DuckDB-WASM / Leaflet │
                               │    Siting Report)       │     │   MapLibre GL / Potree  │
                               └─────────────────────────┘     └─────────────────────────┘
```

---

## Directory Structure

| Path | Purpose |
|---|---|
| `config/national.json` | National siting parameters, CRS definitions, default buffer thresholds |
| `config/regions/` | Regional configuration overrides (e.g. `hunter.json`, `gladstone.json`) |
| `config/dataset_manifest_v2.json` | Authoritative statutory dataset catalog (16 national & state portals) |
| `src/Ingestion/` | Apache Sedona spatial ETL pipelines (`spatial_ingest.py`, `data_ingest.py`) |
| `src/Ingestion_v2/` | Incremental spatial ingest & telemetry v2 |
| `src/Analysis/` | National Multi-Criteria Decision Analysis scoring engine (`national_suitability_analysis.py`, `datacenter_suitability.py`) |
| `src/geolibre_frontend/` | Client-side WebGIS application (`index.html`, `map.html`, `data_qa.html`, Potree/Cesium 3D viewers) |
| `src/geolibre_proxy/` | FastAPI Spatial AI proxy container for Cloud Run deployment |
| `runner/` | Automated report & ETL generators (`build_suitability_report.py`, `etl_runner.html`) |
| `notebooks/` | Interactive Wherobots exploratory notebooks (`Spatial_ETL_Pipeline.ipynb`, `Precinct_Suitability_Analysis.ipynb`) |
| `docs/` | Technical methodology, architecture decisions, and spatial engineering documentation |
| `tests/lint/` | Zero-mock AST verification, security scanning, link validation, and import tests |
| `tools/` | Deployment scripts (`deploy_geolibre_gcp.ps1`, `deploy_geolibre_gcp.sh`) and graph analysis (`graphify_analysis.py`) |

---

## Quick Start

### 1. Local Python Environment
```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run full lint verification suite
pytest tests/lint/ -v

# Run national suitability scoring
python -m src.Analysis.national_suitability_analysis
```

### 2. Regional vs National Scoping
```bash
# Run for national scope
export AURA_REGION=national
python -m src.Ingestion.spatial_ingest

# Run for regional precinct (cost-optimized ETL)
export AURA_REGION=hunter
python -m src.Ingestion.spatial_ingest
```

### 3. Regenerating Siting Reports
```bash
# Rebuild the canonical index.html report with updated basemaps and layer metadata
python runner/build_suitability_report.py
```

### 4. Deploying to Google Cloud Platform
```bash
# On Windows (PowerShell)
.\tools\deploy_geolibre_gcp.ps1 -GcpProjectId "aura-siting-crafter"

# On Linux / macOS (Bash)
./tools/deploy_geolibre_gcp.sh
```

---

## Security & Attribution
- All credentials and API tokens must be supplied via `.env` or runtime environment variables. Never commit API keys or private session IDs.
- Licensed under the [MIT License](LICENSE).
