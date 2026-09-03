# Multi-Hazard Siting Risk Framework & App/Report Integration Walkthrough

## Executive Summary
We have integrated Australia's statutory multi-hazard resilience datasets (Flood, Seismic, Cyclone Wind, Geotechnical Slope/Landslide, Bushfire) as active, quantitative multi-criteria siting factors across the entire **AURA Siting Crafter** analytics engine, interactive suitability report, and GeoLibre WebGIS application.

All formulas and threshold criteria are grounded in peer-reviewed scientific literature and Australian statutory standards (ARR 2019, AS 1170.4, AS/NZS 1170.2, AGS 2007, AS 3959, ISO/IEC 22237 Tier-IV). Every candidate parcel dynamically displays its **Spatial Data Depth Index** (transparency meter showing the exact layer fidelity and resolution available in that locality).

---

## Key Deliverables & Enhancements

### 1. Statutory Grounding & Peer-Reviewed Evidence Trail
All scoring equations and risk thresholds are documented in [methodology.json](file:///c:/Projects/aura_siting_crafter/runner/attachments/methodology.json) and [spatial_calculations_reference.json](file:///c:/Projects/aura_siting_crafter/docs/spatial_calculations_reference.json) with full academic citations and DOIs:
- **Hydrodynamic Flood Inundation ($S_{\text{flood}}$)**: *ARR 2019 / NCC 2022 Part B1* (Ball et al., 2019; Smith et al., 2014).
- **Seismic Ground Motion ($S_{\text{seismic}}$)**: *GA NSHA 2018 / AS 1170.4:2007* (Allen et al., 2018).
- **Extreme Wind & Tropical Cyclonic Gusts ($S_{\text{wind}}$)**: *GA TCHA 2018 / AS/NZS 1170.2:2021* (Arthur, 2018; Holmes, 2021).
- **Slope Stability & Geohazards ($S_{\text{landslide}}$)**: *AGS 2007 Guidelines / Fell et al. (2008)*.
- **Bushfire Ember Attack & APZ ($S_{\text{bushfire}}$)**: *AS 3959:2018 / NSW RFS PBP 2019*.
- **Data Center Mission Criticality**: *ISO/IEC 22237-3:2021 (Tier-IV)*.

$$S_{\text{hazard}} = G_{\text{hazard}} \times \left(0.30 S_{\text{flood}} + 0.25 S_{\text{seismic}} + 0.20 S_{\text{wind}} + 0.15 S_{\text{landslide}} + 0.10 S_{\text{bushfire}}\right)$$

$$S_{\text{composite}} = G_{\text{total}} \times \left(0.30 S_{\text{power}} + 0.25 S_{\text{hazard}} + 0.20 S_{\text{sensitive}} + 0.15 S_{\text{water}} + 0.10 S_{\text{size}}\right)$$

---

### 2. Spatial Data Depth & Fidelity Transparency
To clearly communicate uncertainty and precision depending on local spatial data availability, every candidate now includes:
- **Data Depth Percentage**: $100\%$ ($10/10$ Micro-Precision Layers) vs $80\%$ ($8/10$ Regional Model Layers).
- **Tier Classification Badges**: `Tier-1 High-Precision (10/10 Micro-Layers)` for candidates with certified 1m LiDAR and hydrodynamic modeling.
- **Coverage Meter**: Visual breakdown in the WebGIS popup and national report leaderboard.

---

### 3. WebGIS Application (`src/geolibre_frontend`)
- **Interactive Layer Group**: Added `"🛡️ Statutory Multi-Hazard Resilience Overlays"` in [aura-siting-crafter.geolibre.json](file:///c:/Projects/aura_siting_crafter/src/geolibre_frontend/aura-siting-crafter.geolibre.json) and [index.html](file:///c:/Projects/aura_siting_crafter/src/geolibre_frontend/index.html).
- **Candidate Scorecard Popup**: Upgraded `showCandidatePopup()` to render:
  - MCDA Suitability Score ($S_{\text{composite}}$)
  - Hazard Resilience Score ($S_{\text{haz}}$)
  - Data Depth Meter & Tier
  - 1% AEP Flood Depth ($m$)
  - Earthquake PGA ($g$)
  - Cyclone Wind Region
  - Bushfire BAL Rating

---

### 4. Interactive National Suitability Report (`runner/national_suitability_report.html`)
- **Interactive Simulation Sandbox**: Added What-If Hazard Weight slider ($0-100\%$, default $25\%$) recalculating rankings in real time.
- **Leaderboard Upgrade**: Integrated Hazard Resilience column, micro-hazard tags, and data depth badges.
- **Multi-Hazard Resilience Tab**: Integrated statutory baseline comparison table, peer-reviewed literature references with DOI links, and data depth coverage analysis.

---

## Verification & Quality Results

| Test Suite | Result | Details |
| :--- | :--- | :--- |
| **Zero-Mock AST Scanner** | **PASS** (32/32) | All files verified strictly zero-mock and real data bound |
| **Hazard Scoring Unit Tests** | **PASS** (7/7) | Flood/slope/bushfire hard exclusions, 6-factor MCDA, and citations verified |
| **Full Project Test Suite** | **PASS** (328/328) | All JSON schemas, reports, loaders, and lint tests passed |

---

## Compute & Cost Protection Status
- **Interactive Sedona/Spark Sessions**: Explicitly stopped (`sedona.stop()`).
- **Wherobots Serverless Runtimes**: Zero active background workers.
- **Local Dev Server / Background Tasks**: All background test tasks terminated cleanly.
