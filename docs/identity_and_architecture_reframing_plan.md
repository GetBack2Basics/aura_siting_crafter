# Implementation Plan — Resolving the AURA Siting Crafter Identity Crisis & Architecture Framing (Updated)

This plan integrates the user feedback to establish an **open-source first commercial initiative by GetBack2Basics** hosted at `https://aura.getback2basics.net`. 

All documentation, architecture reports, and interactive UI components (including the Cost tab, modals, and universal footers) will be reframed using **clear, business- and engineering-first language** that technical buyers, infrastructure funds, energy developers, and statutory planning authorities can instantly understand and trust.

---

## User Direction & Business Positioning

1. **Domain & Brand Identity**:
   - Primary Cloud Root: **`https://aura.getback2basics.net`**
   - Organization: **GetBack2Basics** (`https://getback2basics.net` / `https://github.com/GetBack2Basics`)
   - Model: **Open-Source First Commercial Solution** (The Red Hat / Databricks enterprise pattern).
2. **Tone & Style**:
   - Business & Engineering First: Translate complex spatial jargon into tangible business outcomes (de-risking capital expenditure, audited net developable land yield, statutory compliance, grid interconnection certainty).
   - Authoritative & Transparent: Strip out self-deprecating hobby/weekend language ("student driver sticker").
3. **Pillars to Execute**:
   - **Pillar 1: Commercial & Open-Source Dual Identity** (AURA Open Spatial Core vs. AURA Enterprise Siting Solutions).
   - **Pillar 2: Deterministic AI Safety Guardrails** (Read-only text-to-SQL compiler trapped in a deterministic sandbox querying pre-certified data assets).
   - **Pillar 3: Asymmetric Compute & Cost Tab Overhaul** (Update all Cost tabs, modals, and tooltips to present the Asymmetric Compute Model with transparent upstream batch ETL costs vs. $0 marginal downstream client execution).

---

## Planned File Modifications

### 1. Core Documentation & Public Articles (`docs/`)
- [`docs/linkedin_aura_siting_evolution.md`](file:///c:/Projects/aura_siting_crafter/docs/linkedin_aura_siting_evolution.md):
  - Strip all hobbyist disclaimers.
  - Position AURA as an open-source first commercial project of GetBack2Basics (`aura.getback2basics.net`).
  - Add the **Deterministic Spatial AI Sandbox** flowchart and text-to-SQL security boundary explanation.
  - Add the **Asymmetric Compute Model** section and the comparative cost breakdown table.
  - Reframe delivery model into Open Source Core vs. Certified Turnkey Commercial Service.
- [`docs/aura_enterprise_asymmetric_compute_and_ai_safety.md`](file:///c:/Projects/aura_siting_crafter/docs/aura_enterprise_asymmetric_compute_and_ai_safety.md) [NEW]:
  - Dedicated whitepaper on Asymmetric Compute Architecture, Deterministic AI Sandboxing, and Enterprise Multi-Hazard Due Diligence.
- [`docs/project_specific_site_enhancement_architecture_plan.md`](file:///c:/Projects/aura_siting_crafter/docs/project_specific_site_enhancement_architecture_plan.md):
  - Align with business/engineering-first terminology and `aura.getback2basics.net` links.

### 2. Universal Template Footers & Generator Tooling (`tools/`)
- [`tools/convert_docs_to_html.py`](file:///c:/Projects/aura_siting_crafter/tools/convert_docs_to_html.py):
  - Replace legacy footer disclaimer with official GetBack2Basics enterprise/open-source footer linking to `https://aura.getback2basics.net`.
  - Ensure all markdown whitepapers compile to high-fidelity HTML.
- [`tools/build_project_package.py`](file:///c:/Projects/aura_siting_crafter/tools/build_project_package.py):
  - Update generated HTML template footers and project headers.

### 3. Cost Tabs, Stat Cards, & Suitability Report (`runner/`, `runner/attachments/`)
- [`runner/attachments/cost_reduction_tips.html`](file:///c:/Projects/aura_siting_crafter/runner/attachments/cost_reduction_tips.html):
  - Reframe Strategy 4 into the **Asymmetric Compute Model** with clear upstream vs. downstream cost mechanics.
- [`runner/build_suitability_report.py`](file:///c:/Projects/aura_siting_crafter/runner/build_suitability_report.py) & [`runner/national_suitability_report.html`](file:///c:/Projects/aura_siting_crafter/runner/national_suitability_report.html):
  - Update Cost stat cards, tooltips, and universal footers to reflect the Asymmetric Compute Model and `aura.getback2basics.net`.

### 4. Web Application Frontend (`src/geolibre_frontend/`, `docs/index.html`)
- [`src/geolibre_frontend/index.html`](file:///c:/Projects/aura_siting_crafter/src/geolibre_frontend/index.html) & [`docs/index.html`](file:///c:/Projects/aura_siting_crafter/docs/index.html):
  - Update the Help/About modal, footer, and AI query placeholder/info text to clearly state the read-only deterministic SQL compiler architecture and enterprise foundation.

---

## Verification Plan

1. **Lint & Zero-Mock Verification**:
   ```bash
   pytest tests/lint/ -v
   pytest tests/ -v
   ```
2. **Recompile Documentation HTML**:
   ```bash
   python tools/convert_docs_to_html.py
   ```
3. **Rebuild Project Packages & Suitability Reports**:
   ```bash
   python tools/build_project_package.py --project-id LMCC_MacquarieCoal
   python runner/build_suitability_report.py
   ```
4. **Visual & Content Inspection**:
   - Verify that all footers, articles, cost tabs, and AI tooltips are 100% free of hobby disclaimers and consistently reflect `aura.getback2basics.net`.
