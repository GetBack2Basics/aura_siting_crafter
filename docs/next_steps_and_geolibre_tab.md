# Next Steps: GeoLibre Open-Source AI Spatial Platform Integration

## Executive Summary

The primary next step for the **National Data Center Siting Suitability Model** (`aura_siting_crafter`) is connecting our spatial outputs to an open-source [opengeos/GeoLibre](https://github.com/opengeos/GeoLibre) deployment hosted serverless on **Google Cloud Platform (GCP)** to enable free public conversational spatial analytics ("Ask AI") using DuckDB-WASM and Gemini.

---

## 1. GeoLibre AI Spatial Platform Architecture on Google Cloud Platform (GCP)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                GOOGLE CLOUD PLATFORM (GCP)                              │
│                                                                                         │
│   ┌────────────────────────────────┐                 ┌──────────────────────────────┐   │
│   │ Google Cloud Storage (GCS)     │                 │ GCP Cloud Run (Serverless)   │   │
│   │                                │                 │                              │   │
│   │ • GeoParquet Suitability Data  │◄────────────────┤ • FastAPI Spatial AI Proxy   │   │
│   │ • PMTiles Vector Layers        │ (Direct HTTP)   │ • Scale-to-Zero Container    │   │
│   │ • Static GeoLibre App UI       │                 │ • Gemini & OpenRouter Client │   │
│   └───────────────▲────────────────┘                 └──────────────▲───────────────┘   │
└───────────────────┼─────────────────────────────────────────────────┼───────────────────┘
                    │                                                 │
                    │ static assets & byte-range queries              │ Prompts & AI SQL
                    ▼                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                END-USER WEB BROWSER                                     │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ GeoLibre Web Application (Free Web Platform)                                    │   │
│   │                                                                                 │   │
│   │  ┌─────────────────────────────┐           ┌─────────────────────────────────┐  │   │
│   │  │ Client-Side DuckDB-WASM     │           │ AI Spatial Chat Drawer          │  │   │
│   │  │ (Zero-Cost In-Browser SQL)  │           │ (Free Tier + BYOK OpenRouter)   │  │   │
│   │  └─────────────────────────────┘           └─────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Shared Cloud Data Storage Architecture (Wherobots & GeoLibre Integration)

Rather than maintaining separate file servers or copying data onto local web server disk storage, GeoLibre and Wherobots share the exact same cloud-native dataset repository:

1. **Zero-Duplication Central Data Layer**:
   - Wherobots Cloud (Apache Sedona Spark) outputs suitability modeling layers directly into a central Google Cloud Storage (GCS) / S3 bucket as **GeoParquet** and **PMTiles**.
   - GeoLibre queries these exact same files in GCS without needing any dataset conversion or server duplication.

2. **HTTP Range-Request Querying**:
   - GeoLibre’s in-browser DuckDB-WASM engine fetches only the required byte ranges and spatial row groups via HTTP range requests (`read_parquet('https://storage.googleapis.com/.../datacenter_candidates.parquet')`).
   - Eliminates downloading large files to the client or maintaining expensive local web server NVMe storage drives.

3. **Cloud-Native Storage Tradeoff Analysis**:

```
Architecture Model         Data Sync / Duplication    Storage & Server Cost        Scalability
---------------------------------------------------------------------------------------------------------
Shared Cloud Storage (GCS) Zero Duplication (Unified)  Near-Zero (~$0.02/GB/mo)     Infinite Public Scale
Local Web Server Storage   High Duplication Needed     Expensive Server Disks       Constrained by VM I/O
```

---

## 3. Free Public Conversational AI Workflow ("Ask AI")

1. **User Ask**: The user types a natural language query in the GeoLibre chat drawer:  
   *"Show me all candidate sites in VIC larger than 10 hectares that are within 2km of high-voltage transmission lines and at least 1km away from any school or hospital."*
2. **AI Translation**: GeoLibre sends the user prompt + active dataset schemas to the FastAPI gateway on GCP Cloud Run. Cloud Run queries Gemini LLM to generate DuckDB Spatial SQL:
   ```sql
   SELECT site_name, area_ha, power_dist_km, sensitive_dist_km, suitability_score
   FROM read_parquet('https://storage.googleapis.com/hunter-spatial-data/datacenter_candidates.parquet')
   WHERE state = 'VIC' 
     AND area_ha > 10.0 
     AND power_dist_km <= 2.0 
     AND school_dist_km >= 1.0 
     AND hospital_dist_km >= 1.0;
   ```
3. **In-Browser Compute**: The SQL query is executed directly inside the user's browser using DuckDB-WASM, fetching only required byte ranges from GCS using HTTP range requests.
4. **Instant Visualisation**: GeoLibre renders matching candidates on an interactive Mapbox/Leaflet map with dynamic stats and spatial boundaries.

---

## 4. Dual-Model LLM Access: Free Tier & OpenRouter BYOK

Inspired by [GetBack2Basics/LivePersonaCrafter](https://github.com/GetBack2Basics/LivePersonaCrafter), GeoLibre provides a flexible dual-tier model:
- **Free Default Tier**: Powered by Google Cloud Gemini API (hosted on Cloud Run), allowing the public to ask natural language questions for free without creating accounts.
- **OpenRouter BYOK Tier**: Users can enter their own OpenRouter API key directly in the GeoLibre settings drawer to unlock premium models (e.g., Claude 3.5 Sonnet, GPT-4o, DeepSeek-R1, Llama 3) for specialized spatial reasoning.

---

## 5. Planned Conversational AI Benchmark Queries

- *"Show me all candidate sites in NSW within 2km of 330kV transmission lines that are at least 1km away from schools and child care centers."*
- *"Which sites in Latrobe Valley or Gladstone score highest for recycled water availability without impacting residential meshblocks?"*
- *"Find data center parcels co-located within Renewable Energy Zones that have over 15 hectares of developable land."*
- *"Compare the developable pad area of the Macquarie Coal Complex against the proponent masterplan after deducting 30m riparian buffers and slope constraints."*
