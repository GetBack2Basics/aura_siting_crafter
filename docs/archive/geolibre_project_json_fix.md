# GeoLibre Project Spec Fix & Desktop WebGIS Integration

## Executive Summary
This document records the resolution of the GeoLibre project specification issue where importing `aura-siting-crafter.geolibre.json` into the GeoLibre application ([https://geolibre.app/demo/](https://geolibre.app/demo/)) loaded the layer tree in the sidebar but failed to render vector feature geometries on the map canvas.

## Root Cause Analysis
1. **Invalid `type` declaration**: The original file used non-standard vector types (`"type": "point"`, `"type": "polygon"`, `"type": "line"`). According to `@geolibre/core`, vector datasets must declare `"type": "geojson"` (with geometry classification handled dynamically at the feature level).
2. **Missing GeoJSON `FeatureCollection` payload**: Spatial features were stored in non-standard keys (e.g. `"candidates": [...]` or relative local stream paths `/runner/attachments/...`), which are unrecognized by the GeoLibre MapLibre sync engine (`@geolibre/map/src/layer-sync.ts`).
3. **Missing `source` descriptor**: GeoLibre requires `source: {"type": "geojson"}` alongside `geojson: {"type": "FeatureCollection", "features": [...]}`.

## Implemented Fixes
1. **Specification Compliance (`src/geolibre_frontend/aura-siting-crafter.geolibre.json`)**:
   - Upgraded format to standard GeoLibre project schema version `0.2.0`.
   - Populated complete GeoJSON `FeatureCollection` objects across all 11 active layers:
     - 🎯 **National Siting Candidate Hubs** (17 MCE Scored Hubs with full attributes and GDA2020/WGS84 coordinates)
     - ⚡ **Electrical Substations & Terminal Stations** (17 bulk supply/terminal substations)
     - ⚡ **Interstate Transmission Grid** (High-voltage power transmission alignments)
     - 💧 **Recycled Wastewater Treatment Plants (WWTW)** (10 tertiary reclamation facilities)
     - 💧 **BoM Surface Water HydroLine & HydroArea** (Surface waterways)
     - 🛡️ **ACARA National Schools** (Statutory educational receptors with 500m buffers)
     - 🛡️ **NHSD National Healthcare & Hospitals** (Regional hospital receptors)
     - 🌿 **NSW BioNet Biodiversity Area** (High Environmental Value conservation envelopes)
     - 🏗️ **Macquarie Transformation Envelope** (350 ha transformation precinct)
     - 🏗️ **Net Developable Pad Area** (59.7 ha engineered pad)
     - 🏗️ **High Pressure Gas Pipeline Corridor** (20m APZ trunk corridor)
   - Structured layer hierarchy into 6 collapsible `layerGroups` (`grp_candidates`, `grp_energy`, `grp_water`, `grp_receptors`, `grp_environment`, `grp_precincts`).
   - Configured styling according to GeoLibre's `LayerStyle` schema (colors, stroke widths, fill opacities, and labels).

2. **GeoLibre WebGIS Link Integration**:
   - Added direct clickable links and action buttons to **[https://geolibre.app/demo/](https://geolibre.app/demo/)** across the UI:
     - `src/geolibre_frontend/index.html` (modal step and footer actions)
     - `runner/attachments/geolibre_guide.html`
     - `runner/attachments/geolibre_help.html`

3. **Automated Verification & Schema Gate**:
   - Created `tools/build_geolibre_project.py` for deterministic project compilation.
   - Added `tests/test_geolibre_project_json.py` to validate project schema, map view, layer types, and feature collections.
   - Passed full test suite (`182 passed, 1 skipped`).
