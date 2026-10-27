#!/usr/bin/env python3
"""
Helper script to inject Data QA links into AURA frontend pages.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def update_index_html():
    path = os.path.join(BASE_DIR, "src", "geolibre_frontend", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    target = """      <a href="data_lineage_audit.html" class="metadata-pill" target="_blank" style="background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.3); color: #34d399; text-decoration: none;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        Data Provenance & Lineage Audit
      </a>"""

    replacement = """      <a href="data_lineage_audit.html" class="metadata-pill" target="_blank" style="background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.3); color: #34d399; text-decoration: none;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        Data Provenance & Lineage Audit
      </a>
      <a href="data_qa.html" class="metadata-pill" target="_blank" style="background: rgba(16, 185, 129, 0.2); border-color: rgba(16, 185, 129, 0.5); color: #6ee7b7; text-decoration: none; font-weight: 700;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
        Data QA Report ↗
      </a>"""

    if "href=\"data_qa.html\"" in content:
        print("data_qa.html link already present in index.html")
        return

    assert target in content, "Target string not found in index.html"
    content = content.replace(target, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated index.html with Data QA Report link.")

def update_data_lineage_audit():
    path = os.path.join(BASE_DIR, "src", "geolibre_frontend", "data_lineage_audit.html")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    target = """    <div class="nav-pills">
      <a href="index.html" class="nav-pill nav-pill-primary">🌐 Launch National WebGIS</a>
      <a href="national_suitability_report.html" class="nav-pill" target="_blank">📑 Full Siting Report ↗</a>
      <a href="projects/index_LMCC_MacquarieCoal.html" class="nav-pill" target="_blank" style="border-color: #38bdf8; color: #38bdf8;">✨ Site-Specific Demo ↗</a>
    </div>"""

    replacement = """    <div class="nav-pills">
      <a href="index.html" class="nav-pill nav-pill-primary">🌐 Launch National WebGIS</a>
      <a href="national_suitability_report.html" class="nav-pill" target="_blank">📑 Full Siting Report ↗</a>
      <a href="data_qa.html" class="nav-pill" target="_blank" style="border-color: #10b981; color: #34d399; font-weight: 600;">✅ Data QA Report ↗</a>
      <a href="projects/index_LMCC_MacquarieCoal.html" class="nav-pill" target="_blank" style="border-color: #38bdf8; color: #38bdf8;">✨ Site-Specific Demo ↗</a>
    </div>"""

    if "href=\"data_qa.html\"" in content:
        print("data_qa.html link already present in data_lineage_audit.html")
        return

    assert target in content, "Target string not found in data_lineage_audit.html"
    content = content.replace(target, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated data_lineage_audit.html with Data QA link.")

def update_digital_twin_lmcc():
    path = os.path.join(BASE_DIR, "src", "geolibre_frontend", "projects", "digital_twin_LMCC_MacquarieCoal.html")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    target = """            <a href="../map.html" class="hud-btn">
                🌐 National Map
            </a>"""

    replacement = """            <a href="../map.html" class="hud-btn">
                🌐 National Map
            </a>
            <a href="../data_qa.html" target="_blank" class="hud-btn" style="border-color: rgba(16, 185, 129, 0.4); color: #34d399;">
                ✅ Data QA ↗
            </a>"""

    if "href=\"../data_qa.html\"" in content:
        print("data_qa.html link already present in digital_twin_LMCC_MacquarieCoal.html")
        return

    assert target in content, "Target string not found in digital_twin_LMCC_MacquarieCoal.html"
    content = content.replace(target, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated digital_twin_LMCC_MacquarieCoal.html with Data QA link.")

def update_index_lmcc():
    path = os.path.join(BASE_DIR, "src", "geolibre_frontend", "projects", "index_LMCC_MacquarieCoal.html")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    target = """        <a href="../map.html" class="btn btn-outline">
            🌐 National WebGIS Map ↗
        </a>"""

    replacement = """        <a href="../map.html" class="btn btn-outline">
            🌐 National WebGIS Map ↗
        </a>
        <a href="../data_qa.html" target="_blank" class="btn btn-outline" style="border-color: rgba(16, 185, 129, 0.4); color: #34d399;">
            ✅ Automated QA Audit ↗
        </a>"""

    if "href=\"../data_qa.html\"" in content:
        print("data_qa.html link already present in index_LMCC_MacquarieCoal.html")
        return

    assert target in content, "Target string not found in index_LMCC_MacquarieCoal.html"
    content = content.replace(target, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated index_LMCC_MacquarieCoal.html with Data QA link.")

def update_report_lmcc():
    path = os.path.join(BASE_DIR, "src", "geolibre_frontend", "projects", "report_LMCC_MacquarieCoal.html")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    target = """        <a href="../index.html" target="_blank" class="top-nav-link">🇦🇺 National Baseline</a>"""

    replacement = """        <a href="../index.html" target="_blank" class="top-nav-link">🇦🇺 National Baseline</a>
        <a href="../data_qa.html" target="_blank" class="top-nav-link" style="border-color: rgba(16, 185, 129, 0.4); color: #34d399;">✅ Data QA Report ↗</a>"""

    if "href=\"../data_qa.html\"" in content:
        print("data_qa.html link already present in report_LMCC_MacquarieCoal.html")
        return

    assert target in content, "Target string not found in report_LMCC_MacquarieCoal.html"
    content = content.replace(target, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated report_LMCC_MacquarieCoal.html with Data QA link.")

if __name__ == "__main__":
    update_index_html()
    update_data_lineage_audit()
    update_digital_twin_lmcc()
    update_index_lmcc()
    update_report_lmcc()
