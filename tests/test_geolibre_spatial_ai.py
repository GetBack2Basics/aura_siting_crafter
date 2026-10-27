"""Tests for the GeoLibre FastAPI Spatial AI Gateway.
"""

import pytest
fastapi = pytest.importorskip("fastapi")
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


def test_multi_region_query_and_clarifications():
    request_data = {
        "query": "Find candidate sites in Latrobe Valley or Gladstone with recycled water proximity <= 2km",
        "region": "national"
    }
    response = client.post("/api/ai/spatial-query", json=request_data)
    assert response.status_code == 200
    data = response.json()
    sql = data["translated_sql"]
    assert "state_name = 'Victoria' OR state_name = 'Queensland'" in sql
    assert "dist_to_wwtw_km <= 2.0" in sql
    assert "clarifying_questions" in data
    assert "issues_detected" in data
    assert "recommendations" in data


def test_issue_detection_oversized_parcel_and_ambiguity():
    request_data = {
        "query": "Show me large sites with area >= 60 ha near power lines",
        "region": "national"
    }
    response = client.post("/api/ai/spatial-query", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["issues_detected"]) >= 1
    # Check that it warns about the 44.5 ha max candidate limit
    assert any("44.5 ha" in issue for issue in data["issues_detected"])
    assert len(data["clarifying_questions"]) >= 1
    assert len(data["recommendations"]) >= 1


def test_root_serves_webgis_map():
    response = client.get("/")
    assert response.status_code == 200
    assert "GeoLibre WebGIS" in response.text or "map" in response.text
    # Verify the 2-step stepper button is present
    assert "Step 1: Translate to Spatial SQL" in response.text


def test_serve_html_files():
    for page in ["map", "data_qa", "data_lineage_audit"]:
        response = client.get(f"/{page}.html")
        assert response.status_code == 200, f"Page {page}.html failed to load"


def test_spatial_query_prompt_alias():
    response = client.post("/api/ai/spatial-query", json={"prompt": "Sites in NSW within 1.5km of substation"})
    assert response.status_code == 200
    data = response.json()
    assert "state_name = 'New South Wales'" in data["translated_sql"]


def test_serve_docs_qa_inspector():
    """Asserts that QA inspect links like /docs/qa/geolibre_qa_inspect.html resolve with HTTP 200."""
    response = client.get("/docs/qa/geolibre_qa_inspect.html?dataset=national_cyclone_hazard_tcha_v2")
    assert response.status_code == 200
    assert "AURA - QA Inspection" in response.text


def test_docs_redirect_to_qa_report():
    """Asserts that navigating to /docs or /docs/ redirects directly to /data_qa.html."""
    response = client.get("/docs", follow_redirects=False)
    assert response.status_code in [301, 302, 307, 308]
    assert response.headers["location"] == "/data_qa.html"


def test_api_docs_swagger():
    """Asserts that FastAPI Swagger UI is cleanly available at /api/docs."""
    response = client.get("/api/docs")
    assert response.status_code == 200



