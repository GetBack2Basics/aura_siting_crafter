#!/usr/bin/env python3
"""
AURA Siting Crafter — Spatial ETL Module.
National and Regional Spatial Ingestion Pipeline.
"""

import os
import sys
import json
import requests
import pandas as pd
import geopandas as gpd
import pyproj

from sedona.spark import SedonaContext
from pyspark.sql.functions import col, to_json, expr, lit, when, concat_ws

# =============================================================================
# Utilities
# =============================================================================

def _cfg() -> dict:
    """Load configuration from config/national.json with optional region overrides from config/regions/{region}.json."""
    region = os.environ.get("AURA_REGION", os.environ.get("WHEROBOTS_ENV", "national")).lower()
    
    # Candidates for national config
    candidates = [
        os.path.join(os.getcwd(), "config", "national.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../config/national.json"),
        "/opt/wherobots/national.json",
        "national.json",
    ]
    
    config = {}
    for p in candidates:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                config = json.load(f)
            break
            
    # Load region overrides if applicable and not 'national'
    if region and region != "national":
        region_candidates = [
            os.path.join(os.getcwd(), "config", "regions", f"{region}.json"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../../config/regions/{region}.json"),
            f"/opt/wherobots/regions/{region}.json",
            f"config/regions/{region}.json"
        ]
        for rp in region_candidates:
            if os.path.exists(rp):
                with open(rp, "r", encoding="utf-8") as rf:
                    reg_data = json.load(rf)
                    config.update(reg_data)
                break
                
    return config


def _sedona() -> SedonaContext:
    return SedonaContext.create(SedonaContext.builder().getOrCreate())


def _has_none_coordinates(coords) -> bool:
    if coords is None:
        return True
    if isinstance(coords, (int, float)):
        return False
    if isinstance(coords, list):
        for item in coords:
            if item is None:
                return True
            if isinstance(item, list):
                if _has_none_coordinates(item):
                    return True
            elif not isinstance(item, (int, float)):
                return True
        return False
    return True


def _is_valid_geojson_geometry(geom) -> bool:
    if not geom:
        return False
    gtype = geom.get("type")
    if not gtype:
        return False
    if gtype == "GeometryCollection":
        geoms = geom.get("geometries", [])
        if not geoms:
            return False
        return all(_is_valid_geojson_geometry(g) for g in geoms)
    return not _has_none_coordinates(geom.get("coordinates"))


def _clean_coordinates(coords):
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


def _fetch_featureserver_geojson(base_url: str, layer_id: int, max_features: int = 5000, bbox: list = None) -> list:
    query_url = f"{base_url}/{layer_id}/query"
    out = []
    offset = 0
    page = 1000
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    while len(out) < max_features:
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "outSR": "4326",
            "resultOffset": offset,
            "resultRecordCount": page,
        }
        if bbox:
            params["geometry"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["inSR"] = "4326"
            params["spatialRel"] = "esriSpatialRelIntersects"
            
        resp = requests.get(query_url, params=params, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"[aura] FeatureServer partial or complete stop at HTTP {resp.status_code}: {query_url}")
            break
        try:
            features = resp.json().get("features", [])
        except Exception as json_err:
            print(f"[aura] JSON parse error: {json_err}")
            print(f"[aura] Status: {resp.status_code}")
            print(f"[aura] Content: {resp.text[:500]}")
            break
        if not features:
            break
        for f in features:
            if f.get("geometry") and f["geometry"].get("coordinates"):
                f["geometry"]["coordinates"] = _clean_coordinates(f["geometry"]["coordinates"])
                
        valid_features = [
            f for f in features 
            if f.get("geometry") is not None and _is_valid_geojson_geometry(f["geometry"])
        ]
        out.extend(valid_features)
        if len(features) < page or len(out) >= max_features:
            break
        offset += page
    print(f"[aura] Retrieved {len(out)} features from {query_url}")
    return out


def _to_sedona(sedona: SedonaContext, gdf: gpd.GeoDataFrame, srid: int = 4326) -> "pyspark.sql.DataFrame":
    gdf = gdf.copy()
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    if getattr(gdf.crs, "to_epsg", None)() != srid:
        gdf.to_crs(epsg=srid, inplace=True)
    gdf["wkt_geometry"] = gdf.geometry.apply(lambda g: g.wkt if g is not None else None)
    pdf = pd.DataFrame(gdf.drop(columns=["geometry"]))
    
    # Restrict to standard columns to prevent Spark type inference errors on empty/mixed columns
    pdf.columns = [c.lower() for c in pdf.columns]
    keep_cols = ["wkt_geometry", "layer", "precinct_key", "objectid", "sub_precinct", "use_case"]
    cols_to_keep = [c for c in keep_cols if c in pdf.columns]
    if not cols_to_keep:
        cols_to_keep = ["wkt_geometry"]
    pdf = pdf[cols_to_keep]
    
    for col_name in pdf.columns:
        if pd.api.types.is_numeric_dtype(pdf[col_name]):
            pdf[col_name] = pd.to_numeric(pdf[col_name], errors='coerce')
        else:
            pdf[col_name] = pdf[col_name].astype(str).replace({"nan": None, "<NA>": None, "None": None})
    sdf = sedona.createDataFrame(pdf)
    return sdf.withColumn("geometry", expr(f"ST_GeomFromWKT(wkt_geometry)")).drop("wkt_geometry")


def save_table(sedona: SedonaContext, sdf, table_name: str, storage_root: str, partition_col: str = "precinct_key"):
    is_wherobots = os.getenv("WHEROBOTS_ENV") in ("stg", "prod") or storage_root.startswith("wherobots://")
    full_name = f"org_catalog.fgsdb.{table_name}"
    if is_wherobots:
        try:
            sedona.sql("CREATE DATABASE IF NOT EXISTS org_catalog.fgsdb")
            writer = sdf.write.format("havasu.iceberg").mode("overwrite")
            if partition_col:
                writer = writer.partitionBy(partition_col)
            writer.saveAsTable(full_name)
            print(f"[aura] Saved Havasu table: {full_name}")
            return
        except Exception as exc:
            print(f"[aura] Havasu save failed ({exc}); falling back to GeoParquet")
    clean_root = storage_root
    if clean_root.startswith("wherobots://"):
        clean_root = "file:///tmp/aura_siting"
    path = f"{clean_root}/{table_name}.parquet"
    writer = sdf.write.format("geoparquet").mode("overwrite")
    if partition_col:
        writer = writer.partitionBy(partition_col)
    writer.save(path)
    print(f"[aura] Saved GeoParquet: {path}")


# =============================================================================
# 1. Precinct boundary and sub-precincts
# =============================================================================

def load_precinct_boundary(sedona: SedonaContext, storage_root: str) -> list:
    """
    Loads/creates precinct boundary, study area boundary, 100km buffer boundary, and sub-precinct metadata.
    Replace the placeholder geometry with an actual precinct boundary when available.
    """
    placeholder = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"precinct": "PrecinctCoalComplex", "precinct_key": "mcc"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [151.65, -32.93], [151.72, -32.93],
                        [151.72, -32.88], [151.65, -32.88], [151.65, -32.93]
                    ]],
                },
            }
        ],
    }
    tgt = _cfg().get("target_crs", "EPSG:7856")
    tgt_epsg = int(tgt.split(":")[1]) if ":" in tgt else 7856
    
    # 1. Actual precinct boundary
    gdf = gpd.GeoDataFrame.from_features(placeholder, crs="EPSG:4326")
    gdf_tgt = gdf.to_crs(tgt)
    boundary_sdf = _to_sedona(sedona, gdf_tgt, srid=tgt_epsg).withColumn("precinct_key", lit("mcc"))
    save_table(sedona, boundary_sdf, "precinct_boundary", storage_root, partition_col=None)

    # 2. Expanded study area boundary (5km buffer)
    study_buffer = _cfg().get("study_buffers_m", {}).get("study_area", 5000.0)
    gdf_study = gdf_tgt.copy()
    gdf_study["geometry"] = gdf_study.geometry.buffer(study_buffer)
    study_sdf = _to_sedona(sedona, gdf_study, srid=tgt_epsg).withColumn("precinct_key", lit("mcc"))
    save_table(sedona, study_sdf, "precinct_study_area_boundary", storage_root, partition_col=None)

    # 3. 100km buffer boundary
    buffer_100km = _cfg().get("study_buffers_m", {}).get("buffer_100km", 100000.0)
    gdf_100km = gdf_tgt.copy()
    gdf_100km["geometry"] = gdf_100km.geometry.buffer(buffer_100km)
    buffer_100km_sdf = _to_sedona(sedona, gdf_100km, srid=tgt_epsg).withColumn("precinct_key", lit("mcc"))
    save_table(sedona, buffer_100km_sdf, "precinct_buffer_100km_boundary", storage_root, partition_col=None)

    sub_precincts = pd.DataFrame([
        {"sub_precinct": "Killingworth",  "precinct_key": "mcc", "use_case": "AdvancedMfg_DataHub"},
        {"sub_precinct": "WestLake",      "precinct_key": "mcc", "use_case": "NatureTourism_Recreation"},
        {"sub_precinct": "CockleCreek",   "precinct_key": "mcc", "use_case": "IndustrialGateway_TSF"},
        {"sub_precinct": "Teralba",       "precinct_key": "mcc", "use_case": "TransitOriented_Residential"},
    ])
    sub_sdf = sedona.createDataFrame(sub_precincts)
    save_table(sedona, sub_sdf, "precinct_sub_precincts", storage_root, partition_col=None)
    
    # Calculate 100km buffer bbox in EPSG:4326 for querying external REST services
    gdf_100km_wgs84 = gdf_100km.to_crs("EPSG:4326")
    bounds = gdf_100km_wgs84.total_bounds
    bbox_100km = bounds.tolist()
    
    gdf_study_wgs84 = gdf_study.to_crs("EPSG:4326")
    bbox_study = gdf_study_wgs84.total_bounds.tolist()
    
    print("[aura] Loaded precinct boundary + sub-precinct registry")
    return {"bbox_100km": bbox_100km, "bbox_study": bbox_study}


# =============================================================================
# 2. Water / Hydrology
# =============================================================================

def load_water_infrastructure(sedona: SedonaContext, storage_root: str, cfg: dict, bbox: list = None) -> None:
    tgt = cfg.get("target_crs", "EPSG:7856")
    tgt_epsg = int(tgt.split(":")[1]) if ":" in tgt else 7856
    nsw_base = cfg["data_sources"]["nsw_spatial_services"]

    print("[aura] Fetching NSW Water Theme HydroLine and HydroArea …")
    try:
        # Load HydroLine (Layer 5)
        feats_line = _fetch_featureserver_geojson(nsw_base + "/NSW_Water_Theme/FeatureServer", 5, max_features=5000, bbox=bbox)
        # Load HydroArea (Layer 6)
        feats_area = _fetch_featureserver_geojson(nsw_base + "/NSW_Water_Theme/FeatureServer", 6, max_features=5000, bbox=bbox)
        
        combined_feats = feats_line + feats_area
        combined_feats = [f for f in combined_feats if f.get("geometry") is not None]
        if not combined_feats:
            print("[aura] No water infrastructure features retrieved.")
            return
        gdf = gpd.GeoDataFrame.from_features(combined_feats, crs="EPSG:4326")
        gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]
        gdf = gdf.to_crs(tgt)
        water_sdf = _to_sedona(sedona, gdf, srid=tgt_epsg).withColumn("layer", lit("water_infrastructure"))
        save_table(sedona, water_sdf, "precinct_water_hydrography", storage_root, partition_col="layer")
        print("[aura] Water infrastructure loaded.")
    except Exception as exc:
        print(f"[aura] WARNING: Failed to load water infrastructure: {exc}")


# =============================================================================
# 3. Biodiversity
# =============================================================================

def load_biodiversity_constraints(sedona: SedonaContext, storage_root: str, cfg: dict, bbox: list = None) -> None:
    tgt = cfg.get("target_crs", "EPSG:7856")
    tgt_epsg = int(tgt.split(":")[1]) if ":" in tgt else 7856
    
    # In a full-scale pipeline, this queries the NSW BioNet or SEED portal REST services.
    # We will generate simulated biodiversity corridors overlapping our precinct to represent constraints.
    print("[aura] Ingesting simulated biodiversity corridors overlapping precinct …")
    try:
        placeholder_biodiversity = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"layer": "biodiversity_corridor"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [151.68, -32.92], [151.70, -32.92],
                            [151.70, -32.90], [151.68, -32.90], [151.68, -32.92]
                        ]]
                    }
                }
            ]
        }
        gdf = gpd.GeoDataFrame.from_features(placeholder_biodiversity, crs="EPSG:4326").to_crs(tgt)
        bio_sdf = _to_sedona(sedona, gdf, srid=tgt_epsg).withColumn("layer", lit("biodiversity"))
        save_table(sedona, bio_sdf, "precinct_biodiversity_constraints", storage_root, partition_col="layer")
        print("[aura] Biodiversity constraints loaded.")
    except Exception as exc:
        print(f"[aura] WARNING: Failed to load biodiversity constraints: {exc}")


# =============================================================================
# 4. Energy Grid (Substations & lines)
# =============================================================================

def load_energy_infrastructure(sedona: SedonaContext, storage_root: str, cfg: dict, bbox: list = None) -> None:
    tgt = cfg.get("target_crs", "EPSG:7856")
    tgt_epsg = int(tgt.split(":")[1]) if ":" in tgt else 7856
    nsw_base = cfg["data_sources"]["nsw_spatial_services"]

    print("[aura] Fetching NSW Transmission Substations …")
    try:
        feats = _fetch_featureserver_geojson(nsw_base + "/NSW_Features_of_Interest_Category/FeatureServer", 6, max_features=5000, bbox=bbox)
        feats = [f for f in feats if f.get("geometry") is not None]
        if not feats:
            print("[aura] No electricity features retrieved; skipping energy infrastructure.")
            return
        gdf = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
        gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]
        gdf = gdf.to_crs(tgt)
        energy_sdf = _to_sedona(sedona, gdf, srid=tgt_epsg).withColumn("layer", lit("energy_infrastructure"))
        save_table(sedona, energy_sdf, "precinct_energy_infrastructure", storage_root, partition_col="layer")
        print("[aura] Energy infrastructure loaded.")
    except Exception as exc:
        print(f"[aura] WARNING: Failed to load energy infrastructure: {exc}")


# =============================================================================
# 5. Pipeline corridors
# =============================================================================

def load_pipeline_corridors(sedona: SedonaContext, storage_root: str, cfg: dict, bbox: list = None) -> None:
    tgt = cfg.get("target_crs", "EPSG:7856")
    tgt_epsg = int(tgt.split(":")[1]) if ":" in tgt else 7856
    
    # Using placeholder or mock coordinates if pipeline service is down
    print("[aura] Generating placeholder pipeline corridors for safety buffer modeling …")
    try:
        placeholder_pipeline = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"pipeline_id": "pl_01", "name": "Hunter Gas Pipeline Mock"},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[151.66, -32.91], [151.71, -32.90]]
                    }
                }
            ]
        }
        gdf = gpd.GeoDataFrame.from_features(placeholder_pipeline, crs="EPSG:4326").to_crs(tgt)
        pipe_sdf = _to_sedona(sedona, gdf, srid=tgt_epsg).withColumn("layer", lit("pipeline_corridor"))
        save_table(sedona, pipe_sdf, "precinct_pipeline_corridors", storage_root, partition_col="layer")
        print("[aura] Pipeline corridors loaded.")
    except Exception as exc:
        print(f"[aura] WARNING: Failed to load pipeline corridors: {exc}")


# =============================================================================
# 6. Rail + Active transport networks
# =============================================================================

def load_transport_networks(sedona: SedonaContext, storage_root: str, cfg: dict, bbox: list = None) -> None:
    tgt = cfg.get("target_crs", "EPSG:7856")
    tgt_epsg = int(tgt.split(":")[1]) if ":" in tgt else 7856
    src = cfg.get("source_crs", "EPSG:4326")

    print("[aura] Fetching NSW Transport Theme (Railway) …")
    try:
        feats = _fetch_featureserver_geojson(cfg["data_sources"]["nsw_spatial_services"] + "/NSW_Transport_Theme/FeatureServer", 7, max_features=4000, bbox=bbox)
        feats = [f for f in feats if f.get("geometry") is not None]
        if not feats:
            print("[aura] Could not fetch rail lines; leaving rail network empty.")
        else:
            gdf = gpd.GeoDataFrame.from_features(feats, crs=src)
            gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]
            gdf = gdf.to_crs(tgt)
            rail_sdf = _to_sedona(sedona, gdf, srid=tgt_epsg).withColumn("layer", lit("main_northern_rail"))
            save_table(sedona, rail_sdf, "precinct_rail_network", storage_root, partition_col="layer")
            print("[aura] Rail network loaded and reprojected to target CRS.")
    except Exception as exc:
        print(f"[aura] WARNING: Failed to load rail network: {exc}")

    # Active transport layers from Lake Precinct Open Data
    active_datasets = [
        "cycling-planning-network-wayfinding-map",
        "principal-pedestrian-network-map"
    ]
    active_frames = []
    for dataset_id in active_datasets:
        url = f"{cfg['data_sources']['lakemac_open_data']}/{dataset_id}/exports/geojson"
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                gdf = gpd.GeoDataFrame.from_features(r.json(), crs=src)
                gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]
                if not gdf.empty:
                    # Clip to 100km bbox boundary to avoid keeping the entire Lake Mac LGA if huge (though LGA is small)
                    active_frames.append(gdf)
        except Exception as exc:
            print(f"[aura] Active transport dataset {dataset_id} skip: {exc}")
            
    if active_frames:
        gdf_all = pd.concat(active_frames, ignore_index=True)
        gdf_all = gpd.GeoDataFrame(gdf_all, crs=src)
        gdf_all = gdf_all.to_crs(tgt)
        active_sdf = _to_sedona(sedona, gdf_all, srid=tgt_epsg).withColumn("layer", lit("active_transport"))
        save_table(sedona, active_sdf, "precinct_active_transport", storage_root, partition_col="layer")
        print("[aura] Active transport loaded and reprojected to target CRS.")
    else:
        print("[aura] No active transport datasets retrieved.")


# =============================================================================
# 7. ABS Meshblocks clipped to precinct
# =============================================================================

def load_abs_meshblocks(sedona: SedonaContext, storage_root: str, cfg: dict, bbox: list = None) -> None:
    tgt = cfg.get("target_crs", "EPSG:7856")
    tgt_epsg = int(tgt.split(":")[1]) if ":" in tgt else 7856
    abs_base = cfg["data_sources"]["abs_geo"]
    
    try:
        print("[aura] Fetching ABS Meshblocks for region …")
        feats = _fetch_featureserver_geojson(abs_base + "/MB/MapServer", 0, max_features=15000, bbox=bbox)
        feats = [f for f in feats if f.get("geometry") is not None]
        if not feats:
            print("[aura] WARNING: ABS Meshblock response empty.")
            return
        tbl = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
        tbl = tbl[tbl.geometry.notnull() & ~tbl.geometry.is_empty]
        gdf = tbl.to_crs(tgt)
        mb_sdf = _to_sedona(sedona, gdf, srid=tgt_epsg).withColumn("layer", lit("abs_meshblocks"))
        save_table(sedona, mb_sdf, "precinct_abs_meshblocks", storage_root, partition_col="layer")
        print("[aura] ABS Meshblocks loaded.")
    except Exception as exc:
        print(f"[aura] WARNING: Failed to load ABS Meshblocks: {exc}")


# =============================================================================
# 8. Hazard & Terrain Constraints (TSF & Slope)
# =============================================================================

def load_hazard_constraints(sedona: SedonaContext, storage_root: str, cfg: dict, bbox: list = None) -> None:
    tgt = cfg.get("target_crs", "EPSG:7856")
    tgt_epsg = int(tgt.split(":")[1]) if ":" in tgt else 7856

    print("[aura] Loading hazard and terrain constraints...")
    try:
        # 1. TSF Risk Zone (Simulated)
        tsf_polygon = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"layer": "tsf_risk_zone", "dam_status": "declared"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [151.70, -32.90], [151.72, -32.90],
                            [151.72, -32.89], [151.70, -32.89], [151.70, -32.90]
                        ]]
                    }
                }
            ]
        }
        gdf_tsf = gpd.GeoDataFrame.from_features(tsf_polygon, crs="EPSG:4326").to_crs(tgt)
        tsf_sdf = _to_sedona(sedona, gdf_tsf, srid=tgt_epsg).withColumn("layer", lit("tsf_risk"))
        save_table(sedona, tsf_sdf, "precinct_tsf_risk_zones", storage_root, partition_col="layer")

        # 2. Slope > 12% constraints (Simulated)
        slope_polygon = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"layer": "slope_gt_12"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [151.66, -32.92], [151.68, -32.92],
                            [151.68, -32.91], [151.66, -32.91], [151.66, -32.92]
                        ]]
                    }
                }
            ]
        }
        gdf_slope = gpd.GeoDataFrame.from_features(slope_polygon, crs="EPSG:4326").to_crs(tgt)
        slope_sdf = _to_sedona(sedona, gdf_slope, srid=tgt_epsg).withColumn("layer", lit("slope_constraints"))
        save_table(sedona, slope_sdf, "precinct_slope_constraints", storage_root, partition_col="layer")
        print("[aura] Hazard and slope constraints loaded.")
    except Exception as exc:
        print(f"[aura] WARNING: Failed to load hazard constraints: {exc}")


# =============================================================================
# 9. Spatial processing: constraints overlay → net developable zones
# =============================================================================

def build_net_developable_zones(sedona: SedonaContext, storage_root: str, cfg: dict) -> None:
    target_crs = cfg.get("target_crs", "EPSG:7856")
    src = cfg.get("source_crs", "EPSG:4326")
    buffers = cfg.get("buffers_m", {})
    dam_status = cfg.get("dam_status", "declared")

    print(f"[aura] Building developable zones with dam_status={dam_status}")

    sedona.sql(f"""
        CREATE OR REPLACE TEMP VIEW precinct_transform AS
        SELECT precinct_key,
               geometry AS geom
        FROM org_catalog.fgsdb.precinct_boundary
    """)

    constraints = []

    if sedona.catalog.tableExists("org_catalog.fgsdb.precinct_water_hydrography"):
        hydro = f"""
            SELECT 'hydro_30m' AS constraint_type, ST_Buffer(g.geometry, 30.0) AS geom 
            FROM org_catalog.fgsdb.precinct_water_hydrography g
            JOIN precinct_transform p ON ST_Intersects(g.geometry, p.geom)
        """
        constraints.append(hydro)

    if sedona.catalog.tableExists("org_catalog.fgsdb.precinct_biodiversity_constraints"):
        bio = f"""
            SELECT 'biodiversity' AS constraint_type, g.geometry AS geom 
            FROM org_catalog.fgsdb.precinct_biodiversity_constraints g
            JOIN precinct_transform p ON ST_Intersects(g.geometry, p.geom)
        """
        constraints.append(bio)

    if sedona.catalog.tableExists("org_catalog.fgsdb.precinct_pipeline_corridors"):
        pipe_q = f"""
            SELECT 'pipeline_20m' AS constraint_type, ST_Buffer(g.geometry, 20.0) AS geom 
            FROM org_catalog.fgsdb.precinct_pipeline_corridors g
            JOIN precinct_transform p ON ST_Intersects(g.geometry, p.geom)
        """
        constraints.append(pipe_q)

    if sedona.catalog.tableExists("org_catalog.fgsdb.precinct_rail_network"):
        rail_q = f"""
            SELECT 'rail_10m' AS constraint_type, ST_Buffer(g.geometry, 10.0) AS geom 
            FROM org_catalog.fgsdb.precinct_rail_network g
            JOIN precinct_transform p ON ST_Intersects(g.geometry, p.geom)
        """
        constraints.append(rail_q)

    # 12% Slope Constraint
    if sedona.catalog.tableExists("org_catalog.fgsdb.precinct_slope_constraints"):
        slope_q = f"""
            SELECT 'slope_gt_12' AS constraint_type, g.geometry AS geom 
            FROM org_catalog.fgsdb.precinct_slope_constraints g
            JOIN precinct_transform p ON ST_Intersects(g.geometry, p.geom)
        """
        constraints.append(slope_q)

    # Dam safety risk area subtraction (applied ONLY if dam_status is 'declared')
    if dam_status != "de-declared":
        if sedona.catalog.tableExists("org_catalog.fgsdb.precinct_tsf_risk_zones"):
            tsf_q = f"""
                SELECT 'tsf_risk' AS constraint_type, g.geometry AS geom 
                FROM org_catalog.fgsdb.precinct_tsf_risk_zones g
                JOIN precinct_transform p ON ST_Intersects(g.geometry, p.geom)
            """
            constraints.append(tsf_q)

    if constraints:
        unioned = " UNION ALL ".join(constraints)
        sedona.sql(f"CREATE OR REPLACE TEMP VIEW constraints AS {unioned}")
        net = sedona.sql(f"""
            SELECT
                p.precinct_key,
                ST_Difference(p.geom, ST_Union_Aggr(c.geom)) AS net_developable_geom
            FROM precinct_transform p
            LEFT JOIN constraints c ON ST_Intersects(p.geom, c.geom)
            GROUP BY p.precinct_key, p.geom
        """)
    else:
        print("[aura] Warning: No constraint tables available. Developable zones will equal precinct boundaries.")
        net = sedona.sql("""
            SELECT precinct_key, geom AS net_developable_geom
            FROM precinct_transform
        """)
    
    if "precinct" in net.columns:
        net = net.drop("precinct")

    save_table(sedona, net, "precinct_net_developable_zones", storage_root, partition_col="precinct_key")
    print("[aura] Computed net developable zones.")


# =============================================================================
# 10. Verification
# =============================================================================

def run_verification(sedona: SedonaContext) -> None:
    print("\n[demo] Tables now available under org_catalog.fgsdb:")
    for row in sedona.sql("SHOW TABLES IN org_catalog.fgsdb").collect():
        print("  -", row["tableName"])

    for tbl in [
        "precinct_boundary",
        "precinct_study_area_boundary",
        "precinct_buffer_100km_boundary",
        "precinct_water_hydrography",
        "precinct_biodiversity_constraints",
        "precinct_energy_infrastructure",
        "precinct_pipeline_corridors",
        "precinct_rail_network",
        "precinct_active_transport",
        "precinct_abs_meshblocks",
        "precinct_tsf_risk_zones",
        "precinct_slope_constraints",
        "precinct_net_developable_zones",
    ]:
        try:
            cnt = sedona.table(f"org_catalog.fgsdb.{tbl}").count()
            print(f"[demo] {tbl}: {cnt} rows")
        except Exception as exc:
            print(f"[demo] {tbl} unavailable: {exc}")


# =============================================================================
# Main
# =============================================================================

def main():
    storage_root = _cfg().get("storage_root", "wherobots://fgsdb/aura_siting")
    print(f"[aura] Storage root: {storage_root}")
    sedona = _sedona()
    try:
        sedona.sql("CREATE DATABASE IF NOT EXISTS org_catalog.fgsdb")

        bboxes = load_precinct_boundary(sedona, storage_root)
        bbox_100km = bboxes["bbox_100km"]
        bbox_study = bboxes["bbox_study"]

        load_water_infrastructure(sedona, storage_root, _cfg(), bbox=bbox_100km)
        load_biodiversity_constraints(sedona, storage_root, _cfg(), bbox=bbox_100km)
        load_energy_infrastructure(sedona, storage_root, _cfg(), bbox=bbox_100km)
        load_pipeline_corridors(sedona, storage_root, _cfg(), bbox=bbox_100km)
        load_transport_networks(sedona, storage_root, _cfg(), bbox=bbox_100km)
        load_abs_meshblocks(sedona, storage_root, _cfg(), bbox=bbox_study)
        load_hazard_constraints(sedona, storage_root, _cfg(), bbox=bbox_100km)
        build_net_developable_zones(sedona, storage_root, _cfg())
        run_verification(sedona)
        print("\n[aura] Precinct ETL complete.")
    finally:
        print("[aura] Stopping SedonaContext session...")
        sedona.stop()


if __name__ == "__main__":
    main()

