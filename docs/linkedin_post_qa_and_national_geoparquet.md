What happens when you let an AI agent build spatial pipelines without strict guardrails? It "fakes it till it (doesn’t) make it."

LLMs seek the path of least resistance. Faced with heavy spatial transforms, schema drift, or API latency, an unconstrained agent will mock responses, append "real" to logs, and simulate success while skipping critical steps.

In spatial engineering and statutory planning, hallucinated data is fatal.

To scale AURA Siting Crafter nationally (as a personal research exercise), I engineered a deterministic architecture: the Human-AI Triad.

#The_Human_AI_Triad:
#The_Orchestrator: Human intent sets statutory thresholds, canonical themes, and universal EPSG:7844 baselines.
#The_AI_Engine: High-speed translation into declarative configs, two-phase ETL scripts, and differential sync tools.
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
#GeoLibre_App: https://github.com/GetBack2Basics/aura_siting_crafter/blob/main/docs/qa/geolibre_qa_inspect.html
#Anti_Mock_Playbook: https://github.com/GetBack2Basics/CheatSheets/blob/main/ai_anti_mock_hallucination_playbook.md

#Discussion:
#Q1 - How are you preventing AI hallucinations in your spatial pipelines?
#Q2 - Are you using dry-run airlocks before lakehouse commits?

*Note: Independent personal research project exploring open data and AI in the loop.*

#SpatialAI #DataEngineering #GIS #GeoParquet #DuckDB #ApacheSedona #Wherobots #MapLibre #GeoLibre #OpenData #QA #WebGIS
