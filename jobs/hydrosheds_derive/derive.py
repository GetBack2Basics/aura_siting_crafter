"""Regional and national drainage derivatives and GeoLibre display tiles (runs as a Cloud Run job).

Reads the HydroSHEDS COGs written by jobs/hydrosheds_ingest from the public bucket and produces:
  slope (deg), hand_euclid_m (height above nearest drainage, straight-line approximation),
  streams_mask (acc >= threshold), s_drainage (experimental 0..1 hazard score)
as COGs under processed/<key>/ (for national) or processed/<key>/regions/<region>/ (for regional),
plus colourised XYZ PNG tiles under tiles/<key>/<region>/{z}/{x}/{y}.png with a legend.json.
Every output passes the publish gate first.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUCKET = os.environ.get("AURA_BUCKET", "aura-siting-crafter-geolibre-app")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools"))
import build_parts_index  # noqa: E402
import derive_lib as lib  # noqa: E402
from publish_gate import PublishBlocked, assert_publishable  # noqa: E402

SRC_ACC = "hydrosheds_au_acc_3s_v1"
SRC_CON = "hydrosheds_au_con_3s_v1"
OUT_KEYS = {
    "slope_deg": "aura_drainage_slope_deg_v1",
    "hand_euclid_m": "aura_drainage_hand_euclid_m_v1",
    "streams_mask": "aura_drainage_streams_mask_v1",
    "s_drainage": "aura_drainage_s_drainage_v1",
}
NODATA_F32 = -9999.0
TILE_ZOOMS = os.environ.get("AURA_TILE_ZOOMS", "8-12")
NATIONAL_TILE_ZOOMS = os.environ.get("AURA_NATIONAL_TILE_ZOOMS", "3-7")
NATIONAL_BBOX = [112.0, -44.0, 154.0, -10.0]
NATIONAL_GRID_SIZE = (5040, 4080)  # 30 arc-second (~900 m) overview grid across Australia (20.5M cells < MAX_PIXELS)

# colour ramps: (value, (r, g, b, a)); value domain noted in the legend
RAMPS = {
    "acc_log10": [(1, (0, 0, 0, 0)), (2, (186, 228, 250, 150)), (3, (116, 180, 232, 200)),
                  (4, (49, 130, 206, 230)), (5, (8, 81, 156, 255)), (6, (8, 29, 88, 255))],
    "slope_deg": [(0, (0, 0, 0, 0)), (3, (255, 255, 178, 120)), (8, (254, 204, 92, 180)),
                  (15, (253, 141, 60, 210)), (25, (240, 59, 32, 230)), (40, (128, 0, 38, 255))],
    "hand_euclid_m": [(0, (8, 48, 107, 235)), (2, (33, 113, 181, 210)), (5, (107, 174, 214, 170)),
                      (10, (198, 219, 239, 110)), (25, (222, 235, 247, 50)), (50, (0, 0, 0, 0))],
    "streams_mask": [(0, (0, 0, 0, 0)), (1, (30, 100, 255, 255))],
    "s_drainage": [(0, (0, 0, 0, 0)), (0.3, (255, 255, 178, 120)), (0.5, (254, 204, 92, 180)),
                   (0.7, (253, 141, 60, 210)), (0.85, (240, 59, 32, 230)), (1.0, (189, 0, 38, 255))],
}
CON_COLOURS = [(35, 120, 60, 255), (140, 190, 90, 255), (240, 230, 130, 255), (190, 140, 80, 255), (250, 250, 250, 255)]


def load_manifest():
    with open(os.path.join(HERE, "dataset_manifest_v2.json"), "r", encoding="utf-8") as f:
        return json.load(f)["datasets"]


def load_params():
    with open(os.path.join(HERE, "s_drainage_params.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def region_cog(key: str, name: str, region: str) -> str:
    if region == "national":
        return f"/vsigs/{BUCKET}/processed/{key}/{name}"
    return f"/vsigs/{BUCKET}/processed/{key}/regions/{region}/{name}"


def cog_out_object(key: str, name: str, region: str) -> str:
    if region == "national":
        return f"processed/{key}/{name}.tif"
    return f"processed/{key}/regions/{region}/{name}.tif"


def prov_out_object(key: str, region: str) -> str:
    if region == "national":
        return f"processed/{key}/provenance.json"
    return f"processed/{key}/regions/{region}/provenance.json"


def read_raster(path, region="hunter", resample="nearest", tmp=None):
    from osgeo import gdal

    target_path = path
    if region == "national" and tmp is not None:
        warped = os.path.join(tmp, f"national_{os.path.basename(path)}")
        w, h = NATIONAL_GRID_SIZE
        gdal.Warp(
            warped,
            path,
            outputBounds=NATIONAL_BBOX,
            width=w,
            height=h,
            resampleAlg=resample,
            dstSRS="EPSG:4326",
        )
        target_path = warped

    ds = gdal.Open(target_path)
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray().astype("float64")
    nodata = band.GetNoDataValue()
    if nodata is not None:
        arr[arr == nodata] = np.nan
    return arr, ds.GetGeoTransform(), ds.GetProjection()


def write_geotiff(path, arr, gt, proj, nodata=None, dtype=None):
    from osgeo import gdal, gdal_array

    gdal_dtype = gdal_array.NumericTypeCodeToGDALTypeCode(arr.dtype) if dtype is None else dtype
    ds = gdal.GetDriverByName("GTiff").Create(path, arr.shape[1], arr.shape[0], 1, gdal_dtype)
    ds.SetGeoTransform(gt)
    ds.SetProjection(proj)
    band = ds.GetRasterBand(1)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    band.WriteArray(arr)
    ds.FlushCache()
    ds = None


def to_cog(src_tif, dst_tif):
    from osgeo import gdal

    gdal.Translate(dst_tif, src_tif, format="COG",
                   creationOptions=["COMPRESS=DEFLATE", "PREDICTOR=YES", "BIGTIFF=IF_SAFER", "BLOCKSIZE=512"])


def compute_slope(dem, gt, proj, params, tmp):
    from osgeo import gdal

    dem_path = os.path.join(tmp, "dem.tif")
    write_geotiff(dem_path, np.where(np.isnan(dem), NODATA_F32, dem).astype("float32"), gt, proj, NODATA_F32)
    slope_path = os.path.join(tmp, "slope.tif")
    gdal.DEMProcessing(slope_path, dem_path, "slope", scale=params["slope_scale_m_per_degree"], computeEdges=True)
    slope, _, _ = read_raster(slope_path)
    return slope


def ramp_file(path, ramp):
    with open(path, "w", encoding="ascii") as f:
        for value, (r, g, b, a) in ramp:
            f.write(f"{value} {r} {g} {b} {a}\n")
        f.write("nv 0 0 0 0\n")


def upload_dir(client, local_dir, prefix):
    bucket = client.bucket(BUCKET)
    files = [(os.path.join(r, n), os.path.relpath(os.path.join(r, n), local_dir).replace(os.sep, "/"))
             for r, _, names in os.walk(local_dir) for n in names if n.endswith(".png")]

    def push(item):
        path, rel = item
        blob = bucket.blob(f"{prefix}/{rel}")
        blob.cache_control = "public, max-age=31536000, immutable"
        blob.upload_from_filename(path, content_type="image/png")

    with ThreadPoolExecutor(max_workers=32) as pool:
        list(pool.map(push, files))
    return len(files)


def make_tiles(client, tile_key, label, units, arr, gt, proj, ramp, domain_note, region, tmp):
    from osgeo import gdal

    zooms = NATIONAL_TILE_ZOOMS if region == "national" else TILE_ZOOMS
    work = os.path.join(tmp, tile_key)
    os.makedirs(work, exist_ok=True)
    src = os.path.join(work, "value.tif")
    write_geotiff(src, np.where(np.isfinite(arr), arr, NODATA_F32).astype("float32"), gt, proj, NODATA_F32)
    ramp_path = os.path.join(work, "ramp.txt")
    ramp_file(ramp_path, ramp)
    rgba = os.path.join(work, "rgba.tif")
    gdal.DEMProcessing(rgba, src, "color-relief", colorFilename=ramp_path, addAlpha=True)
    tiles_dir = os.path.join(work, "tiles")
    subprocess.run([sys.executable, "-m", "osgeo_utils.gdal2tiles", "--xyz", "-z", zooms, "-w", "none",
                    "--processes=4", rgba, tiles_dir], check=True)
    prefix = f"tiles/{tile_key}/{region}"
    count = upload_dir(client, tiles_dir, prefix)
    finite = arr[np.isfinite(arr)]
    legend = {
        "dataset_key": tile_key, "label": label, "units": units, "region": region,
        "domain_note": domain_note, "zooms": zooms, "tile_count": count,
        "tiles_url_template": f"https://storage.googleapis.com/{BUCKET}/{prefix}/{{z}}/{{x}}/{{y}}.png",
        "ramp": [{"value": v, "rgba": list(c)} for v, c in ramp],
        "stats": {"min": float(finite.min()), "max": float(finite.max()),
                  "p02": float(np.percentile(finite, 2)), "p50": float(np.percentile(finite, 50)),
                  "p98": float(np.percentile(finite, 98)), "valid_cells": int(finite.size)},
        "processed_utc": datetime.now(timezone.utc).isoformat(),
    }
    client.bucket(BUCKET).blob(f"{prefix}/legend.json").upload_from_string(
        json.dumps(legend, indent=2), content_type="application/json")
    print(f"tiles: {prefix} count={count}")


def publish_cog(client, key, name, arr, gt, proj, region, tmp, derived_from, params, extra_note, dtype_f32=True):
    raw = os.path.join(tmp, f"{key}_raw.tif")
    cog = os.path.join(tmp, f"{key}.tif")
    if dtype_f32:
        write_geotiff(raw, np.where(np.isfinite(arr), arr, NODATA_F32).astype("float32"), gt, proj, NODATA_F32)
    else:
        write_geotiff(raw, arr.astype("uint8"), gt, proj)
    to_cog(raw, cog)
    obj = cog_out_object(key, name, region)
    blob = client.bucket(BUCKET).blob(obj)
    blob.cache_control = "public, max-age=31536000, immutable"
    blob.upload_from_filename(cog, content_type="image/tiff")
    res_note = (
        "National overview grid at 30 arc-seconds (~900 m) clipped to Australia [112,-44,154,-10]."
        if region == "national"
        else "Derived from 3 arc-second (~90 m) HydroSHEDS v1 data; screening use only."
    )
    prov = {
        "dataset_key": key, "object": obj, "bytes": os.path.getsize(cog), "region": region,
        "derived_from": derived_from, "note": extra_note,
        "params_sha256": hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest(),
        "params": params, "processed_utc": datetime.now(timezone.utc).isoformat(),
        "limitations": f"{res_note} "
                       "hand_euclid_m uses straight-line nearest drainage, not flow path. "
                       "s_drainage is experimental and uncalibrated.",
    }
    client.bucket(BUCKET).blob(prov_out_object(key, region)).upload_from_string(
        json.dumps(prov, indent=2), content_type="application/json")
    print(f"cog: gs://{BUCKET}/{obj} bytes={prov['bytes']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default=os.environ.get("AURA_REGION", "hunter"))
    args = parser.parse_args()

    datasets = load_manifest()
    params = load_params()
    for key in [SRC_ACC, SRC_CON, *OUT_KEYS.values()]:
        try:
            assert_publishable(datasets[key])
        except (PublishBlocked, KeyError) as exc:
            sys.exit(f"BLOCKED: {exc!r}")

    from google.cloud import storage
    from osgeo import gdal
    gdal.UseExceptions()
    client = storage.Client()

    with tempfile.TemporaryDirectory() as tmp:
        acc, gt, proj = read_raster(
            region_cog(SRC_ACC, "au_acc_3s.tif", args.region),
            region=args.region,
            resample="max",
            tmp=tmp,
        )
        dem, gt2, _ = read_raster(
            region_cog(SRC_CON, "au_con_3s.tif", args.region),
            region=args.region,
            resample="average",
            tmp=tmp,
        )
        if acc.shape != dem.shape or gt != gt2:
            sys.exit(f"acc and con grids differ: {acc.shape} {gt} vs {dem.shape} {gt2}")
        if acc.size > lib.MAX_PIXELS:
            sys.exit(f"{acc.size} pixels exceeds the in-memory limit {lib.MAX_PIXELS}")

        slope = compute_slope(dem, gt, proj, params, tmp)
        streams = lib.stream_mask(acc, params["stream_threshold_cells"])
        hand = lib.height_above_drainage(dem, streams)
        score = lib.s_drainage(acc, hand, slope, params).astype("float64")
        score[~np.isfinite(acc) | ~np.isfinite(dem)] = np.nan
        both = [SRC_ACC, SRC_CON]

        publish_cog(client, OUT_KEYS["slope_deg"], "slope_deg", slope, gt, proj, args.region, tmp, [SRC_CON],
                    params, "slope in degrees (GDAL, scale 111120 m/degree)")
        publish_cog(client, OUT_KEYS["hand_euclid_m"], "hand_euclid_m", hand, gt, proj, args.region, tmp, both,
                    params, f"elevation above nearest stream cell (acc >= {params['stream_threshold_cells']})")
        publish_cog(client, OUT_KEYS["streams_mask"], "streams_mask", streams.astype("uint8"), gt, proj,
                    args.region, tmp, [SRC_ACC], params, "1 where flow accumulation >= threshold", dtype_f32=False)
        publish_cog(client, OUT_KEYS["s_drainage"], "s_drainage", score, gt, proj, args.region, tmp, both, params,
                    "experimental uncalibrated drainage hazard score 0..1")

        make_tiles(client, SRC_ACC, "Flow accumulation (log10 cells)", "log10(upstream cells)",
                   np.log10(np.maximum(acc, 1.0)), gt, proj, RAMPS["acc_log10"], "log10(acc)", args.region, tmp)
        finite_dem = dem[np.isfinite(dem)]
        stops = lib.percentile_stops(dem)
        con_ramp = [(v, c) for v, c in zip(stops, CON_COLOURS)]
        make_tiles(client, SRC_CON, "Conditioned elevation", "m", dem, gt, proj, con_ramp,
                   f"percentile stops p2..p98 of {finite_dem.size} valid cells", args.region, tmp)
        make_tiles(client, OUT_KEYS["slope_deg"], "Slope", "degrees", slope, gt, proj, RAMPS["slope_deg"],
                   "fixed 0..40 deg", args.region, tmp)
        make_tiles(client, OUT_KEYS["hand_euclid_m"], "Height above nearest drainage (straight-line)", "m",
                   hand, gt, proj, RAMPS["hand_euclid_m"], "fixed 0..50 m", args.region, tmp)
        make_tiles(client, OUT_KEYS["streams_mask"], "Derived streams", "mask", streams.astype("float64"), gt, proj,
                   RAMPS["streams_mask"], "0/1", args.region, tmp)
        make_tiles(client, OUT_KEYS["s_drainage"], "S_drainage (experimental)", "0..1", score, gt, proj,
                   RAMPS["s_drainage"], "0..1 uncalibrated", args.region, tmp)
    build_parts_index.refresh_keys(client, [SRC_ACC, SRC_CON, *OUT_KEYS.values()], base_dir=HERE, bucket=BUCKET)
    print("done")


if __name__ == "__main__":
    main()
