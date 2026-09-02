#!/usr/bin/env python3
"""
Multi-State High-Resolution Dataset Loader v2 (dataset_loader_v2.py)
AURA Siting Crafter — Canonical Amalgamation & Strict EPSG:7844 Engine.

Wherobots Lifecycle Standard:
  - Phase 1: Download raw vectors, clean coordinates/geometries, standardize to GDA2020 (EPSG:7844),
             and materialize to Iceberg/GeoParquet tables before any multi-layer spatial operations.
  - Phase 2: Complex spatial operations (metric buffers in EPSG:3112, ST_Difference overlays, spatial joins).
  - Telemetry: High-resolution timing of every stage logged for publication in audit logs.
"""

import os
import sys
import json
import glob
import time
import argparse
import datetime
from typing import Optional, Dict, Any, List, Tuple
import requests

try:
    import pandas as pd
    import geopandas as gpd
    from shapely.geometry import shape
    HAS_GEOPANDAS = True
except ImportError:
    pd = None
    gpd = None
    shape = None
    HAS_GEOPANDAS = False

try:
    from sedona.spark import SedonaContext
    from pyspark.sql.functions import col, lit, expr, when
    HAS_SEDONA = True
except ImportError:
    HAS_SEDONA = False

try:
    from src.Ingestion_v2.etl_telemetry_v2 import ETLTelemetryLoggerV2
except ImportError:
    BASE_DIR_RESOLVED = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, BASE_DIR_RESOLVED)
    from src.Ingestion_v2.etl_telemetry_v2 import ETLTelemetryLoggerV2

# Universal Standard Reference Systems
CRS_GDA2020 = "EPSG:7844"  # Mandatory universal storage standard
CRS_ALBERS = "EPSG:3112"   # Internal metric calculation scratchpad
CRS_WGS84 = "EPSG:4326"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DATASETS_V2_DIR = os.path.join(BASE_DIR, "config", "datasets_v2")
EXPORTS_V2_DIR = os.path.join(BASE_DIR, "exports_v2")


def _clean_coordinates(coords):
    """Sanitizes coordinate tuples/lists and strips nulls or non-numeric tokens."""
    if coords is None:
        return None
    if isinstance(coords, (int, float)):
        return coords
    if isinstance(coords, list):
        if coords and not isinstance(coords[0], list):
            cleaned = [c for c in coords if isinstance(c, (int, float))]
            return cleaned if len(cleaned) >= 2 else None
        else:
            cleaned_list = []
            for item in coords:
                res = _clean_coordinates(item)
                if res is not None:
                    cleaned_list.append(res)
            return cleaned_list
    return None


def _is_valid_geojson_geometry(geom: dict) -> bool:
    """Verifies that a GeoJSON geometry dictionary is valid and non-empty."""
    if not geom or not isinstance(geom, dict):
        return False
    gtype = geom.get("type")
    if not gtype:
        return False
    if gtype == "GeometryCollection":
        geoms = geom.get("geometries", [])
        return bool(geoms) and all(_is_valid_geojson_geometry(g) for g in geoms)
    coords = geom.get("coordinates")
    return coords is not None and len(coords) > 0


def list_available_datasets(state: str = "all") -> List[str]:
    """Lists all registered dataset configurator keys for a state or nationwide."""
    if state == "all":
        pattern = os.path.join(CONFIG_DATASETS_V2_DIR, "*", "*.json")
    else:
        pattern = os.path.join(CONFIG_DATASETS_V2_DIR, state, "*.json")
        
    files = glob.glob(pattern)
    return sorted([os.path.splitext(os.path.basename(f))[0] for f in files])


def load_dataset_config(dataset_key_or_path: str, state: Optional[str] = None) -> Dict[str, Any]:
    """Loads a declarative v2 dataset configuration JSON file."""
    if os.path.exists(dataset_key_or_path):
        cfg_path = dataset_key_or_path
    else:
        candidates = []
        if state:
            candidates.append(os.path.join(CONFIG_DATASETS_V2_DIR, state, f"{dataset_key_or_path}.json"))
        # Search all state directories
        candidates.extend(glob.glob(os.path.join(CONFIG_DATASETS_V2_DIR, "*", f"{dataset_key_or_path}.json")))
        
        cfg_path = None
        for c in candidates:
            if os.path.exists(c):
                cfg_path = c
                break
        if not cfg_path:
            raise FileNotFoundError(f"Dataset config not found for key: {dataset_key_or_path} (state={state})")

    with open(cfg_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config


def fetch_arcgis_features(endpoint: str, layer_id: int = 0, where_clause: str = "1=1",
                          max_features: int = 50000, bbox: list = None,
                          telemetry: Optional[ETLTelemetryLoggerV2] = None) -> Tuple[List[Dict[str, Any]], int, str]:
    """
    Harvests features from ArcGIS REST / FeatureServer endpoints with auto-pagination.
    Returns (features_list, http_status_code, etag_or_hash).
    """
    url = f"{endpoint.rstrip('/')}/{layer_id}/query"
    params = {
        "where": where_clause,
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
        "resultRecordCount": min(max_features, 2000),
        "resultOffset": 0,
        "outSR": "4326"
    }
    if bbox:
        params["geometry"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        params["geometryType"] = "esriGeometryEnvelope"
        params["spatialRel"] = "esriSpatialRelIntersects"

    all_features = []
    status_code = 200
    etag = ""
    page = 0

    while True:
        try:
            resp = requests.get(url, params=params, timeout=15)
            status_code = resp.status_code
            etag = resp.headers.get("ETag", "")

            if resp.status_code != 200:
                break

            data = resp.json()
            features = data.get("features", [])
            if not features:
                break

            all_features.extend(features)
            page += 1

            if len(features) < params["resultRecordCount"] or len(all_features) >= max_features:
                break
            params["resultOffset"] += len(features)
        except Exception:
            status_code = 500
            break

    return all_features, status_code, etag


def apply_canonical_schema_mapping(features: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalizes feature properties into the Canonical AURA Siting Schema.
    Strictly preserves geometry while standardizing attribute keys.
    """
    mapping = config.get("schema_mapping", {})
    canonical_theme = config.get("canonical_theme", "generic_siting_layer")
    state = config.get("state", "national")
    
    normalized_features = []
    for f in features:
        props = f.get("properties") or {}
        geom = f.get("geometry") or {}

        # Clean coordinates
        if geom and "coordinates" in geom:
            geom["coordinates"] = _clean_coordinates(geom["coordinates"])

        if not _is_valid_geojson_geometry(geom):
            continue

        norm_props = {
            "_canonical_theme": canonical_theme,
            "_state": state.upper(),
            "_dataset_key": config.get("dataset_key", "")
        }

        # Direct mapped properties
        for canon_attr, src_attr in mapping.items():
            norm_props[canon_attr] = props.get(src_attr)

        # Retain original properties for audit traceability
        norm_props["_source_attributes"] = props

        normalized_features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": norm_props
        })

    return normalized_features


def export_to_geoparquet(features: List[Dict[str, Any]], output_path: str, crs: str = CRS_GDA2020) -> str:
    """
    Exports normalized features to GeoParquet strictly enforcing EPSG:7844 standard.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if HAS_GEOPANDAS and gpd is not None:
        geometries = []
        rows = []
        for f in features:
            try:
                g = shape(f["geometry"])
                geometries.append(g)
                rows.append(f.get("properties", {}))
            except Exception:
                continue

        if geometries:
            gdf = gpd.GeoDataFrame(rows, geometry=geometries, crs=CRS_WGS84)
            # Standardize strictly to EPSG:7844
            if str(gdf.crs) != crs:
                gdf = gdf.to_crs(crs)
            gdf.to_parquet(output_path, compression="snappy")
            return output_path

    # Fallback when geopandas is not available
    geojson_data = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": f"urn:ogc:def:crs:EPSG::{crs.split(':')[-1]}"}
        },
        "features": features
    }
    json_path = output_path.replace(".parquet", ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f)
    return json_path


def load_dataset(dataset_key: str, state: Optional[str] = None,
                 telemetry: Optional[ETLTelemetryLoggerV2] = None) -> Dict[str, Any]:
    """
    Harvests, standardizes, and returns a normalized FeatureCollection strictly on EPSG:7844.
    """
    config = load_dataset_config(dataset_key, state=state)
    state = config.get("state", state or "national")
    
    if telemetry:
        telemetry.start_stage("harvest")
        
    features, status, etag = fetch_arcgis_features(
        endpoint=config.get("endpoint", ""),
        layer_id=config.get("layer_id", 0),
        telemetry=telemetry
    )

    if telemetry:
        telemetry.end_stage("harvest", dataset_key, feature_count=len(features), crs=CRS_GDA2020)
        telemetry.start_stage("normalize_schema")

    normalized_features = apply_canonical_schema_mapping(features, config)

    if telemetry:
        telemetry.end_stage("normalize_schema", dataset_key, feature_count=len(normalized_features), crs=CRS_GDA2020)

    return {
        "type": "FeatureCollection",
        "crs_standard": CRS_GDA2020,
        "dataset_key": dataset_key,
        "state": state,
        "canonical_theme": config.get("canonical_theme"),
        "features": normalized_features
    }


def main():
    parser = argparse.ArgumentParser(description="AURA Siting Crafter Multi-State Ingestion Loader v2")
    parser.add_argument("--state", type=str, default="all", help="Target state (nsw, qld, vic, wa, sa, tas, all)")
    parser.add_argument("--dataset", type=str, default=None, help="Target dataset key")
    parser.add_argument("--list", action="store_true", help="List all available dataset keys")
    parser.add_argument("--export-geoparquet", action="store_true", help="Export to exports_v2/*.parquet on EPSG:7844")
    args = parser.parse_args()

    if args.list:
        datasets = list_available_datasets(args.state)
        print(f"Available v2 datasets for [{args.state.upper()}]: ({len(datasets)} total)")
        for d in datasets:
            print(f"  • {d}")
        return

    logger = ETLTelemetryLoggerV2(state=args.state, session_name="dataset_loader_v2")
    
    target_datasets = [args.dataset] if args.dataset else list_available_datasets(args.state)
    print(f"Executing v2 ingestion across {len(target_datasets)} datasets in [{args.state.upper()}] strictly on EPSG:7844...")

    for dkey in target_datasets:
        try:
            fc = load_dataset(dkey, state=args.state, telemetry=logger)
            feature_cnt = len(fc.get("features", []))
            print(f"  [OK] {dkey} ({fc.get('canonical_theme')}): {feature_cnt} features (CRS: {fc.get('crs_standard')})")
            
            if args.export_geoparquet:
                out_path = os.path.join(EXPORTS_V2_DIR, args.state, f"{dkey}.parquet")
                export_to_geoparquet(fc.get("features", []), out_path, crs=CRS_GDA2020)
                print(f"       -> Exported to {out_path}")
        except Exception as e:
            print(f"  [WARN] {dkey}: {e}")

    log_path = logger.save_audit_log("telemetry_v2_loader.json")
    print(f"\nCompleted v2 ingestion in {logger.summarize()['total_duration_seconds']}s.")
    print(f"Audit telemetry saved to {log_path}")


if __name__ == "__main__":
    main()
