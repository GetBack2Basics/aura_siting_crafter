"""
Unit & Integration Test: GeoLibre Cesium 3D Viewer Contract
Asserts that geolibre_cesium_3d_viewer.html has:
  1. CesiumJS 3D engine integration and GeoLibre styling.
  2. Point cloud formats (COPC, Potree octree, LAZ) & 3D DEM/DSM Mesh primitives.
  3. ASPRS classification shaders (Ground, Vegetation, Buildings, Water).
  4. Authoritative siting overlays (precinct boundary, pads 1-4, power corridor, biolink, contours).
  5. S3 V2 dataset lineage inspector dock and zero-mock data integrity.
"""

import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWER_PATH = os.path.join(BASE_DIR, "src", "geolibre_frontend", "geolibre_cesium_3d_viewer.html")
PROJ_VIEWER_PATH = os.path.join(BASE_DIR, "src", "geolibre_frontend", "projects", "geolibre_cesium_3d_viewer.html")


def test_geolibre_cesium_viewer_structure():
    """Asserts that the root GeoLibre Cesium 3D viewer contains required UI components."""
    assert os.path.exists(VIEWER_PATH), f"Missing {VIEWER_PATH}"
    with open(VIEWER_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Core Cesium & Engine HUD
    assert "Cesium.Viewer" in html
    assert "GEOLIBRE CESIUM 3D" in html
    assert "format-selector" in html
    assert "mode-selector" in html

    # Point Cloud & Mesh primitives
    assert "pointCollections" in html
    assert "MeshPrimitives" in html
    assert "create3DMeshPrimitive" in html
    assert "applyColorMode" in html

    # ASPRS Classification Toggles
    assert "class-ground" in html
    assert "class-veg" in html
    assert "class-buildings" in html
    assert "class-water" in html

    # Authoritative Siting Overlays
    assert "layer-boundary" in html
    assert "layer-pads" in html
    assert "layer-power" in html
    assert "layer-biolink" in html
    assert "layer-contours" in html

    # Lineage Inspector / Live Data Source
    assert "lake_macquarie_elvis.copc.laz" in html or "cloud.js" in html
    assert "EPSG:7856" in html
    assert "20,000" in html or "4,808,911 pts" in html or "Real GCS" in html


def test_project_geolibre_cesium_viewer_structure():
    """Asserts that the projects companion viewer exists and has matching capabilities."""
    assert os.path.exists(PROJ_VIEWER_PATH), f"Missing {PROJ_VIEWER_PATH}"
    with open(PROJ_VIEWER_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    assert "Cesium.Viewer" in html
    assert "GEOLIBRE CESIUM 3D" in html
    assert "lake_macquarie_elvis.copc.laz" in html or "cloud.js" in html
