# GeoLibre Deployment Plan on Google Cloud (Direct Wherobots S3 Zero-Copy & Thematic Spatial AI)

## Executive Summary

This document establishes the architecture and implementation roadmap for deploying a customized fork of **[opengeos/GeoLibre](https://github.com/opengeos/GeoLibre)** on **Google Cloud Platform (GCP)**. The platform connects **directly to the live Wherobots S3 storage root** (`wherobots://fgsdb/aura_siting`) as a **single source of truth with zero copying, cloning, or dataset conversion**. It exposes all S3 datasets in a structured **thematic layer catalog**, enables in-browser DuckDB-WASM GIS operations, integrates a conversational "Ask AI" natural language to Spatial SQL engine (Google Cloud Gemini + OpenRouter BYOK), and applies the dark-mode cartographic symbology from `runner/national_suitability_report.html`.

---

## 1. System Architecture (Strict Zero-Copy Direct Wherobots S3 Access)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          WHEROBOTS CLOUD STORAGE ROOT (AWS S3)                          │
│                                                                                         │
│   s3://wherobots-user-storage/.../aura_siting/  (Single Source of Truth)                 │
│   ├── candidates/ (datacenter_candidates_national.parquet)                              │
│   ├── energy/ (transmission_lines.parquet, substations.parquet, pmtiles)                │
│   ├── water/ (recycled_water_wwtw.parquet, rivers_riparian.parquet)                     │
│   ├── constraints/ (sensitive_receptors.parquet, biodiversity.parquet, slope.parquet)   │
│   ├── cadastre/ (cadastral_lots_hunter.parquet, state_parcels.parquet)                  │
│   └── micro_siting/ (precinct_boundaries, net_developable_pad, pipelines, rail)         │
└─────────────────────────────────────────▲───────────────────────────────────────────────┘
                                          │ Direct HTTPS / S3 Range Requests (Zero-Copy)
                                          │ No duplicate buckets, no data conversion
┌─────────────────────────────────────────┼───────────────────────────────────────────────┐
│                                GOOGLE CLOUD PLATFORM (GCP)                              │
│                                                                                         │
│   ┌────────────────────────────────┐                 ┌──────────────────────────────┐   │
│   │ Google Cloud Storage / CDN     │                 │ GCP Cloud Run (Serverless)   │   │
│   │ • Static GeoLibre Web App UI   │                 │ • FastAPI Spatial AI Proxy   │   │
│   │ • AURA Thematic Catalog Config │                 │ • Scale-to-Zero Container    │   │
│   │ • Dark Theme Assets & WASM     │                 │ • Gemini & OpenRouter Client │   │
│   └───────────────▲────────────────┘                 └──────────────▲───────────────┘   │
└───────────────────┼─────────────────────────────────────────────────┼───────────────────┘
                    │                                                 │
                    │ Static UI Assets & Catalog Defs                 │ Prompts & AI SQL
                    ▼                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                END-USER WEB BROWSER                                     │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ GeoLibre Web Application (AURA Siting Edition)                                  │   │
│   │  ┌──────────────────────────────┐           ┌─────────────────────────────────┐ │   │
│   │  │ Client-Side DuckDB-WASM      │           │ Conversational AI Spatial Chat  │ │   │
│   │  │ • Direct S3 Byte-Range SQL   │           │ • Default Free Tier (Gemini)    │ │   │
│   │  │ • Zero-Cost Local GIS Compute│           │ • BYOK Tier (OpenRouter)        │ │   │
│   │  └──────────────────────────────┘           └─────────────────────────────────┘ │   │
│   │  ┌────────────────────────────────────────────────────────────────────────────┐ │   │
│   │  │ Thematic Layer Tree (Full S3 Catalog Categorized & Grouped)                │ │   │
│   │  └────────────────────────────────────────────────────────────────────────────┘ │   │
│   │  ┌────────────────────────────────────────────────────────────────────────────┐ │   │
│   │  │ MapLibre GL JS Cartographic Viewport (Exact AURA Dark Mode Symbology)      │ │   │
│   │  └────────────────────────────────────────────────────────────────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Pillars

### 2.1 Single Source of Truth & Zero Data Duplication
- Spatial layers remain in their native Wherobots S3 location (`s3://wherobots-user-storage/.../aura_siting/`).
- **No data copying or cloning**: GeoLibre reads the Parquet and PMTiles files directly where Wherobots writes them.
- Any new run or pipeline calculation produced by Wherobots updates the S3 bucket and is immediately reflected in both the HTML reports and GeoLibre simultaneously.

### 2.2 Comprehensive Thematic S3 Layer Catalog
All datasets present in the S3 storage root are organized into intuitive thematic categories within GeoLibre's layer manager:
1. **⚡ Energy & Electrical Grid**: High-voltage transmission lines (voltage-tiered: $\ge$275kV Interstate, $\ge$132kV Regional, Local), substations, and power generating stations.
2. **💧 Water & Cooling Infrastructure**: Wastewater treatment plants (WWTW), recycled water outfalls, and river/riparian statutory 30m buffer zones.
3. **🛡️ Social & Environmental Receptors**: Sensitive receptors (schools, childcare, hospitals) with 500m EPA acoustic setbacks and sigmoidal buffer decay, residential meshblocks, and biodiversity exclusion zones.
4. **📐 Cadastre, Land Use & Topography**: Standardized lot/plan cadastre boundaries, DEM slope grade masks ($>5\%$), elevation heads ($\Delta h$), and pumped hydro potential (MWh).
5. **🏗️ High-Precision Precinct Micro-Siting**: Net Developable Pad Area (with TSF Dam buffer toggle), 20m linear infrastructure easements, and freight rail network paths.
6. **🎯 Data Center Candidate Parcels**: Siting candidate leaderboards with composite suitability scores ($S_{\text{power}}$, $S_{\text{sensitive}}$, $S_{\text{water}}$, $S_{\text{size}}$, $S_{\text{slope}}$).

### 2.3 Cartographic Symbology Matching `national_suitability_report.html`

| Layer | Symbology / Styling | Behavior & Filtering |
| :--- | :--- | :--- |
| **Dark Theme Canvas** | Background: `#0a0f1d`, Cards: `rgba(19, 26, 44, 0.75)`, Border: `rgba(59, 130, 246, 0.2)` | Carto Dark / MapLibre dark basemap |
| **Suitability Score Markers** | • Score ≥ 0.85 (Optimal): `#10b981` (Emerald)<br>• Score 0.70–0.85 (Moderate): `#f59e0b` (Amber)<br>• Score < 0.70 (Penalty): `#ef4444` (Rose) | Radius: `8 + (score * 6)` px; Rich popup showing power, water, buffer, and slope stats |
| **Power Transmission Grid** | • ≥275kV (Interstate): `#38bdf8` (Cyan, 3px)<br>• ≥132kV (Regional): `#60a5fa` (Blue, 2px)<br>• <132kV (Local): `#94a3b8` (Slate, 1px) | Dynamic zoom-dependent layer definitions (`capacity_kv`) |
| **Substations & Power Stations** | `#eab308` (Yellow circle marker with dark outline) | Cluster markers with substation capacity and fuel type |
| **Precinct Boundary** | `#1d4ed8` (Dashed blue line, weight 3, dash `5,5`, fillOpacity `0.03`) | Regional masterplan envelope |
| **Net Developable Area (NDA)** | `#14b8a6` (Teal polygon, fillOpacity `0.30` / `0.45` de-declared) | Net buildable pad area after setback subtractions |
| **Pipeline Corridors** | `#f97316` (Orange line, weight 3, opacity `0.9`) | 20m linear infrastructure corridor |
| **Rail Network** | `#0f172a` (Slate / dark navy line with `#475569` casing, weight 3.5) | Heavy freight rail network paths |
| **Biodiversity & Constraints** | `#881337` (Maroon/Rose polygon, fillOpacity `0.20`) | Environmental conservation buffers |

### 2.4 In-Browser GIS Operations via DuckDB-WASM
- **Direct S3 Range Queries**: In-browser DuckDB-WASM fetches Parquet row groups directly from Wherobots S3 with zero server computation cost.
- **Dynamic Multi-Criteria Evaluation (MCE)**: Interactive slider re-weighting computed client-side in under 1ms.
- **Persona Presets**: Pre-configured weighting presets (*General Public, Planner, Regulator, Developer, Community*).
- **Spatial Functions**: Native `spatial` extension execution (`ST_Point`, `ST_Distance`, `ST_Buffer`, `ST_Intersects`, `ST_Area`).

### 2.5 Conversational "Ask AI" Spatial Query Gateway (Cloud Run)
- **FastAPI AI Spatial Proxy**: Deployed on GCP Cloud Run with scale-to-zero configuration (`min-instances: 0` for $0 idle cost).
- **Schema-Aware Prompt Ingestion**: Injects table schemas of all S3 datasets into the LLM system prompt.
- **Dual-Tier Model Access**:
  - **Free Default Tier**: Google Cloud Gemini 2.5/3.7 Flash API key managed securely on Cloud Run.
  - **OpenRouter BYOK Tier**: Allows users to enter their own OpenRouter API key in GeoLibre settings for premium models (Claude 3.5 Sonnet, GPT-4o, DeepSeek-R1).
- **Workflow Loop**: User natural language question $\rightarrow$ Gemini/OpenRouter outputs DuckDB Spatial SQL $\rightarrow$ Browser executes SQL locally against Wherobots S3 data $\rightarrow$ Renders on MapLibre map and data grid.

---

## 3. Google Cloud Deployment Architecture

1. **Artifact Registry & Cloud Build**: Container build pipeline for GeoLibre frontend and FastAPI proxy.
2. **GCP Cloud Run**: Serverless container execution for FastAPI proxy with automatic scale-to-zero.
3. **Google Cloud Storage (GCS) + Cloud CDN**: Static web asset hosting (HTML/JS/CSS/WASM) with Cloud CDN caching.

---

## 4. Cost and Security Protections

- **Compute Teardown & Zero-Cost Idle**: Cloud Run automatically scales to 0 instances when no requests are active; DuckDB-WASM executes queries in client browsers with $0 server compute cost.
- **Security & Secret Hygiene**: All Gemini API keys and cloud credentials are kept in environment variables / Secret Manager; no private keys are exposed in client-side code or committed to Git.
