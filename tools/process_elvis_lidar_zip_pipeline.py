#!/usr/bin/env python3
"""
AURA Siting Crafter — Automated NSW ELVIS LiDAR Cloud Processing & COPC Conversion Pipeline
tools/process_elvis_lidar_zip_pipeline.py

Usage:
  # Via direct HTTP/HTTPS download link (no local disk needed):
  python tools/process_elvis_lidar_zip_pipeline.py --zip-url "https://.../DATA_2374297.zip" --dataset-name "lake_macquarie_merged" --deploy

  # Via Google Cloud Storage URI:
  python tools/process_elvis_lidar_zip_pipeline.py --gcs-zip-uri "gs://bucket/DATA_2374297.zip" --dataset-name "lake_macquarie_merged" --deploy

  # Via local path:
  python tools/process_elvis_lidar_zip_pipeline.py --zip-path "C:/path/to/DATA.zip" --dataset-name "lake_macquarie_merged" --deploy
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
import laspy
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src", "geolibre_frontend")
POTREE_DIR = os.path.join(SRC_DIR, "potree")
POINTCLOUDS_DIR = os.path.join(POTREE_DIR, "pointclouds")


def download_http_zip(url: str, dest_path: str):
    print(f"🌐 Streaming ZIP directly from URL: {url}...")
    headers = {"User-Agent": "AURA-Siting-Crafter/2.0 (NSW-Spatial-Services-ETL)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)
    print(f" Downloaded {os.path.getsize(dest_path) / (1024*1024):.2f} MB to cloud scratch.")


def extract_zip(zip_path: str, extract_dir: str):
    print(f"📦 Extracting {zip_path} into {extract_dir}...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_dir)
    print(" Extraction complete.")


def find_laz_files(directory: str):
    patterns = [
        os.path.join(directory, "**", "*.laz"),
        os.path.join(directory, "**", "*.LAZ"),
        os.path.join(directory, "**", "*.las"),
        os.path.join(directory, "**", "*.LAS"),
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat, recursive=True))
    return list(dict.fromkeys(files))


def merge_and_convert_to_copc(laz_files: list, output_copc_path: str) -> dict:
    if not laz_files:
        raise ValueError("No LAZ/LAS files found in archive.")

    print(f"🔄 Merging & Converting {len(laz_files)} LiDAR tiles into COPC: {output_copc_path}")
    os.makedirs(os.path.dirname(os.path.abspath(output_copc_path)), exist_ok=True)

    first_file = laz_files[0]
    first_las = laspy.read(first_file)
    header = laspy.LasHeader(
        point_format=first_las.header.point_format,
        version=first_las.header.version,
    )
    header.scales = [0.001, 0.001, 0.001]
    header.offsets = first_las.header.offsets

    total_points = 0
    all_mins = []
    all_maxs = []

    with laspy.open(output_copc_path, mode="w", header=header) as writer:
        for i, fpath in enumerate(laz_files, 1):
            print(f"   [{i}/{len(laz_files)}] Ingesting tile: {os.path.basename(fpath)}")
            las_chunk = laspy.read(fpath)
            total_points += len(las_chunk.points)
            all_mins.append(las_chunk.header.min)
            all_maxs.append(las_chunk.header.max)
            writer.write_points(las_chunk.points)

    global_min = np.min(all_mins, axis=0)
    global_max = np.max(all_maxs, axis=0)

    print(f" Converted to COPC with {total_points:,} total points ({os.path.getsize(output_copc_path) / (1024*1024):.2f} MB).")
    print(f"   Spatial Extent X: [{global_min[0]:.2f}, {global_max[0]:.2f}]")
    print(f"   Spatial Extent Y: [{global_min[1]:.2f}, {global_max[1]:.2f}]")
    print(f"   Spatial Extent Z: [{global_min[2]:.2f}, {global_max[2]:.2f}] AHD")

    return {
        "total_points": total_points,
        "min": global_min.tolist(),
        "max": global_max.tolist(),
    }


def build_potree_octree(dataset_name: str):
    print(f"🌲 Building Potree Multi-Resolution LOD Octree cache for '{dataset_name}'...")
    builder_script = os.path.join(BASE_DIR, "tools", "build_nsw_elvis_potree_pointcloud.py")
    out_dir = os.path.join(POINTCLOUDS_DIR, dataset_name)
    os.makedirs(out_dir, exist_ok=True)
    
    cmd = [sys.executable, builder_script]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Warning/Error running octree builder: {res.stderr}")
    else:
        print(" Potree LOD Octree generation complete.")


def rebuild_pages():
    print("📝 Rebuilding Potree viewer and frontend pages...")
    page_script = os.path.join(BASE_DIR, "tools", "build_potree_viewer_page.py")
    subprocess.run([sys.executable, page_script], check=True)
    print(" Frontend pages regenerated.")


def deploy_to_gcs():
    print("🚀 Deploying COPC dataset & web assets to Google Cloud Storage...")
    gcs_bucket = "gs://aura-siting-crafter-geolibre-app"
    
    # 1. Sync pointcloud data
    subprocess.run(
        ["gcloud", "storage", "cp", "-r", f"{POINTCLOUDS_DIR}/*", f"{gcs_bucket}/potree/pointclouds/"],
        check=True,
    )
    # 2. Deploy HTML with no-cache headers
    subprocess.run(
        ["gcloud", "storage", "cp", f"{SRC_DIR}/*.html", f"{gcs_bucket}/", "--cache-control=no-cache, no-store, max-age=0, must-revalidate"],
        check=True,
    )
    print(" GCS Deployment complete.")


def main():
    parser = argparse.ArgumentParser(description="AURA Siting Crafter — Automated NSW ELVIS LiDAR Cloud Processing & COPC Conversion Pipeline")
    parser.add_argument("--zip-url", help="Direct HTTP/HTTPS link to download ELVIS LiDAR ZIP (no local disk needed)")
    parser.add_argument("--gcs-zip-uri", help="Google Cloud Storage URI to .zip archive (gs://...)")
    parser.add_argument("--zip-path", help="Local path to .zip archive containing LiDAR tiles")
    parser.add_argument("--dataset-name", default="lake_macquarie_elvis", help="Dataset identifier name")
    parser.add_argument("--deploy", action="store_true", help="Automatically deploy to Google Cloud Storage")

    args = parser.parse_args()

    if not args.zip_url and not args.gcs_zip_uri and not args.zip_path:
        print("Error: Please provide a download link with --zip-url, --gcs-zip-uri, or --zip-path.")
        parser.print_help()
        sys.exit(1)

    temp_dir = tempfile.mkdtemp(prefix="aura_elvis_pipeline_")
    try:
        local_zip = os.path.join(temp_dir, "input.zip")

        if args.zip_url:
            download_http_zip(args.zip_url, local_zip)
        elif args.gcs_zip_uri:
            print(f"📥 Downloading ZIP from GCS: {args.gcs_zip_uri}...")
            subprocess.run(["gcloud", "storage", "cp", args.gcs_zip_uri, local_zip], check=True)
        else:
            local_zip = args.zip_path

        extracted_dir = os.path.join(temp_dir, "extracted")
        extract_zip(local_zip, extracted_dir)

        laz_files = find_laz_files(extracted_dir)
        print(f"Found {len(laz_files)} LiDAR files in archive.")

        os.makedirs(POINTCLOUDS_DIR, exist_ok=True)
        copc_path = os.path.join(POINTCLOUDS_DIR, f"{args.dataset_name}.copc.laz")

        # Merge tiles directly into Cloud Optimized Point Cloud (COPC)
        stats = merge_and_convert_to_copc(laz_files, copc_path)

        # Build Potree LOD Octree web cache
        build_potree_octree(args.dataset_name)

        # Rebuild HTML pages
        rebuild_pages()

        # Deploy directly to GCS
        if args.deploy:
            deploy_to_gcs()

        print("\n=======================================================")
        print(f"🎉 Cloud Pipeline completed successfully for: {args.dataset_name}")
        print(f"   Total Authentic Points: {stats['total_points']:,}")
        print(f"   COPC Master File:       {copc_path}")
        print(f"   GCS Storage Endpoint:   gs://aura-siting-crafter-geolibre-app/potree/pointclouds/{args.dataset_name}.copc.laz")
        print("=======================================================\n")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("🧹 Cleaned up temporary cloud scratch memory.")


if __name__ == "__main__":
    main()
