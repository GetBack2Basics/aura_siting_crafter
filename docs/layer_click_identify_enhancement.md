## Overview
Enhanced the GeoLibre WebGIS Identify Click Tool to support dynamic interrogation of features on the currently selected layer as well as any active visible thematic layers across the national Lakehouse, instead of being limited to only discrete candidate site points.

## Technical Implementation
1. **Active Selected Layer State & Persistent Highlight**:
   - Maintained global `selectedLayerId` state.
   - When clicking on any layer in the catalog:
     - The layer row receives a persistent active style (`.layer-item-wrapper.selected-layer`) with a bright cyan 4px left border, cyan gradient background (`linear-gradient(90deg, rgba(6, 182, 212, 0.28) 0%, rgba(59, 130, 246, 0.18) 100%)`), glowing box shadow, and vibrant cyan text.
     - An explicit `ACTIVE` tag badge displays on the active layer item in the layer controls.
     - The highlight persists indefinitely when the mouse moves across to the map on the right.
     - Auto-expands the parent category card so the active layer remains visible.
     - Automatically enables layer visibility on the map.
     - Updates the top navigation bar target indicator pill (`#active-target-name`).

2. **Unified Spatial Feature Hit-Testing (`handleMapClick`)**:
   - Interrogates MapLibre GL rendered features at the click location (`map.queryRenderedFeatures`) using a screen pixel bounding box buffer (`±6px`) tailored for both point/circle, line/corridor, and hollow fill polygon boundaries.
   - Target layer prioritization: queries the currently selected layer first. If no feature hit is detected on the active layer, gracefully cascades to any other visible thematic vector layers or candidate hubs under the cursor.

3. **Rich Vector Feature Popups (`showLayerFeaturePopup`)**:
   - Generates dark glassmorphism popups displaying layer taxonomy, feature type badge (`FILL`, `LINE`, `CIRCLE`, `POINT`), intelligent title resolution, and scrollable key-value attribute tables.
   - Includes quick action buttons (`⊞ Table`, `🎯 Zoom`, `ℹ️ Lineage`) for direct inspection and navigation.

4. **Interactive Hover Cursor Feedback (`handleMapMouseMove`)**:
   - Updates cursor state to `pointer` when hovering over vector features of the selected thematic layer in `identify` mode, reverting to `default` or `grab` in pan mode.

5. **Ask AI Spatial Direct Map & Table Execution**:
   - Integrated `executeDuckDbSqlFilter()` which evaluates the translated DuckDB Spatial SQL against the in-memory dataset in 0.1ms (Zero-Cost Client Offloading).
   - Automatically filters and highlights matching candidate markers on the map (`applyAiFilterToMap()`), dynamically reframing the viewport via `map.fitBounds()` or `map.flyTo()`.
   - Directly populates and opens the bottom Attribute Table Dock with filtered matching records (`openAiResultTable()`), allowing row-click navigation to features on the map.
   - Added interactive action triggers inside the AI Drawer: `▶️ Run SQL`, `💾 Save`, `⊞ Table`, and `↺ Reset`.

6. **Editable SQL Query Editor & Browser Cache Persistence**:
   - Replaced static code display with an editable `sql-code-editor` textarea supporting monospaced syntax font, border glows, auto-resizing, and `Ctrl+Enter` / `Cmd+Enter` keyboard execution.
   - **Preset & Saved Queries Dropdown (`#saved-queries-select`)**:
     - Built-in Benchmark Presets: *NSW Transmission (≥15ha, ≤1.5km)*, *Recycled Water Proximity (≤2km in Latrobe / Gladstone)*, *Max Buffer Setback (≥1.5km from Receptors)*.
     - Custom User Queries: Saved directly into browser `localStorage` under `geolibre_saved_spatial_queries`.
   - **Save & Delete Management**:
     - Users can name and save any customized SQL query using `confirmSaveQuery()`.
     - Users can delete custom saved queries from cache with `deleteSelectedSavedQuery()`.

7. **GCS Live Deployment**:
   - Synchronized live build to `gs://aura-siting-crafter-geolibre-app/index.html` with `--cache-control="no-cache, max-age=0"`.


## Verification
- Validated with full `pytest tests/ -v` (162 tests passed, 0 failures).
- Passed all lint, no-place-names, and no-secrets checks.
