# Spatial Quality Assurance, Telemetry & Zero-Mock Standards

**Standard:** AURA Quality Assurance & Zero-Mock Integrity  
**Organization:** GetBack2Basics Spatial AI Engineering  
**Enforcement:** Mandatory Pre-Commit & CI Test Gates  

---

## 1. Zero-Mock Data Integrity Protocol

In mission-critical geospatial engineering, synthetic coordinates or fake mock arrays (`sample_features = [...]`) corrupt spatial analysis and introduce catastrophic legal liability.

### Strict Enforcement Rules
1. **AST Scanner Gate**: All pull requests must pass the Python AST scanner (`tests/lint/test_no_mock_data.py`), which traverses the abstract syntax tree to detect mock dictionaries, synthetic coordinate lists, and placeholder bounding boxes.
2. **Dynamic Manifest Loading**: UI viewers and inspection docks must load genuine data from live endpoints or verified JSON/GeoParquet assets (`config/dataset_manifest_v2.json`).
3. **Explicit Connection Failure Handling**: If an external data source is offline, the interface must display genuine connection status or error boundaries—never synthetic fallback records.

---

## 2. Compute Lifecycle & Resource Teardown

To protect against cloud resource leaks and billing blowouts:
1. **Apache Sedona Session Teardown**: Every SedonaContext script must explicitly execute `sedona.stop()` in `finally:` blocks.
2. **Headless Cluster Lifecycle**: Headless Wherobots Cloud runtimes are spawned per batch and terminated immediately upon GeoParquet asset compilation.
3. **Automated Verification**:
   ```bash
   pytest tests/lint/ -v
   pytest tests/test_hazard_scoring.py -v
   ```

---

## 3. Spatial ETL Telemetry & Performance Benchmarks

| Metric | Target Standard | Production Benchmark |
| :--- | :--- | :--- |
| **Cadastre Ingestion Throughput** | > 200,000 parcels/sec | ~310,000 parcels/sec (Sedona medium runtime) |
| **GDA2020 CRS Projection Precision** | Sub-millimetre ($\le 0.001\text{m}$) | Exact EPSG:7844 ellipsoidal transformation |
| **DuckDB-WASM In-Memory Scoring Latency** | < 50ms | 12–15ms (10,000 parcels) |
| **WebGL Render Frame Rate** | 60 fps continuous | 60 fps (Area-Priority Limiter enabled) |
