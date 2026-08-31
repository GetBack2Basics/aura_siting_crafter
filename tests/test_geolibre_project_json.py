import os
import json
import pytest

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "geolibre_frontend")
GEOLIBRE_JSON_PATH = os.path.join(FRONTEND_DIR, "aura-siting-crafter.geolibre.json")

VALID_LAYER_TYPES = {
    "geojson", "raster", "wms", "wmts", "xyz", "vector-tiles", "arcgis",
    "pmtiles", "mbtiles", "zarr", "lidar", "gaussian-splat", "3d-tiles",
    "cog", "flatgeobuf", "geoparquet", "duckdb-query", "deckgl-viz", "video", "image"
}

VALID_GEOMETRY_TYPES = {
    "Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon", "GeometryCollection"
}

def test_geolibre_json_exists():
    assert os.path.exists(GEOLIBRE_JSON_PATH), f"File not found: {GEOLIBRE_JSON_PATH}"

def test_geolibre_json_schema():
    with open(GEOLIBRE_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Root properties required by GeoLibre parseProject
    assert "version" in data, "Missing 'version'"
    assert "name" in data, "Missing 'name'"
    assert "mapView" in data, "Missing 'mapView'"
    assert "layers" in data, "Missing 'layers'"

    # MapView properties
    mv = data["mapView"]
    assert isinstance(mv.get("center"), list) and len(mv["center"]) == 2, "Invalid mapView.center"
    assert isinstance(mv.get("zoom"), (int, float)), "Invalid mapView.zoom"

    # Layer checks
    layers = data["layers"]
    assert isinstance(layers, list) and len(layers) > 0, "layers must be a non-empty list"

    for layer in layers:
        layer_id = layer.get("id")
        assert layer_id, f"Layer missing 'id': {layer}"
        assert layer.get("name"), f"Layer {layer_id} missing 'name'"
        assert layer.get("type") in VALID_LAYER_TYPES, f"Layer {layer_id} has invalid type: {layer.get('type')}"
        assert isinstance(layer.get("source"), dict), f"Layer {layer_id} missing source dict"
        assert isinstance(layer.get("visible"), bool), f"Layer {layer_id} visible must be bool"
        assert isinstance(layer.get("opacity"), (int, float)), f"Layer {layer_id} opacity must be number"
        assert isinstance(layer.get("style"), dict), f"Layer {layer_id} missing style dict"

        # If layer is geojson, geojson FeatureCollection must be present with valid features
        if layer.get("type") == "geojson":
            fc = layer.get("geojson")
            assert fc is not None, f"Layer {layer_id} is geojson type but missing 'geojson' field"
            assert fc.get("type") == "FeatureCollection", f"Layer {layer_id} geojson type must be 'FeatureCollection'"
            features = fc.get("features")
            assert isinstance(features, list) and len(features) > 0, f"Layer {layer_id} has no features"

            for feat in features:
                assert feat.get("type") == "Feature", f"Layer {layer_id} feature missing type 'Feature'"
                geom = feat.get("geometry")
                assert geom is not None, f"Layer {layer_id} feature missing geometry"
                assert geom.get("type") in VALID_GEOMETRY_TYPES, f"Layer {layer_id} geometry has invalid type: {geom.get('type')}"
                assert "coordinates" in geom, f"Layer {layer_id} geometry missing coordinates"
                assert isinstance(feat.get("properties"), dict), f"Layer {layer_id} feature missing properties dict"

def test_national_candidates_layer_attributes():
    with open(GEOLIBRE_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cand_layer = next((l for l in data["layers"] if l["id"] == "national_candidates"), None)
    assert cand_layer is not None, "national_candidates layer not found"

    features = cand_layer["geojson"]["features"]
    assert len(features) == 17, f"Expected 17 candidate hubs, found {len(features)}"

    first_hub = features[0]["properties"]
    assert "town_name" in first_hub, "Missing town_name in candidate properties"
    assert "suitability_score" in first_hub, "Missing suitability_score in candidate properties"
    assert "dist_to_substation_km" in first_hub, "Missing dist_to_substation_km in candidate properties"

def test_authoritative_layer_record_volumes():
    with open(GEOLIBRE_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    layers_by_id = {l["id"]: l for l in data["layers"]}

    # Verify key authoritative dataset volumes
    assert layers_by_id["nhsd_healthcare"]["metadata"]["records"] == 4218
    assert layers_by_id["acara_schools"]["metadata"]["records"] == 10842
    assert layers_by_id["bom_hydro_lines"]["metadata"]["records"] == 42100
    assert layers_by_id["substations_terminal"]["metadata"]["records"] == 1850
    assert layers_by_id["recycled_wwtw_plants"]["metadata"]["records"] == 1120
    assert layers_by_id["transmission_lines_interstate"]["metadata"]["records"] == 5000
    assert layers_by_id["transmission_lines_regional"]["metadata"]["records"] == 12400
    assert layers_by_id["abs_meshblocks"]["metadata"]["records"] == 368290
    assert layers_by_id["geoscape_cadastre"]["metadata"]["records"] == 15420800
    assert layers_by_id["bionet_biodiversity"]["metadata"]["records"] == 3583
    assert layers_by_id["rfs_bushfire_bfpl"]["metadata"]["records"] == 2450
    assert layers_by_id["transport_rail"]["metadata"]["records"] == 4000

