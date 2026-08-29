---
name: wherobots-spatial-sql
description: Expert guidance on Wherobots Cloud, SedonaContext, Spatial SQL queries, and the Wherobots MCP Server.
---
# Wherobots Spatial SQL & MCP Skill

This skill provides guidelines and best practices for writing Wherobots Spatial SQL, initializing `SedonaContext`, executing spatial ETL workflows, and configuring the Wherobots MCP Server.

## Reference Playbook
For enterprise architecture guidelines, consult the [Wherobots & Antigravity Engineering Playbook](https://github.com/GetBack2Basics/CheatSheets/blob/main/wherobots_antigravity_playbook.md).

## 1. Sedona & Wherobots Context Initialization
Always initialize the `SedonaContext` to compile spatial SQL functions:
```python
from sedona.spark import *
spark = SedonaContext.create(SedonaContext.builder().getOrCreate())
```

## 2. Configuring the Wherobots MCP Server
To configure the Wherobots MCP server manually in your editor:
1. Open the Command Palette and run **MCP: Add Server**.
2. Choose **HTTP (HTTP or Server-Sent Events)**.
3. Use the URL: `https://api.cloud.wherobots.com/mcp/`
4. Set the name to `wherobots-mcp-server`.
5. Add your Wherobots API Key in `mcp.json` headers:
   ```json
   "headers": {
     "x-api-key": "<YOUR_WHEROBOTS_API_KEY>"
   }
   ```

## 3. Spatial SQL Best Practices
- **CRS Reprojections**: Ensure geometries are in a projected coordinate system (e.g., `EPSG:7856` GDA2020 / MGA Zone 56) before executing metric buffers (`ST_Buffer`) or calculating area (`ST_Area`). Use `ST_Transform(geom, 'EPSG:4326', 'EPSG:7856')`.
- **Prevalent Functions**:
  - `ST_Point(x, y)`: Construct points from coordinates.
  - `ST_Buffer(geom, distance)`: Buffer geometries in coordinate units.
  - `ST_Contains(a, b)`, `ST_Intersects(a, b)`: Perform spatial predicate checks.
  - `ST_Area(geom)`: Computes metric or degree area.

## 4. Incremental Spatial Compute & Cost Optimization Principles

> [!CAUTION]
> **Avoid Unintentional Billing Blowouts**: Interactive General Purpose SUs bill continuously per hour while a runtime session remains open (e.g. $1.50+/SU-hour). Always follow these safety rules.

1. **Prefer Headless Batch Execution (`WherobotsJob`) Over Interactive Runtimes**:
   - Use `WherobotsJob(runtime="tiny")` for routine ETL and analysis runs.
   - Batch jobs automatically terminate as soon as the script exits, charging only for active execution time (typically $0.05–$0.20 per run vs $100s for idle interactive sessions).

2. **Explicit Session Teardown (`spark.stop()` / `sedona.stop()`)**:
   - Always wrap PySpark / Sedona execution in a `try...finally` block in Python scripts:
     ```python
     sedona = SedonaContext.create(SedonaContext.builder().getOrCreate())
     try:
         # Spatial transformations and queries...
         pass
     finally:
         sedona.stop()
     ```

3. **Decouple Heavy Geometry Joins from Lightweight Multi-Criteria Scoring**:
   - Never re-execute multi-million feature spatial overlays and buffer unions when only tweaking MCDA weighting coefficients or sigmoidal curve steepness ($k$).
   - Persist intermediate topological distance matrices and net developable pad boundaries in Havasu/GeoParquet.

4. **Data Fingerprinting & Snapshot Memoization**:
   - Check upstream dataset hashes (ETags, Iceberg snapshot IDs) to skip re-ingesting static layers (e.g., rail networks, power grids, cadastre).

5. **Managing Interactive MCP Server & Notebook Sessions**:
   - **Wherobots MCP Server**: Keep the server stopped when not actively executing queries (`MCP: List Servers` -> `Stop Server`).
   - **Session Idle Timeouts**: Configure interactive session auto-shutdown in Wherobots Cloud console to **5 minutes** of inactivity.
   - **Kernel Shutdown**: Explicitly shut down Jupyter notebook kernels immediately after completing interactive spatial exploration.

6. **Spatial Query & I/O Optimization**:
   - **Spatial Envelope Filtering**: Filter bounding boxes (`ST_Intersects(geom, ST_MakeEnvelope(...))`) BEFORE running heavy spatial operations (`ST_Buffer`, `ST_Intersection`).
   - **Avoid `SELECT *`**: Request only specific columns to enable Parquet/Havasu projection pushdown.
   - **DataFrame Caching**: Call `.cache()` on complex intermediate geometry DataFrames that are evaluated multiple times, and `.unpersist()` when complete.
   - **Single Region Lock**: Standardize environment configuration to a single cloud region (e.g., `aws-us-west-2`) to avoid running concurrent runtime clusters across multiple regions.
