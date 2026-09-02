"""
Unit & Integration Test: Cross-Stack Single Source of Truth Catalog Synchronization Gate
Asserts that all dataset configurations, proxy streams, frontend layers, and project JSONs
remain 100% synchronized across the entire stack.
"""

import os
import glob
import json
import re
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DATASETS_V2 = os.path.join(BASE_DIR, "config", "datasets_v2")
MANIFEST_PATH = os.path.join(BASE_DIR, "config", "dataset_manifest_v2.json")
GEOLIBRE_PROJECT_PATH = os.path.join(BASE_DIR, "config", "geolibre_aura_project.json")
PROXY_MAIN_PATH = os.path.join(BASE_DIR, "src", "geolibre_proxy", "main.py")
FRONTEND_INDEX_PATH = os.path.join(BASE_DIR, "src", "geolibre_frontend", "index.html")


def test_manifest_synchronization():
    """Asserts that every dataset in config/datasets_v2/ is present in dataset_manifest_v2.json."""
    assert os.path.exists(MANIFEST_PATH), "dataset_manifest_v2.json is missing"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest_datasets = manifest.get("datasets", {})
    configs = glob.glob(os.path.join(CONFIG_DATASETS_V2, "*", "*.json"))
    assert len(configs) > 0, "No dataset JSONs found in config/datasets_v2"

    missing_in_manifest = []
    for cfg in configs:
        with open(cfg, "r", encoding="utf-8") as f:
            data = json.load(f)
        dkey = data.get("dataset_key")
        if dkey not in manifest_datasets:
            missing_in_manifest.append(dkey)

    assert len(missing_in_manifest) == 0, f"Datasets missing from manifest: {missing_in_manifest}"


def test_proxy_streams_synchronization():
    """Asserts that all active live streams are registered in main.py LIVE_STREAMS and S3_AUTHORITATIVE_TOTALS."""
    assert os.path.exists(PROXY_MAIN_PATH), "src/geolibre_proxy/main.py is missing"
    with open(PROXY_MAIN_PATH, "r", encoding="utf-8") as f:
        proxy_code = f.read()

    # Extract LIVE_STREAMS keys
    live_streams_match = re.search(r"LIVE_STREAMS\s*=\s*\{([^}]+)\}", proxy_code)
    assert live_streams_match, "LIVE_STREAMS dictionary not found in main.py"
    live_stream_keys = re.findall(r'["\']([a-zA-Z0-9_]+)["\']\s*:', live_streams_match.group(1))

    # Extract S3_AUTHORITATIVE_TOTALS keys
    totals_match = re.search(r"S3_AUTHORITATIVE_TOTALS\s*=\s*\{([^}]+)\}", proxy_code)
    assert totals_match, "S3_AUTHORITATIVE_TOTALS dictionary not found in main.py"
    total_keys = re.findall(r'["\']([a-zA-Z0-9_]+)["\']\s*:', totals_match.group(1))

    # Required core statutory streams
    required_streams = [
        "national_seismic_hazard_nsha",
        "national_cyclone_hazard_tcha",
        "nsw_coastal_inundation_hazard",
        "landslide_susceptibility",
        "transmission_lines_interstate",
        "substations_terminal",
        "bom_hydro_lines",
        "recycled_wwtw_plants",
        "acara_schools",
        "nhsd_healthcare",
    ]

    missing_live = [k for k in required_streams if k not in live_stream_keys]
    assert len(missing_live) == 0, f"Required streams missing from LIVE_STREAMS in main.py: {missing_live}"

    missing_totals = [k for k in required_streams if k not in total_keys]
    assert len(missing_totals) == 0, f"Required streams missing from S3_AUTHORITATIVE_TOTALS in main.py: {missing_totals}"


def test_frontend_layers_and_direct_fallback_synchronization():
    """Asserts that all streamable layers in index.html have DIRECT_STREAM_URLS entries and clean placeholders."""
    assert os.path.exists(FRONTEND_INDEX_PATH), "src/geolibre_frontend/index.html is missing"
    with open(FRONTEND_INDEX_PATH, "r", encoding="utf-8") as f:
        html_code = f.read()

    # Assert search placeholder cleanliness
    assert 'placeholder="🔍 Search real attributes..."' not in html_code, "Forbidden token 'Search real attributes...' found in index.html"

    # Extract DIRECT_STREAM_URLS keys
    direct_match = re.search(r"const\s+DIRECT_STREAM_URLS\s*=\s*\{([^}]+)\}", html_code)
    assert direct_match, "DIRECT_STREAM_URLS not found in index.html"
    direct_keys = re.findall(r'["\']([a-zA-Z0-9_]+)["\']\s*:', direct_match.group(1))

    required_direct = [
        "national_seismic_hazard_nsha",
        "national_cyclone_hazard_tcha",
        "nsw_coastal_inundation_hazard",
        "landslide_susceptibility",
        "transmission_lines_interstate",
        "substations_terminal",
        "bom_hydro_lines",
    ]

    missing_direct = [k for k in required_direct if k not in direct_keys]
    assert len(missing_direct) == 0, f"Required streams missing from DIRECT_STREAM_URLS in index.html: {missing_direct}"


def test_geolibre_project_json_synchronization():
    """Asserts that config/geolibre_aura_project.json categories include statutory multi-hazard overlays."""
    assert os.path.exists(GEOLIBRE_PROJECT_PATH), "geolibre_aura_project.json is missing"
    with open(GEOLIBRE_PROJECT_PATH, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    categories = project_data.get("categories", [])
    category_ids = [c.get("id") for c in categories]
    assert "hazards" in category_ids, "'hazards' category missing from geolibre_aura_project.json"

    hazard_cat = next(c for c in categories if c.get("id") == "hazards")
    hazard_layer_ids = [l.get("id") for l in hazard_cat.get("layers", [])]

    required_hazards = [
        "national_seismic_hazard_nsha",
        "national_cyclone_hazard_tcha",
        "nsw_coastal_inundation_hazard",
        "landslide_susceptibility"
    ]
    missing_hazards = [h for h in required_hazards if h not in hazard_layer_ids]
    assert len(missing_hazards) == 0, f"Hazard layers missing from geolibre_aura_project.json: {missing_hazards}"
