import re
import requests

with open("docs/qa/QA_Report_20260902.html", "r", encoding="utf-8") as f:
    html = f.read()

hrefs = [h for h in re.findall(r'href=[\'"](.*?)[\'"]', html) if h.startswith("http")]
print(f"Testing {len(hrefs)} external query links from QA Report:")

failed = 0
for h in hrefs:
    try:
        r = requests.get(h, timeout=6)
        has_err = False
        if r.status_code == 200 and r.text.strip().startswith("{"):
            try:
                j = r.json()
                if "error" in j:
                    has_err = True
            except Exception:
                pass
        
        if r.status_code == 200 and not has_err:
            print(f"  [OK 200] {h}")
        else:
            print(f"  [FAIL {r.status_code}] {h}")
            failed += 1
    except Exception as e:
        print(f"  [ERROR] {h} -> {e}")
        failed += 1

print(f"\nResult: {len(hrefs) - failed}/{len(hrefs)} links verified live.")
