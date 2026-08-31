"""Tests for the GeoLibre FastAPI Spatial AI Gateway.
"""

import pytest
from fastapi.testclient import TestClient
from src.geolibre_proxy.main import app
from src.geolibre_proxy.schemas import SpatialQueryRequest

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "geolibre-spatial-ai-proxy"


def test_get_catalog_endpoint():
    response = client.get("/api/catalog")
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "AURA National Siting Crafter — GeoLibre WebGIS"
    assert len(data["categories"]) >= 6


def test_spatial_query_translation_substation_and_buffer():
    request_data = {
        "query": "Show me all candidate sites in NSW within 2km of transmission lines and at least 1km away from sensitive receptors with area >= 15 ha",
        "region": "national"
    }
    response = client.post("/api/ai/spatial-query", json=request_data)
    assert response.status_code == 200
    data = response.json()
    sql = data["translated_sql"]
    assert "FROM read_parquet('s3://wherobots-user-storage/aura_siting/candidates/datacenter_candidates_national.parquet')" in sql
    assert "state_name = 'New South Wales'" in sql
    assert "dist_to_substation_km <= 2.0" in sql
    assert "dist_to_sensitive_km >= 1.0" in sql
    assert "area_ha >= 15.0" in sql
    assert data["execution_engine"] == "DuckDB-WASM"


def test_spatial_query_empty_error():
    request_data = {"query": "   "}
    response = client.post("/api/ai/spatial-query", json=request_data)
    assert response.status_code == 400


def test_get_live_layer_data_viewport_and_s3_total():
    # Test requesting live layer data with viewport bbox
    response = client.get("/api/data/nhsd_healthcare?bbox=151.5,-33.0,151.7,-32.8&zoom=12.0&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert "viewport_count" in data
    assert data["s3_total_records"] == 4218
    assert data["s3_path"] == "s3://wherobots-user-storage/aura_siting/receptors/nhsd_national_healthcare.parquet"
    assert data["bbox_applied"] is True

