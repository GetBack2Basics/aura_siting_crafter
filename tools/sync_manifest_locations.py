"""Sync config/dataset_manifest_v2.json with what really exists in GCS and Wherobots.

Read-only against both stores. Default is a dry run that prints a reconciliation report;
`--write` updates the manifest (kind / access / licence stubs / locations) in place.

  python tools/sync_manifest_locations.py                         # dry run, no network
  python tools/sync_manifest_locations.py --gcs                   # also list the GCS bucket (read-only)
  python tools/sync_manifest_locations.py --wherobots-snapshot f  # merge a catalog snapshot JSON
  python tools/sync_manifest_locations.py --write                 # persist changes

Unknown values stay null. Nothing is invented (zero-mock rule).
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(BASE_DIR, "config", "dataset_manifest_v2.json")

REPO_GCP_PROJECT = "aura-siting-crafter"
BUCKET = "aura-siting-crafter-geolibre-app"
WHEROBOTS_ROOT = "wherobots://fgsdb/aura_siting"

KIND_BY_SERVICE_TYPE = {
    "arcgis_mapserver": "vector",
    "arcgis_featureserver": "vector",
    "geoserver_wfs": "vector",
    "gcs_contours": "vector",
    "gcs_octree_dem": "point_cloud",
    "gcs_octree_dsm": "point_cloud",
    "gcs_copc_laz": "point_cloud",
    "raster_file_download": "raster",
}

GCS_HTTPS_RE = re.compile(r"^https://storage\.googleapis\.com/([^/]+)/(.+?)(?:\?.*)?$")


def derive_kind(entry: dict):
    return KIND_BY_SERVICE_TYPE.get(entry.get("service_type"))


def gcs_uri_from_https(url):
    match = GCS_HTTPS_RE.match(url or "")
    return f"gs://{match.group(1)}/{match.group(2)}" if match else None


def gcs_prefix_for(uri):
    """Object prefix covered by a dataset: the file itself, or the directory for index files like cloud.js."""
    if not uri:
        return None
    path = uri.split("/", 3)[3]
    return path.rsplit("/", 1)[0] + "/" if path.endswith("cloud.js") else path


def build_locations(entry: dict) -> dict:
    gcs_uri = gcs_uri_from_https(entry.get("endpoint"))
    gcs = (
        {"uri": gcs_uri, "https_url": entry["endpoint"], "format": entry.get("service_type"), "present": None,
         "object_count": None, "bytes": None, "updated": None}
        if gcs_uri else None
    )
    table = (entry.get("storage") or {}).get("table_name")
    wherobots = (
        {"uri": f"{WHEROBOTS_ROOT}/{table}", "format": (entry["storage"].get("format")), "present": None,
         "snapshot_id": None}
        if table else None
    )
    return {"gcs": gcs, "wherobots": wherobots}


def backfill(manifest: dict) -> int:
    """Add missing kind/access/licence/locations. Never overwrites existing values."""
    changed = 0
    for entry in manifest.get("datasets", {}).values():
        if "kind" not in entry and derive_kind(entry):
            entry["kind"] = derive_kind(entry)
            changed += 1
        if "access" not in entry:
            entry["access"] = "public"
            changed += 1
        if "licence" not in entry:
            entry["licence"] = {"name": None, "url": None, "attribution": None, "redistribution": None,
                                "verified_on": None}
            changed += 1
        if "locations" not in entry:
            entry["locations"] = build_locations(entry)
            changed += 1
    return changed


def reconcile_gcs(manifest: dict, objects: list) -> dict:
    """objects: [{name, size, updated}] from a real bucket listing."""
    covered = {}
    for key, entry in manifest.get("datasets", {}).items():
        gcs = (entry.get("locations") or {}).get("gcs")
        prefix = gcs_prefix_for(gcs["uri"]) if gcs else None
        if prefix:
            covered[key] = prefix
    report = {"missing": [], "present": [], "orphans": {}}
    claimed = set()
    for key, prefix in covered.items():
        hits = [o for o in objects if o["name"].startswith(prefix)]
        claimed.update(o["name"] for o in hits)
        gcs = manifest["datasets"][key]["locations"]["gcs"]
        gcs["present"] = bool(hits)
        gcs["object_count"] = len(hits)
        gcs["bytes"] = sum(int(o["size"] or 0) for o in hits)
        gcs["updated"] = max((o["updated"] for o in hits), default=None)
        (report["present"] if hits else report["missing"]).append(key)
    orphan_groups = Counter()
    for o in objects:
        if o["name"] not in claimed:
            orphan_groups["/".join(o["name"].split("/")[:3])] += 1
    report["orphans"] = dict(sorted(orphan_groups.items()))
    return report


def reconcile_wherobots(manifest: dict, tables: list) -> dict:
    """tables: [{name, snapshot_id}] from a real catalog listing, matched on table name."""
    by_name = {t["name"]: t for t in tables}
    report = {"missing": [], "present": [], "orphans": []}
    expected = set()
    for key, entry in manifest.get("datasets", {}).items():
        wb = (entry.get("locations") or {}).get("wherobots")
        if not wb:
            continue
        table = wb["uri"].rsplit("/", 1)[-1]
        expected.add(table)
        hit = by_name.get(table)
        wb["present"] = bool(hit)
        wb["snapshot_id"] = hit.get("snapshot_id") if hit else None
        (report["present"] if hit else report["missing"]).append(key)
    report["orphans"] = sorted(set(by_name) - expected)
    return report


def check_cost_project():
    """Repo rule: ADC quota project must equal this repo's GCP project."""
    adc = os.path.join(os.environ.get("APPDATA", ""), "gcloud", "application_default_credentials.json")
    quota = os.environ.get("GOOGLE_CLOUD_QUOTA_PROJECT")
    if not quota and os.path.exists(adc):
        with open(adc, "r", encoding="utf-8") as f:
            quota = json.load(f).get("quota_project_id")
    if quota != REPO_GCP_PROJECT:
        sys.exit(f"STOP: ADC quota project is {quota!r}, expected {REPO_GCP_PROJECT!r}. "
                 f"Run: gcloud auth application-default set-quota-project {REPO_GCP_PROJECT}")


def list_gcs_objects():
    check_cost_project()
    from google.cloud import storage  # imported lazily so dry runs need no credentials
    client = storage.Client(project=REPO_GCP_PROJECT)
    return [{"name": b.name, "size": b.size, "updated": b.updated.isoformat() if b.updated else None}
            for b in client.list_blobs(BUCKET)]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gcs", action="store_true", help="list the GCS bucket (read-only)")
    parser.add_argument("--wherobots-snapshot", help="JSON file: [{name, snapshot_id}] from a real catalog listing")
    parser.add_argument("--write", action="store_true", help="persist changes to the manifest")
    args = parser.parse_args()

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"backfilled fields: {backfill(manifest)}")
    if args.gcs:
        report = reconcile_gcs(manifest, list_gcs_objects())
        print(f"GCS present={len(report['present'])} missing={report['missing']}")
        print(f"GCS orphan groups (in bucket, not in manifest): {json.dumps(report['orphans'], indent=1)}")
    if args.wherobots_snapshot:
        with open(args.wherobots_snapshot, "r", encoding="utf-8") as f:
            report = reconcile_wherobots(manifest, json.load(f))
        print(f"Wherobots present={len(report['present'])} missing={report['missing']}")
        print(f"Wherobots orphan tables: {report['orphans']}")

    if args.write:
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print("manifest written")
    else:
        print("dry run: manifest not modified (use --write)")


if __name__ == "__main__":
    main()

