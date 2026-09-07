# Project-Specific Siting Architecture & Site Enhancement Plan (_LMCC_MacquarieCoal)

## Executive Summary & Commercial Yield Framework

This architecture plan formalizes the methodology for delivering **Project-Specific Siting Deliverables & High-Resolution Interactive Applications** (patterned as `_{Org/LGA}_{ProjectName}`, e.g., `_LMCC_MacquarieCoal`).

By bridging national-scale candidate screening with micro-level statutory synthesis, AURA extracts maximum net developable land yield while insulating institutional buyers and planning authorities from developmental liability.

```mermaid
graph LR
    subgraph National["1. Continental Macro Baseline"]
        N1["15.4M Cadastral Parcels<br/>(National Siting Viewer: index.html)"]
        N2["Synchronized Statutory Hazard Grids<br/>(ARR 2019, Seismic, Wind, Bushfire)"]
    end

    subgraph DeepBridge["2. Authenticated Bridge"]
        B1["Candidate Deep-Link<br/>(AURA-NSW-0001)"]
    end

    subgraph ProjectSpecific["3. Micro-Level Precision Yield"]
        P1["10 Certified Net Developable Pads<br/>(64.0% Net-to-Gross vs. 42.0% Baseline)"]
        P2["3D Topographic Land Reclamation<br/>(Acoustic Bunds & 1% AEP Flood Cuts)"]
        P3["Sovereign Utility Synthesis<br/>(330kV Grid & 1.2 GL/yr Recycled Cooling)"]
    end

    National --> DeepBridge --> ProjectSpecific

    style National fill:#1e293b,stroke:#3b82f6,color:#f8fafc
    style DeepBridge fill:#1e1b4b,stroke:#818cf8,color:#ffffff,stroke-width:2px
    style ProjectSpecific fill:#0f2942,stroke:#38bdf8,color:#ffffff,stroke-width:2px
```

---

## 1. Flagship Implementation: Macquarie Coal Complex (`_LMCC_MacquarieCoal`)

Synthesizing all 15 public exhibition technical studies (>135 MB of engineering, geotechnical, and environmental data), AURA resolves critical site friction points into **9 certified commercial components**:

```mermaid
flowchart TD
    subgraph NationalMaster["National Master Baseline (Untouched)"]
        N1["National Siting Viewer (index.html)"] -->|Click Candidate Site AURA-NSW-0001| N2["Site Modal & Link"]
        N3["National Report (national_suitability_report.html)"]
    end

    subgraph ProjectProducts["Project-Specific Deliverables (_LMCC_MacquarieCoal)"]
        N2 -->|Authenticated Deep-Link| P1["Project Interactive WebGIS (index_LMCC_MacquarieCoal.html)"]
        N2 -->|Authenticated Deep-Link| P2["Site Statutory Report (report_LMCC_MacquarieCoal.html)"]
        
        P1 & P2 --> S1["1. 10 Net Developable Pads (NDPs) & 3-Phase Staging (320.1 ha)"]
        P1 & P2 --> S2["2. TSF Consolidation & Bearing Capacity (25 kPa -> >150 kPa)"]
        P1 & P2 --> S3["3. 330kV Substation Reserve + 49 MWh Pit-Void PHES Model"]
        P1 & P2 --> S4["4. 1.8km Rail Intermodal Loop + 7.8km Haul Road Arterial Spine"]
        P1 & P2 --> S5["5. Subsidence Advisory NSW Foundation Matrix (Zones G1-G3)"]
        P1 & P2 --> S6["6. 250m C2 Koala Bio-Link & Engineered Fauna Overpasses"]
        P1 & P2 --> S7["7. 3D Overburden Acoustic Bunds (35 dBA Nighttime Criteria)"]
        P1 & P2 --> S8["8. Edgeworth WWTW Recycled Cooling Pipeline (1.2 GL/yr Savings)"]
        P1 & P2 --> S9["9. Site vs. National Comparative Benchmark Card (64% Yield)"]
    end

    style NationalMaster fill:#1e293b,stroke:#f59e0b,color:#f8fafc
    style ProjectProducts fill:#0f2942,stroke:#38bdf8,color:#ffffff,stroke-width:2px
```

### 1.1 Specific Engineering Layers & Commercial Deliverables:
1. **10 Certified Net Developable Pads (NDPs) with Staging Geometry:**
   - **Pads A1–A4 (48.5 ha hardstand):** Fully remediated plateaus for hyperscale sovereign AI data centres.
   - **Pads B1–B3 (72.0 ha void floor):** Engineered benched pads for heavy clean-tech manufacturing.
   - **Pads C1–C2 (34.2 ha portal logistics):** Direct arterial connection to Cessnock Road and rail siding.
   - **Pad D1 (85.0 ha TSF solar/storage plateau):** Consolidated tailings land for solar PV and 100MW BESS.
   - **3-Phase Staging Schedule:** Phase 1 Immediate (Years 0–3: 82.7 ha), Phase 2 Medium-Term (Years 3–7: 125.4 ha), Phase 3 Long-Term (Years 7–12+: 112.0 ha).
2. **TSF & Dams Safety NSW De-Declaration Sandbox:**
   - 3D isopach tailings contours (up to 18m fine reject).
   - Dynamic wick-drain consolidation simulation showing settlement rate and bearing capacity evolution from 25 kPa to >150 kPa.
3. **Sovereign High-Voltage & Micro-Pumped Hydro (PHES) Scheme:**
   - SP2 Substation pad geometry (4.5 ha) with 330kV/132kV dual-bus layout.
   - Hydraulic cross-section: 120m elevation head between upper reservoir (+145m AHD) and pit void (+25m AHD), delivering up to 49.0 MWh daily storage capacity at 78% round-trip efficiency.
4. **Macquarie Intermodal Rail Terminal (MIRT) & Heavy Haul Road Corridor:**
   - 1.8 km rail loop geometry with 650m siding staging tracks and reach-stacker hardstand.
   - 7.8 km gazetted internal haul road arterial bypassing Barnsley and Teralba residential streets.
5. **Subsidence Advisory NSW Pre-Approved Foundation Matrix:**
   - Overlay of underground workings across Great Northern, Fassifern, and Young Wallsend seams.
   - Foundation engineering lookup: Zone G1 shallow spread footings, Zone G2 articulated stiffened rafts, Zone G3 pressure-grouted void piles.
6. **Sugarloaf-to-Awaba C2 Biodiversity Bio-Link:**
   - 250m–300m ecological corridor (~320 ha) with preferred Koala feed tree density targets and 2 engineered fauna overpasses along the haul road.
7. **3D Overburden Acoustic Bunds & Topographical Sound Shield:**
   - 6m–8m sculpted earthen bunds reclaiming 45 ha of land that naive 2D buffer circles would exclude.
   - Validates strict compliance with NSW EPA **35 dBA night-time criteria** at Barnsley, Teralba, and Wakefield residential receivers.
8. **Edgeworth WWTW Recycled Water Pipeline (Zero Potable Cooling):**
   - 4.2 km dual-pipe alignment connecting Edgeworth WWTW to the precinct boundary, delivering **1.2 GL/year potable water savings**.
9. **Site vs. National Comparative Benchmark Card:**
   - *Transmission Offset:* 0.35 km (Macquarie) vs. 4.8 km (National Avg) — **Top 5%**
   - *Net-to-Gross Yield:* 64% (Macquarie) vs. 42% Regional Benchmark.
   - *Water Circularity:* 100% Recycled vs. 35% Potable Reliance.

---

## 2. Standardized Multi-Project Ingestion & Report Generation Blueprint

To enable third parties (councils, industrial developers, energy consortiums) to submit site data and receive an automated, audit-ready site package, AURA establishes a repeatable 4-part framework:

```mermaid
flowchart TD
    subgraph Submission["1. Proponent Data Submission"]
        P1["Proponent Engineering Studies & Vectors<br/>(CAD / GIS / Boreholes / EIS Reports)"] --> P2["Structured Project Manifest<br/>(Standardized Spatial Configuration)"]
    end

    subgraph Verification["2. Automated Statutory & Geometric Gate"]
        P2 --> V1["Schema & Topology Validation<br/>(GDA2020 CRS & Boundary Checks)"]
        V1 --> V2["Topological Net Developable Area Audit<br/>(Multi-Hazard Constraint Subtraction)"]
    end

    subgraph Deliverables["3. Certified Decision Packages"]
        V2 --> D1["Interactive Project WebGIS Portal<br/>(Pad Staging & Localized Spatial Engine)"]
        V2 --> D2["Statutory Site Assessment Report<br/>(Audit-Ready Planning Panel Dossier)"]
        V2 --> D3["National-to-Site Deep-Link Bridge<br/>(Macro Baseline to Micro Inspection)"]
    end

    style Submission fill:#1e293b,stroke:#3b82f6,color:#f8fafc
    style Verification fill:#1e1b4b,stroke:#818cf8,color:#ffffff,stroke-width:2px
    style Deliverables fill:#065f46,stroke:#34d399,color:#ffffff,stroke-width:2px
```

---

## 3. Executive Delivery Architecture & Asset Integration

1. **Structured Manifest Specifications**: Standardizes proponent metadata, engineering capacity targets (power MVA, recycled water GL/yr), and localized micro-layer geometries into a unified, version-controlled format.
2. **Dedicated Project Spatial Portals**: Each project receives a self-contained, high-performance WebGIS application featuring pad staging timelines, infrastructure overlays, and real-time DuckDB-WASM analytical filtering.
3. **Statutory Decision Dossiers**: Automated generation of publication-grade assessment reports containing comparative benchmark radar matrices, geotechnical foundation engineering schedules, and environmental bio-link allocations.
4. **National Macro-to-Micro Continuity**: Seamless transition from Australia-wide candidate identification to deep site-level forensic due diligence via authenticated deep-linking.

---

## 4. Statutory Verification & Quality Assurance Protocol

Every submitted project package undergoes rigorous automated and statutory quality assurance prior to certification:

1. **Automated Schema & Quality Gate Enforcement**: Ingested datasets are scanned against strict schema definitions to verify structural integrity and data provenance before pipeline processing.
2. **Geometric & Topological Integrity Audits**: Automated spatial validation verifies that all developable pad polygons sit strictly within precinct boundaries, contain zero self-intersections, and maintain statutory clearance from ecological conservation corridors.
3. **Statutory Benchmark Verification**: Geotechnical, acoustic, and hydraulic metrics are benchmarked against NSW EPA, ARR 2019, and Subsidence Advisory guidelines to ensure full compliance before planning panel exhibition.
4. **Interactive Digital Twin Audit**: Visual inspection confirms pad staging schedules, multi-layer toggling, and client-side analytical calculations operate with sub-second responsiveness across all target stakeholder devices.
