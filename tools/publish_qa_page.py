"""Publish the GeoLibre QA inspector page and its runtime dependencies to the public app bucket.

  python tools/publish_qa_page.py            # dry run: list what would be uploaded
  python tools/publish_qa_page.py --upload   # upload, then verify each object over public HTTPS

Only the QA page, its layer-registry module and the frontend manifest copy are published.
Guards: the ADC quota project must equal the repo project (GCP Cost Project Rule), object names
pass the publish gate, and no value from .env may appear in any uploaded file.
"""

import argparse
import os
import sys
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src", "Ingestion_v2"))
from publish_gate import assert_safe_object_name  # noqa: E402

PROJECT = "aura-siting-crafter"
BUCKET = os.environ.get("AURA_BUCKET", "aura-siting-crafter-geolibre-app")
FRONTEND = os.path.join(BASE, "src", "geolibre_frontend")
FILES = [
    ("docs/qa/index.html", "text/html; charset=utf-8"),
    ("docs/qa/geolibre_qa_inspect.html", "text/html; charset=utf-8"),
    ("js/geolibre-qa-layer-registry.js", "application/javascript; charset=utf-8"),
    ("config/dataset_manifest_v2.json", "application/json"),
]
# Mutable app files: short cache so redeploys show up quickly.
CACHE_CONTROL = "public, max-age=60"


def env_secret_values():
    path = os.path.join(BASE, ".env")
    values = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if len(v) >= 8:
                    values.append(v)
    return values


def preflight():
    secrets = env_secret_values()
    for rel, _ in FILES:
        assert_safe_object_name(rel)
        local = os.path.join(FRONTEND, rel)
        if not os.path.isfile(local):
            raise SystemExit(f"missing local file: {local}")
        text = open(local, encoding="utf-8").read()
        if any(s in text for s in secrets):
            raise SystemExit(f"BLOCKED: {rel} contains a value from .env")


def check_quota_project():
    import google.auth
    creds, project = google.auth.default()
    quota = getattr(creds, "quota_project_id", None)
    if quota != PROJECT:
        raise SystemExit(f"ADC quota project is {quota!r}, expected {PROJECT!r}. Fix before publishing.")
    return project


def upload():
    from google.cloud import storage
    client = storage.Client(project=PROJECT)
    bucket = client.bucket(BUCKET)
    for rel, ctype in FILES:
        blob = bucket.blob(rel)
        blob.cache_control = CACHE_CONTROL
        blob.upload_from_filename(os.path.join(FRONTEND, rel), content_type=ctype)
        print(f"uploaded gs://{BUCKET}/{rel} ({os.path.getsize(os.path.join(FRONTEND, rel)):,} bytes)")


def verify():
    ok = True
    for rel, _ in FILES:
        url = f"https://storage.googleapis.com/{BUCKET}/{rel}"
        local = open(os.path.join(FRONTEND, rel), "rb").read()
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                remote = r.read()
                same = remote == local
                print(f"{'OK ' if same else 'DIFF'} HTTP {r.status} {url}")
                ok = ok and same
        except Exception as e:  # report and fail
            print(f"FAIL {url}: {e}")
            ok = False
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--upload", action="store_true")
    args = ap.parse_args()
    preflight()
    if not args.upload:
        for rel, ctype in FILES:
            print(f"would upload {rel} -> gs://{BUCKET}/{rel} [{ctype}]")
        return
    check_quota_project()
    upload()
    sys.exit(0 if verify() else 1)


if __name__ == "__main__":
    main()

