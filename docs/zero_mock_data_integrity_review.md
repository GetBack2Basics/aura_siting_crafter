# Zero-Mock & Real Data Integrity Standard — Audit & Review

## 1. Core Rule Established
The **Zero-Mock & Real Data Integrity Rule** has been codified into `.agents/AGENTS.md`:
> **Never use mocked, placeholder, synthetic, or simplified mock datasets in any tool, pipeline, UI, or table.**  
> All spatial data, attributes, coordinates, and metrics MUST be 100% genuine and drawn directly from live S3/Iceberg lakehouses (`s3://wherobots-user-storage/aura_siting/`) or authoritative government spatial endpoints (NSW Spatial Services, Geoscience Australia, AEMO, BoM, ACARA, NHSD).  
> If an external service is unreachable, report the live connection state or query failure explicitly rather than displaying mock or synthetic fallback objects.

---

## 2. Comprehensive Codebase Review & Remediation

| Component | Status Before Review | Remediation Performed | Verified Real Data Source |
| :--- | :--- | :--- | :--- |
| **Energy Grid Layer** | 4 inlined mock lines (`TL_NSW_330`, etc.) | Removed hardcoded arrays. Connected to live NSW FeatureServer layer 6 | NSW Spatial Services / Transgrid (`NSW_Features_of_Interest_Category/FeatureServer/6`) |
| **WWTW & Recycled Water** | 3 inlined mock points | Removed hardcoded arrays. Connected to live NSW FeatureServer layer 11 | WaterNSW / Hunter Water (`NSW_Features_of_Interest_Category/FeatureServer/11`) |
| **ACARA National Schools** | 3 inlined mock points | Removed hardcoded arrays. Connected to live Education FeatureServer layer 1 | ACARA National Directory (`FeatureServer/1`) |
| **NHSD Healthcare Directory** | 2 inlined mock points | Removed hardcoded arrays. Connected to live Medical FeatureServer layer 2 | Australian Digital Health Agency / NHSD (`FeatureServer/2`) |
| **Candidate Siting Parcels** | Inlined array | 16 Genuine Candidates computed by the AURA Spatial Siting Engine | `s3://wherobots-user-storage/aura_siting/candidates/datacenter_candidates_national.parquet` |
| **Basemap Dependency** | CARTO dependency | Removed CARTO. Pure zero-network CSS/Canvas `#ffffff` white canvas & OSM Terrain at 50% opacity | Zero third-party API keys |
| **Attribute Table** | Rendered only 4 mock rows | Now dynamically queries live REST FeatureServer streams or DuckDB S3 Proxy | Real multi-column properties (`OBJECTID`, `VOLTAGE`, `SHAPE__LENGTH`, etc.) |

---

## 3. Infrastructure & Cost Verification
- **Cloud Run Deployment**: `geolibre-spatial-ai-proxy` on `australia-southeast1` (Serverless, min instances: 0, idle rate: $0.00/hr).
- **GCS Static Storage**: `gs://aura-siting-crafter-geolibre-app/` (<500 KB, <$0.001/month).
- **Compute VMs**: 0 active instances.
- **Sedona / Spark Contexts**: Explicitly stopped (`sedona.stop()`).
