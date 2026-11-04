"""Build per-dataset parts indexes so split rasters load by viewport in the QA page.

  python tools/build_parts_index.py            # dry run: print the indexes
  python tools/build_parts_index.py --upload   # write gs://<bucket>/processed/<key>/parts.json

For every raster dataset in config/dataset_manifest_v2.json, lists the real objects under
processed/<key>/ and tiles/<key>/ (read-only), then records one part per region with:
  bbox (from config/regions/<region>.json, the box the ingest job clipped to), COG URL and size,
  and, if published, the display tile template, zoom range and legend URL.
A national (unclipped) COG at processed/<key>/<name>.tif becomes a part with id "national".
Re-run after any ingest/derive job. Nothing is invented: a dataset with no objects gets no index.
"""

import argparse
import glob
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = "aura-siting-crafter"
BUCKET = os.environ.get("AURA_BUCKET", "aura-siting-crafter-geolibre-app")
PUBLIC = f"https://storage.googleapis.com/{BUCKET}"
NATIONAL_BBOX = [112.0, -44.0, 154.0, -10.0]


def _find_dir(base_dir, *rel_candidates):
    for rel in rel_candidates:
        p = os.path.join(base_dir, *rel)
        if os.path.exists(p):
            return p
    return os.path.join(base_dir, *rel_candidates[0])


def region_bboxes(base_dir=BASE):
    out = {}
    reg_dir = _find_dir(base_dir, ("config", "regions"), ("regions",))
    for path in glob.glob(os.path.join(reg_dir, "*.json")):
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        if cfg.get("region_key") and len(cfg.get("bbox_wgs84") or []) == 4:
            out[cfg["region_key"]] = [float(v) for v in cfg["bbox_wgs84"]]
    return out


def raster_keys(base_dir=BASE):
    mpath = _find_dir(base_dir, ("config", "dataset_manifest_v2.json"), ("dataset_manifest_v2.json",))
    with open(mpath, encoding="utf-8") as f:
        manifest = json.load(f)
    return sorted(k for k, v in manifest["datasets"].items() if v.get("kind") == "raster")


def check_quota_project():
    import google.auth
    creds, _ = google.auth.default()
    if getattr(creds, "quota_project_id", None) != PROJECT:
        raise SystemExit(f"ADC quota project is {creds.quota_project_id!r}, expected {PROJECT!r}.")


def build(client, keys=None, base_dir=BASE, bucket=BUCKET):
    public = f"https://storage.googleapis.com/{bucket}"
    regions = region_bboxes(base_dir)
    target_keys = sorted(keys) if keys is not None else raster_keys(base_dir)
    indexes = {}
    for key in target_keys:
        cogs = {}
        for b in client.list_blobs(bucket, prefix=f"processed/{key}/"):
            if not b.name.lower().endswith((".tif", ".tiff")):
                continue
            bits = b.name.split("/")
            if len(bits) == 5 and bits[2] == "regions":
                cogs[bits[3]] = (b.name, b.size)
            elif len(bits) == 3:
                cogs["national"] = (b.name, b.size)
        legends = {}
        for b in client.list_blobs(bucket, prefix=f"tiles/{key}/", match_glob=f"tiles/{key}/*/legend.json"):
            region = b.name.split("/")[2]
            legends[region] = (b.name, json.loads(b.download_as_text()))
        parts, skipped = [], []
        for pid in sorted(set(cogs) | set(legends), key=lambda p: (0 if p == "national" else 1, p)):
            bbox = NATIONAL_BBOX if pid == "national" else regions.get(pid)
            if bbox is None:
                skipped.append(f"{pid}: no config/regions/{pid}.json bbox")
                continue
            part = {"id": pid, "bbox": bbox}
            if pid in cogs:
                part["cog_url"] = f"{public}/{cogs[pid][0]}"
                part["cog_bytes"] = cogs[pid][1]
            if pid in legends:
                name, legend = legends[pid]
                z = [int(v) for v in str(legend.get("zooms", "")).split("-") if v.strip().isdigit()]
                part["legend_url"] = f"{public}/{name}"
                if legend.get("tiles_url_template"):
                    part["tiles_url_template"] = legend["tiles_url_template"]
                if len(z) == 2:
                    part["minzoom"], part["maxzoom"] = z
            parts.append(part)
        if parts:
            indexes[key] = {"dataset_key": key, "generated_utc": datetime.now(timezone.utc).isoformat(),
                            "part_count": len(parts), "parts": parts, "skipped": skipped}
        else:
            print(f"{key}: no published objects, no index written")
    return indexes


def refresh_keys(client, keys, base_dir=BASE, bucket=BUCKET):
    """Rebuild and upload processed/<key>/parts.json for the given raster dataset keys."""
    public = f"https://storage.googleapis.com/{bucket}"
    indexes = build(client, keys=keys, base_dir=base_dir, bucket=bucket)
    bkt = client.bucket(bucket)
    for key, idx in indexes.items():
        blob = bkt.blob(f"processed/{key}/parts.json")
        blob.cache_control = "public, max-age=60"
        blob.upload_from_string(json.dumps(idx, indent=2), content_type="application/json")
        print(f"parts: {public}/processed/{key}/parts.json ({idx['part_count']} part(s))")
    return indexes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--upload", action="store_true")
    args = ap.parse_args()
    check_quota_project()
    from google.cloud import storage
    client = storage.Client(project=PROJECT)
    indexes = build(client)
    for key, idx in indexes.items():
        print(f"{key}: {idx['part_count']} part(s) {[p['id'] for p in idx['parts']]}"
              + (f" skipped={idx['skipped']}" if idx["skipped"] else ""))
        if args.upload:
            blob = client.bucket(BUCKET).blob(f"processed/{key}/parts.json")
            blob.cache_control = "public, max-age=60"
            blob.upload_from_string(json.dumps(idx, indent=2), content_type="application/json")
            print(f"  -> {PUBLIC}/processed/{key}/parts.json")
    if not args.upload:
        print("dry run; pass --upload to write the indexes")


if __name__ == "__main__":
    sys.exit(main())

