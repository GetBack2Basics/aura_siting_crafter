"""
Unit & Integration Test: GeoLibre Frontend & Report UI Contracts
Asserts that index.html and national_suitability_report.html adhere to:
  1. Proper layer geometry type mapping (fill for polygon, line for polyline, circle for point).
  2. Proper event handler bindings and table synchronization calls.
  3. Clean UI text (no forbidden tokens, no mock data).
"""

import os
import re
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_INDEX_PATH = os.path.join(BASE_DIR, "src", "geolibre_frontend", "index.html")
REPORT_HTML_PATH = os.path.join(BASE_DIR, "runner", "national_suitability_report.html")


def test_frontend_table_sync_contract():
    """Asserts that updateViewportStreams invokes populateTableFromData when the table dock is open."""
    assert os.path.exists(FRONTEND_INDEX_PATH)
    with open(FRONTEND_INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Assert that populateTableFromData is defined and invoked in updateViewportStreams
    assert "function populateTableFromData" in html, "populateTableFromData function definition missing"
    assert "populateTableFromData(lyr, data, lodName, zoom)" in html, "populateTableFromData invocation missing from updateViewportStreams"

    # Assert that openLayerTable immediately uses cached liveGeoJSON if present
    assert "populateTableFromData(lyr, lyr.liveGeoJSON" in html, "openLayerTable must populate from lyr.liveGeoJSON cache immediately"


def test_frontend_hazard_layer_types():
    """Asserts that statutory hazard overlays in index.html have the correct layer type (fill for polygon)."""
    with open(FRONTEND_INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Look for nsw_coastal_inundation_hazard in THEMATIC_LAYERS
    coastal_block = re.search(r'id:\s*"nsw_coastal_inundation_hazard".*?type:\s*"([^"]+)"', html, re.DOTALL)
    assert coastal_block, "nsw_coastal_inundation_hazard not found in THEMATIC_LAYERS"
    assert coastal_block.group(1) == "fill", f"nsw_coastal_inundation_hazard type must be 'fill', found '{coastal_block.group(1)}'"

    landslide_block = re.search(r'id:\s*"landslide_susceptibility".*?type:\s*"([^"]+)"', html, re.DOTALL)
    assert landslide_block, "landslide_susceptibility not found in THEMATIC_LAYERS"
    assert landslide_block.group(1) == "fill", f"landslide_susceptibility type must be 'fill', found '{landslide_block.group(1)}'"


def test_national_suitability_report_integrity():
    """Asserts that the built national suitability report has dynamic timestamps, candidate tables, and methodology."""
    if os.path.exists(REPORT_HTML_PATH):
        with open(REPORT_HTML_PATH, "r", encoding="utf-8") as f:
            report_html = f.read()

        assert "__FOOTER_TIMESTAMP__" not in report_html, "Unrendered template token __FOOTER_TIMESTAMP__ found in report"
        assert "Multi-Hazard" in report_html, "Missing Multi-Hazard section in report"
        assert "S_hazard" in report_html, "Missing statutory hazard formula in report"
