"""
Unit & Integration Test: Live Endpoint Auditing
Tests that all dataset configurations in config/datasets_v2/ point to live, reachable endpoints.
"""

import os
import glob
import json
import requests
import pytest

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "datasets_v2")

@pytest.fixture(scope="module")
def dataset_configs():
    configs = sorted(glob.glob(os.path.join(CONFIG_DIR, "*", "*.json")))
    assert len(configs) > 0, "No dataset configurations found in config/datasets_v2/"
    return configs

def test_all_dataset_endpoints_reachable(dataset_configs):
    """Asserts that each configured live spatial endpoint returns HTTP 200."""
    failures = []
    for cfg_path in dataset_configs:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        dkey = data.get("dataset_key")
        endpoint = data.get("endpoint")
        
        assert endpoint, f"Missing endpoint in {dkey}"
        
        try:
            r = requests.get(endpoint, timeout=6, allow_redirects=True)
            if r.status_code != 200:
                failures.append(f"{dkey} -> {endpoint} returned HTTP {r.status_code}")
        except Exception as ex:
            failures.append(f"{dkey} -> {endpoint} connection error: {type(ex).__name__}")
            
    assert len(failures) == 0, f"Endpoint audit failures:\n" + "\n".join(failures)
