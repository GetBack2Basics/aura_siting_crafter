# 🚀 Launching AURA Siting Crafter & GeoLibre WebGIS v1.0: Zero-Copy, Serverless Spatial AI for National Infrastructure

Excited to unveil **AURA Siting Crafter** (Australian Urban & Regional AI Siting Crafter) and **GeoLibre WebGIS v1.0** — an open, cloud-native spatial multi-criteria decision analysis (MCDA) and precision siting platform for critical infrastructure and next-gen data centers across Australia. 🇦🇺⚡

Finding optimal, low-risk sites for multi-gigawatt compute hubs, transmission connections, and clean energy assets usually takes months of siloed GIS consultancy. We engineered an end-to-end, zero-copy, serverless geospatial pipeline that delivers live national site intelligence in milliseconds.

---

### 🌐 What’s New in AURA Siting Crafter & GeoLibre WebGIS:

1️⃣ **Direct Zero-Copy Lakehouse Streaming**
• Direct HTTP range requests against Wherobots Cloud GeoParquet lakehouses (`s3://wherobots-user-storage/aura_siting/`).
• Zero data duplication or slow ETL hops — updates in cloud spatial storage stream instantly to the browser.

2️⃣ **Zero-Cost Client-Side Scenario Simulation**
• Offloaded heavy MCDA parameter re-scoring and sensitivity curves to in-browser DuckDB-WASM and JavaScript.
• Adjust power, water, cooling, and environmental weights in real time with instant viewport re-ranking — at **$0 server compute cost**.

3️⃣ **Conversational Spatial AI Assistant (Cloud Run)**
• Natural language to Spatial SQL agent deployed on Google Cloud Run (`australia-southeast1`).
• Translates queries like *"Show me candidate parcels >50 ha within 5 km of 330kV transmission and recycled water"* into live DuckDB spatial queries with scale-to-zero efficiency.

4️⃣ **Streamlined WebGIS & Multi-Frame Resizing**
• Interactive MapLibre GL engine with draggable splitters for sidebar, attribute tables, and AI drawer.
• Hover-activated layer telemetry, responsive SVG distribution charts (NEM voltage tiers, water capacity, slope grades), and mobile-responsive off-canvas drawer.

5️⃣ **100% Real Data Integrity (Zero-Mock Standard)**
• Fully grounded in authoritative data: AEMO transmission topology (500kV to 66kV), Geoscience Australia, NSW Spatial Services cadastre, EPA sensitive receptor setbacks, and BoM hydrology.

---

### 🛠️ The Tech Stack:
- **Spatial Lakehouse**: Wherobots Cloud / Apache Sedona / GeoParquet / Iceberg
- **Serverless AI Gateway**: FastAPI + Cloud Run + DuckDB Spatial
- **Client Engine**: MapLibre GL JS + DuckDB-WASM + Vanilla JS / CSS
- **Automated Quality**: Pytest lint gates ensuring 0 secret leaks & strict catalog validation

The future of infrastructure planning is transparent, instantaneous, and cloud-native.

Check out the documentation and live deployment in the repository! 🔗👇

#Geospatial #SpatialAI #DataCenters #CleanEnergy #GIS #Wherobots #GoogleCloud #CloudRun #ApacheSedona #DuckDB #Infrastructure #OpenSource #Innovation
