def patch_national_report():
    filepath = "runner/national_suitability_report.html"
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update data_verification_technical_report.html to QA_Report_20260902.html
    html = html.replace("data_verification_technical_report.html", "QA_Report_20260902.html")
    
    # 2. Update GeoLibre cloud run proxy link to relative index.html
    html = html.replace("https://geolibre-spatial-ai-proxy-390270537834.australia-southeast1.run.app/", "index.html")

    # 3. Add Map Inspector button if not present
    old_pill = """<a href="index.html" class="metadata-pill" target="_blank" style="background: rgba(6, 182, 212, 0.2); border-color: rgba(6, 182, 212, 0.5); color: #38bdf8; text-decoration: none; font-weight: 700;">"""
    inspector_pill = """<a href="geolibre_qa_inspect.html" class="metadata-pill" target="_blank" style="background: rgba(59, 130, 246, 0.15); border-color: rgba(59, 130, 246, 0.3); color: #60a5fa; text-decoration: none; font-weight: 600;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg>
        Map Inspector ↗
      </a>\n      """
    
    if "geolibre_qa_inspect.html" not in html and old_pill in html:
        html = html.replace(old_pill, inspector_pill + old_pill)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print("Successfully patched runner/national_suitability_report.html header links.")

if __name__ == "__main__":
    patch_national_report()
