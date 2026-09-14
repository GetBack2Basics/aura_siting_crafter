#!/usr/bin/env python3
"""
AURA Siting Crafter — Lake Macquarie ELVIS LiDAR COPC Generator
tools/build_lake_macquarie_copc.py

Generates Cloud-Optimized Point Cloud (.copc.laz) from authentic
Lake Macquarie ELVIS LiDAR point cloud dataset.
"""

import os
import sys
import struct
import numpy as np
import laspy
import copclib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC_DIR = os.path.join(BASE_DIR, "src", "geolibre_frontend", "potree", "pointclouds")

PRIMARY_SOURCE = r"C:\Users\corea\Downloads\DATA_2374297\NSW Government - Spatial Services\Point Clouds\AHD\LakeMacquarie201409-LID1-C3-AHD_3666336_56_0002_0002.laz"
LOCAL_SOURCE = os.path.join(PC_DIR, "LakeMacquarie201409-LID1-C3-AHD_3666336_56_0002_0002.laz")

OUT_COPC_FILES = [
    os.path.join(PC_DIR, "lake_macquarie_elvis.copc.laz"),
    os.path.join(PC_DIR, "nsw_elvis_lake_macquarie.copc.laz"),
    os.path.join(PC_DIR, "lion_takanawa.copc.laz")  # Keep Deck.gl default pointer in sync
]


def convert_to_copc():
    src_path = PRIMARY_SOURCE if os.path.exists(PRIMARY_SOURCE) else LOCAL_SOURCE
    print(f"1. Reading authentic Lake Macquarie LiDAR from {src_path}...")
    las = laspy.read(src_path)

    xs = np.array(las.x, dtype=np.float64)
    ys = np.array(las.y, dtype=np.float64)
    zs = np.array(las.z, dtype=np.float64)
    classes = np.array(las.classification, dtype=np.uint8)
    intensities = np.array(las.intensity, dtype=np.uint16) if hasattr(las, 'intensity') else np.zeros(len(xs), dtype=np.uint16)

    # Filter out extreme anomalies
    valid = (zs >= -5.0) & (zs <= 250.0)
    xs, ys, zs = xs[valid], ys[valid], zs[valid]
    classes, intensities = classes[valid], intensities[valid]
    n = len(xs)
    print(f"   -> Processing {n:,} points...")

    min_x, min_y, min_z = float(xs.min()), float(xs.min()), float(zs.min())
    scale = copclib.Vector3(0.01, 0.01, 0.01)
    offset = copclib.Vector3(min_x, min_y, min_z)

    # Pack into LAS 1.4 Point Format 7 (36 bytes per point)
    print("2. Packing points into LAS 1.4 format 7 buffer (RGB + ASPRS Class)...")
    buf = bytearray(n * 36)
    
    sx = np.round((xs - min_x) / 0.01).astype(np.int32)
    sy = np.round((ys - min_y) / 0.01).astype(np.int32)
    sz = np.round((zs - min_z) / 0.01).astype(np.int32)

    for i in range(n):
        c = int(classes[i])
        if c == 9:  # Water
            r, g, b = 3500, 30000, 56000
        elif c in (2, 8, 14, 15):  # Ground
            r, g, b = 43000, 35000, 21000
        elif c in (3, 4, 5, 17):  # Veg
            r, g, b = 8000, 48000, 16000
        elif c == 6:  # Buildings
            r, g, b = 61000, 17000, 17000
        else:
            r, g, b = 30000, 32000, 28000
        
        struct.pack_into('<iiiHBBBBhhqHHH', buf, i * 36, int(sx[i]), int(sy[i]), int(sz[i]), int(intensities[i]), 1, 0, c, 0, 0, 0, 0, r, g, b)

    vc = copclib.VectorChar(np.frombuffer(buf, dtype=np.int8))
    pts = copclib.Points.Unpack(vc, 7, 0, scale, offset)

    for out_file in OUT_COPC_FILES:
        print(f"3. Writing COPC file: {out_file}...")
        cfg = copclib.CopcConfigWriter(
            point_format_id=7,
            scale=scale,
            offset=offset,
            wkt="EPSG:7856"
        )
        writer = copclib.FileWriter(out_file, cfg)
        writer.AddNode(copclib.VoxelKey(0, 0, 0, 0), pts)
        writer.Close()
        print(f"   -> Generated {out_file} ({os.path.getsize(out_file)/(1024*1024):.2f} MB)")


if __name__ == "__main__":
    convert_to_copc()
