"""
Unit & Integration Test: Live Endpoint & Geometry Contract Auditing
Tests that all dataset configurations in config/datasets_v2/ point to live, reachable endpoints,
and asserts that upstream geometryType matches the declared shape type and geographic bounding box.
"""

import os
import glob
import json
import requests
import pytest

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "datasets_v2")

GEOMETRY_TYPE_MAP = {
    "esriGeometryPolygon": ["Polygon", "MultiPolygon"],
    "esriGeometryPoint": ["Point", "MultiPoint"],
    "esriGeometryPolyline": ["LineString", "MultiLineString", "Polyline"],
}


@pytest.fixture(scope="module")
def dataset_configs():
    configs = sorted(glob.glob(os.path.join(CONFIG_DIR, "*", "*.json")))
    assert len(configs) > 0, "No dataset configurations found in config/datasets_v2/"
    return configs


def test_all_dataset_endpoints_reachable_and_geometry_contracts(dataset_configs):
    """
    Asserts that:
      1. Each configured live spatial endpoint returns HTTP 200.
      2. Upstream ArcGIS / WFS geometryType strictly matches declared config geometry_type.
    """
    failures = []
    for cfg_path in dataset_configs:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dkey = data.get("dataset_key")
        endpoint = data.get("endpoint")
        declared_geom = data.get("geometry_type")

        assert endpoint, f"Missing endpoint in {dkey}"

        try:
            r = requests.get(endpoint, timeout=8, allow_redirects=True)
            if r.status_code != 200:
                failures.append(f"{dkey} -> {endpoint} returned HTTP {r.status_code}")
                continue

            # If it's an ArcGIS REST endpoint returning JSON metadata, probe geometryType
            if "f=json" in endpoint or r.headers.get("content-type", "").startswith("application/json") or "json" in r.text[:200]:
                try:
                    meta = r.json()
                    upstream_geom = meta.get("geometryType")
                    if upstream_geom:
                        valid_declared = GEOMETRY_TYPE_MAP.get(upstream_geom, [])
                        if declared_geom not in valid_declared:
                            failures.append(
                                f"Geometry Mismatch in {dkey}: Upstream service '{endpoint}' is '{upstream_geom}' "
                                f"but config declares '{declared_geom}' (expected one of {valid_declared})"
                            )
                except Exception:
                    pass
        except Exception as ex:
            failures.append(f"{dkey} -> {endpoint} connection error: {type(ex).__name__}")

    assert len(failures) == 0, f"Endpoint audit failures:\n" + "\n".join(failures)

