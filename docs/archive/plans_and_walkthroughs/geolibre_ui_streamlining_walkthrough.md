# Walkthrough: GeoLibre WebGIS UI Streamlining & Multi-Frame Resizing

The AURA Siting Crafter GeoLibre WebGIS application ([`index.html`](file:///c:/Projects/aura_siting_crafter/src/geolibre_frontend/index.html)) has been updated to streamline the interface, save horizontal screen space, add draggable multi-frame resizers, and provide full mobile responsiveness.

---

## Key Changes Implemented

### 1. Top Navbar Header & Navigation Actions
- **Branding**:
  - Primary title: **`🌐 AURA Siting Crafter`**
  - Subtitle: **`Australian urban & regional AI siting crafter`** (sentence case, clean typography, without "GeoLibre").
- **Clean Action Items**:
  - **`❔ Help`** (`openHelpModal()`): Opens the comprehensive System Guide with map navigation, layer controls, and GCP Serverless credit telemetry.
  - **`📑 Published Report`**: Direct link to the national suitability report (`runner/national_suitability_report.html`).
  - **`⬇️ GeoLibre JSON`** (`openGeolibreModal()`): Opens the desktop GIS integration guide popup with one-click project download.
  - **`✨ Ask AI`** (`toggleAiDrawer()`): Toggles conversational Spatial SQL engine.
  - **`🗺️ Basemap ▾`**: Compact button with an interactive popup card containing the Basemap selector AND Opacity slider (freeing horizontal navbar space).
  - Target layer badge and top credit badge removed from the navbar.

### 2. Hover-Only Layer Actions Menu
- In the left sidebar layer list, the action buttons (`🎚️` Opacity drawer, `ℹ️` Metadata lineage, `📊` Analytics charts, `⊞` Viewport attribute table) are wrapped in `.layer-actions`.
- `.layer-actions` is hidden by default (`opacity: 0; pointer-events: none;`) and smoothly appears only on layer row hover (`.layer-item-wrapper:hover`).
- Layer titles and corpus count badges have maximum horizontal breathing room.

### 3. Multi-Frame Draggable Resizers
- **Left Sidebar Resizer (`#sidebar-resizer`)**: Vertical splitter between Sidebar and Map allowing width adjustment (220px to 650px).
- **Attribute Table Resizer (`#dock-resizer`)**: Horizontal splitter on top of the dock allowing height adjustment (130px to 75vh).
- **AI Spatial Drawer Resizer (`#ai-drawer-resizer`)**: Vertical splitter on the left edge of the AI drawer allowing width adjustment (300px to 750px).
- Dynamic MapLibre canvas reflow (`map.resize()`) on pointer drag.

### 4. Floating Bottom-Left Interaction Mode Dock
- Moved the interaction mode switcher to the bottom-left corner of the map (`.map-mode-dock`).
- Buttons display **👆** (Identify/Popup) and **✋** (Pan Map) icons in compact pill format.
- On mouseover, smooth CSS transitions expand the text labels (`Click (Identify)`, `Hand (Pan)`).

### 5. Fixed & Enhanced Responsive SVG Charts
- Added responsive SVG `viewBox="0 0 600 260"` to prevent clipping across screen sizes.
- Added rich data distribution visualizations across all thematic layers:
  - **Candidate Sites**: Parcel area bars, suitability histogram, state distribution donut, substation vs water proximity scatter.
  - **NEM Substations**: Voltage tier distribution (500kV, 330kV, 275kV, 220kV, 132kV, 66kV).
  - **Transmission Lines**: Voltage hierarchy breakdown.
  - **Recycled Water / WWTW**: Plant capacity tiers (Tier 1 ≥50 ML/d to Tier 4).
  - **Sensitive Receptors**: School types (Primary, Secondary, Combined, Special).
  - **Protected Areas**: IUCN reserve categories (National Parks, Nature Reserves, Conservation Areas).

### 6. Mobile & Touch Screen Responsiveness
- Collapsible off-canvas sidebar drawer with backdrop overlay for screens $\le 768\text{px}$.
- Mobile `☰ Layers` toggle button in the navbar.
- 44px minimum touch targets and adaptive modal dialog sizing.

---

## Verification Results

- **Automated Lint Tests**:
  ```powershell
  pytest tests/lint/ -v
  # 156 passed, 1 skipped in 4.11s (100% PASS)
  ```
- **Compute & Instance Status**: No unmanaged cloud instances or lingering background compute tasks remain active.
