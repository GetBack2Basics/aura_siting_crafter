# AURA Siting Crafter (Australian Urban & Regional AI Siting Crafter)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Dockerized](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](Dockerfile)

**AURA Siting Crafter** is an open-source, cloud-native spatial data engineering and Multi-Criteria Decision Analysis (MCDA) framework for regional and national infrastructure siting (Data Centers, Clean Energy, Renewable Hydrogen, and Advanced Manufacturing Hubs across Australia).

---

## Architecture Overview

```
                          ┌────────────────────────────┐
                          │    National & State APIs   │
                          │  (Geoscape, GA, SEED, Open)│
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                          ┌────────────────────────────┐
                          │  Wherobots / Apache Sedona │
                          │     Spatial ETL Engine     │
                          │ (src/Ingestion/spatial_ingest.py)
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                          ┌────────────────────────────┐
                          │  Apache Iceberg / Havasu   │
                          │   org_catalog.fgsdb.*      │
                          └─────────────┬──────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
       ┌─────────────────────────┐             ┌─────────────────────────┐
       │   Spatial MCDA Engine   │             │ Interactive Dashboards  │
       │ (src/Analysis/national_ │             │ (runner/etl_runner.html │
       │ suitability_analysis.py)│             │  notebooks/*.ipynb)     │
       └─────────────────────────┘             └─────────────────────────┘
```

---

## Directory Structure

| Path | Purpose |
|---|---|
| `config/national.json` | National siting parameters, CRS definitions, default buffer thresholds |
| `config/regions/` | Regional configuration overrides (e.g. `hunter.json`, `gladstone.json`) |
| `src/Ingestion/` | Apache Sedona spatial ETL pipelines (`spatial_ingest.py`, `data_ingest.py`) |
| `src/Analysis/` | National Multi-Criteria Decision Analysis scoring engine (`national_suitability_analysis.py`, `datacenter_suitability.py`) |
| `runner/` | Automated job submitters (`etl_runner.html`, `build_suitability_report.py`, `submit_analysis_jobs.py`) |
| `notebooks/` | Interactive Wherobots exploratory notebooks (`Spatial_ETL_Pipeline.ipynb`, `Precinct_Suitability_Analysis.ipynb`, `National_Siting_Dashboard.ipynb`) |
| `docs/` | Technical methodology, incremental compute architecture, and spatial calculations reference |
| `tests/lint/` | Security, place-name decoupling, and import integrity tests |
| `tools/` | Automated repository graph & dependency analysis (`graphify_analysis.py`) |

---

## Quick Start

### 1. Local Python Environment
```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run lint verification
pytest tests/lint/ -v

# Run national suitability scoring
python -m src.Analysis.national_suitability_analysis
```

### 2. Regional vs National Scoping
```bash
# Run for national scope
export AURA_REGION=national
python -m src.Ingestion.spatial_ingest

# Run for Hunter regional precinct (cost-optimized ETL)
export AURA_REGION=hunter
python -m src.Ingestion.spatial_ingest
```

### 3. Docker Usage
```bash
# Build image
docker build -t aura-siting .

# Run national analysis in container
docker run --rm aura-siting

# Or use docker-compose
docker compose up aura-analysis
```

---

## Security & Attribution
- All credentials and API tokens must be supplied via `.env` or runtime environment variables.
- Project developed under the MIT License.
