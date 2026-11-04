"""HydroSHEDS ingest job (runs in Cloud Run, not on a workstation).

Stages, per dataset key from config/dataset_manifest_v2.json:
  1. publish gate (licence/access) - nothing is written to the public bucket if it fails
  2. raw:  stream the source zip straight into the PRIVATE bucket gs://<raw bucket>/raw/<key>/ (sha256 recorded)
  3. cog:  read the raster inside the zip via GDAL /vsizip/, convert to a Cloud Optimized GeoTIFF
           (optionally clipped to a region bbox from config/regions/<region>.json) and write to the PUBLIC
           gs://<bucket>/processed/<key>/ together with a provenance.json

Environment: AURA_BUCKET (public, default aura-siting-crafter-geolibre-app), AURA_RAW_BUCKET (private,
default aura-siting-crafter-private-raw). Credentials come from the job's
service account via the metadata server; no keys are used or stored.
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
BUCKET = os.environ.get("AURA_BUCKET", "aura-siting-crafter-geolibre-app")  # public: processed outputs only
RAW_BUCKET = os.environ.get("AURA_RAW_BUCKET", "aura-siting-crafter-private-raw")  # private: source archives
RASTER_EXTS = (".tif", ".tiff", ".bil")

sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools"))
import build_parts_index  # noqa: E402
from publish_gate import PublishBlocked, assert_publishable  # noqa: E402


def load_manifest_entry(key: str) -> dict:
    with open(os.path.join(HERE, "dataset_manifest_v2.json"), "r", encoding="utf-8") as f:
        datasets = json.load(f)["datasets"]
    if key not in datasets:
        raise KeyError(f"{key} is not in the manifest")
    return datasets[key]


def load_region_bbox(region: str):
    """Return [minx, miny, maxx, maxy] in WGS84 for a region, or None for national."""
    if region == "national":
        return None
    with open(os.path.join(HERE, "regions", f"{region}.json"), "r", encoding="utf-8") as f:
        bbox = json.load(f)["bbox_wgs84"]
    if len(bbox) != 4:
        raise ValueError(f"region {region}: bbox_wgs84 must have 4 numbers")
    return bbox


def pick_raster(paths):
    """Pick the single raster file inside the zip listing; refuse to guess between several."""
    candidates = sorted(p for p in paths if p.lower().endswith(RASTER_EXTS))
    if len(candidates) != 1:
        raise RuntimeError(f"expected exactly one raster in the archive, found {candidates or 'none'}; "
                           f"listing: {sorted(paths)[:20]}")
    return candidates[0]


def raw_object(key: str, source_url: str) -> str:
    return f"raw/{key}/{os.path.basename(source_url)}"


def cog_object(key: str, raster_name: str, region: str) -> str:
    stem = os.path.splitext(os.path.basename(raster_name))[0]
    if region == "national":
        return f"processed/{key}/{stem}.tif"
    return f"processed/{key}/regions/{region}/{stem}.tif"


def overview_resampling(entry: dict) -> str:
    """Counts (flow accumulation) must not be averaged; elevation can be."""
    return "NEAREST" if "accumulation" in (entry.get("band_semantics") or "") else "AVERAGE"


def stage_raw(entry: dict, client) -> dict:
    import requests

    url = entry["endpoint"]
    obj = raw_object(entry["dataset_key"], url)
    blob = client.bucket(RAW_BUCKET).blob(obj)
    sha = hashlib.sha256()
    size = 0
    with requests.get(url, stream=True, timeout=(30, 300)) as resp:
        resp.raise_for_status()
        source_etag = resp.headers.get("ETag")
        with blob.open("wb", content_type="application/zip") as out:
            for chunk in resp.iter_content(chunk_size=8 * 1024 * 1024):
                sha.update(chunk)
                size += len(chunk)
                out.write(chunk)
    print(f"raw: gs://{RAW_BUCKET}/{obj} bytes={size} sha256={sha.hexdigest()}")
    return {"object": obj, "bytes": size, "sha256": sha.hexdigest(), "source_etag": source_etag}


def stage_cog(entry: dict, raw: dict, region: str, client) -> dict:
    from osgeo import gdal

    gdal.UseExceptions()
    gdal.SetConfigOption("CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE", "YES")
    key = entry["dataset_key"]
    bbox = load_region_bbox(region) or ([112.0, -44.0, 154.0, -10.0] if region == "national" else None)
    options = dict(
        format="COG",
        creationOptions=["COMPRESS=DEFLATE", "PREDICTOR=YES", "BIGTIFF=IF_SAFER",
                         "BLOCKSIZE=512", f"OVERVIEW_RESAMPLING={overview_resampling(entry)}",
                         "NUM_THREADS=ALL_CPUS"],
    )
    if bbox:
        options["projWin"] = [bbox[0], bbox[3], bbox[2], bbox[1]]  # ulx, uly, lrx, lry
        options["projWinSRS"] = "EPSG:4326"
    with tempfile.TemporaryDirectory() as tmp:
        local_zip = None
        if region == "national":
            local_zip = os.path.join(tmp, os.path.basename(raw["object"]))
            print(f"downloading gs://{RAW_BUCKET}/{raw['object']} to local temp for fast national COG build...", flush=True)
            client.bucket(RAW_BUCKET).blob(raw["object"]).download_to_filename(local_zip)
            vsi_zip = f"/vsizip/{local_zip}"
        else:
            vsi_zip = f"/vsizip//vsigs/{RAW_BUCKET}/{raw['object']}"
        inner = pick_raster(gdal.ReadDirRecursive(vsi_zip) or [])
        src_path = f"{vsi_zip}/{inner}"
        out_obj = cog_object(key, inner, region)
        local_out = os.path.join(tmp, "out.tif")
        ds = gdal.Translate(local_out, src_path, **options)
        info = {"width": ds.RasterXSize, "height": ds.RasterYSize,
                "nodata": ds.GetRasterBand(1).GetNoDataValue(),
                "dtype": gdal.GetDataTypeName(ds.GetRasterBand(1).DataType),
                "crs": ds.GetSpatialRef().GetAuthorityCode(None) if ds.GetSpatialRef() else None}
        ds = None
        if local_zip and os.path.exists(local_zip):
            os.remove(local_zip)
        size = os.path.getsize(local_out)
        blob = client.bucket(BUCKET).blob(out_obj)
        blob.cache_control = "public, max-age=31536000, immutable"
        blob.upload_from_filename(local_out, content_type="image/tiff")
    print(f"cog: gs://{BUCKET}/{out_obj} bytes={size} {info}")
    return {"object": out_obj, "bytes": size, "inner_raster": inner, **info}


def write_provenance(entry: dict, raw: dict, cog: dict, region: str, client) -> None:
    licence = entry.get("licence") or {}
    doc = {
        "dataset_key": entry["dataset_key"],
        "source_url": entry["endpoint"],
        "region": region,
        "bbox_wgs84": load_region_bbox(region),
        "raw": raw,
        "cog": cog,
        "licence": {"name": licence.get("name"), "attribution": licence.get("attribution"),
                    "redistribution": licence.get("redistribution")},
        "processed_utc": datetime.now(timezone.utc).isoformat(),
        "modification_note": "Converted to Cloud Optimized GeoTIFF"
                             + (f" and clipped to region '{region}'" if region != "national" else "")
                             + "; values unchanged.",
    }
    base = os.path.dirname(cog["object"])
    client.bucket(BUCKET).blob(f"{base}/provenance.json").upload_from_string(
        json.dumps(doc, indent=2), content_type="application/json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", required=True)
    parser.add_argument("--region", default=os.environ.get("AURA_REGION", "national"))
    parser.add_argument("--skip-raw", action="store_true", help="reuse the raw zip already in GCS")
    args = parser.parse_args()

    from google.cloud import storage
    client = storage.Client()
    for key in args.datasets:
        entry = load_manifest_entry(key)
        try:
            assert_publishable(entry)
        except PublishBlocked as exc:
            sys.exit(f"BLOCKED: {exc}")
        if args.skip_raw:
            blob = client.bucket(RAW_BUCKET).blob(raw_object(key, entry["endpoint"]))
            blob.reload()
            raw = {"object": blob.name, "bytes": blob.size, "etag": blob.etag, "md5_base64": blob.md5_hash}
        else:
            raw = stage_raw(entry, client)
        cog = stage_cog(entry, raw, args.region, client)
        write_provenance(entry, raw, cog, args.region, client)
    build_parts_index.refresh_keys(client, args.datasets, base_dir=HERE, bucket=BUCKET)
    print("done")


if __name__ == "__main__":
    main()
