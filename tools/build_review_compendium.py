#!/usr/bin/env python3
"""
AURA Siting Crafter & GeoLibre Ecosystem
Master External Review Compendium Builder

Compiles all active text, architecture specs, strategic guides, site plans,
and quality standards into:
1. docs/reviews/text_for_review_20260907.md (Markdown with embedded screenshot references)
2. docs/reviews/text_for_review_20260907.docx (Styled Word Document with embedded high-res images, tables, headers, and callouts)
"""

import os
import sys
import re
from datetime import datetime, timezone
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
REVIEWS_DIR = os.path.join(DOCS_DIR, "reviews")
SCREENSHOTS_DIR = os.path.join(REVIEWS_DIR, "screenshots")

os.makedirs(REVIEWS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

DATE_STR = datetime.now().strftime("%Y%m%d")
MD_OUTPUT_PATH = os.path.join(REVIEWS_DIR, f"text_for_review_{DATE_STR}.md")
DOCX_OUTPUT_PATH = os.path.join(REVIEWS_DIR, f"text_for_review_{DATE_STR}.docx")

print(f"Building Master Review Compendium...")
print(f"Target MD:   {MD_OUTPUT_PATH}")
print(f"Target DOCX: {DOCX_OUTPUT_PATH}")

def clean_xml_string(s):
    if not isinstance(s, str):
        return str(s)
    # Remove control characters that violate XML specification
    return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', s)

def read_file(rel_path):
    full_path = os.path.join(DOCS_DIR, rel_path)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            return clean_xml_string(f.read())
    print(f"Warning: {full_path} not found.")
    return ""

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def add_callout(doc, text, title="KEY ARCHITECTURAL PRINCIPLE", color_hex="0284C7"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F0F9FF")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    
    # Left border styling
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="{color_hex}"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    run_title = p.add_run(f"{title}\n")
    run_title.bold = True
    run_title.font.size = Pt(10)
    run_title.font.color.rgb = RGBColor(2, 132, 199)
    
    run_text = p.add_run(text)
    run_text.font.size = Pt(9.5)
    run_text.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph() # spacer

def markdown_to_docx_elements(doc, md_text, img_map=None):
    """
    Parses markdown text into styled docx paragraphs, headings, bullet lists, tables, and images.
    """
    lines = md_text.split('\n')
    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []
    
    def flush_code():
        nonlocal code_lines
        if code_lines:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(clean_xml_string('\n'.join(code_lines)))
            run.font.name = 'Consolas'
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(15, 23, 42)
            code_lines = []

    def flush_table():
        nonlocal table_lines
        if not table_lines:
            return
        # Parse markdown table
        rows_data = []
        for tl in table_lines:
            if re.match(r'^\s*\|?\s*[-:]+[-| :]*\|?\s*$', tl):
                continue
            cells = [clean_xml_string(c.strip()) for c in tl.strip().strip('|').split('|')]
            if cells:
                rows_data.append(cells)
        
        if rows_data:
            num_cols = max(len(r) for r in rows_data)
            tbl = doc.add_table(rows=len(rows_data), cols=num_cols)
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            for r_idx, row in enumerate(rows_data):
                for c_idx in range(num_cols):
                    cell = tbl.cell(r_idx, c_idx)
                    val = row[c_idx] if c_idx < len(row) else ""
                    cell.text = clean_xml_string(val)
                    set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
                    
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    
                    if r_idx == 0:
                        set_cell_background(cell, "0F172A")
                        for run in p.runs:
                            run.bold = True
                            run.font.size = Pt(9)
                            run.font.color.rgb = RGBColor(248, 250, 252)
                    else:
                        bg_color = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
                        set_cell_background(cell, bg_color)
                        for run in p.runs:
                            run.font.size = Pt(8.5)
                            run.font.color.rgb = RGBColor(30, 41, 59)
            doc.add_paragraph() # spacer
        table_lines = []

    for line in lines:
        stripped = line.strip()
        
        # Code block fence
        if stripped.startswith('```'):
            if in_code_block:
                in_code_block = False
                flush_code()
            else:
                if in_table:
                    in_table = False
                    flush_table()
                in_code_block = True
                code_lines = []
            continue
            
        if in_code_block:
            code_lines.append(line)
            continue
            
        # Table detection
        if '|' in line and (line.strip().startswith('|') or len(line.split('|')) >= 3):
            in_table = True
            table_lines.append(line)
            continue
        elif in_table:
            in_table = False
            flush_table()
            
        # Empty line
        if not stripped:
            continue
            
        # Heading 1
        if stripped.startswith('# '):
            p = doc.add_heading(level=1)
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(clean_xml_string(stripped[2:]))
            run.font.color.rgb = RGBColor(15, 23, 42)
            run.bold = True
            continue
            
        # Heading 2
        if stripped.startswith('## '):
            p = doc.add_heading(level=2)
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(clean_xml_string(stripped[3:]))
            run.font.color.rgb = RGBColor(2, 132, 199)
            run.bold = True
            continue
            
        # Heading 3
        if stripped.startswith('### '):
            p = doc.add_heading(level=3)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(clean_xml_string(stripped[4:]))
            run.font.color.rgb = RGBColor(51, 65, 85)
            run.bold = True
            continue

        # Heading 4
        if stripped.startswith('#### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(clean_xml_string(stripped[5:]))
            run.bold = True
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(71, 85, 105)
            continue

        # Bullet list
        if stripped.startswith('- ') or stripped.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            text_content = stripped[2:]
            _add_formatted_runs(p, text_content)
            continue

        # Numbered list
        if re.match(r'^\d+\.\s', stripped):
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            text_content = re.sub(r'^\d+\.\s', '', stripped)
            _add_formatted_runs(p, text_content)
            continue

        # Standard Paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        _add_formatted_runs(p, stripped)
        
    if in_code_block:
        flush_code()
    if in_table:
        flush_table()

def _add_formatted_runs(paragraph, text):
    """
    Parses bold **text**, code `text`, and simple markdown links [title](url)
    """
    text = clean_xml_string(text)
    pattern = re.compile(r'(\*\*.*?\*\*|\`.*?\`|\[.*?\]\(.*?\))')
    tokens = pattern.split(text)
    
    for token in tokens:
        if not token:
            continue
        cleaned = clean_xml_string(token)
        if cleaned.startswith('**') and cleaned.endswith('**') and len(cleaned) >= 4:
            run = paragraph.add_run(clean_xml_string(cleaned[2:-2]))
            run.bold = True
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(30, 41, 59)
        elif cleaned.startswith('`') and cleaned.endswith('`') and len(cleaned) >= 2:
            run = paragraph.add_run(clean_xml_string(cleaned[1:-1]))
            run.font.name = 'Consolas'
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(14, 116, 144)
        elif cleaned.startswith('[') and '](' in cleaned and cleaned.endswith(')'):
            m = re.match(r'\[(.*?)\]\((.*?)\)', cleaned)
            if m:
                label, url = m.groups()
                run = paragraph.add_run(clean_xml_string(label))
                run.font.color.rgb = RGBColor(2, 132, 199)
                run.underline = True
                run.font.size = Pt(9.5)
            else:
                run = paragraph.add_run(cleaned)
                run.font.size = Pt(9.5)
        else:
            run = paragraph.add_run(cleaned)
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(51, 65, 85)

print("Reading and structuring all project documentation...")

# Load core files
docs_dict = {
    "whitepaper": read_file("business/aura_enterprise_asymmetric_compute_and_ai_safety.md"),
    "macquarie_site_plan": read_file("business/macquarie_coal_precinct_site_enhancement_plan.md"),
    "site_architecture_plan": read_file("business/project_specific_site_enhancement_architecture_plan.md"),
    "nsw_govt_benefits": read_file("business/nsw_govt_geospatial_benefits.md"),
    "geolibre_proposals": read_file("engineering/upstream_geolibre_contributions.md"),
    "evolution_odyssey": read_file("articles/linkedin_aura_siting_evolution.md"),
    "geolibre_web_engine": read_file("articles/linkedin_geolibre_web_engine.md"),
    "rendering_spec": read_file("engineering/geolibre_webgis_rendering_spec.md"),
    "pipeline_schemas": read_file("engineering/multi_project_pipeline_and_schemas.md"),
    "qa_standards": read_file("engineering/spatial_qa_and_telemetry_standards.md"),
    "identity_reframing": read_file("archive/identity_and_architecture_reframing_plan.md"),
    "walkthrough_identity": read_file("archive/walkthrough_identity_and_architecture_reframing.md"),
    "walkthrough_macquarie": read_file("archive/walkthrough_macquarie_coal_precinct.md"),
    "macquarie_findings": read_file("archive/macquarie_coal_precinct_docs/key_technical_findings.md"),
    "macquarie_structure_summary": read_file("archive/macquarie_coal_precinct_docs/precinct_structure_plan_summary.md"),
    "macquarie_structure_analysis": read_file("archive/macquarie_coal_precinct_docs/structure_plan_analysis.md"),
    "macquarie_technical_digest": read_file("archive/macquarie_coal_precinct_docs/technical_studies_digest.md"),
    "anti_mock_playbook": read_file("archive/anti_mock_ai_playbook.md"),
    "semi_manual_qa": read_file("archive/semi_manual_qa_process.md"),
    "zero_mock_standard": read_file("archive/zero_mock_data_integrity_standard.md"),
    "telemetry_report": read_file("audit_logs/telemetry_report.md"),
}

# ==========================================
# 1. BUILD MASTER MARKDOWN FILE
# ==========================================
md_compendium = f"""# AURA Siting Crafter & GeoLibre Ecosystem: Master Review Compendium

**Document Reference:** `AURA-REVIEW-{DATE_STR}-V2.4`  
**Date of Compilation:** {datetime.now().strftime("%B %d, %Y")}  
**Status:** Official External Review & Technical Dossier  
**Author & Organization:** GetBack2Basics Spatial AI Engineering & Siting Intelligence  
**Online Platform:** [https://aura.getback2basics.net](https://aura.getback2basics.net)  
**Open-Source Collaboration:** [https://github.com/GetBack2Basics/aura_siting_crafter](https://github.com/GetBack2Basics/aura_siting_crafter)

---

## Executive Review Overview & Table of Contents

This dossier provides a complete compilation of the **AURA Siting Crafter** spatial computing system, the **GeoLibre** web-native geospatial GIS engine, deterministic AI safety architectures, statutory site enhancement methodologies (exemplified through the Macquarie Coal Complex Transformation Precinct), and strategic value realization guides for government and enterprise infrastructure siting.

### Document Navigation Map

1. **[Visual System Portfolio & Screen Capture Dossier](#visual-system-portfolio--screen-capture-dossier)**
2. **[Part I: Enterprise Architecture & Deterministic AI Safety (Whitepaper)](#part-i-enterprise-architecture--deterministic-ai-safety)**
3. **[Part II: Project-Specific Site Siting & Enhancement Methodologies](#part-ii-project-specific-site-siting--enhancement-methodologies)**
   - *Section 2.1: Macquarie Coal Complex Site Enhancement Plan*
   - *Section 2.2: Project-Specific Siting Architecture & Precision Hybrid Engine*
   - *Section 2.3: Statutory Studies Digest & Technical Findings*
4. **[Part III: Strategic Government Value & Benefits Realization Guide](#part-iii-strategic-government-value--benefits-realization-guide)**
5. **[Part IV: Open Source GeoLibre Ecosystem & Upstream Collaboration Proposals](#part-iv-open-source-geolibre-ecosystem--upstream-collaboration-proposals)**
   - *Section 4.1: Upstream PR Proposals & Modular Architecture*
   - *Section 4.2: Web-Native Siting Engine Specification*
6. **[Part V: The Spatial Siting Odyssey: Evolution & Production Milestones](#part-v-the-spatial-siting-odyssey-evolution--production-milestones)**
7. **[Part VI: Platform Engineering Specifications & Architectural Decoupling](#part-vi-platform-engineering-specifications--architectural-decoupling)**
   - *Section 6.1: Default WebGIS Rendering & Visual Hierarchy Specification*
   - *Section 6.2: Identity Reframing & National vs Regional Decoupling*
8. **[Part VII: Quality Assurance, Telemetry & Zero-Mock Integrity Standards](#part-vii-quality-assurance-telemetry--zero-mock-integrity-standards)**
   - *Appendix A: Anti-Mock AI Playbook*
   - *Appendix B: Semi-Manual QA & Ground-Truth Verification*
   - *Appendix C: Zero-Mock Real Data Standard*
   - *Appendix D: Spatial ETL Telemetry Benchmark*

---

## Visual System Portfolio & Screen Capture Dossier

The following screen captures demonstrate the live running interfaces across the National WebGIS, Project-Level Siting Tools, Lineage Audits, and Technical Whitepapers. All images are stored in `docs/reviews/screenshots/`.

### 1. GeoLibre National Spatial Viewer
![GeoLibre National Viewer](screenshots/01_geolibre_national_viewer.png)
*Figure 1: GeoLibre Web-Native National Viewer showing Australia-wide cadastre, transmission line overlays, and real-time DuckDB-WASM spatial query engine.*

### 2. Macquarie Coal Complex Project WebGIS
![Macquarie Coal Complex WebGIS](screenshots/02_macquarie_coal_precinct_webgis.png)
*Figure 2: Site-level WebGIS for the Macquarie Coal Complex showing transmission easement buffers, mine workings hazard zones, and ecological conservation boundaries.*

### 3. Statutory Site Enhancement Report & Evaluation
![Macquarie Coal Complex Site Report](screenshots/03_macquarie_coal_precinct_report.png)
*Figure 3: Statutory site enhancement report evaluating multi-hazard constraints, power injection headroom, and renewable industrial redevelopment potential.*

### 4. National Siting Suitability Baseline Report
![National Suitability Report](screenshots/04_national_suitability_report.png)
*Figure 4: National baseline suitability analysis across 15.4M records with multi-criteria weighted scoring.*

### 5. Data Lineage & Spatial Audit Inspector
![Data Lineage Audit](screenshots/05_data_lineage_audit.png)
*Figure 5: Cryptographic data lineage, spatial layer checksums, and transformation audit trails.*

### 6. Interactive QA & Layer Inspection Tool
![QA Inspector](screenshots/06_qa_inspector.png)
*Figure 6: High-precision GeoLibre QA tool validating coordinate precision, CRS transformations, and attribute integrity.*

### 7. 15.4M Dataset National QA Audit Report
![QA 15.4M Report](screenshots/07_qa_15_4m_report.png)
*Figure 7: Comprehensive statistical QA report validating zero-mock data integrity across all Australian states.*

### 8. Enterprise Asymmetric Compute Whitepaper
![Enterprise Whitepaper](screenshots/08_asymmetric_compute_whitepaper.png)
*Figure 8: High-fidelity interactive technical paper detailing dual-engine compute and AI safety.*

### 9. Macquarie Coal Complex Site Enhancement Strategy
![Site Enhancement Plan](screenshots/09_macquarie_site_enhancement_plan.png)
*Figure 9: Master planning document for transitioning brownfield mining land into a zero-carbon compute hub.*

### 10. NSW Government Geospatial Strategic Benefits Guide
![NSW Government Geospatial Benefits](screenshots/10_nsw_govt_geospatial_benefits.png)
*Figure 10: Economic ROI and inter-agency acceleration model for government geospatial infrastructure.*

### 11. GeoLibre OpenGeos Upstream Proposals
![GeoLibre Contribution Proposals](screenshots/11_geolibre_contribution_proposals.png)
*Figure 11: Five modular PR proposals for upstream integration with opengeos/GeoLibre.*

### 12. The Spatial Siting Odyssey Case Study
![Evolution Odyssey](screenshots/12_evolution_odyssey.png)
*Figure 12: Architectural retrospectives, performance breakthroughs, and technical lessons learned.*

---

# Part I: Enterprise Architecture & Deterministic AI Safety

{docs_dict['whitepaper']}

---

# Part II: Project-Specific Site Siting & Enhancement Methodologies

## Section 2.1: Macquarie Coal Complex Site Enhancement Plan
{docs_dict['macquarie_site_plan']}

## Section 2.2: Project-Specific Siting Architecture & Precision Hybrid Engine
{docs_dict['site_architecture_plan']}

## Section 2.3: Statutory Studies Digest & Key Technical Findings
{docs_dict['macquarie_findings']}

### Precinct Structure Plan Summary
{docs_dict['macquarie_structure_summary']}

### Structure Plan Comprehensive Analysis
{docs_dict['macquarie_structure_analysis']}

---

# Part III: Strategic Government Value & Benefits Realization Guide

{docs_dict['nsw_govt_benefits']}

---

# Part IV: Open Source GeoLibre Ecosystem & Upstream Collaboration Proposals

## Section 4.1: Upstream PR Proposals & Modular Architecture
{docs_dict['geolibre_proposals']}

## Section 4.2: Web-Native Siting Engine Specification
{docs_dict['geolibre_web_engine']}

---

# Part V: The Spatial Siting Odyssey: Evolution & Production Milestones

{docs_dict['evolution_odyssey']}

---

# Part VI: Platform Engineering Specifications & Architectural Decoupling

## Section 6.1: GeoLibre WebGIS Rendering & Visual Hierarchy Specification
{docs_dict['rendering_spec']}

## Section 6.2: Multi-Project Ingestion Pipeline & Schema Blueprint
{docs_dict['pipeline_schemas']}

## Section 6.3: Identity Reframing & National vs Regional Decoupling
{docs_dict['identity_reframing']}

### Identity Walkthrough
{docs_dict['walkthrough_identity']}

### Macquarie Precinct Walkthrough
{docs_dict['walkthrough_macquarie']}

---

# Part VII: Quality Assurance, Telemetry & Zero-Mock Integrity Standards

## Section 7.1: Spatial QA, Telemetry & Zero-Mock Test Standards
{docs_dict['qa_standards']}

## Appendix A: Anti-Mock AI Playbook
{docs_dict['anti_mock_playbook']}

## Appendix B: Semi-Manual QA & Ground-Truth Verification
{docs_dict['semi_manual_qa']}

## Appendix C: Zero-Mock Real Data Standard
{docs_dict['zero_mock_standard']}

## Appendix D: Spatial ETL Telemetry Benchmark
{docs_dict['telemetry_report']}

---
*End of Master Review Compendium — AURA Siting Crafter & GeoLibre Platform*
"""

with open(MD_OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(md_compendium)

print(f"Generated Markdown Compendium: {MD_OUTPUT_PATH} ({len(md_compendium):,} chars)")

# ==========================================
# 2. BUILD WORD DOCUMENT (.DOCX)
# ==========================================
print("Building Word Document (.docx)...")
doc = docx.Document()

# Set standard margins (0.8 inch)
for section in doc.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)
    
    # Configure Header & Footer
    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hrun = hp.add_run("AURA Siting Crafter | Master Technical & Review Compendium")
    hrun.font.name = "Outfit"
    hrun.font.size = Pt(8)
    hrun.font.color.rgb = RGBColor(148, 163, 184)
    
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    frun = fp.add_run("©® 2026 GetBack2Basics • https://aura.getback2basics.net • External Review Copy")
    frun.font.name = "Outfit"
    frun.font.size = Pt(8)
    frun.font.color.rgb = RGBColor(148, 163, 184)

# Document Title Cover Page / Block
p_title = doc.add_paragraph()
p_title.paragraph_format.space_before = Pt(24)
p_title.paragraph_format.space_after = Pt(4)
r_title = p_title.add_run("AURA Siting Crafter & GeoLibre Ecosystem")
r_title.bold = True
r_title.font.name = "Outfit"
r_title.font.size = Pt(24)
r_title.font.color.rgb = RGBColor(15, 23, 42)

p_sub = doc.add_paragraph()
p_sub.paragraph_format.space_before = Pt(0)
p_sub.paragraph_format.space_after = Pt(16)
r_sub = p_sub.add_run("Comprehensive Technical, Strategic & Site Review Compendium")
r_sub.font.name = "Outfit"
r_sub.font.size = Pt(14)
r_sub.font.color.rgb = RGBColor(2, 132, 199)

# Metadata Table
tbl_meta = doc.add_table(rows=5, cols=2)
tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
meta_data = [
    ("Document Reference", f"AURA-REVIEW-{DATE_STR}-V2.4"),
    ("Compilation Date", datetime.now().strftime("%B %d, %Y")),
    ("Review Scope", "Enterprise Compute Architecture, Deterministic AI Safety, Macquarie Site Plan, NSW Govt Value, GeoLibre Open-Source Proposals, Anti-Mock QA"),
    ("Author & Engineering Organization", "GetBack2Basics Spatial AI Engineering & Siting Intelligence"),
    ("Public Platforms", "https://aura.getback2basics.net | https://github.com/GetBack2Basics/aura_siting_crafter")
]
for idx, (k, v) in enumerate(meta_data):
    cell_k = tbl_meta.cell(idx, 0)
    cell_v = tbl_meta.cell(idx, 1)
    cell_k.width = Inches(2.2)
    cell_v.width = Inches(4.5)
    cell_k.text = k
    cell_v.text = v
    set_cell_background(cell_k, "F1F5F9")
    set_cell_background(cell_v, "FFFFFF")
    set_cell_margins(cell_k, top=50, bottom=50, left=100, right=100)
    set_cell_margins(cell_v, top=50, bottom=50, left=100, right=100)
    cell_k.paragraphs[0].runs[0].bold = True
    cell_k.paragraphs[0].runs[0].font.size = Pt(9)
    cell_v.paragraphs[0].runs[0].font.size = Pt(9)

doc.add_paragraph() # spacing

add_callout(
    doc,
    "This compendium gathers the entire active suite of technical whitepapers, statutory site plans, "
    "architecture blueprints, government benefits models, and open-source contribution proposals into a single "
    "exhaustive document for external peer review, stakeholder presentation, and strategic evaluation.",
    title="EXECUTIVE REVIEW BRIEFING",
    color_hex="0284C7"
)

# Insert Screenshot Portfolio Section
h_port = doc.add_heading(level=1)
h_port.add_run("Visual System Portfolio & Screen Capture Dossier")

screenshots_to_embed = [
    ("01_geolibre_national_viewer.png", "Figure 1: GeoLibre Web-Native National Viewer showing Australia-wide cadastre, transmission line overlays, and real-time DuckDB-WASM spatial query engine."),
    ("02_macquarie_coal_precinct_webgis.png", "Figure 2: Site-level WebGIS for the Macquarie Coal Complex showing transmission easement buffers, mine workings hazard zones, and ecological conservation boundaries."),
    ("03_macquarie_coal_precinct_report.png", "Figure 3: Statutory site enhancement report evaluating multi-hazard constraints, power injection headroom, and renewable industrial redevelopment potential."),
    ("04_national_suitability_report.png", "Figure 4: National baseline suitability analysis across 15.4M records with multi-criteria weighted scoring."),
    ("05_data_lineage_audit.png", "Figure 5: Cryptographic data lineage, spatial layer checksums, and transformation audit trails."),
    ("06_qa_inspector.png", "Figure 6: High-precision GeoLibre QA tool validating coordinate precision, CRS transformations, and attribute integrity."),
    ("07_qa_15_4m_report.png", "Figure 7: Comprehensive statistical QA report validating zero-mock data integrity across all Australian states."),
    ("08_asymmetric_compute_whitepaper.png", "Figure 8: High-fidelity interactive technical paper detailing dual-engine compute and AI safety."),
    ("09_macquarie_site_enhancement_plan.png", "Figure 9: Master planning document for transitioning brownfield mining land into a zero-carbon compute hub."),
    ("10_nsw_govt_geospatial_benefits.png", "Figure 10: Economic ROI and inter-agency acceleration model for government geospatial infrastructure."),
    ("11_geolibre_contribution_proposals.png", "Figure 11: Five modular PR proposals for upstream integration with opengeos/GeoLibre."),
    ("12_evolution_odyssey.png", "Figure 12: Architectural retrospectives, performance breakthroughs, and technical lessons learned.")
]

for filename, caption in screenshots_to_embed:
    img_path = os.path.join(SCREENSHOTS_DIR, filename)
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(2)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(6.2))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(12)
        run_cap = p_cap.add_run(caption)
        run_cap.italic = True
        run_cap.font.size = Pt(8.5)
        run_cap.font.color.rgb = RGBColor(100, 116, 139)

doc.add_page_break()

# Function to add major parts
def add_part_heading(title):
    p = doc.add_heading(level=1)
    p.paragraph_format.space_before = Pt(24)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(title)
    run.font.name = "Outfit"
    run.font.size = Pt(16)
    run.bold = True
    run.font.color.rgb = RGBColor(15, 23, 42)

print("Adding Part I: Enterprise Architecture & AI Safety...")
add_part_heading("Part I: Enterprise Architecture & Deterministic AI Safety")
markdown_to_docx_elements(doc, docs_dict["whitepaper"])
doc.add_page_break()

print("Adding Part II: Project-Specific Site Siting & Enhancement...")
add_part_heading("Part II: Project-Specific Site Siting & Enhancement Methodologies")
h2_1 = doc.add_heading(level=2)
h2_1.add_run("Section 2.1: Macquarie Coal Complex Site Enhancement Plan")
markdown_to_docx_elements(doc, docs_dict["macquarie_site_plan"])

h2_2 = doc.add_heading(level=2)
h2_2.add_run("Section 2.2: Project-Specific Siting Architecture & Precision Hybrid Engine")
markdown_to_docx_elements(doc, docs_dict["site_architecture_plan"])

h2_3 = doc.add_heading(level=2)
h2_3.add_run("Section 2.3: Statutory Studies Digest & Technical Findings")
markdown_to_docx_elements(doc, docs_dict["macquarie_findings"])
markdown_to_docx_elements(doc, docs_dict["macquarie_structure_summary"])
markdown_to_docx_elements(doc, docs_dict["macquarie_structure_analysis"])
doc.add_page_break()

print("Adding Part III: Strategic Government Value & Benefits...")
add_part_heading("Part III: Strategic Government Value & Benefits Realization Guide")
markdown_to_docx_elements(doc, docs_dict["nsw_govt_benefits"])
doc.add_page_break()

print("Adding Part IV: Open Source GeoLibre Ecosystem...")
add_part_heading("Part IV: Open Source GeoLibre Ecosystem & Upstream Proposals")
h4_1 = doc.add_heading(level=2)
h4_1.add_run("Section 4.1: Upstream PR Proposals & Modular Architecture")
markdown_to_docx_elements(doc, docs_dict["geolibre_proposals"])

h4_2 = doc.add_heading(level=2)
h4_2.add_run("Section 4.2: Web-Native Siting Engine Specification")
markdown_to_docx_elements(doc, docs_dict["geolibre_web_engine"])
doc.add_page_break()

print("Adding Part V: Evolution Odyssey...")
add_part_heading("Part V: The Spatial Siting Odyssey: Evolution & Production Milestones")
markdown_to_docx_elements(doc, docs_dict["evolution_odyssey"])
doc.add_page_break()

print("Adding Part VI: Platform Specifications...")
add_part_heading("Part VI: Platform Engineering Specifications & Architectural Decoupling")
h6_1 = doc.add_heading(level=2)
h6_1.add_run("Section 6.1: GeoLibre WebGIS Rendering & Visual Hierarchy Specification")
markdown_to_docx_elements(doc, docs_dict["rendering_spec"])

h6_2 = doc.add_heading(level=2)
h6_2.add_run("Section 6.2: Multi-Project Ingestion Pipeline & Schema Blueprint")
markdown_to_docx_elements(doc, docs_dict["pipeline_schemas"])

h6_3 = doc.add_heading(level=2)
h6_3.add_run("Section 6.3: Identity Reframing & National vs Regional Decoupling")
markdown_to_docx_elements(doc, docs_dict["identity_reframing"])
markdown_to_docx_elements(doc, docs_dict["walkthrough_identity"])
markdown_to_docx_elements(doc, docs_dict["walkthrough_macquarie"])
doc.add_page_break()

print("Adding Part VII: Quality Assurance & Zero-Mock Standards...")
add_part_heading("Part VII: Quality Assurance, Telemetry & Zero-Mock Integrity Standards")
h7_0 = doc.add_heading(level=2)
h7_0.add_run("Section 7.1: Spatial QA, Telemetry & Zero-Mock Test Standards")
markdown_to_docx_elements(doc, docs_dict["qa_standards"])

h7_1 = doc.add_heading(level=2)
h7_1.add_run("Appendix A: Anti-Mock AI Playbook")
markdown_to_docx_elements(doc, docs_dict["anti_mock_playbook"])

h7_2 = doc.add_heading(level=2)
h7_2.add_run("Appendix B: Semi-Manual QA & Ground-Truth Verification")
markdown_to_docx_elements(doc, docs_dict["semi_manual_qa"])

h7_3 = doc.add_heading(level=2)
h7_3.add_run("Appendix C: Zero-Mock Real Data Standard")
markdown_to_docx_elements(doc, docs_dict["zero_mock_standard"])

h7_4 = doc.add_heading(level=2)
h7_4.add_run("Appendix D: Spatial ETL Telemetry Benchmark")
markdown_to_docx_elements(doc, docs_dict["telemetry_report"])

# Save Document
doc.save(DOCX_OUTPUT_PATH)
print(f"Successfully created: {DOCX_OUTPUT_PATH} ({os.path.getsize(DOCX_OUTPUT_PATH):,} bytes)")
print("Master Review Compendium Build Complete!")
