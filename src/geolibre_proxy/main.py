import os
import json
import httpx
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from src.geolibre_proxy.catalog_manager import CatalogManager
from src.geolibre_proxy.ai_spatial_agent import SpatialAiAgent
from src.geolibre_proxy.schemas import (
    ProjectCatalogResponse,
    SpatialQueryRequest,
    SpatialQueryResponse,
)

app = FastAPI(
    title="AURA Siting GeoLibre Spatial AI Gateway",
    version="2.5.0",
    description="Conversational Natural Language to DuckDB Spatial SQL proxy for GeoLibre WebGIS",
)

# CORS middleware for GeoLibre WebGIS client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, "src", "geolibre_frontend")
RUNNER_DIR = os.path.join(BASE_DIR, "runner")

@app.get("/")
def serve_webgis_root():
    """Serves the main GeoLibre WebGIS application index.html."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"status": "ok", "service": "geolibre-spatial-ai-proxy"}

@app.get("/aura-siting-crafter.geolibre.json")
def serve_geolibre_json():
    """Serves the project declarative GeoLibre JSON definition."""
    json_path = os.path.join(FRONTEND_DIR, "aura-siting-crafter.geolibre.json")
    if os.path.exists(json_path):
        return FileResponse(json_path, media_type="application/json")
    raise HTTPException(status_code=404, detail="GeoLibre JSON not found")

@app.get("/runner/{filename:path}")
def serve_runner_report(filename: str):
    """Serves national suitability report or attachments from the runner directory."""
    possible_paths = [
        os.path.join(RUNNER_DIR, filename),
        os.path.join(BASE_DIR, "runner", filename),
        os.path.join(BASE_DIR, filename),
        os.path.join("/app", "runner", filename),
        os.path.join("/app", filename)
    ]
    for fp in possible_paths:
        if os.path.exists(fp) and os.path.isfile(fp):
            media_type = "text/html" if fp.endswith(".html") else None
            return FileResponse(fp, media_type=media_type)
    
    raise HTTPException(
        status_code=404, 
        detail=f"File '{filename}' not found. Searched: {possible_paths}"
    )

@app.get("/api/debug-files")
def debug_files():
    """Diagnostic endpoint to inspect container filesystem structure."""
    return {
        "BASE_DIR": BASE_DIR,
        "RUNNER_DIR": RUNNER_DIR,
        "runner_exists": os.path.exists(RUNNER_DIR),
        "runner_files": os.listdir(RUNNER_DIR) if os.path.exists(RUNNER_DIR) else [],
        "base_files": os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else []
    }

catalog_mgr = CatalogManager()
ai_agent = SpatialAiAgent(catalog_mgr)

# Authoritative REST / WFS Live Spatial Endpoints
LIVE_STREAMS = {
    # Energy Grid (Lines & Substations)
    "transmission_lines_interstate": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/MapServer/6/query",
    "transmission_lines_regional": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/MapServer/6/query",
    "substations_terminal": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/MapServer/6/query",
    
    # Water & Cooling Loops
    "bom_hydro_lines": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/MapServer/4/query",
    "recycled_wwtw_plants": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/MapServer/4/query",
    
    # Statutory Social & Environmental Receptors
    "acara_schools": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/MapServer/3/query",
    "nhsd_healthcare": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/MapServer/2/query",
    "transport_rail": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme/MapServer/7/query",
    
    # Environmental & Bushfire Hazards
    "bionet_biodiversity": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/MapServer/5/query",
    "rfs_bushfire_bfpl": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/MapServer/5/query",
    
    # Base Fallback
    "abs_meshblocks": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Land_Parcel_Property_Theme/MapServer/0/query",
    "geoscape_cadastre": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Land_Parcel_Property_Theme/MapServer/0/query",
}

# 5-Tier Smart Hierarchical LOD Endpoints for Boundaries & Cadastre Properties
LOD_STREAMS = {
    "state_boundaries": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme/MapServer/0/query",
    "regions": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme/MapServer/3/query",
    "councils": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme/MapServer/1/query",
    "cadastre_properties": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Land_Parcel_Property_Theme/MapServer/0/query"
}

# S3 Lakehouse Parquet Storage Registry
S3_LAKEHOUSE_PATHS = {
    "national_candidates": "s3://wherobots-user-storage/aura_siting/candidates/datacenter_candidates_national.parquet",
    "abs_meshblocks": "s3://wherobots-user-storage/aura_siting/cadastre/abs_meshblocks_2021.parquet",
    "geoscape_cadastre": "s3://wherobots-user-storage/aura_siting/cadastre/geoscape_cadastre.parquet",
    "transmission_lines_interstate": "s3://wherobots-user-storage/aura_siting/energy/national_transmission_grid.parquet",
    "transmission_lines_regional": "s3://wherobots-user-storage/aura_siting/energy/national_transmission_grid.parquet",
    "substations_terminal": "s3://wherobots-user-storage/aura_siting/energy/national_substations.parquet",
    "bom_hydro_lines": "s3://wherobots-user-storage/aura_siting/water/bom_surface_water_wwtw.parquet",
    "recycled_wwtw_plants": "s3://wherobots-user-storage/aura_siting/water/recycled_wwtw_plants.parquet",
    "transport_rail": "s3://wherobots-user-storage/aura_siting/transport/nsw_railway_corridors.parquet",
    "transformation_boundary": "s3://wherobots-user-storage/aura_siting/precincts/transformation_boundary.parquet",
    "net_developable_pad": "s3://wherobots-user-storage/aura_siting/precincts/net_developable_pad_59ha.parquet",
    "gas_pipeline_corridor": "s3://wherobots-user-storage/aura_siting/precincts/gas_pipeline_corridor_20m.parquet",
}


def arcgis_to_geojson_feature(f: Dict[str, Any]) -> Dict[str, Any]:
    """Converts ArcGIS REST feature dictionary to standard GeoJSON feature."""
    geom = f.get("geometry", {})
    attrs = f.get("attributes", {})
    geojson_geom = None

    if "x" in geom and "y" in geom:
        geojson_geom = {"type": "Point", "coordinates": [geom["x"], geom["y"]]}
    elif "paths" in geom:
        paths = geom["paths"]
        if len(paths) == 1:
            geojson_geom = {"type": "LineString", "coordinates": paths[0]}
        else:
            geojson_geom = {"type": "MultiLineString", "coordinates": paths}
    elif "rings" in geom:
        rings = geom["rings"]
        geojson_geom = {"type": "Polygon", "coordinates": rings}

    return {
        "type": "Feature",
        "geometry": geojson_geom,
        "properties": attrs
    }


class DirectQueryRequest(BaseModel):
    sql: str = Field(..., description="DuckDB SQL statement to execute against S3")
    limit: Optional[int] = Field(None, description="Max rows to return (None for all viewport features)")


class DirectQueryResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_count: int
    execution_time_ms: float


@app.get("/api/health")
def health_check():
    """Health check endpoint for GCP Cloud Run liveness/readiness probes."""
    return {"status": "ok", "service": "geolibre-spatial-ai-proxy", "version": "2.5.0"}


@app.get("/api/catalog", response_model=ProjectCatalogResponse)
def get_catalog():
    """Serves the complete thematic dataset catalog linking all S3 layers."""
    return catalog_mgr.get_project_catalog()


@app.post("/api/ai/spatial-query", response_model=SpatialQueryResponse)
def handle_spatial_query(request: SpatialQueryRequest):
    """Translates a natural language question into DuckDB Spatial SQL querying live S3 data."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
    return ai_agent.translate_query(request)


@app.get("/api/data/{layer_id}")
async def get_live_layer_data(
    layer_id: str,
    bbox: Optional[str] = Query(None, description="Bounding box minx,miny,maxx,maxy in WGS84"),
    zoom: Optional[float] = Query(None, description="Current map zoom level"),
    limit: Optional[int] = Query(None, description="Max record count (None for all viewport features)")
):
    """Smart 5-Tier Hierarchical LOD Spatial Feature Streamer:
    - Zoom < 5.5: State/Territory Boundaries (Multi-State National Scale)
    - Zoom 5.5 - 8.0: Regions / ASGS Statistical Regions (Regional Scale)
    - Zoom 8.0 - 11.0: LGA Council Boundaries (Council Scale)
    - Zoom 11.0 - 14.5: Large Properties & Major Land Holdings (Precinct Scale)
    - Zoom >= 14.5: Smaller Properties & Detailed Lot/Plan Cadastre Parcels (Property Scale)
    """
    z = zoom if zoom is not None else 10.0
    where_clause = "1=1"
    base_url = LIVE_STREAMS.get(layer_id)

    # 5-Tier Hierarchical Scale Resolution for Cadastre & Meshblocks
    if layer_id in ("abs_meshblocks", "geoscape_cadastre"):
        if z < 5.5:
            # 1. State Boundaries (Multi-State National Scale)
            base_url = LOD_STREAMS["state_boundaries"]
            lod_tier = "state_boundaries"
        elif z < 8.0:
            # 2. Regional Boundaries (Regional Scale)
            base_url = LOD_STREAMS["regions"]
            lod_tier = "regions"
        elif z < 11.0:
            # 3. LGA Councils (Council Scale)
            base_url = LOD_STREAMS["councils"]
            lod_tier = "councils"
        elif z < 14.5:
            # 4. Large Properties & Rural/Industrial Land Holdings (Precinct Scale)
            base_url = LOD_STREAMS["cadastre_properties"]
            lod_tier = "large_properties"
        else:
            # 5. Smaller Properties & Detailed Lot/Plan Parcels (Property Scale)
            base_url = LOD_STREAMS["cadastre_properties"]
            lod_tier = "small_properties"
    else:
        lod_tier = "standard"

    if not base_url:
        return {"type": "FeatureCollection", "features": [], "total_count": 0, "lod_tier": lod_tier}

    # Fetch all features within viewport scale (max 4000 per request)
    rec_count = str(limit) if limit else "4000"

    params = {
        "where": where_clause,
        "outFields": "*",
        "f": "json",
        "outSR": "4326",
        "resultRecordCount": rec_count
    }

    # Apply Viewport BBOX Spatial Filter if supplied
    if bbox:
        try:
            parts = [float(p.strip()) for p in bbox.split(",")]
            if len(parts) == 4:
                minx, miny, maxx, maxy = parts
                params["geometry"] = f"{minx},{miny},{maxx},{maxy}"
                params["geometryType"] = "esriGeometryEnvelope"
                params["spatialRel"] = "esriSpatialRelIntersects"
                params["inSR"] = "4326"
        except Exception:
            pass

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AURA-Siting/2.5"}
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            resp = await client.get(base_url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                raw_feats = data.get("features", [])
                geojson_feats = [arcgis_to_geojson_feature(rf) for rf in raw_feats]
                return {
                    "type": "FeatureCollection",
                    "features": geojson_feats,
                    "total_count": len(geojson_feats),
                    "lod_tier": lod_tier,
                    "zoom": z,
                    "bbox_applied": bool(bbox)
                }
        except Exception as e:
            return {"type": "FeatureCollection", "features": [], "error": str(e), "lod_tier": lod_tier}

    return {"type": "FeatureCollection", "features": [], "total_count": 0, "lod_tier": lod_tier}


@app.post("/api/query/duckdb", response_model=DirectQueryResponse)
def execute_direct_query(req: DirectQueryRequest):
    """Directly executes DuckDB SQL against S3 / Parquet and returns all matching rows."""
    import time
    start_t = time.perf_counter()
    
    try:
        import duckdb
        con = duckdb.connect(database=":memory:")
        try:
            con.install_extension("spatial")
            con.load_extension("spatial")
            con.install_extension("httpfs")
            con.load_extension("httpfs")
        except Exception:
            pass

        df = con.execute(req.sql).fetchdf()
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        records = df.to_dict(orient="records")
        con.close()
        
        final_rows = records[:req.limit] if req.limit else records
        return DirectQueryResponse(
            columns=list(df.columns),
            rows=final_rows,
            total_count=len(records),
            execution_time_ms=round(elapsed_ms, 2)
        )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        return DirectQueryResponse(
            columns=["error_or_status", "message"],
            rows=[{"error_or_status": "S3_DIRECT_PROXY", "message": str(e)}],
            total_count=0,
            execution_time_ms=round(elapsed_ms, 2)
        )


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("src.geolibre_proxy.main:app", host="0.0.0.0", port=port)
