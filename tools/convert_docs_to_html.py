#!/usr/bin/env python3
"""
Convert markdown planning documents in docs/ to high-fidelity HTML reports
with interactive navigation, Mermaid diagrams, live Google Cloud links, and universal footer.
"""

import os
import re
import markdown

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | AURA Siting Crafter</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <!-- Mermaid JS for Dynamic Architecture Diagrams -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});</script>
  <style>
    :root {{
      --bg-primary: #0a0f1d;
      --bg-secondary: #111827;
      --card-bg: rgba(17, 24, 39, 0.85);
      --border-color: rgba(59, 130, 246, 0.25);
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-green: #22c55e;
      --accent-amber: #f59e0b;
      --accent-purple: #a855f7;
      --font-sans: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: var(--font-sans);
      background-color: var(--bg-primary);
      color: var(--text-primary);
      line-height: 1.6;
      padding: 0;
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(34, 197, 94, 0.08) 0%, transparent 40%);
    }}
    .nav-bar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(10, 15, 29, 0.92);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-color);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .nav-brand {{
      font-weight: 800;
      font-size: 16px;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .nav-brand span {{ color: var(--accent-blue); }}
    .nav-links {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .nav-link {{
      font-size: 12px;
      font-weight: 600;
      color: #93c5fd;
      text-decoration: none;
      padding: 5px 10px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      background: rgba(59, 130, 246, 0.1);
      transition: all 0.2s ease;
    }}
    .nav-link:hover {{
      background: var(--accent-blue);
      color: #0f172a;
    }}
    .container {{
      max-width: 1080px;
      margin: 32px auto 64px auto;
      padding: 0 24px;
    }}
    .content-card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 44px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }}
    h1 {{
      font-size: 28px;
      font-weight: 800;
      color: #ffffff;
      margin-bottom: 12px;
      line-height: 1.3;
    }}
    h2 {{
      font-size: 20px;
      font-weight: 700;
      color: var(--accent-blue);
      margin: 36px 0 16px 0;
      padding-bottom: 8px;
      border-bottom: 1px solid rgba(56, 189, 248, 0.2);
    }}
    h3 {{
      font-size: 16px;
      font-weight: 600;
      color: #e2e8f0;
      margin: 24px 0 12px 0;
    }}
    p, li {{
      font-size: 14.5px;
      color: #cbd5e1;
      margin-bottom: 12px;
    }}
    ul, ol {{ padding-left: 24px; margin-bottom: 16px; }}
    a {{
      color: var(--accent-blue);
      text-decoration: underline;
    }}
    a:hover {{ color: #7dd3fc; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
      font-size: 13.5px;
    }}
    th, td {{
      padding: 10px 14px;
      text-align: left;
      border: 1px solid var(--border-color);
    }}
    th {{
      background: rgba(30, 41, 59, 0.8);
      color: #93c5fd;
      font-weight: 600;
    }}
    tr:nth-child(even) {{
      background: rgba(15, 23, 42, 0.4);
    }}
    code {{
      font-family: var(--font-mono);
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 12.5px;
      color: #38bdf8;
    }}
    pre {{
      background: #090d16;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      margin: 16px 0;
    }}
    pre code {{
      background: none;
      border: none;
      padding: 0;
      color: #f1f5f9;
      font-size: 13px;
    }}
    .mermaid {{
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 20px;
      margin: 20px 0;
      display: flex;
      justify-content: center;
    }}
  </style>
</head>
<body>

<nav class="nav-bar">
  <div class="nav-brand">
    AURA <span>Siting Crafter</span>
  </div>
  <div class="nav-links">
    {nav_links}
  </div>
</nav>

<div class="container">
  <div class="content-card">
    {content}
  </div>
</div>

<footer style="margin-top: 3rem; padding: 1.25rem 1.5rem; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 0.8rem; color: #94a3b8; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; line-height: 1.5;">
  <div style="text-align: left;">
    &copy;&reg; 2026 <a href="https://github.com/GetBack2Basics" target="_blank" style="color: #60a5fa; text-decoration: underline;">GetBack2Basics</a> &bull; <a href="https://aura.getback2basics.net" target="_blank" style="color: #60a5fa; text-decoration: underline;">aura.getback2basics.net</a> &bull; An open-source first commercial initiative
  </div>
  <div style="text-align: right; color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem;">
    Built {timestamp} UTC
  </div>
</footer>

</body>
</html>
"""

BUSINESS_NAV_LINKS = """
    <a href="../../src/geolibre_frontend/projects/index_LMCC_MacquarieCoal.html" target="_blank" class="nav-link">Live Site WebGIS</a>
    <a href="../../src/geolibre_frontend/projects/report_LMCC_MacquarieCoal.html" target="_blank" class="nav-link">Statutory Site Report</a>
    <a href="aura_enterprise_asymmetric_compute_and_ai_safety.html" class="nav-link">Enterprise Architecture</a>
    <a href="macquarie_coal_precinct_site_enhancement_plan.html" class="nav-link">Site Enhancement Plan</a>
    <a href="project_specific_site_enhancement_architecture_plan.html" class="nav-link">Architecture Plan</a>
    <a href="nsw_govt_geospatial_benefits.html" class="nav-link">NSW Govt Guide</a>
    <a href="../articles/linkedin_aura_siting_evolution.html" class="nav-link">Evolution Odyssey</a>
    <a href="../engineering/upstream_geolibre_contributions.html" class="nav-link">Engineering Specs</a>
    <a href="../../src/geolibre_frontend/national_suitability_report.html" target="_blank" class="nav-link">National Baseline</a>
"""

ARTICLES_NAV_LINKS = """
    <a href="../business/aura_enterprise_asymmetric_compute_and_ai_safety.html" class="nav-link">Enterprise Architecture</a>
    <a href="linkedin_aura_siting_evolution.html" class="nav-link">Evolution Odyssey</a>
    <a href="../engineering/upstream_geolibre_contributions.html" class="nav-link">Engineering Specs</a>
    <a href="../../src/geolibre_frontend/index.html" target="_blank" class="nav-link">National Viewer</a>
    <a href="../../src/geolibre_frontend/national_suitability_report.html" target="_blank" class="nav-link">National Baseline</a>
"""

ENGINEERING_NAV_LINKS = """
    <a href="../business/aura_enterprise_asymmetric_compute_and_ai_safety.html" class="nav-link">Enterprise Architecture</a>
    <a href="geolibre_webgis_rendering_spec.html" class="nav-link">Rendering Spec</a>
    <a href="multi_project_pipeline_and_schemas.html" class="nav-link">Pipeline & Schemas</a>
    <a href="upstream_geolibre_contributions.html" class="nav-link">GeoLibre Upstream</a>
    <a href="spatial_qa_and_telemetry_standards.html" class="nav-link">QA & Telemetry</a>
    <a href="../../src/geolibre_frontend/index.html" target="_blank" class="nav-link">National Viewer</a>
"""

def convert_md_to_html(md_path, html_path, title, nav_links=BUSINESS_NAV_LINKS):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Pre-process Mermaid blocks so markdown doesn't mess with them
    mermaid_blocks = []
    def replace_mermaid(match):
        idx = len(mermaid_blocks)
        mermaid_blocks.append(match.group(1))
        return f"<!--MERMAID_BLOCK_{idx}-->"

    md_text = re.sub(r'```mermaid\n(.*?)\n```', replace_mermaid, md_text, flags=re.DOTALL)

    # Convert to HTML
    html_body = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])

    # Re-insert Mermaid blocks
    for idx, block in enumerate(mermaid_blocks):
        clean_block = block.strip()
        html_body = html_body.replace(
            f"<!--MERMAID_BLOCK_{idx}-->",
            f'<div class="mermaid">\n{clean_block}\n</div>'
        )

    from datetime import datetime, timezone
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')

    # Wrap in template
    full_html = HTML_TEMPLATE.format(
        title=title,
        content=html_body,
        timestamp=timestamp,
        nav_links=nav_links.strip()
    )

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"Generated: {html_path}")

def main():
    # 1. Business Stream HTML conversions
    biz_dir = os.path.join(DOCS_DIR, "business")
    if os.path.exists(biz_dir):
        for f in os.listdir(biz_dir):
            if f.endswith(".md"):
                src_md = os.path.join(biz_dir, f)
                dst_html = os.path.join(biz_dir, f.replace(".md", ".html"))
                page_title = f.replace(".md", "").replace("_", " ").title()
                convert_md_to_html(src_md, dst_html, f"AURA Business | {page_title}", nav_links=BUSINESS_NAV_LINKS)

    # 2. Articles Stream HTML conversions
    art_dir = os.path.join(DOCS_DIR, "articles")
    if os.path.exists(art_dir):
        for f in os.listdir(art_dir):
            if f.endswith(".md"):
                src_md = os.path.join(art_dir, f)
                dst_html = os.path.join(art_dir, f.replace(".md", ".html"))
                page_title = f.replace(".md", "").replace("_", " ").title()
                convert_md_to_html(src_md, dst_html, f"AURA Articles | {page_title}", nav_links=ARTICLES_NAV_LINKS)

    # 3. Engineering Hub HTML conversions
    eng_dir = os.path.join(DOCS_DIR, "engineering")
    if os.path.exists(eng_dir):
        for f in os.listdir(eng_dir):
            if f.endswith(".md"):
                src_md = os.path.join(eng_dir, f)
                dst_html = os.path.join(eng_dir, f.replace(".md", ".html"))
                page_title = f.replace(".md", "").replace("_", " ").title()
                convert_md_to_html(src_md, dst_html, f"AURA Engineering | {page_title}", nav_links=ENGINEERING_NAV_LINKS)

if __name__ == "__main__":
    main()
