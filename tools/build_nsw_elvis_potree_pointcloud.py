#!/usr/bin/env python3
"""
AURA Siting Crafter — Genuine Lake Macquarie ELVIS LiDAR Potree Octree Builder
tools/build_nsw_elvis_potree_pointcloud.py

Processes the authentic Lake Macquarie ELVIS Classified LiDAR tile
(LakeMacquarie201409-LID1-C3-AHD_3666336_56_0002_0002.laz) from:
C:\\Users\\corea\\Downloads\\DATA_2374297\\NSW Government - Spatial Services\\Point Clouds\\AHD

into a multi-resolution Potree octree (.bin) with Level-Of-Detail (LOD) hierarchy
and ASPRS classification colors.
"""

import os
import struct
import json
import laspy
import numpy as np
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC_DIR = os.path.join(BASE_DIR, "src", "geolibre_frontend", "potree", "pointclouds")

PRIMARY_SOURCE = r"C:\Users\corea\Downloads\DATA_2374297\NSW Government - Spatial Services\Point Clouds\AHD\LakeMacquarie201409-LID1-C3-AHD_3666336_56_0002_0002.laz"
LOCAL_SOURCE = os.path.join(PC_DIR, "LakeMacquarie201409-LID1-C3-AHD_3666336_56_0002_0002.laz")

TARGET_DIRS = [
    os.path.join(PC_DIR, "nsw_elvis_lidar_laz_pointcloud_v2"),
    os.path.join(PC_DIR, "nsw_elvis_lake_macquarie_lidar")
]

SCALE = 0.01  # 1cm precision


def get_classification_color(cls: int, z: float, min_z: float, max_z: float) -> tuple:
    """Return RGBA color tuple for a given classification code and elevation."""
    # Water (Class 9)
    if cls == 9:
        return (14, 116, 144, 255)
    # Ground (Class 2, 8, 14, 15)
    elif cls in (2, 8, 14, 15):
        norm = max(0.0, min(1.0, (z - min_z) / max(1.0, max_z - min_z)))
        r = int(170 + norm * 50)
        g = int(140 + norm * 45)
        b = int(85 + norm * 30)
        return (min(255, r), min(255, g), min(255, b), 255)
    # Vegetation (Class 3, 4, 5, 17)
    elif cls in (3, 4, 5, 17):
        if cls == 3:  # Low veg
            return (74, 222, 128, 255)
        elif cls == 4:  # Med veg
            return (34, 197, 94, 255)
        else:  # High veg / canopy
            return (21, 128, 61, 255)
    # Buildings & Structures (Class 6)
    elif cls == 6:
        return (239, 68, 68, 255)
    # High/Low noise (Class 7)
    elif cls == 7:
        return (148, 163, 184, 255)
    # Unclassified / Default
    else:
        norm = max(0.0, min(1.0, (z - min_z) / max(1.0, max_z - min_z)))
        return (int(120 + norm * 80), int(130 + norm * 80), int(110 + norm * 80), 255)


def build_octree():
    source_file = PRIMARY_SOURCE if os.path.exists(PRIMARY_SOURCE) else LOCAL_SOURCE
    if not os.path.exists(source_file):
        raise FileNotFoundError(f"Could not find source LiDAR file at {PRIMARY_SOURCE} or {LOCAL_SOURCE}")

    print(f"1. Reading authentic Lake Macquarie ELVIS LiDAR: {source_file}...")
    las = laspy.read(source_file)
    
    xs = np.array(las.x, dtype=np.float64)
    ys = np.array(las.y, dtype=np.float64)
    zs = np.array(las.z, dtype=np.float64)
    classes = np.array(las.classification, dtype=np.uint8)
    
    n_points = len(xs)
    print(f"   -> Loaded {n_points:,} genuine points.")

    # Filter any extreme telemetry noise (elevation -5m to 250m AHD for Lake Macquarie)
    valid_mask = (zs >= -5.0) & (zs <= 250.0)
    xs = xs[valid_mask]
    ys = ys[valid_mask]
    zs = zs[valid_mask]
    classes = classes[valid_mask]
    n_points = len(xs)
    print(f"   -> Cleaned valid points within terrain bounds: {n_points:,}")
    
    min_x, max_x = float(xs.min()), float(xs.max())
    min_y, max_y = float(ys.min()), float(ys.max())
    min_z, max_z = float(zs.min()), float(zs.max())
    
    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z
    max_side = max(size_x, size_y, size_z) * 1.02
    
    lx, ly, lz = min_x, min_y, min_z
    ux = lx + max_side
    uy = ly + max_side
    uz = lz + max_side
    
    print(f"   -> Tight Bounding Box: [{min_x:.2f}, {min_y:.2f}, {min_z:.2f}] to [{max_x:.2f}, {max_y:.2f}, {max_z:.2f}]")
    print(f"   -> Octree Cubic Box: [{lx:.2f}, {ly:.2f}, {lz:.2f}] to [{ux:.2f}, {uy:.2f}, {uz:.2f}] (Side: {max_side:.2f}m)")

    print("2. Computing ASPRS classification colors...")
    colors = np.zeros((n_points, 4), dtype=np.uint8)
    for i in range(n_points):
        colors[i] = get_classification_color(int(classes[i]), zs[i], min_z, max_z)

    print("3. Generating multi-resolution LOD octree...")
    hierarchy = []
    node_bins = {}

    def partition_node(name: str, idxs: np.ndarray, b_min: np.ndarray, b_max: np.ndarray, depth: int):
        count = len(idxs)
        if count == 0:
            return

        # Target sample per node (LOD)
        target_lod_sample = min(count, 20000 if depth == 0 else 10000)
        if count <= target_lod_sample or depth >= 7:
            sample_idxs = idxs
            remaining_idxs = np.array([], dtype=np.int64)
        else:
            step = count / target_lod_sample
            sel = (np.arange(target_lod_sample) * step).astype(np.int64)
            mask = np.zeros(count, dtype=bool)
            mask[sel] = True
            sample_idxs = idxs[mask]
            remaining_idxs = idxs[~mask]

        n_sample = len(sample_idxs)
        buf = bytearray(n_sample * 16)
        
        px = xs[sample_idxs]
        py = ys[sample_idxs]
        pz = zs[sample_idxs]
        pc = colors[sample_idxs]

        ux_arr = np.round((px - lx) / SCALE).astype(np.uint32)
        uy_arr = np.round((py - ly) / SCALE).astype(np.uint32)
        uz_arr = np.round((pz - lz) / SCALE).astype(np.uint32)

        for j in range(n_sample):
            struct.pack_into(
                "<III4B",
                buf,
                j * 16,
                int(ux_arr[j]),
                int(uy_arr[j]),
                int(uz_arr[j]),
                int(pc[j, 0]),
                int(pc[j, 1]),
                int(pc[j, 2]),
                int(pc[j, 3]),
            )

        node_bins[name] = bytes(buf)
        hierarchy.append([name, n_sample])

        if len(remaining_idxs) > 0 and depth < 7:
            mid = (b_min + b_max) * 0.5
            rx = xs[remaining_idxs]
            ry = ys[remaining_idxs]
            rz = zs[remaining_idxs]

            for octant in range(8):
                cx = (octant & 4) != 0
                cy = (octant & 2) != 0
                cz = (octant & 1) != 0

                mask_x = (rx >= mid[0]) if cx else (rx < mid[0])
                mask_y = (ry >= mid[1]) if cy else (ry < mid[1])
                mask_z = (rz >= mid[2]) if cz else (rz < mid[2])

                oct_mask = mask_x & mask_y & mask_z
                oct_idxs = remaining_idxs[oct_mask]

                if len(oct_idxs) > 0:
                    child_min = np.array([
                        mid[0] if cx else b_min[0],
                        mid[1] if cy else b_min[1],
                        mid[2] if cz else b_min[2],
                    ])
                    child_max = np.array([
                        b_max[0] if cx else mid[0],
                        b_max[1] if cy else mid[1],
                        b_max[2] if cz else mid[2],
                    ])
                    partition_node(f"{name}{octant}", oct_idxs, child_min, child_max, depth + 1)

    initial_indices = np.arange(n_points, dtype=np.int64)
    partition_node("r", initial_indices, np.array([lx, ly, lz]), np.array([ux, uy, uz]), 0)

    print(f"   -> Built octree with {len(hierarchy)} nodes across {sum(cnt for _, cnt in hierarchy):,} packed points.")

    cloud_meta = {
        "version": "1.4",
        "octreeDir": "data",
        "projection": "+proj=utm +zone=56 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs",
        "boundingBox": {
            "lx": lx,
            "ly": ly,
            "lz": lz,
            "ux": ux,
            "uy": uy,
            "uz": uz
        },
        "tightBoundingBox": {
            "lx": min_x,
            "ly": min_y,
            "lz": min_z,
            "ux": max_x,
            "uy": max_y,
            "uz": max_z
        },
        "pointAttributes": [
            "POSITION_CARTESIAN",
            "COLOR_PACKED"
        ],
        "spacing": 5.0,
        "scale": SCALE,
        "hierarchy": hierarchy,
        "description": "Lake Macquarie Classified 3D LiDAR (LakeMacquarie201409-LID1-C3-AHD_3666336_56_0002_0002.laz)",
        "source_dataset_key": "nsw_elvis_lidar_laz_pointcloud_v2",
        "storage_source": "s3://wherobots-user-storage/aura_siting_v2/nsw_elvis_lidar_laz_pointcloud_v2"
    }

    for target_dir in TARGET_DIRS:
        data_dir = os.path.join(target_dir, "data")
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
        os.makedirs(data_dir, exist_ok=True)

        for name, bin_data in node_bins.items():
            bin_path = os.path.join(data_dir, f"{name}.bin")
            with open(bin_path, "wb") as f:
                f.write(bin_data)

        cloud_path = os.path.join(target_dir, "cloud.js")
        with open(cloud_path, "w", encoding="utf-8") as f:
            json.dump(cloud_meta, f, indent=2)

        print(f"4. Successfully generated Potree point cloud package in: {target_dir}")


if __name__ == "__main__":
    build_octree()
