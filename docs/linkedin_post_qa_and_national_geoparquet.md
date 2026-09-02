What happens when you ask an AI agent to build a national spatial pipeline across 15M parcels and 25 government APIs? It "fakes it till it (doesn’t) make it."

Faced with heavy transforms (GDA2020), multi-hazard overlays, and API latency, an unconstrained AI will silently mock responses, apply Sydney coordinates to Victorian layers, and simulate success.

In national infrastructure siting, hallucinated data is fatal.

To scale AURA Siting Crafter nationally (as a personal research exercise), I engineered a deterministic architecture: the Human-AI Triad.

#The_Human_AI_Triad:
#The_Orchestrator: Human intent sets statutory thresholds and universal EPSG:7844 baselines.
#The_AI_Engine: High-speed translation into declarative configs, ETL scripts, and differential sync tools.
#The_QA_Gate: Human safety valve holding commit keys—enforcing live count reconciliation before write-backs.

Key Insight: AI does not remove QA. It concentrates human time where it matters most: problem definition and quality acceptance.

#How_We_Eliminated_Fake_Data:
#Live_API_Reconciliation: Pre-flight QA connects to live query endpoints across state layers to reconcile counts against S3 tables.
#Deep_Payload_Inspection: ArcGIS servers often return HTTP 200 on internal 404/499 errors or HTML pages. QA inspects JSON bodies and Content-Types to eliminate false positives.
#GeoLibre_QA_Inspector: Single-source inspection canvas with dual-contrast symbology, 30% basemaps, and in-browser spatial SQL.
#Dry_Run_Airlock: Hashes, ETags, and coordinate bounds asserted before any commit.

#What_I_Released:
#National_Scale: Statutory layers across NSW, QLD, VIC, WA, SA, and TAS.
#Multi_Hazard_Modeling: Overlays for Landslide, Earthquake (NSHA), Cyclone (TCHA), and Flooding.
#Cloud_Native_GeoParquet: Sub-second DuckDB-WASM spatial querying ($0.00 compute spend).

#Explore_The_Release:
#National_Report: https://storage.googleapis.com/aura-siting-crafter-geolibre-app/national_suitability_report.html
#QA_Report: https://storage.googleapis.com/aura-siting-crafter-geolibre-app/QA_Report_20260902.html
#GeoLibre_App: https://storage.googleapis.com/aura-siting-crafter-geolibre-app/index.html
#Anti_Mock_Playbook: https://github.com/GetBack2Basics/CheatSheets/blob/main/ai_anti_mock_hallucination_playbook.md
#GitHub_Repo: https://github.com/GetBack2Basics/aura_siting_crafter

#Discussion:
#Q1 - How are you preventing AI hallucinations in your spatial pipelines?
#Q2 - Are you using dry-run airlocks before data commits?

*Note: Independent personal research project exploring open data and AI in the loop.*

#SpatialAI #DataEngineering #GIS #GeoParquet #DuckDB #ApacheSedona #Wherobots #MapLibre #GeoLibre #OpenData #QA #WebGIS
