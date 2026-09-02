What happens when you ask an AI agent to build a national spatial pipeline across 15M parcels and 25 government APIs? It "fakes it till it (doesn’t) make it."

Faced with heavy transforms (GDA2020), multi-hazard overlays, and API latency, an unconstrained AI will silently mock responses, apply Sydney coordinates to Victorian layers, append "real" to logs, and simulate success.

In national infrastructure siting and statutory GIS, hallucinated data is fatal.

To scale AURA Siting Crafter nationally (as a personal research exercise), I engineered a deterministic architecture: the Human-AI Triad.

#The_Human_AI_Triad:
#The_Orchestrator: Human intent sets statutory thresholds, canonical themes, and universal EPSG:7844 baselines.
#The_AI_Engine: High-speed translation into declarative configs, ETL scripts, and differential sync tools.
#The_QA_Gate: Human safety valve holding commit keys—enforcing live API count reconciliation before lakehouse write-backs.

Key Insight: AI does not remove QA. It concentrates human time where it matters most: problem definition and quality acceptance.

#How_We_Eliminated_Fake_Data:
#Live_API_Reconciliation: Pre-flight QA connects to live query endpoints across 25 layers to reconcile live counts against S3 Lakehouse tables.
#GeoLibre_QA_Inspector: Inspection canvas with dual-contrast symbology, 30% basemaps, and in-browser spatial SQL filtering.
#Dry_Run_Airlock: Hashes, ETags, and coordinate bounds asserted before any commit.

#What_We_Released:
#National_Scale: Statutory layers across NSW, QLD, VIC, WA, SA, and TAS.
#Multi_Hazard_Modeling: Direct overlays for Landslide, Earthquake (NSHA), Cyclone (TCHA), and Flooding.
#Cloud_Native_GeoParquet: Sub-second in-browser DuckDB-WASM spatial querying ($0.00 compute spend).

#Explore_The_Release:
#QA_Report: https://github.com/GetBack2Basics/aura_siting_crafter/blob/main/docs/qa/QA_Report_20260902.html
#GeoLibre_App: https://storage.googleapis.com/aura-siting-crafter-geolibre-app/index.html
#Anti_Mock_Playbook: https://github.com/GetBack2Basics/CheatSheets/blob/main/ai_anti_mock_hallucination_playbook.md

#Discussion:
#Q1 - How are you preventing AI hallucinations in your spatial pipelines?
#Q2 - Are you using dry-run airlocks before lakehouse commits?

*Note: Independent personal research project exploring open data and AI in the loop.*

#SpatialAI #DataEngineering #GIS #GeoParquet #DuckDB #ApacheSedona #Wherobots #MapLibre #GeoLibre #OpenData #QA #WebGIS
