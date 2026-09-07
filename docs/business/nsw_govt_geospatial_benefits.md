# Strategic Value & Application Guide: Transferring Cloud Spatial Lakehouse Lessons to NSW Government & Waratah HPC

**Target Audience:** Senior Geospatial Leadership, Spatial Data Architects, HPC Systems Engineers & Policy Executives (NSW DCCEEW, NSW Spatial Services, Department of Planning, Housing and Infrastructure – DPHI, EnergyCo, Environment & Heritage, and Land Administration)  
**Procurement Reference Context:** [NSW Buy Notice C85F11C0-9984-4C2A-AE897364B13F4B7A](https://buy.nsw.gov.au/notices/C85F11C0-9984-4C2A-AE897364B13F4B7A) (NSW DCCEEW Waratah HPC Facility)  
**Reference Portals:** [NSW Spatial Services](https://www.spatial.nsw.gov.au/) | [NSW Planning Portal](https://www.planningportal.nsw.gov.au/) | [NSW SEED Portal](https://www.seed.nsw.gov.au/)  
**Document Purpose:** Strategic and technical transfer guide detailing how the architectural patterns, cost optimizations, and distributed spatial ETL lessons developed in **AURA Siting Crafter** (deployed on Wherobots Cloud, AWS, and Google Cloud) can be directly applied to accelerate on-premise government supercomputing—specifically the **NSW DCCEEW Waratah High Performance Computing (HPC) Facility** and enterprise state GIS platforms.

---

> [!IMPORTANT]
> ### ⚡ Executive Briefing: Cloud-to-HPC Architectural Transfer
> * **Cloud-Native Provenance:** AURA Siting Crafter executes natively on **Wherobots Cloud, AWS (S3 / EMR / Sedona), and Google Cloud (BigQuery / GCS)**, processing 15.91M+ national spatial geometries with statutory multi-hazard scoring.
> * **The Core Objective:** Translating cloud spatial engineering breakthroughs—distributed Apache Sedona memory models, decoupled geometry/scoring engines, and GeoParquet lakehouse structures—into concrete design patterns for NSW Government compute environments, notably **Waratah HPC** ([buy.nsw Notice C85F11C0-9984-4C2A-AE897364B13F4B7A](https://buy.nsw.gov.au/notices/C85F11C0-9984-4C2A-AE897364B13F4B7A)).
> * **Lustre Parallel Storage Unlocking (DDN ExaScaler 7990X):** How replacing single-threaded desktop GIS formats with partitioned GeoParquet unlocks the full multi-gigabyte/sec parallel throughput of Waratah HPC's Lustre storage array during 3.5M+ parcel cadastral joins.
> * **Spectra Logic T950 Cold-Tier Integration:** How spatial data fingerprinting and incremental memoization prevent re-processing petabytes of static historical baselines (SLATS vegetation, 30m DEMs, multi-decade climate grids), preserving them on archival tape while streaming hot candidate parcels to compute nodes.
> * **Extreme Cost & Compute Optimization:** How decoupling heavy geometric buffering (`ST_Difference`, `ST_Buffer`) from lightweight mathematical scoring reduced cloud pipeline execution to **$0.69 USD** per full national run—a pattern that prevents HPC cluster queue exhaustion during multi-scenario policy sweeps.
> * **Zero-Cost Client Offloading:** How packaging spatial outputs for client-side **DuckDB-WASM and WebGIS** shields government HPC infrastructure from public interactive queries, delivering instant scenario modeling at zero compute cost.

---

## Executive Summary

State-level geospatial data in New South Wales is growing exponentially in volume, spatial resolution, and statutory complexity. From the 3.5M+ parcels of the NSW Digital Cadastral Data Base (DCDB) and high-resolution LiDAR elevation models, to multi-decade climate projections (NARCLiM) and environmental sensor networks under **NSW DCCEEW**, traditional single-node desktop GIS tools (`.mxd`, `.qgz`, Shapefiles) face severe scalability bottlenecks.

The **AURA Siting Crafter** project was architected on commercial cloud infrastructure (**Wherobots Cloud, AWS, and Google Cloud**) using **Apache Sedona (PySpark)**, **Apache Iceberg**, and **GeoParquet** to solve large-scale spatial siting, multi-hazard constraint analysis, and circular economy modeling.

This document synthesizes the operational, mathematical, and architectural lessons learned from AURA's cloud implementation into a roadmap for NSW Government agencies. It demonstrates how these patterns can modernize state workflows and maximize return-on-investment for specialized state computing assets such as the **NSW DCCEEW Waratah HPC Facility**.

---

## The Reference Environment: NSW DCCEEW Waratah HPC

The **Waratah High Performance Computing (HPC) facility** is a government-managed supercomputing cluster operated by the **NSW Department of Climate Change, Energy, the Environment and Water (DCCEEW)** ([buy.nsw Notice C85F11C0-9984-4C2A-AE897364B13F4B7A](https://buy.nsw.gov.au/notices/C85F11C0-9984-4C2A-AE897364B13F4B7A), supported by Xenon Systems).

```
+----------------------------------------------------------------------------------------------------+
|                         NSW DCCEEW WARATAH HPC FACILITY ARCHITECTURE                                |
|                        (Procurement: buy.nsw Notice C85F11C0-9984-4C2A-AE897364B13F4B7A)           |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [ PRIMARY STORAGE ]                                           [ ARCHIVAL & BACKUP ]               |
|  DDN ExaScaler 7990X Lustre Storage Array                      Spectra Logic T950 Tape Library     |
|  • High-throughput parallel filesystem                         • Petabyte-scale preservation       |
|  • Optimized for massive concurrent streaming                  • Multi-decade environmental data   |
|                                                                                                    |
|  [ COMPUTATIONAL MANDATE ]                                     [ VENDOR & SYSTEM SUPPORT ]         |
|  Dedicated to NSW DCCEEW Policy & Science                      Maintained by Xenon Systems         |
|  • Climate Modeling (NARCLiM) & Extreme Projections            • Node reconfiguration & tuning     |
|  • Environmental Monitoring, SLATS & Biodiversity              • Continuous system maintenance     |
|  • Renewable Energy Zone (REZ) & Grid Simulations              • High-throughput interconnects     |
|  • River Basin, Flood & Water Resource Management                                                  |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

Unlike academic compute facilities, Waratah HPC is dedicated to direct public policy, environmental stewardship, and statutory spatial planning. AURA's cloud-proven engineering patterns offer a blueprint for running high-throughput spatial analytics across these portfolios.

---

## 5 Transferable Spatial Engineering Lessons: Cloud (AURA) to On-Premise HPC

```
+----------------------------------------------------------------------------------------------------+
|                      AURA CLOUD PIPELINE (Wherobots / AWS / GCP)                                   |
|   15.91M Geometries | Decoupled Geometry/Scoring | GeoParquet / Iceberg | $0.69 USD Full Run       |
+----------------------------------------------------------------------------------------------------+
                                               |
                     ARCHITECTURAL LESSONS & PATTERNS TRANSFERRED
                                               v
+----------------------------------------------------------------------------------------------------+
|                        NSW DCCEEW WARATAH HPC FACILITY ADOPTION                                    |
|  1. GeoParquet Parallel I/O on DDN Lustre Storage Array (ExaScaler 7990X)                          |
|  2. Memoized Partition Pruning & Cold Data Preservation (Spectra Logic T950 Tape)                  |
|  3. Decoupled Heavy Geometric Transforms from Rapid Multi-Scenario Scoring                         |
|  4. Statutory 6-Factor Multi-Hazard Scoring Engine (ARR 2019, AS 1170, AS 3959)                   |
|  5. Zero-Cost Client-Side Offloading via DuckDB-WASM for Public Planners                           |
+----------------------------------------------------------------------------------------------------+
```

---

### Lesson 1: Unlocking Lustre Parallel Storage via Partitioned GeoParquet

* **Cloud Experience (AURA):** Legacy shapefiles and single-file geodatabases created severe I/O bottlenecks in cloud object storage (S3/GCS). Migrating to **GeoParquet** with spatial R-Tree / Hilbert curve partitioning allowed worker nodes to read and process spatial extents independently in parallel without I/O locking.
* **HPC Translation (Waratah Lustre Array):**
  * Waratah HPC's **DDN ExaScaler 7990X Lustre filesystem** is designed for massive concurrent read/write throughput across distributed stripes.
  * Storing statewide layers (DCDB parcels, 30m DEM, biodiversity zones) in partitioned GeoParquet allows Spark/Sedona nodes to saturate Lustre striping channels simultaneously.
  * **Result:** Eliminates the I/O choke point when joining 3.5M+ NSW parcels with multi-hazard layers, completing statewide joins in minutes.

---

### Lesson 2: Decoupled Heavy Geometry vs. Lightweight Mathematical Scoring

* **Cloud Experience (AURA):** In early prototypes, adjusting a policy weight (e.g. power grid priority vs. biodiversity buffer weight) re-triggered heavy spatial joins (`ST_Buffer`, `ST_Difference`, `ST_Intersection`), driving up cloud compute costs. By decoupling geometric pre-computations (distance matrices, net developable polygons) from mathematical scoring curves (sigmoidal penalties, weighted MCDA sums), full national runs dropped to **$0.69 USD**.
* **HPC Translation (Waratah Cluster Utilization):**
  * Policy makers often need to run hundreds of "What-If" scenarios with shifting weightings (e.g., varying flood tolerance, sensitive receptor buffers, or grid distance priorities).
  * Pre-computing the geometric distance and topology layer once and caching it on Lustre allows subsequent policy scoring runs to execute as pure mathematical array operations in milliseconds.
  * **Result:** Prevents long cluster queue times and avoids wasting valuable HPC node hours on repetitive geometric recalculations.

---

### Lesson 3: Cold-Tier Data Preservation & Memoized Incremental Pipelines

* **Cloud Experience (AURA):** Large baselines (national topographic grids, geological surveys, baseline census data) rarely change between runs. Cryptographic fingerprinting (ETags, snapshot hashes) ensured untouched layers were skipped, computing only active delta updates.
* **HPC Translation (Spectra Logic T950 Tape Integration):**
  * Waratah HPC uses a **Spectra Logic T950 Tape Library** for long-term preservation of massive multi-decade climate (NARCLiM) and environmental time-series datasets.
  * Using partition fingerprinting, the Sedona spatial pipeline can pull active candidate layers to high-speed NVMe/Lustre storage while keeping cold, multi-petabyte reference datasets safely referenced in tape archives.
  * **Result:** Minimizes active primary storage consumption while guaranteeing 100% reproducible baseline provenance.

---

### Lesson 4: Standardized Multi-Hazard & Circular Physical Engineering

* **Cloud Experience (AURA):** Integrated statutory Australian standards into programmatic Python/SQL formulas rather than subjective manual GIS overlays:
  1. **Flood:** ARR 2019 / 1% AEP inundation exclusion.
  2. **Bushfire:** AS 3959:2018 BAL (Bushfire Attack Level) & PBF 2019 setbacks.
  3. **Landslide:** AGS 2007 slope susceptibility modeling ($>8.0\%$ exclusion).
  4. **Seismic:** AS 1170.4:2007 (R2018) PGA structural hazard baselines.
  5. **Wind:** AS/NZS 1170.2:2021 regional wind design speeds ($45\text{–}69\text{m/s}$).
  6. **Thermodynamic Decay & Pumped Hydro:** Spatial heat loss modeling ($T_{\text{delivery}} \le 38.5^\circ\text{C}$ within $\le 506.8\text{m}$) and void storage capacity ($E = \rho g H V \eta$).
* **HPC Translation (DCCEEW Scientific Portfolios):**
  * These validated, peer-reviewed formula implementations can be deployed as standard batch modules across DCCEEW portfolios (EnergyCo Renewable Energy Zones, DPHI Growth Areas, WaterNSW catchments).
  * **Result:** Ensures legal and statutory defensibility across state planning assessments.

---

### Lesson 5: Zero-Cost Client-Side Scenario Modeling for Planners

* **Cloud Experience (AURA):** Rather than standing up expensive, always-on spatial servers (GeoServer, ArcGIS Enterprise servers) to handle user queries, AURA exports lightweight spatial tables into client-side **DuckDB-WASM and JavaScript**. Users can dynamically drag weight sliders, apply hazard thresholds, and filter sites directly in the browser with sub-second response times.
* **HPC Translation (Protecting Government Infrastructure):**
  * Government supercomputers (like Waratah HPC) should never be directly exposed to public interactive web traffic or burdened with serving live interactive maps.
  * HPC clusters can run heavy overnight distributed batch jobs, export optimized GeoParquet artifacts, and serve interactive decision dashboards via static client-side WASM portals.
  * **Result:** Delivers sub-second interactive tools to regional council planners and executive stakeholders with zero web-tier server costs and complete cybersecurity isolation for the internal HPC cluster.

---

## Domain Capabilities: Applying AURA Lessons Across NSW Portfolios

```
+-----------------------+           +-----------------------+           +-----------------------+
|  PLANNING & HOUSING   |           |      ENVIRONMENT      |           |     LAND ADMIN &      |
|     (DPHI & REZs)     |           |    & MULTI-HAZARDS    |           |   SPATIAL SERVICES    |
| • Net Developable Pad |           | • ARR 2019 Flood 1%   |           | • 3.5M+ DCDB Parcels  |
| • Statutory Setbacks  |           | • AS 3959 Bushfire    |           | • GDA2020 EPSG:7856   |
| • Proponent Claim QA  |           | • AGS 2007 Landslide  |           | • Spatial Digital Twin|
| • 6-Factor MCDA Engine|           | • AS 1170.4 Seismic   |           | • Zero-Copy GeoParquet|
+-----------------------+           +-----------------------+           +-----------------------+
```

### 1. Planning & Precinct Transformation (DPHI & EnergyCo)
* **Automated Net Developable Area (NDA):** Automates topological subtraction of riparian (30m), pipeline (20m), slope (>5%), and infrastructure easements across massive masterplans (e.g. Hunter Transformation, Western Sydney Aerotropolis). For the Macquarie Coal Complex, this verified that a 65.0 ha gross boundary yielded 44.5 ha net developable pad space.
* **Proponent Claim QA:** Audits developer planning submissions against ground-truth state spatial layers using automated topological path calculations.

### 2. Environment, Climate & Energy (NSW DCCEEW)
* **Statewide Multi-Hazard Assessment:** Executes ARR 2019, AS 1170, and AS 3959 evaluations across every parcel in NSW.
* **Clean Energy & REZ Siting:** Evaluates proximity to 132kV/275kV/330kV transmission lines, substations, and recycled water treatment plants (WWTW).
* **Circular Industrial Symbiosis:** Models thermodynamic effluent cooling and mine void micro-pumped hydro potential.

### 3. Cadastre & Land Administration (Spatial Services NSW)
* **DCDB Spatial Enrichment:** Enriches 3.5M+ land parcels with zoning, hazard ratings, and proximity metrics without memory bottlenecks.
* **GDA2020 Compliance:** Enforces automated reprojection and geometry validation across EPSG:7856 (MGA 56 metric engineering) and EPSG:7844 / EPSG:4326.

---

## Feature Comparison: Traditional Desktop GIS vs. Cloud/HPC Modern Architecture

| Feature / Dimension | Traditional Desktop GIS (Manual Single-Node) | AURA Cloud Architecture (Wherobots / AWS / GCP) | Recommended Waratah HPC Adoption Pattern |
| :--- | :--- | :--- | :--- |
| **Execution Scale** | Single-threaded; crashes on large polygons | Distributed multi-node (Apache Sedona PySpark) | Distributed Sedona on Waratah HPC compute nodes |
| **Storage Subsystem** | Local C: drives / SMB network shares | Cloud object storage (S3 / GCS / Iceberg) | **DDN ExaScaler 7990X Lustre Parallel Array** |
| **Cold Data Strategy**| Manual archiving to detached drives | Cloud lifecycle tiering & snapshot hashing | **Spectra Logic T950 Tape Library integration** |
| **Multi-Hazard Model**| Ad-hoc manual layer reclassifications | Statutory AS/NZS & ARR 2019 formula engine | Standardized state-wide automated hazard scoring |
| **Interactive UX** | Requires desktop GIS software install | Zero-cost client-side **DuckDB-WASM** | Static WASM web portals (air-gapped from HPC) |
| **Run Economics** | Days of manual engineering labor | **$0.69 USD** per full national run (15.91M geoms)| Maximized HPC throughput & zero queue bloat |

---

## Recommended Action Plan for NSW Spatial & HPC Leadership

1. **Adopt Partitioned GeoParquet as State Standard:** Transition state spatial distribution from legacy Shapefiles/FileGDBs to cloud-native GeoParquet (EPSG:7844 / EPSG:7856) to unlock parallel I/O on Lustre storage arrays.
2. **Pilot Apache Sedona on Waratah HPC:** Test distributed Apache Sedona PySpark batch scripts on the Waratah HPC cluster for state-wide Net Developable Area (NDA) generation across the 3.5M+ parcel DCDB.
3. **Establish a Decoupled Scoring Framework:** Separate heavy geometric spatial joins from multi-criteria decision scoring across DPHI, EnergyCo, and DCCEEW planning workflows to minimize compute redundancy.
4. **Integrate Output Streams with NSW Spatial Digital Twin:** Connect GeoParquet spatial outputs directly to the NSW Spatial Digital Twin and client-side DuckDB-WASM viewers for secure, zero-cost interactive policy exploration.
