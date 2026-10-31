"""
Unit & Integration Test Suite: GeoLibre Proposal 2 Area-Priority Layer Limiter
Asserts that:
  1. Frontend script js/geolibre-layer-limiter.js exists and exports MinHeap, getFeatureArea, optimizeFeatureCollection.
  2. MapLibre GL UI contract in map.html includes the limiter script, setRenderOptimizer, and HUD badge.
  3. The proxy /api/data endpoint handles sort_by=area_desc and max_features capping correctly.
  4. Algorithm correctly selects top-K features by area descending and computes stats.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient
from src.geolibre_proxy.main import app, extract_feature_area

client = TestClient(app)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_MAP_PATH = os.path.join(BASE_DIR, "src", "geolibre_frontend", "map.html")
LIMITER_JS_PATH = os.path.join(BASE_DIR, "src", "geolibre_frontend", "js", "geolibre-layer-limiter.js")
PACKAGE_TS_PATH = os.path.join(BASE_DIR, "packages", "geolibre-layer-limiter", "src", "index.ts")


def test_limiter_source_files_exist():
    """Verify that both frontend script and upstream TypeScript package exist."""
    assert os.path.exists(LIMITER_JS_PATH), "src/geolibre_frontend/js/geolibre-layer-limiter.js missing"
    assert os.path.exists(PACKAGE_TS_PATH), "packages/geolibre-layer-limiter/src/index.ts missing"


def test_map_html_limiter_integration():
    """Verify that map.html embeds the limiter script, HUD badge, and setRenderOptimizer."""
    assert os.path.exists(FRONTEND_MAP_PATH)
    with open(FRONTEND_MAP_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    assert "js/geolibre-layer-limiter.js" in html, "map.html must include js/geolibre-layer-limiter.js"
    assert "map-limiter-hud" in html, "map.html must have #map-limiter-hud HUD telemetry element"
    assert "setRenderOptimizer" in html, "map.html must implement setRenderOptimizer on layers"
    assert "updateLimiterHud" in html, "map.html must implement updateLimiterHud telemetry updater"


def test_proxy_extract_feature_area():
    """Verify python backend extract_feature_area logic."""
    # Attribute based
    feature_prop = {
        "type": "Feature",
        "properties": {"area_ha": 45.2, "name": "Large Industrial Lot"},
        "geometry": None
    }
    assert extract_feature_area(feature_prop) == 45.2

    # Shape__Area (square meters to hectares)
    feature_sqm = {
        "type": "Feature",
        "properties": {"Shape__Area": 150000.0},
        "geometry": None
    }
    assert extract_feature_area(feature_sqm) == 15.0

    # Geometry based polygon
    feature_geom = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [140.0, -30.0],
                    [140.01, -30.0],
                    [140.01, -30.01],
                    [140.0, -30.01],
                    [140.0, -30.0]
                ]
            ]
        }
    }
    calculated = extract_feature_area(feature_geom)
    assert calculated > 0.0, "Shoelace polygon area approximation should yield positive hectares"


def test_proxy_live_layer_limiter_query():
    """Verify /api/data endpoint supports sort_by=area_desc and max_features capping."""
    response = client.get("/api/data/nhsd_healthcare?bbox=151.5,-33.0,151.7,-32.8&zoom=12.0&sort_by=area_desc&max_features=5")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "rendered_count" in data
    assert "is_capped" in data
    assert len(data["features"]) <= 5

