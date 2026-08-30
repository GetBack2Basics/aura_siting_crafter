# Implementation Plan: GeoLibre UI Streamlining, Resizable Frames & Mobile Optimization

Streamline and enhance the AURA Siting Crafter GeoLibre WebGIS interface based on design feedback:
1. **Layer Action Menu**: Visible only on layer row hover to give maximum horizontal space to layer names and count badges.
2. **Multi-Frame Resizers**: Draggable splitters for Left Sidebar (width), Bottom Attribute Dock (height), and Right AI Drawer (width) with map reflow.
3. **Top Navbar Overhaul**:
   - Header: **AURA Siting Crafter** with sentence-case subtitle: *Australian urban & regional AI siting crafter* (without GeoLibre).
   - Remove Target Layer badge.
   - `?` Help button bringing up the complete system guide & serverless credit telemetry.
   - `📑 Published Report` link to `runner/national_suitability_report.html`.
   - `⬇️ GeoLibre JSON` opening the Desktop GIS Integration guide modal with instant download.
   - `✨ Ask AI` button to open conversational Spatial SQL.
   - Basemap button with popover containing basemap switcher AND opacity slider.
4. **Bottom-Left Map Mode Switcher**:
   - Move Hand (✋) and Finger (👆) mode switchers to the bottom-left of the map.
   - Icon-only by default; expands informative text on hover.
5. **Interactive Charts Fix & Enhancement**:
   - Fix chart rendering across all layers with responsive SVG `viewBox`.
   - Provide rich data breakdown charts for candidate sites (area, suitability score, state distribution, proximity scatter) and thematic infrastructure/environmental layers (voltage tier, IUCN reserve class, school type, etc.).
6. **Mobile & Responsive Optimization**:
   - Adaptive navbar, collapsible off-canvas layer and AI drawers for touch devices, 44px touch targets.

---

## User Review Required

> [!NOTE]
> - **Basemap Popover**: Clicking the Basemap button opens a sleek dropdown popover containing both the basemap style picker and the basemap opacity slider.
> - **GeoLibre JSON Modal**: Clicking GeoLibre JSON displays a guide on desktop GIS access (S3 lakehouse layers, DuckDB-WASM, QGIS/ArcGIS integration) and provides the direct file download button.
> - **Charts Support**: All layers now display meaningful data visualizations (SVG responsive breakdown bars, donuts, and histograms).

---

## Proposed Changes

### WebGIS Frontend (`src/geolibre_frontend/index.html`)

#### [MODIFY] [index.html](file:///c:/Projects/aura_siting_crafter/src/geolibre_frontend/index.html)

1. **Header & Navigation Bar**:
   - Replace title/subtitle markup with:
     ```html
     <div class="nav-brand-container">
       <div class="nav-title">🌐 AURA Siting Crafter</div>
       <div class="nav-subtitle">Australian urban & regional AI siting crafter</div>
     </div>
     ```
   - Add top action links:
     - `? Help` button -> `openHelpModal()`
     - `📑 Published Report` -> opens `/runner/national_suitability_report.html`
     - `⬇️ GeoLibre JSON` -> `openGeolibreModal()`
     - `✨ Ask AI` -> `toggleAiDrawer()`
     - `🗺️ Basemap` dropdown popover with embedded opacity slider.

2. **Hover-Only Layer Actions Menu**:
   - Wrap layer action buttons (`🎚️`, `ℹ️`, `📊`, `⊞`) in `.layer-actions`.
   - Style `.layer-actions` with `opacity: 0; pointer-events: none; transition: opacity 0.15s ease;` and reveal on `.layer-item-wrapper:hover`.

3. **Draggable Resizers**:
   - Add `#sidebar-resizer` between Sidebar and Map.
   - Add `#dock-resizer` above Attribute Table Dock.
   - Add `#ai-drawer-resizer` on AI Drawer edge.
   - Wire unified pointer drag listeners and trigger `map.resize()`.

4. **Floating Bottom-Left Mode Controls**:
   - Place `.map-mode-dock` at the bottom-left of `#map-wrapper`.
   - Icons: 👆 (Identify) and ✋ (Pan).
   - Hover reveals text label smoothly.

5. **Enhanced Responsive Charts**:
   - Fix `openChartModal(layerId)` and `renderActiveChart(chartType)`.
   - Use SVG `viewBox="0 0 600 260"` for responsive scaling on desktop and mobile.
   - Add layer-specific breakdown logic for NEM substations (voltage levels), transmission lines, candidate sites (score histogram, area bars, state donut, scatter), and protected/water layers.

6. **GeoLibre JSON Modal (`#geolibre-modal`)**:
   - Explains how to load S3 lakehouse data in GeoLibre Desktop / QGIS / DuckDB.
   - Direct download button for `aura-siting-crafter.geolibre.json`.

7. **System Help Modal (`#help-modal`)**:
   - Comprehensive User Guide covering Map Navigation, Identify Popups, Spatial SQL AI, Viewport Attribute Filtering.
   - Live GCP Serverless Credit & Cost Telemetry ($0.00/hr active compute, scale-to-zero).

8. **Mobile CSS & Drawer Toggles**:
   - Mobile media queries (`@media (max-width: 768px)`).
   - Off-canvas sidebar toggle button for mobile screens.

---

## Verification Plan

### Automated Verification
- Run project lint gate:
  ```powershell
  pytest tests/lint/ -v
  ```

### Manual & Interactive Verification
- Verify navbar layout, title, sentence-case subtitle, and top action buttons.
- Hover over layer items to verify actions appear on hover only.
- Test dragging panel resizers (Sidebar, Table Dock, AI Drawer).
- Test bottom-left 👆 (Identify) and ✋ (Pan) mode toggle buttons with hover labels.
- Test Basemap popover with embedded opacity slider.
- Test 📊 Charts across multiple layers and verify responsive SVG rendering.
- Open GeoLibre JSON modal and test download functionality.
- Open `?` Help modal and verify system guide & credit telemetry.
- Test mobile viewport layout (<768px).
