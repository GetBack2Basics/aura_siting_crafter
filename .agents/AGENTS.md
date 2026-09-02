# AURA Siting Crafter — Project Rules

## Project Context
This is the **national** version of the spatial siting pipeline: **AURA Siting Crafter** (Australian Urban & Regional AI Siting Crafter).
Region is selected via `AURA_REGION` env var (default: `national`, e.g. `AURA_REGION=hunter` for regional ETL).
Wherobots storage root: `wherobots://fgsdb/aura_siting`.
Do NOT reference legacy place-specific repositories or `fgsdb/macquarie`.

## Documentation & Artifact Persistence Rule
All implementation plans, technical scratchpads, email drafts, articles, and research notes MUST be persisted in `docs/`.

## Compute Resource Teardown & Cost Protection Rule
Always ensure that all compute instances, interactive Wherobots runtimes, Sedona/SparkContext sessions (`sedona.stop()`), and background execution tasks are explicitly terminated immediately after execution to prevent billing blowouts.
In every final response after executing computational jobs, explicitly check and report the compute/instance shutdown status to the user.

## Incremental Spatial Compute & Cost Optimization
- All spatial ETL pipelines must follow the Wherobots & Antigravity Engineering Playbook.
- **Decoupled Geometry vs. Scoring**: Separate heavy geometric calculations (CRS transforms, topological buffers, `ST_Difference` masks) from lightweight mathematical scoring ($S_{\text{power}}$, $S_{\text{sensitive}}$, $S_{\text{water}}$). Changing weights or sigmoidal curve parameters must never re-trigger heavy spatial joins.
- **Data Fingerprinting & Memoization**: Use cryptographic hashing (ETags, GeoParquet file hashes, Iceberg snapshot IDs) to skip re-running untouched spatial layers.
- **Regional Scoping**: Use `AURA_REGION=hunter` or regional configs for targeted ETL runs to avoid full national re-computation.
- **Zero-Cost Client Offloading**: Offload interactive What-If scenario modeling, sensitivity tests, and slider re-scoring 100% to client-side DuckDB-WASM and JavaScript.

## Zero-Mock & Real Data Integrity Standard (Strict & Enforced)
1. NEVER create sample feature arrays, synthetic coordinates, or fallback counts (e.g. `sampleFeatures = [...]`, default 50 records).
2. All UI components, tables, and inspection viewers MUST load real data dynamically from live query endpoints or `config/dataset_manifest_v2.json`.
3. If an external service is unreachable or slow, display the verified live connection URL, genuine state boundary, or error state explicitly rather than displaying mock or synthetic fallback objects.
4. All code changes MUST pass the zero-mock AST scanner (`pytest tests/lint/test_no_mock_data.py -v`).

## Security Rule
Never commit API keys, session IDs, org IDs, or private credentials to this repo.
All runtime secrets must be loaded via environment variables or `.env` (gitignored).

## Lint Gate Rule
All code modifications MUST pass `pytest tests/lint/ -v` before any `git push` or Wherobots deployment.

## Graphify Onboarding Rule
At the start of any refactoring session, run the Graphify analysis tool to establish dependency and reference context:
```bash
python tools/graphify_analysis.py
```

