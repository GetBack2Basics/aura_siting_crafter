import os
import json
import pytest
import jsonschema

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_project_manifest_schema_validation():
    schema_path = os.path.join(ROOT_DIR, "config", "projects", "schema_project_manifest.json")
    manifest_path = os.path.join(ROOT_DIR, "config", "projects", "LMCC_MacquarieCoal.json")

    assert os.path.exists(schema_path), "Project manifest schema missing"
    assert os.path.exists(manifest_path), "Macquarie Coal manifest missing"

    with open(schema_path, "r", encoding="utf-8") as sf:
        schema = json.load(sf)

    with open(manifest_path, "r", encoding="utf-8") as mf:
        manifest = json.load(mf)

    # Validate against JSON Schema
    jsonschema.validate(instance=manifest, schema=schema)
    assert manifest["project_id"] == "LMCC_MacquarieCoal"
    assert manifest["engineering_metrics"]["net_developable_area_ha"] > 0
    assert manifest["engineering_metrics"]["power_capacity_mva"] >= 100

def test_project_spatial_layers_exist_and_valid():
    manifest_path = os.path.join(ROOT_DIR, "config", "projects", "LMCC_MacquarieCoal.json")
    with open(manifest_path, "r", encoding="utf-8") as mf:
        manifest = json.load(mf)

    spatial_layers = manifest["spatial_layers"]
    for layer_name, rel_path in spatial_layers.items():
        full_path = os.path.join(ROOT_DIR, rel_path.replace("/", os.sep))
        assert os.path.exists(full_path), f"Spatial layer {layer_name} file missing: {full_path}"

        with open(full_path, "r", encoding="utf-8") as lf:
            geojson_data = json.load(lf)

        assert geojson_data["type"] == "FeatureCollection", f"{layer_name} is not a FeatureCollection"
        assert len(geojson_data["features"]) > 0, f"{layer_name} contains no features"

def test_generated_project_products_exist():
    app_path = os.path.join(ROOT_DIR, "src", "geolibre_frontend", "projects", "index_LMCC_MacquarieCoal.html")
    report_path = os.path.join(ROOT_DIR, "runner", "projects", "report_LMCC_MacquarieCoal.html")

    assert os.path.exists(app_path), "Site interactive app index_LMCC_MacquarieCoal.html missing"
    assert os.path.exists(report_path), "Site statutory report report_LMCC_MacquarieCoal.html missing"

    with open(app_path, "r", encoding="utf-8") as af:
        app_html = af.read()
        assert "LMCC_MacquarieCoal" in app_html
        assert "Macquarie Coal Complex" in app_html

    with open(report_path, "r", encoding="utf-8") as rf:
        report_html = rf.read()
        assert "LMCC_MacquarieCoal" in report_html
        assert "3-Phase Net Developable Pad Staging Plan" in report_html
