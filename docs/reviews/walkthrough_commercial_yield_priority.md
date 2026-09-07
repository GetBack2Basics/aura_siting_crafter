# Walkthrough: Commercial Yield Priority & Frontend Assembly

We have completed the restructuring of the source files in `runner/attachments/`, the core markdown documents, and the compilation into `src/geolibre_frontend/` to emphasize **Commercial Yield, Investment Due Diligence, and Statutory Liability Shields (The Bank Vault)**.

---

## Key Changes Made

### 1. Attachment Sources & Presets (`runner/attachments/`)
- **`runner/attachments/whitepapers.html`**:
  - Embedded direct access links to the **AURA Enterprise Commercial Siting Prospectus** (64% Net-to-Gross developable yield, 4 Bank Vault guarantees) and the **Macquarie Coal Precinct Site Enhancement Plan**.
- **`runner/attachments/strategic_personas.html` & `runner/attachments/persona_configs.json`**:
  - Added the **Institutional Allocator / Chief Risk Officer (CRO)** persona preset:
    - *Policy Weights*: Power 35%, Sensitive 25%, Water 20%, Size 20%.
    - *Commercial Focus*: 64.0% developable yield targeting, Capex/OpEx grid proximity optimization (&le;0.5km 330kV corridor), 100% recycled cooling, and the 4 Bank Vault guarantees.
- **`runner/attachments/ask_ai_mechanics.html`**:
  - Re-anchored the deterministic text-to-SQL compiler explanation as an enterprise risk firewall protecting statutory data integrity.

### 2. Assembly into Frontend Applications (`src/geolibre_frontend/`)
- **`src/geolibre_frontend/national_suitability_report.html`**:
  - Rebuilt via `python runner/build_suitability_report.py` (9.27 MB single-file standalone web application).
  - Integrates the updated whitepaper reference links, institutional persona presets, and multi-hazard scoring matrices.
- **`src/geolibre_frontend/data_lineage_audit.html`**:
  - Rebuilt via `python tools/build_data_lineage_audit.py` with 100% verified internal relative links.
- **`src/geolibre_frontend/projects/report_LMCC_MacquarieCoal.html` & `index_LMCC_MacquarieCoal.html`**:
  - Rebuilt via `python tools/build_project_package.py --manifest config/projects/LMCC_MacquarieCoal.json`.
  - Features the **Statutory Integrity & Commercial Risk Shield (The Bank Vault)** visual banner directly beneath the site metadata grid.

### 3. Core Markdown Documentation (`docs/business/` & `docs/articles/`)
- Restructured `aura_enterprise_asymmetric_compute_and_ai_safety.md` to lead with commercial yield (64.0% Net-to-Gross vs. 42.0% baseline), 10 certified pads, 1.2 GL/yr potable water savings, and the 4 Bank Vault guarantees, sequestering cloud plumbing to the Technical Appendix.
- Updated `project_specific_site_enhancement_architecture_plan.md`, `macquarie_coal_precinct_site_enhancement_plan.md`, and `linkedin_aura_siting_evolution.md`.

---

## Verification Results

1. **Pre-Release Report Verification**:
   ```bash
   python tools/verify_all_release_reports.py
   ```
   **Result**: `[VERIFICATION RESULT]: PASSED (23/23 files compliant)`

2. **Zero-Mock AST Scan**:
   ```bash
   pytest tests/lint/test_no_mock_data.py -v
   ```
   **Result**: `44 passed` (100% genuine data provenance).

3. **Complete Lint Suite**:
   ```bash
   pytest tests/lint/ -v
   ```
   **Result**: `396 passed, 1 skipped` (0 secrets, 0 broken paths).

4. **Graphify Dependency Scan**:
   ```bash
   python tools/graphify_analysis.py
   ```
   **Result**: 0 secrets detected, clean import graph.

---

## Compute & Cost Protection Status
- All SedonaContext/Spark runtimes, Wherobots jobs, and background pytest tasks have been **terminated cleanly**.
- Zero active idle compute resources remain running.
