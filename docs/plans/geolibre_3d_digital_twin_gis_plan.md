# Plan: GeoLibre 3D Forensic Digital Twin GIS Exporter & Interactive Print Layout

This plan outlines the architecture and implementation of a dedicated Python packaging script and interactive 3D GeoLibre cartographic engine that reproduces the high-impact **Forensic Digital Twin & Developable Pad Siting Analysis** aesthetic shown in [`docs/archive/aura_siting_evolution_assets/05_forensic_digital_twin_pads.jpg`](file:///c:/Projects/aura_siting_crafter/docs/archive/aura_siting_evolution_assets/05_forensic_digital_twin_pads.jpg) for statutory and enhanced siting reports.

---

## 1. Executive Architecture Summary

The target visual consists of five primary cartographic layers and layout components:

1. **3D Oblique Aerial Terrain Basemap**: High-resolution satellite orthophoto draped over a 3D digital elevation model (DEM) at an oblique camera angle (~60° pitch, ~30° bearing).
2. **Neon Cyan Developable Pads (`NDP-00` to `NDP-10`)**: Glowing cyan boundaries (`#00f0ff` / `#38bdf8`), semi-transparent fills, building envelopes / 3D footprint extrusions, and pad identifiers.
3. **Neon Red Constraint & Exclusion Corridors**:
   - *1% AEP Flood Inundation Zone*: Glowing red contour corridor following natural drainage.
   - *Steep Slope (>20%)*: Red contour ribbons along elevated ridgelines.
   - *Mine Subsidence Exclusion Zone*: Diagonal red hatched polygons with hazard warning alert badges (`⚠️`).
4. **Energy, Water & Rail Infrastructure**:
   - *330kV Substation*: Switchyard footprint, transformer callouts, and transmission line corridors.
   - *Pumped-Hydro (PHES)*: Upper reservoir, illuminated cyan penstock conduit, 50MW powerhouse, and lower reservoir void.
   - *Heavy Rail Loop & Siding*: Active rail loop track geometry and intermodal freight siding.
5. **Forensic HUD Leader-Line Callout Cards**: Floating dark glass cards (`rgba(7, 11, 20, 0.90)`) with cyan/red accent borders and leader-lines dynamically pointing to 3D ground coordinates.
6. **Cartographic Furniture**: Stylized HUD North Arrow, dynamic metric scale bar, and 1-click high-res print/export controls.

---

## 2. Core Technical Components

### Component 1: Python Packaging & Export Pipeline (`tools/build_geolibre_digital_twin.py`)
A CLI tool that ingests project manifests (e.g. `config/projects/LMCC_MacquarieCoal.json`) and spatial layers (`data/projects/LMCC_MacquarieCoal/*.geojson`):
- Packages all authoritative spatial layers into a unified project payload with enriched styling metadata.
- Computes optimal 3D camera viewpoints (bounding box, centroid, pitch, bearing, altitude).
- Generates:
  1. `src/geolibre_frontend/projects/digital_twin_LMCC_MacquarieCoal.html`: Standalone, zero-network-dependency interactive 3D WebGIS digital twin viewer.
  2. `src/geolibre_frontend/projects/digital_twin_LMCC_MacquarieCoal.geolibre.json`: GeoLibre project manifest for loading into the central WebGIS suite.
  3. *(Optional)* `exports_v2/projects/LMCC_MacquarieCoal/digital_twin.gpkg` + `digital_twin.qgs` for desktop QGIS / GeoLibre editing.

### Component 2: Interactive 3D Digital Twin Viewer & Symbology Engine
A purpose-built 3D digital twin interface with:
- **MapLibre GL JS 3D Terrain**: Raster DEM terrain tiles + ESRI World Imagery satellite basemap.
- **Custom Shaders / Multi-Pass Styling**:
  - Multi-pass stroke glowing filters for Developable Pads (cyan glow `#00f0ff`) and Hazard Exclusions (coral glow `#ff3366`).
  - 3D Extrusion layer for developable building envelopes (height 10-15m with realistic shadows).
  - SVG diagonal crosshatch pattern for Mine Subsidence G3 exclusion zones.
  - Glowing animated pulse effect for 330kV transmission lines and PHES penstock.
- **Dynamic 3D Leader-Line HUD System**:
  - Responsive SVG leader lines pinned from 3D ground coordinates to screen-space HUD cards.
  - Callout cards matching the exact design in the image.

### Component 3: Edit & High-Resolution Print/Export Engine
- **Live On-Screen Edit Controls**:
  - Camera controller (Pitch slider `0°-85°`, Bearing rotation `0°-360°`, Zoom, Vertical Terrain Exaggeration `1.0x - 2.5x`).
  - Lighting & Sun Position slider (controls terrain hillshade shadows and building ambient occlusion).
  - Callout Editor (toggle, reposition, or edit badge text and statistics).
  - Layer visibility toggles (Pads, Constraints, PHES, Rail, Grid).
- **Print & Statutory Export Suite**:
  - **1-Click 300 DPI Snapshot**: Renders canvas to ultra-high-resolution PNG with crisp text and antialiased glowing vector overlays.
  - **Print Layout View**: Formats the digital twin canvas into a standardized A3/A4 landscape statutory sheet with title block, metadata box, scale bar, north arrow, and legend.

---

## 3. Verification & Quality Gates
- `pytest tests/lint/test_no_mock_data.py -v`
- `pytest tests/lint/ -v`
- Build execution test with `python tools/build_geolibre_digital_twin.py --project LMCC_MacquarieCoal`
- Interactive visual verification in browser
