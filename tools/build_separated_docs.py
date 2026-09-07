#!/usr/bin/env python3
"""
AURA Siting Crafter — Separated DOCX Builder
Builds persona-targeted, standalone Word documents (.docx) in dedicated directories:
1. docs/aura_enterprise_siting_prospectus/
2. docs/macquarie_coal_precinct_site_enhancement/
3. docs/nsw_govt_geospatial_benefits/
4. docs/geolibre_contribution_proposals/
5. docs/linkedin_articles_and_case_studies/

Each directory contains:
- The compiled Word document: <doc_name>_{YYYYMMDD}.docx
- A dedicated screenshots/ folder containing relevant high-resolution UI screen grabs embedded directly in the document.
"""

import os
import sys
import re
import shutil
from datetime import datetime
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
SOURCE_SCREENSHOTS_DIR = os.path.join(DOCS_DIR, "screenshots")
DATE_STR = datetime.now().strftime("%Y%m%d")

def clean_xml_string(s):
    if not isinstance(s, str):
        return str(s)
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

def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
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

def add_callout(doc, text, title="EXECUTIVE BRIEFING", color_hex="0284C7"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F0F9FF")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    
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
    doc.add_paragraph()

def _add_formatted_runs(paragraph, text):
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

def markdown_to_docx(doc, md_text):
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
                    set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
                    
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
            doc.add_paragraph()
        table_lines = []

    for line in lines:
        stripped = line.strip()
        
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
            
        if '|' in line and (line.strip().startswith('|') or len(line.split('|')) >= 3):
            in_table = True
            table_lines.append(line)
            continue
        elif in_table:
            in_table = False
            flush_table()
            
        if not stripped:
            continue
            
        if stripped.startswith('# '):
            p = doc.add_heading(level=1)
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(clean_xml_string(stripped[2:]))
            run.font.color.rgb = RGBColor(15, 23, 42)
            run.bold = True
            continue
            
        if stripped.startswith('## '):
            p = doc.add_heading(level=2)
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(clean_xml_string(stripped[3:]))
            run.font.color.rgb = RGBColor(2, 132, 199)
            run.bold = True
            continue
            
        if stripped.startswith('### '):
            p = doc.add_heading(level=3)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(clean_xml_string(stripped[4:]))
            run.font.color.rgb = RGBColor(51, 65, 85)
            run.bold = True
            continue

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

        if stripped.startswith('- ') or stripped.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            text_content = stripped[2:]
            _add_formatted_runs(p, text_content)
            continue

        if re.match(r'^\d+\.\s', stripped):
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            text_content = re.sub(r'^\d+\.\s', '', stripped)
            _add_formatted_runs(p, text_content)
            continue

        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        _add_formatted_runs(p, stripped)
        
    if in_code_block:
        flush_code()
    if in_table:
        flush_table()

def create_styled_document(title, subtitle, meta_items, header_text):
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run(header_text)
        hrun.font.name = "Outfit"
        hrun.font.size = Pt(8)
        hrun.font.color.rgb = RGBColor(148, 163, 184)
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        frun = fp.add_run("©® 2026 GetBack2Basics • https://aura.getback2basics.net • Commercial Open-Source First")
        frun.font.name = "Outfit"
        frun.font.size = Pt(8)
        frun.font.color.rgb = RGBColor(148, 163, 184)

    # Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(18)
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run(title)
    r_title.bold = True
    r_title.font.name = "Outfit"
    r_title.font.size = Pt(22)
    r_title.font.color.rgb = RGBColor(15, 23, 42)

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run(subtitle)
    r_sub.font.name = "Outfit"
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = RGBColor(2, 132, 199)

    # Meta table
    tbl_meta = doc.add_table(rows=len(meta_items), cols=2)
    tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, (k, v) in enumerate(meta_items):
        cell_k = tbl_meta.cell(idx, 0)
        cell_v = tbl_meta.cell(idx, 1)
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(4.5)
        cell_k.text = k
        cell_v.text = v
        set_cell_background(cell_k, "F1F5F9")
        set_cell_background(cell_v, "FFFFFF")
        set_cell_margins(cell_k, top=40, bottom=40, left=80, right=80)
        set_cell_margins(cell_v, top=40, bottom=40, left=80, right=80)
        cell_k.paragraphs[0].runs[0].bold = True
        cell_k.paragraphs[0].runs[0].font.size = Pt(8.5)
        cell_v.paragraphs[0].runs[0].font.size = Pt(8.5)

    doc.add_paragraph()
    return doc

BUSINESS_DIR = os.path.join(DOCS_DIR, "business")
ENGINEERING_DIR = os.path.join(DOCS_DIR, "engineering")
ARTICLES_DIR = os.path.join(DOCS_DIR, "articles")

def embed_screenshots(doc, screenshot_items, domain_dir):
    h = doc.add_heading(level=1)
    h.add_run("Visual Portfolio & Interactive System Captures")
    
    shots_dir = os.path.join(domain_dir, "screenshots")
    for filename, caption in screenshot_items:
        src_path = os.path.join(shots_dir, filename)
        if not os.path.exists(src_path):
            # Fallback check
            src_path = os.path.join(DOCS_DIR, "screenshots", filename)
        if os.path.exists(src_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(8)
            p_img.paragraph_format.space_after = Pt(2)
            run_img = p_img.add_run()
            run_img.add_picture(src_path, width=Inches(6.2))
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(2)
            p_cap.paragraph_format.space_after = Pt(10)
            run_cap = p_cap.add_run(caption)
            run_cap.italic = True
            run_cap.font.size = Pt(8.5)
            run_cap.font.color.rgb = RGBColor(100, 116, 139)
    doc.add_page_break()

# ==============================================================================
# 1. AURA Enterprise Siting Prospectus & Asymmetric Compute Architecture
# ==============================================================================
def build_aura_enterprise_prospectus():
    out_docx = os.path.join(BUSINESS_DIR, f"aura_enterprise_siting_prospectus_{DATE_STR}.docx")
    
    print(f"Compiling: {out_docx}")
    doc = create_styled_document(
        title="AURA Enterprise: Commercial Siting Yield & Statutory Liability Shields",
        subtitle="Institutional Siting Intelligence, 64% Net-to-Gross Land Yield & Deterministic AI Safety",
        meta_items=[
            ("Document Reference", f"AURA-ENT-{DATE_STR}-V2.4"),
            ("Target Audience", "Enterprise Infrastructure Buyers, AI Data Centre Developers, REITs, Institutional Allocators"),
            ("Commercial Highlights", "64.0% Net-to-Gross Yield (10 Certified Pads) | 1.2 GL/yr Recycled Water Savings | Top 5% Grid Access"),
            ("Statutory Guarantees", "Zero Spatial Hallucinations | 100% Sovereign Privacy | 0 Exhibition Downtime | <15ms Recalculation"),
            ("Organization", "GetBack2Basics Spatial AI Engineering"),
            ("Platform Gateway", "https://aura.getback2basics.net"),
            ("Source Materials", "docs/business/aura_enterprise_asymmetric_compute_and_ai_safety.md | docs/business/project_specific_site_enhancement_architecture_plan.md")
        ],
        header_text="AURA Enterprise | Commercial Siting Prospectus & Architecture"
    )
    
    add_callout(
        doc,
        "This dossier establishes the commercial yield and statutory risk mitigation framework of AURA Siting Crafter. "
        "Delivering a 64.0% net-to-gross developable yield across 10 certified pads and saving 1.2 GL/year of drinking water, "
        "AURA protects institutional capital via four unbreakable Bank Vault guarantees: zero spatial hallucinations, "
        "100% sovereign client-side data privacy, zero statutory exhibition downtime for 10,000+ simultaneous users, "
        "and instant <15ms due diligence recalculation—backed by an asymmetric multi-cloud compute architecture.",
        title="EXECUTIVE COMMERCIAL & STATUTORY BRIEFING"
    )
    
    shots = [
        ("08_asymmetric_compute_whitepaper.png", "Figure 1: Interactive Asymmetric Compute & AI Safety Reference Architecture."),
        ("01_geolibre_national_viewer.png", "Figure 2: Continental-scale spatial engine with sub-second vector rendering."),
        ("04_national_suitability_report.png", "Figure 3: National multi-criteria weighted scoring across 15.4M records."),
        ("05_data_lineage_audit.png", "Figure 4: Cryptographic data lineage, layer hashes, and transformation audit trails.")
    ]
    embed_screenshots(doc, shots, BUSINESS_DIR)
    
    # Ingest pure business whitepaper & statutory site enhancement methodology
    markdown_to_docx(doc, read_file("business/aura_enterprise_asymmetric_compute_and_ai_safety.md"))
    doc.add_page_break()
    doc.add_heading("Project-Level Siting Architecture & Delivery Methodology", level=1)
    markdown_to_docx(doc, read_file("business/project_specific_site_enhancement_architecture_plan.md"))
    
    doc.save(out_docx)
    print(f"  OK: {out_docx} ({os.path.getsize(out_docx):,} bytes)")

# ==============================================================================
# 2. Macquarie Coal Complex Site Enhancement & Statutory Prospectus
# ==============================================================================
def build_macquarie_site_enhancement_prospectus():
    out_docx = os.path.join(BUSINESS_DIR, f"macquarie_coal_precinct_site_enhancement_{DATE_STR}.docx")
    
    print(f"Compiling: {out_docx}")
    doc = create_styled_document(
        title="Macquarie Coal Complex Transformation Precinct",
        subtitle="Site-Level Enhancement Plan, Statutory Due Diligence & Technical Studies Digest",
        meta_items=[
            ("Document Reference", f"AURA-SITE-LMCC-{DATE_STR}-V2.4"),
            ("Target Audience", "Planning Authorities (NSW DPHI/IPC), Clean Energy Consortiums, Land Developers"),
            ("Key Metrics", "320 ha Gross Site Area | 44.5 ha Net Developable Pads | 500 MVA Substation | 49 MWh Void PHES"),
            ("Statutory Base", "Synthesis of 15 Public Exhibition Technical Documents (>135 MB)"),
            ("Interactive WebGIS", "https://aura.getback2basics.net/projects/index_LMCC_MacquarieCoal.html"),
            ("Source Materials", "docs/business/macquarie_coal_precinct_site_enhancement_plan.md | docs/archive/macquarie_coal_precinct_docs/*.md")
        ],
        header_text="Macquarie Coal Complex | Site-Level Enhancement Plan"
    )
    
    add_callout(
        doc,
        "A rigorous statutory-grade site evaluation demonstrating AURA's forensic siting capability. "
        "Topologically extracts 10 Net Developable Pads (NDPs) from raw brownfield mining land, integrating 1% AEP flood modeling, "
        "geotechnical mine subsidence strain zones (G1–G3), 330kV transmission injection headroom, and closed-loop thermodynamic cooling.",
        title="STATUTORY SITE EVALUATION SUMMARY"
    )
    
    shots = [
        ("02_macquarie_coal_precinct_webgis.png", "Figure 1: Macquarie Coal Complex Site-Level 3D WebGIS showing 10 developable pads and hazard setbacks."),
        ("03_macquarie_coal_precinct_report.png", "Figure 2: Forensic statutory planning report evaluating power headroom and flood constraints."),
        ("09_macquarie_site_enhancement_plan.png", "Figure 3: Master site enhancement strategy transforming mining land into a green compute hub.")
    ]
    embed_screenshots(doc, shots, BUSINESS_DIR)
    
    markdown_to_docx(doc, read_file("business/macquarie_coal_precinct_site_enhancement_plan.md"))
    doc.add_page_break()
    doc.add_heading("Comprehensive Technical Studies Digest", level=1)
    markdown_to_docx(doc, read_file("archive/macquarie_coal_precinct_docs/key_technical_findings.md"))
    markdown_to_docx(doc, read_file("archive/macquarie_coal_precinct_docs/precinct_structure_plan_summary.md"))
    markdown_to_docx(doc, read_file("archive/macquarie_coal_precinct_docs/structure_plan_analysis.md"))
    
    doc.save(out_docx)
    print(f"  OK: {out_docx} ({os.path.getsize(out_docx):,} bytes)")

# ==============================================================================
# 3. NSW Government Geospatial Modernization Guide
# ==============================================================================
def build_nsw_govt_benefits_guide():
    out_docx = os.path.join(BUSINESS_DIR, f"nsw_govt_geospatial_benefits_{DATE_STR}.docx")
    
    print(f"Compiling: {out_docx}")
    doc = create_styled_document(
        title="NSW Government Geospatial Value & Strategic Benefits Guide",
        subtitle="Transferring Cloud Spatial Analytics Patterns to State Supercomputing & Inter-Agency Planning",
        meta_items=[
            ("Document Reference", f"AURA-GOV-NSW-{DATE_STR}-V2.4"),
            ("Target Audience", "NSW DCCEEW, NSW Spatial Services, State Planning Panels, Treasury & Finance"),
            ("Strategic Pillars", "Statutory Approvals Acceleration, Waratah HPC Integration, Inter-Agency Digital Twin Alignment"),
            ("Delivery Entity", "GetBack2Basics Spatial Analytics"),
            ("Platform Gateway", "https://aura.getback2basics.net"),
            ("Source Materials", "docs/business/nsw_govt_geospatial_benefits.md")
        ],
        header_text="NSW Government | Geospatial Value & Strategic Guide"
    )
    
    add_callout(
        doc,
        "Outlines the strategic and economic return on investment (ROI) for state agencies adopting modern cloud-native "
        "geospatial architectures. Highlights how high-throughput GeoParquet pipelines, parallel spatial I/O on Waratah HPC, "
        "and client-side zero-cost query offloading accelerate statutory assessment timelines while maintaining sovereign data integrity.",
        title="PUBLIC SECTOR VALUE REALIZATION"
    )
    
    shots = [
        ("10_nsw_govt_geospatial_benefits.png", "Figure 1: Strategic benefits matrix and economic ROI model for NSW Government."),
        ("05_data_lineage_audit.png", "Figure 2: Verifiable cryptographic data lineage and automated compliance auditing.")
    ]
    embed_screenshots(doc, shots, BUSINESS_DIR)
    
    markdown_to_docx(doc, read_file("business/nsw_govt_geospatial_benefits.md"))
    
    doc.save(out_docx)
    print(f"  OK: {out_docx} ({os.path.getsize(out_docx):,} bytes)")

# ==============================================================================
# 4. Developer & Engineering Technical Manual (Dedicated Engineering Hub)
# ==============================================================================
def build_developer_engineering_guide():
    out_docx = os.path.join(ENGINEERING_DIR, f"developer_engineering_guide_{DATE_STR}.docx")
    
    print(f"Compiling: {out_docx}")
    doc = create_styled_document(
        title="AURA & GeoLibre: Developer & Engineering Reference Manual",
        subtitle="Client-Side Rendering Specs, Manifest Schemas, Ingestion Pipelines & QA Testing Standards",
        meta_items=[
            ("Document Reference", f"AURA-ENG-{DATE_STR}-V2.4"),
            ("Target Audience", "Software Engineers, Open-Source GIS Developers, Data Pipeline Engineers"),
            ("Core Topics", "WebGIS 60fps Optimization, DuckDB-WASM, Manifest Schemas, Zero-Mock AST Verification"),
            ("Organization", "GetBack2Basics Spatial AI Engineering"),
            ("Code Repository", "https://github.com/GetBack2Basics/aura_siting_crafter"),
            ("Source Materials", "docs/engineering/*.md")
        ],
        header_text="AURA Engineering | Developer Reference Manual"
    )
    
    add_callout(
        doc,
        "Comprehensive technical reference for developers, open-source contributors, and spatial engineers. "
        "Details client-side GPU shader interpolation, HTTP range-request streaming, multi-project manifest schemas, "
        "and zero-mock automated test gates.",
        title="ENGINEERING SPECIFICATION & DEVELOPER GUIDE"
    )
    
    shots = [
        ("01_geolibre_national_viewer.png", "Figure 1: High-throughput GeoLibre WebGIS client running DuckDB-WASM."),
        ("06_qa_inspector.png", "Figure 2: Interactive QA and layer coordinate precision inspector."),
        ("11_geolibre_contribution_proposals.png", "Figure 3: Modular architecture and upstream PR integration roadmap.")
    ]
    embed_screenshots(doc, shots, ENGINEERING_DIR)
    
    # Ingest all engineering specifications
    markdown_to_docx(doc, read_file("engineering/geolibre_webgis_rendering_spec.md"))
    doc.add_page_break()
    doc.add_heading("Multi-Project Ingestion Pipeline & Schema Blueprint", level=1)
    markdown_to_docx(doc, read_file("engineering/multi_project_pipeline_and_schemas.md"))
    doc.add_page_break()
    doc.add_heading("GeoLibre Upstream PR Contribution Proposals", level=1)
    markdown_to_docx(doc, read_file("engineering/upstream_geolibre_contributions.md"))
    doc.add_page_break()
    doc.add_heading("Spatial QA, Telemetry & Zero-Mock Test Standards", level=1)
    markdown_to_docx(doc, read_file("engineering/spatial_qa_and_telemetry_standards.md"))
    
    doc.save(out_docx)
    print(f"  OK: {out_docx} ({os.path.getsize(out_docx):,} bytes)")

# ==============================================================================
# 5. GeoLibre Open-Source Contribution Proposals
# ==============================================================================
def build_geolibre_proposals_manifesto():
    out_docx = os.path.join(ENGINEERING_DIR, f"geolibre_contribution_proposals_{DATE_STR}.docx")
    
    print(f"Compiling: {out_docx}")
    doc = create_styled_document(
        title="GeoLibre Upstream Contribution Proposals & Architecture",
        subtitle="Five Modular Pull Request Blueprints for opengeos/GeoLibre WebGIS Engine",
        meta_items=[
            ("Document Reference", f"GEOLIBRE-OSS-{DATE_STR}-V2.4"),
            ("Target Community", "opengeos/GeoLibre Core Maintainers, Open Source Geospatial Developers"),
            ("5 Core Modules", "DuckDB-WASM Spatial SQL, Feature Limiter, Dynamic Ramps, Single-File HTML Twin, Lineage Auditor"),
            ("Upstream Repo", "https://github.com/opengeos/GeoLibre"),
            ("AURA Fork / Code", "https://github.com/GetBack2Basics/aura_siting_crafter"),
            ("Source Materials", "docs/engineering/upstream_geolibre_contributions.md | docs/articles/linkedin_geolibre_web_engine.md")
        ],
        header_text="GeoLibre | Open-Source Contribution Proposals"
    )
    
    add_callout(
        doc,
        "Technical blueprints and formal pull request designs to contribute AURA's web-native GIS breakthroughs back to the "
        "open-source GeoLibre ecosystem. Designed as 5 cleanly decoupled, non-breaking modular enhancements.",
        title="OPEN SOURCE UPSTREAM PROPOSAL"
    )
    
    shots = [
        ("11_geolibre_contribution_proposals.png", "Figure 1: Upstream PR roadmap and modular architecture specification."),
        ("01_geolibre_national_viewer.png", "Figure 2: Production web-native GeoLibre client executing spatial joins locally."),
        ("06_qa_inspector.png", "Figure 3: Interactive QA inspector validating coordinate transformations.")
    ]
    embed_screenshots(doc, shots, ENGINEERING_DIR)
    
    markdown_to_docx(doc, read_file("engineering/upstream_geolibre_contributions.md"))
    doc.add_page_break()
    doc.add_heading("GeoLibre Web-Native GIS Engine Post", level=1)
    markdown_to_docx(doc, read_file("articles/linkedin_geolibre_web_engine.md"))
    
    doc.save(out_docx)
    print(f"  OK: {out_docx} ({os.path.getsize(out_docx):,} bytes)")

# ==============================================================================
# 6. LinkedIn Articles, Retrospectives & Technical Case Studies
# ==============================================================================
def build_linkedin_articles_case_studies():
    out_docx = os.path.join(ARTICLES_DIR, f"linkedin_articles_and_case_studies_{DATE_STR}.docx")
    
    print(f"Compiling: {out_docx}")
    doc = create_styled_document(
        title="AURA Siting Crafter: Evolution Odyssey & Technical Case Studies",
        subtitle="From Personal Learning Experiment to Commercial Open-Source First Initiative | Wherobots Guest Feature",
        meta_items=[
            ("Document Reference", f"AURA-ARTICLES-{DATE_STR}-V2.4"),
            ("Platform & Channels", "LinkedIn Engineering Articles, Technical Case Studies, Wherobots Technical Guest Blog"),
            ("Technical Validation", "Official Wherobots Guest Blog Feature Invitation (Cloud Spatial SQL & Apache Sedona)"),
            ("Origin & Trajectory", "Exploratory Spatial Research Experiment → Battle-Tested Commercial Open-Source Platform"),
            ("Author & Organization", "GetBack2Basics Spatial AI Engineering (https://aura.getback2basics.net)"),
            ("Source Materials", "docs/articles/linkedin_aura_siting_evolution.md | docs/archive/linkedin_post_*.md")
        ],
        header_text="AURA Siting Crafter | Articles & Technical Odyssey"
    )
    
    add_callout(
        doc,
        "This compendium collects the public articles, engineering retrospectives, and technical case studies chronicling "
        "AURA's development. It highlights the authentic trajectory: starting as an exploratory personal learning project "
        "to test continental-scale spatial algorithms, maturing into an open-source first commercial initiative by GetBack2Basics, "
        "with planned upstream contributions to opengeos/GeoLibre, and technical validation through an official Wherobots Guest Blog Invitation.",
        title="TECHNICAL ODYSSEY & PROVENANCE"
    )
    
    shots = [
        ("12_evolution_odyssey.png", "Figure 1: The Spatial Siting Odyssey: 5-stage evolutionary roadmap."),
        ("07_qa_15_4m_report.png", "Figure 2: Statistical QA audit confirming zero-mock data integrity across 15.4M records.")
    ]
    embed_screenshots(doc, shots, ARTICLES_DIR)
    
    markdown_to_docx(doc, read_file("articles/linkedin_aura_siting_evolution.md"))
    doc.add_page_break()
    doc.add_heading("Release Announcement & Technical Digest", level=1)
    markdown_to_docx(doc, read_file("archive/linkedin_post_aura_release.md"))
    markdown_to_docx(doc, read_file("archive/linkedin_post_qa_and_national_geoparquet.md"))
    doc.add_page_break()
    doc.add_heading("Appendix: Anti-Mock Engineering Standards", level=1)
    markdown_to_docx(doc, read_file("archive/anti_mock_ai_playbook.md"))
    markdown_to_docx(doc, read_file("archive/zero_mock_data_integrity_standard.md"))
    
    doc.save(out_docx)
    print(f"  OK: {out_docx} ({os.path.getsize(out_docx):,} bytes)")

def main():
    print("=" * 70)
    print("Compiling Standalone Persona-Targeted Word Documents (.docx)")
    print("Destination directories: docs/business/, docs/engineering/, docs/articles/")
    print("=" * 70)
    build_aura_enterprise_prospectus()
    build_macquarie_site_enhancement_prospectus()
    build_nsw_govt_benefits_guide()
    build_developer_engineering_guide()
    build_geolibre_proposals_manifesto()
    build_linkedin_articles_case_studies()
    print("=" * 70)
    print("All standalone documents compiled successfully in their domain folders!")
    print("=" * 70)

if __name__ == "__main__":
    main()
