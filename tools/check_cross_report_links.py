import re
import os
import requests

reports = {
    "national_suitability_report.html": "runner/national_suitability_report.html",
    "QA_Report_20260902.html": "docs/qa/QA_Report_20260902.html",
    "geolibre_qa_inspect.html": "docs/qa/geolibre_qa_inspect.html",
    "index.html": "src/geolibre_frontend/index.html"
}

print("======================================================================")
print("AURA Siting Crafter — Local & GCS Cross-Report Link Verification")
print("======================================================================")

base_url = "https://storage.googleapis.com/aura-siting-crafter-geolibre-app/"

for name, path in reports.items():
    if not os.path.exists(path):
        print(f"[MISSING] {name} at {path}")
        continue
    
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    
    print(f"\n--- Links inside {name} ({len(html):,} bytes) ---")
    
    # Extract relative hrefs
    hrefs = re.findall(r'href=[\'"](.*?)[\'"]', html)
    rel_hrefs = [h for h in hrefs if not h.startswith("http") and not h.startswith("#") and not h.startswith("javascript") and not h.startswith("data:")]
    
    for h in sorted(set(rel_hrefs)):
        target_clean = h.split("?")[0].split("#")[0]
        if target_clean in reports:
            # Test live on GCS
            gcs_link = base_url + h
            try:
                resp = requests.get(gcs_link, timeout=5)
                print(f"  [GCS {resp.status_code}] href='{h}' -> {target_clean} (MATCHED)")
            except Exception as e:
                print(f"  [GCS ERROR] href='{h}' -> {e}")
        else:
            print(f"  [OTHER / ASSET] href='{h}'")
