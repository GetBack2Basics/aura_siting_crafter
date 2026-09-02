"""
AURA Siting Crafter — Automated Endpoint Audit Tool
Audits 100% of live government endpoints across National and State datasets.
"""

import sys
import glob
import json
import requests

def audit_endpoints(timeout=6):
    configs = sorted(glob.glob("config/datasets_v2/*/*.json"))
    print("=" * 70)
    print("AURA Siting Crafter — Live Endpoint Audit Tool")
    print(f"Auditing {len(configs)} dataset configurations...")
    print("=" * 70)

    success_count = 0
    failed_count = 0
    results = []

    for c in configs:
        with open(c, "r", encoding="utf-8") as f:
            d = json.load(f)
        k = d.get("dataset_key")
        endpoint = d.get("endpoint", "")

        if not endpoint:
            print(f"[FAIL NO_ENDPOINT] {k}")
            failed_count += 1
            results.append((k, "NO_ENDPOINT", False))
            continue

        try:
            r = requests.get(endpoint, timeout=timeout, allow_redirects=True)
            has_error_json = False
            if r.status_code == 200 and r.text.strip().startswith("{"):
                try:
                    j = r.json()
                    if "error" in j and ("code" in j["error"] or "message" in j["error"]):
                        has_error_json = True
                except Exception:
                    pass

            if r.status_code == 200 and not has_error_json:
                print(f"[200 OK] {k} -> {endpoint}")
                success_count += 1
                results.append((k, endpoint, True))
            else:
                err_msg = f"HTTP {r.status_code}" if r.status_code != 200 else "ArcGIS JSON Error"
                print(f"[{err_msg}] {k} -> {endpoint}")
                failed_count += 1
                results.append((k, endpoint, False))
        except Exception as ex:
            print(f"[ERROR: {type(ex).__name__}] {k} -> {endpoint}")
            failed_count += 1
            results.append((k, endpoint, False))

    print("=" * 70)
    print(f"Audit Summary: {success_count}/{len(configs)} Passed (HTTP 200), {failed_count} Failed.")
    print("=" * 70)

    return failed_count == 0

if __name__ == "__main__":
    ok = audit_endpoints()
    if not ok:
        sys.exit(1)
    sys.exit(0)
