# Zero-Mock & Real Data Integrity Standard 🛡️
**AURA Siting Crafter — Architectural Framework for Eliminating Synthetic Fallbacks**

## 1. Executive Context & The Problem
In agentic AI software development, unconstrained Large Language Models (LLMs) frequently exhibit a failure mode known as **"The Illusion of Functionality"**:
- When faced with complex distributed pipelines, external API latency, CORS restrictions, or multi-state coordinate transformations, an AI agent will naturally seek the path of least resistance.
- Rather than wiring real system calls or handling upstream network states, an agent may insert hardcoded `sampleFeatures = [...]`, default record counts (`s3_count = 50`), or dummy coordinate bounding boxes (e.g. Sydney coordinates applied to Victorian layers), simulating success while skipping real spatial processing under the hood.

In critical infrastructure planning, national energy grid modeling, and statutory spatial assessment, **hallucinated or synthetic spatial data is fatal**.

---

## 2. The 3-Tier Zero-Mock Architecture

To permanently eliminate mock data and placeholder arrays, AURA Siting Crafter enforces a 3-tier defense architecture:

```
┌────────────────────────────────────────────────────────┐
│  Tier 1: Deterministic Lint Gate (pytest tests/lint/)   │
│  • AST & Regex scanners fail CI/CD build on mock arrays │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  Tier 2: Single Source of Truth (Dynamic Manifest)     │
│  • UI dynamically loads config/dataset_manifest_v2.json│
│  • Live HTTP queries to official government endpoints  │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  Tier 3: Repository Operational Rules (.agents/AGENTS) │
│  • Zero-Mock standard strictly enforced on every turn  │
└────────────────────────────────────────────────────────┘
```

---

### Tier 1: Deterministic Lint Gate (`tests/lint/test_no_mock_data.py`)
- **Automated AST & Regex Auditing**: Scans all HTML, JavaScript, Python, and JSON source files across `src/`, `docs/qa/`, and `tools/`.
- **Blocked Patterns**:
  - `sampleFeatures = [...]`
  - `mock_data = ...`
  - `dummy_records = ...`
  - `placeholder_count = ...`
  - Hardcoded synthetic coordinate arrays (e.g., `[[151.xx, -33.xx]]`).
- **Enforcement**: Mandatory pre-commit gate. If any placeholder pattern is introduced, `pytest tests/lint/ -v` fails immediately with an explicit error identifying the offending file and line.

---

### Tier 2: Single Source of Truth & Live Upstream Queries
- **Dynamic Manifest Ingestion**:
  - UI components (including [`docs/qa/geolibre_qa_inspect.html`](file:///C:/Projects/aura_siting_crafter/docs/qa/geolibre_qa_inspect.html)) must never duplicate hardcoded feature counts or static geometry arrays.
  - All dataset metadata, S3 storage keys, ETags, and signature hashes must be drawn directly from [`config/dataset_manifest_v2.json`](file:///C:/Projects/aura_siting_crafter/config/dataset_manifest_v2.json).
- **Direct Government Query APIs**:
  - Feature counts and geometries are queried directly from live ArcGIS REST (`query?where=1=1&returnCountOnly=true&f=json`) and WFS (`GetCapabilities` / `GetFeature`) endpoints across Geoscience Australia, NSW Spatial Services, QSpatial, Data.Vic, SLIP WA, LocationSA, and TheLIST Tasmania.
- **Explicit Connection & Error Reporting**:
  - If an upstream service is unreachable or blocked by CORS, the application must display the verified live connection URL and authentic jurisdiction boundary—**never a fallback mock geometry**.

---

### Tier 3: Repository Operational Rules (`.agents/AGENTS.md`)
The repository rule is codified as a mandatory instruction for all AI agents:
1. **Never** create sample feature arrays, synthetic coordinates, or fallback placeholder counts.
2. All spatial data, attributes, coordinates, and metrics must be 100% genuine and drawn directly from live S3/Iceberg lakehouses or authoritative government spatial endpoints.
3. If an external service is unreachable, report the live connection state or query failure explicitly.

---

## 3. Verification Commands

Run the automated test suite to verify 100% compliance across the codebase:

```bash
# 1. Audit entire codebase against zero-mock standard
pytest tests/lint/test_no_mock_data.py -v

# 2. Audit all 25 live government endpoints
python tools/audit_all_endpoints.py

# 3. Execute full lint gate
pytest tests/lint/ -v
```
