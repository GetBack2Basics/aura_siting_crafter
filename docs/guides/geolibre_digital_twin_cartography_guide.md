# AURA Siting Crafter — 3D Forensic Digital Twin & Cartographic Siting Guide

## Overview & Purpose
This guide documents the automated pipeline and cartographic design system for generating interactive **3D Forensic Digital Twins & Developable Pad Siting Analyses** in GeoLibre / MapLibre GL JS, matching the forensic precision visual in [`docs/archive/aura_siting_evolution_assets/05_forensic_digital_twin_pads.jpg`](file:///c:/Projects/aura_siting_crafter/docs/archive/aura_siting_evolution_assets/05_forensic_digital_twin_pads.jpg).

---

## 1. Cartographic Layer Hierarchy & Symbology System

| Layer / Feature | Color / Shader | Geometry Type | Purpose & Forensic Rule |
| :--- | :--- | :--- | :--- |
| **Satellite Imagery** | ESRI World Imagery / Maxar | Raster Tiles | Realistic terrain context draped over DEM elevation mesh. |
| **3D Terrain Elevation** | AWS Terrarium RGB DEM | Raster DEM (`exaggeration: 1.5x`) | 3D vertical relief showing ridgelines, plateaus, and open-cut voids. |
| **Net Developable Pads (NDP-00 - 10)** | Neon Cyan (`#00f0ff` glow + `#ffffff` edge) | Multi-Polygon & Extrusions | High-precision certified buildable envelopes (sub-5% slope, non-riparian). |
| **3D Industrial Envelopes** | Light Blue (`#38bdf8` at 8-18m height) | `fill-extrusion` | Volumetric building models illustrating spatial capacity. |
| **1% AEP Flood Corridor** | Neon Coral/Red (`#ff3366` glow ribbon) | Multi-Polygon & Glowing Stroke | Statutory flood inundation zone (ARR 2019 / Diega Creek catchment). |
| **Steep Slope Exclusions** | Neon Red (`#ef4444` contoured ribbon) | Multi-Polygon & Glowing Stroke | Sub-grade filter excluding slopes >20% on surrounding ridges. |
| **Mine Subsidence Exclusion Zone** | Crimson Hatched (`#f43f5e` dashed edge) | Multi-Polygon | Subsidence Advisory G3 exclusion zone requiring specialized foundations. |
| **330kV Substation Connection** | Neon Cyan (`#00f0ff`) + Gold | LineString & Polygon | 330kV Switchyard, Main Transformer T1, and GIS connection point. |
| **Micro-PHES Pumped Hydro** | Deep Cyan (`#0ea5e9`) + Flow Line | Polygon & LineString | Upper reservoir (+145m AHD), DN 3200 penstock, 50MW powerhouse, lower void. |
| **Rail Freight Loop & Siding** | Neon Orange (`#f97316`) | LineString | 1.8km active heavy rail loop siding connected to Main Northern Railway. |
| **Forensic HUD Leader-Lines** | SVG Dynamic Polylines + Dark Glass Cards | Dynamic Screen Projection | Real-time map-space to screen-space leader-line callout annotations. |

---

## 2. Dynamic 3D HUD Leader-Line Architecture

The HUD callout system renders SVG leader lines that dynamically track geographic coordinates in 3D perspective:
```javascript
// Screen projection loop
function updateHudPositions() {
    hudCallouts.forEach(c => {
        const pt = map.project(c.coords); // Projects 3D lon/lat/elev to 2D viewport
        const cardX = pt.x + (c.dx || 0);
        const cardY = pt.y + (c.dy || 0);
        
        // Update card position
        card.style.left = `${cardX}px`;
        card.style.top = `${cardY}px`;
        
        // Draw SVG dashed leader line
        line.setAttribute('points', `${pt.x},${pt.y} ${cardX},${cardY}`);
    });
}
```

---

## 3. Command-Line Usage & Packaging

### Generating a 3D Digital Twin for Any Precinct:
```bash
python tools/build_geolibre_digital_twin.py --project LMCC_MacquarieCoal
```

### Outputs Generated:
1. **Interactive 3D WebGIS App**: `src/geolibre_frontend/projects/digital_twin_LMCC_MacquarieCoal.html`
2. **GeoLibre Project Manifest**: `src/geolibre_frontend/projects/digital_twin_LMCC_MacquarieCoal.geolibre.json`
3. **High-Res 300 DPI PNG Export**: Direct 1-click snapshot via the UI top bar.

---

## 4. Statutory Compliance & Zero-Mock Standard
All pad dimensions, slope filters, flood corridors, and energy metrics are directly coupled to authoritative project manifests (`config/projects/*.json`) and raw GeoJSON datasets in `data/projects/`, strictly adhering to GDA2020 coordinate systems.
