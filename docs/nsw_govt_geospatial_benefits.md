# Strategic Value & Application Guide: AURA Siting Crafter for NSW Government Geospatial Teams

**Target Audience:** Senior Geospatial Leadership & Engineers (NSW Spatial Services, Department of Planning, Housing and Infrastructure – DPHI, Environment, and Land Administration)  
**Reference Portal:** [NSW Spatial Services](https://www.spatial.nsw.gov.au/)  
**Document Purpose:** Strategic and technical summary of how the `aura_siting_crafter` architecture and spatial ETL capabilities deliver operational efficiencies to NSW Government land, planning, and environmental operations.

**Context & Scope:** This project demonstrates the architectural advantages of adopting Apache Sedona, Wherobots Cloud, and GeoParquet workflows. Key potential applications in state programs include SLATS land-clearing monitoring, DCDB cadastral analysis, and bushfire risk computation on state HPC clusters.

---

> [!IMPORTANT]
> ### ⚡ Executive Briefing: Core Architecture Takeaways
> * **Accelerated Processing:** Precinct Net Developable Area (NDA) and constraint modeling (flood, mine subsidence, biodiversity) execute via distributed Apache Sedona PySpark rather than manual single-threaded desktop GIS.
> * **State-Wide Scale (3.5M+ Parcels):** Distributed spatial indexing handles the entire NSW Digital Cadastral Data Base (DCDB) and ABS Meshblocks without memory bottlenecks.
> * **Direct API Integration:** Ingests live layers from the **NSW SEED Portal**, Transport for NSW, and municipal Open Data APIs, reducing reliance on local shapefiles.
> * **Spatial Digital Twin Compatibility:** Uses cloud-native **GeoParquet**, enabling direct interoperability with the NSW Spatial Digital Twin, DuckDB, QGIS, and web viewers without proprietary file conversions.
> * **Reproducible Governance:** Replaces desktop GIS project files with version-controlled Python/SQL pipelines suitable for statutory and audit requirements.

---

## Executive Summary

The **AURA Siting Crafter** repository implements a cloud-native spatial ETL and multi-criteria constraint modeling pipeline using **Apache Sedona (PySpark)**, **Wherobots Cloud Spatial SQL**, and **GeoParquet**. Originally applied to precinct transformation in the Macquarie Coal Complex (Lake Macquarie / Hunter region), the pipeline architecture serves as a repeatable template for state-wide cadastral, planning, environmental, and infrastructure datasets.

By replacing desktop-bound GIS workflows with distributed spatial computing, this codebase enables processing of property boundaries, environmental layers, and terrain models while maintaining code versioning, auditability, and interoperability with the **NSW Spatial Digital Twin**.

---

## Technical Capabilities by NSW Government Domain

```
+-----------------------------------------------------------------------------------+
|                              AURA SITING CRAFTER                                  |
|          Apache Sedona (PySpark) | Wherobots Spatial SQL | GeoParquet              |
+-----------------------------------------------------------------------------------+
          |                                  |                                  |
          v                                  v                                  v
+-----------------------+          +-----------------------+          +-----------------------+
|  PLANNING & HOUSING   |          |      ENVIRONMENT      |          |     LAND ADMIN &      |
|     PRECINCTS         |          |    & NATURAL DATA     |          |   SPATIAL SERVICES    |
| • Net Developable Area|          | • SEED Portal Ingest  |          | • 3.5M+ Parcel Joins  |
| • 5-Tier Constraint   |          | • Hydro & Biodiversity|          | • GDA2020 Standard    |
| • Accelerated TOD/REZ |          | • Mine Subsidence     |          | • Spatial Digital Twin|
+-----------------------+          +-----------------------+          +-----------------------+
```

### 1. Planning & Precinct Transformation (DPHI & Regional NSW)
* **Automated Net Developable Area (NDA) Calculation:**
  * **Operational Context:** Buffering and clipping environmental, physical, and infrastructure constraints across large precincts (e.g. Hunter transformation, Renewable Energy Zones, TOD precincts) can be time-intensive in desktop GIS.
  * **Pipeline Implementation:** `src/Ingestion/spatial_ingest.py` automates the ingestion, buffering, and topological subtraction of water bodies, high-value biodiversity, power lines, and active rail corridors to output quantified Net Developable Zones.
  * **Impact:** Accelerates site assessment turnaround, enabling rapid scenario modeling for state housing targets and precinct master planning.

* **5-Tier Multi-Criteria Siting & Suitability Engine:**
  * **Operational Context:** Balancing competing land-use constraints (geological hazards, terrain slope, flood outfalls, grid proximity).
  * **Pipeline Implementation:** `src/Analysis/national_suitability_analysis.py` implements a 5-tier overlay framework (Terrain/DEM, Mine Subsidence, Flood Risk, Power Infrastructure, and Protected Habitat).
  * **Impact:** Provides a transparent spatial decision matrix configurable for any precinct across NSW.

---

### 2. Environment & Heritage (NSW SEED & Natural Resources)
* **Direct SEED & Open Data Portal Integration:**
  * **Capability:** Programmatically ingests state spatial datasets (NSW SEED Portal hydrography & biodiversity layers, municipal open data, ABS Meshblocks).
  * **Impact:** Eliminates manual data downloads; ensures planning assessments use current authoritative APIs.

* **Automated Environmental Buffer & Constraint Masking:**
  * **Capability:** Constructs precision buffer zones (e.g., 50m riparian corridors, 100m biodiversity protection buffers, mine subsidence exclusion zones).
  * **Impact:** Enforces statutory environmental compliance prior to detailed precinct design.

---

### 3. Land Administration & Cadastre (Spatial Services NSW / DCDB)
* **High-Scale Cadastral & Meshblock Spatial Joins:**
  * **Capability:** Leverages distributed spatial index matching (`R-Tree` / `Quad-Tree`) via Apache Sedona to execute spatial joins over state-wide cadastre (~3.5M+ land parcels in NSW) without memory overflow.
  * **Impact:** Enables rapid attribute enrichment across the entire NSW Digital Cadastral Data Base (DCDB) and ABS Meshblocks.

* **Native Projection & Coordinate Reference System (CRS) Management:**
  * **Capability:** Programmatic handling of Australian spatial standards (`EPSG:7856` - GDA2020 / MGA Zone 56 to `EPSG:4326` WGS84) with automated geometry validation (`ST_IsValid`, `ST_MakeValid`).
  * **Impact:** Maintains positional accuracy required for land administration and legal cadastral overlays.

---

### 4. Enterprise Spatial IT, Spatial Digital Twin & Open Standards
* **Open Formats & Interoperability (GeoParquet):**
  * **Capability:** Exports spatial datasets in cloud-native **GeoParquet**, directly readable in QGIS, ArcGIS Pro, DuckDB, Python, and MapLibre/Mapbox web viewers.
  * **Impact:** Eliminates proprietary format lock-in and optimizes storage/query performance for the **NSW Spatial Digital Twin**.

* **Auditability & DevOps Infrastructure:**
  * **Capability:** Replaces desktop project files with version-controlled Python/SQL scripts, Jupyter notebooks (`notebooks/Spatial_ETL_Pipeline.ipynb`), and HTML status runners (`runner/etl_runner.html`).
  * **Impact:** Fully reproducible pipelines suitable for government audit standards, continuous integration (CI/CD), and automated batch schedules.

* **Cloud Resource Safety & Cost Control:**
  * **Capability:** Includes built-in cluster teardown hooks (`sedona.stop()`, `spark.stop()`) and scale-to-zero serverless configurations.
  * **Impact:** Prevents unintended compute expenditure on Wherobots, AWS, or GCP platforms.

---

## Feature Comparison: Traditional Desktop GIS vs. AURA Siting Crafter Architecture

| Feature / Domain Capability | Traditional Desktop GIS (Manual Single-Node) | AURA Siting Crafter Architecture | NSW Government Impact |
| :--- | :--- | :--- | :--- |
| **Execution Scale** | Single-threaded; constrained on large polygons | Distributed multi-core / multi-node (Apache Sedona) | Scales across 3.5M+ NSW land parcels |
| **Data Format** | Proprietary File Geodatabases / Shapefiles | Open Cloud-Native **GeoParquet** | Native integration with NSW Spatial Digital Twin & Lakehouse |
| **Pipeline Governance** | Ad-hoc `.mxd` / `.qgz` project files | Version-controlled Git repository (Python / SQL) | Reproducible for statutory planning reviews |
| **Integration** | Manual export/import between portals | Programmatic API ETL (NSW SEED, ABS, Councils) | Consistently references authoritative spatial data |
| **Visualization** | Requires desktop GIS software install | Interactive Web Dashboards (MapLibre / HTML) | Accessible across government departments |

---

## Recommended Deployment Steps for NSW Spatial Services & DPHI

1. **State-Wide Net Developable Area Pipeline:** Adapt `src/Ingestion/spatial_ingest.py` with `AURA_REGION=nsw` to ingest state-wide DCDB and SEED layers for automated NDA generation in Growth Areas and REZs.
2. **Spatial Digital Twin Lakehouse Connector:** Connect Sedona / Wherobots GeoParquet outputs directly into the NSW Spatial Digital Twin platform.
3. **Automated Infrastructure Siting:** Use `src/Analysis/national_suitability_analysis.py` to evaluate candidate locations for clean energy infrastructure, battery storage, and high-tech precincts.
