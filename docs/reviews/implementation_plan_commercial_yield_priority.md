# Implementation Plan: Restructure AURA Siting Prospectus & Business Docs for Commercial Yield Priority

## Context & Problem
Based on the executive review debate (*"AURA Technical Transparency Versus Commercial Yield"*), the prospectus and core markdown documents currently suffer from the **"Paradox of Technical Sales"**:
- Despite removing raw code syntax, the documentation still leads with dense cloud and geometric plumbing (Wherobots batch pipelines, Hilbert space-filling GeoParquet partitions, DuckDB-WASM execution internals, AST compiler rules) *before* presenting commercial outcomes and business yield.
- For institutional buyers (REITs, Infrastructure Funds, Chief Risk Officers), this creates an uncompensated cognitive burden.
- The platform's strongest commercial assets—such as the **64% Net-to-Gross developable yield** (vs. 42% regional benchmark), **10 certified Net Developable Pads across 3 phases**, **1.2 GL/yr potable water savings**, **35 dBA acoustic compliance via 3D terrain/bunds**, and the **four unbreakable statutory guarantees (The Titanium Bank Vault)**—are buried behind upstream data engineering diagrams.

## Proposed Strategy: "The Grand Foyer Before the Concrete Specs"
Reorganize the narrative and documentation hierarchy across all core business markdown files and the docx build tooling:

1. **Lead with Commercial Outcomes & Yield on Page 1 / Section 1:**
   - **Executive Investment & Yield Summary**: Lead with the 64% Net-to-Gross developable yield, 10 certified developable pads across 3 phases, 1.2 GL/yr recycled water circularity, and top 5% national transmission proximity.
   - **The Four Unbreakable Guarantees (The Bank Vault)**:
     1. *Zero Spatial Hallucinations* (AI structurally prohibited from authoring uncertified coordinates or boundaries).
     2. *100% Sovereign Data Privacy* (Client-side RAM execution; proprietary acquisition parameters never leave the user's browser).
     3. *Zero Statutory Exhibition Downtime* (Stateless edge vector delivery guaranteeing uninterrupted service for 10,000+ concurrent stakeholders).
     4. *Instant <15ms Due Diligence Recalculation* (Zero-latency sensitivity analysis for boardrooms and planning panels).

2. **Flagship Empirical Demonstration: Macquarie Coal Complex Case Study (Section 2):**
   - Elevate the Macquarie Coal Complex synthesis immediately after the executive yield summary as the live, empirical proof of how AURA transforms complex brownfield constraints (15 statutory studies) into shovel-ready net developable pads (wick-drain settlement 25 kPa -> >150 kPa, 330kV substation + 49 MWh void PHES, 3D terrain/earthen bunds reclaiming land from naive 2D buffers).

3. **Risk Mitigation & Statutory Framework (Section 3):**
   - Translate engineering capabilities directly into institutional liability shields.
   - Ground technical safety mechanisms with clear executive analogies (e.g. the *Titanium Bank Vault*, the *Nightclub Bouncer AST Schema Firewall*, the *3D Topographic Acoustic Shield*).

4. **Macro-to-Micro Continuity & Multi-Project Blueprint (Section 4):**
   - Detail the repeatable ingestion framework for proponent engineering studies and direct deep-linking from national macro baselines to micro-level precinct digital twins.

5. **Architectural Proof & Technical Appendix (Section 5):**
   - House the deep spatial engineering plumbing (Three-tier Asymmetric Compute model, Wherobots Cloud/Apache Sedona batch pipeline, Hilbert space-filling partitions, DuckDB-WASM in-memory execution, AST Schema Firewall mutation rules, cryptographic layer hashing) into a dedicated, rigorous technical proof section at the back of the document for CTOs, spatial engineers, and technical due diligence teams.

---

## User Review Required

> [!IMPORTANT]
> **Narrative Flow Reversal**: This restructuring flips the document hierarchy from *Engineering-First* to *Commercial-Yield-First*. Deep technical plumbing is not removed—it is relocated to a dedicated "Architectural Proof & Technical Appendix" to provide the "titanium locking bolts" for technical auditors without imposing cognitive friction on executive allocators.

---

## Proposed Changes

### Core Business & Prospectus Markdown Documents

#### [MODIFY] [aura_enterprise_asymmetric_compute_and_ai_safety.md](file:///c:/Projects/aura_siting_crafter/docs/business/aura_enterprise_asymmetric_compute_and_ai_safety.md)
- Restructure sections:
  - **Section 1**: Executive Commercial & Yield Summary (64% yield, 10 developable pads, benchmark radar card, 4 Bank Vault guarantees).
  - **Section 2**: Empirical Proof & Site Due Diligence (Macquarie Coal Complex transformation summary & statutory synthesis).
  - **Section 3**: Institutional Risk Mitigation & Statutory Governance Matrix (mapping boardroom risks to architectural shields with executive analogies).
  - **Section 4**: The Commercial & Open-Source Dual Identity (Red Hat / Databricks model).
  - **Section 5 (Appendix)**: Architectural Proof & Technical Reference (Three-tier Asymmetric Compute, Sedona/Wherobots Hilbert partitions, AST Schema Firewall rules, cryptographic lineage).

#### [MODIFY] [project_specific_site_enhancement_architecture_plan.md](file:///c:/Projects/aura_siting_crafter/docs/business/project_specific_site_enhancement_architecture_plan.md)
- Align executive summaries and section flow with commercial yield priorities, highlighting 3D topographical land reclamation vs flat 2D buffers.

#### [MODIFY] [macquarie_coal_precinct_site_enhancement_plan.md](file:///c:/Projects/aura_siting_crafter/docs/business/macquarie_coal_precinct_site_enhancement_plan.md)
- Ensure all metrics (64% yield, 1.2 GL/yr water savings, 10 NDPs, 35 dBA acoustic bunds, 25 kPa -> 150 kPa soil bearing capacity) are harmonized and highlighted in executive sections.

#### [MODIFY] [linkedin_aura_siting_evolution.md](file:///c:/Projects/aura_siting_crafter/docs/articles/linkedin_aura_siting_evolution.md)
- Update narrative flow to reflect the commercial yield vs technical transparency balance.

---

### Build Tooling & Compilation

#### [MODIFY] [build_separated_docs.py](file:///c:/Projects/aura_siting_crafter/tools/build_separated_docs.py)
- Update prospectus docx metadata, callout boxes, and ordering to reflect the commercial yield-first structure when compiling the documents in the subsequent step.

---

## Verification Plan

### Automated Verification
- Run zero-mock AST scanner and lint suite:
  ```bash
  pytest tests/lint/test_no_mock_data.py -v
  pytest tests/lint/ -v
  ```
- Run graphify analysis to ensure no secrets, banned repo names, or broken imports:
  ```bash
  python tools/graphify_analysis.py
  ```

### Document Compilation Verification
- Execute `python tools/build_separated_docs.py` to compile the separated `.docx` files and verify successful generation with zero errors.
