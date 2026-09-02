#!/usr/bin/env python3
"""
Unit and Integration Tests for Ingestion v2 Library & Multi-State Siting Engine.
AURA Siting Crafter — Strict EPSG:7844 & Wherobots Playbook Verification.
"""

import os
import json
import pytest

from src.Ingestion_v2.dataset_loader_v2 import (
    list_available_datasets,
    load_dataset_config,
    apply_canonical_schema_mapping,
    CRS_GDA2020,
    CRS_ALBERS,
    _clean_coordinates
)
from tools.check_for_updates import run_differential_check, load_manifest
from tools.build_geolibre_project_v2 import generate_multi_state_candidate_records


def test_universal_crs_standard_constant():
    """Verifies that the universal CRS is strictly EPSG:7844 (GDA2020)."""
    assert CRS_GDA2020 == "EPSG:7844"
    assert CRS_ALBERS == "EPSG:3112"


def test_multi_state_dataset_listing():
    """Verifies dataset configs exist across all target states."""
    all_datasets = list_available_datasets("all")
    assert len(all_datasets) >= 15

    for state in ["nsw", "qld", "vic", "wa", "sa", "tas"]:
        state_ds = list_available_datasets(state)
        assert len(state_ds) >= 1, f"State {state} should have at least 1 dataset configurator"


def test_all_v2_configs_conform_to_epsg7844_standard():
    """Ensures every v2 dataset configuration specifies EPSG:7844 as target_crs."""
    all_datasets = list_available_datasets("all")
    for dkey in all_datasets:
        cfg = load_dataset_config(dkey)
        assert cfg.get("target_crs") == "EPSG:7844", f"Dataset {dkey} target_crs must be EPSG:7844"
        assert cfg.get("metric_crs") == "EPSG:3112", f"Dataset {dkey} metric_crs must be EPSG:3112"
        assert "canonical_theme" in cfg, f"Dataset {dkey} must specify a canonical_theme"


def test_coordinate_cleaning_sanitizer():
    """Verifies coordinate cleaning strips nulls and non-numeric artifacts."""
    assert _clean_coordinates(None) is None
    assert _clean_coordinates([151.7, -32.9]) == [151.7, -32.9]
    assert _clean_coordinates([[151.7, -32.9], [151.8, -32.8]]) == [[151.7, -32.9], [151.8, -32.8]]


def test_canonical_schema_mapping():
    """Verifies properties are mapped correctly into the Canonical AURA Schema."""
    sample_features = [{
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[151.7, -32.9], [151.8, -32.8]]
        },
        "properties": {
            "OBJECTID": 101,
            "CIRCUIT_NAME": "Gladstone 275kV Feeder",
            "VOLTAGE": 275,
            "OPERATOR": "Powerlink"
        }
    }]
    
    cfg = {
        "dataset_key": "qld_transmission_grid_v2",
        "canonical_theme": "siting_transmission_grid",
        "state": "qld",
        "schema_mapping": {
            "line_id": "OBJECTID",
            "line_name": "CIRCUIT_NAME",
            "voltage_kv": "VOLTAGE",
            "operator": "OPERATOR"
        }
    }
    
    normalized = apply_canonical_schema_mapping(sample_features, cfg)
    assert len(normalized) == 1
    props = normalized[0]["properties"]
    assert props["_canonical_theme"] == "siting_transmission_grid"
    assert props["_state"] == "QLD"
    assert props["line_name"] == "Gladstone 275kV Feeder"
    assert props["voltage_kv"] == 275
    assert props["operator"] == "Powerlink"


def test_differential_update_checker():
    """Tests the differential update checker runs and outputs valid summary."""
    summary = run_differential_check(target_state="all", dry_run=True)
    assert summary["total_datasets_checked"] >= 15
    assert "elapsed_seconds" in summary
    assert isinstance(summary["changed_datasets"], list)


def test_multi_state_candidate_records_contain_multi_hazards():
    """Verifies candidate records include all multi-hazard statutory attributes."""
    records = generate_multi_state_candidate_records()
    assert len(records) > 0
    
    for r in records:
        assert "cyclone_region" in r
        assert "landslide_risk" in r
        assert "earthquake_pga" in r
        assert "coastal_inundation_risk" in r
        assert "power_dist_km" in r
        assert "water_dist_km" in r
        assert "sensitive_dist_km" in r
        assert "suitability_score" in r
