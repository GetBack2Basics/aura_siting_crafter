"""Tests for the GeoLibre S3 Thematic Dataset Catalog.
"""

import pytest
from src.geolibre_proxy.catalog_manager import CatalogManager


def test_catalog_loads_successfully():
    manager = CatalogManager()
    catalog = manager.get_project_catalog()
    assert catalog.project_name == "AURA National Siting Crafter — GeoLibre WebGIS"
    assert catalog.version == "2.0.0"
    assert catalog.storage_root == "s3://wherobots-user-storage/aura_siting"


def test_catalog_has_all_thematic_categories():
    manager = CatalogManager()
    catalog = manager.get_project_catalog()
    category_ids = [cat.id for cat in catalog.categories]
    expected_categories = ["candidates", "energy", "water", "receptors", "cadastre", "micro_siting"]
    for expected in expected_categories:
        assert expected in category_ids, f"Missing thematic category: {expected}"


def test_catalog_s3_paths_zero_copy():
    manager = CatalogManager()
    s3_paths = manager.get_all_s3_paths()
    assert len(s3_paths) >= 10
    for path in s3_paths:
        assert path.startswith("s3://wherobots-user-storage/aura_siting/"), f"Invalid zero-copy S3 path: {path}"


def test_persona_presets_match_report():
    manager = CatalogManager()
    catalog = manager.get_project_catalog()
    presets = catalog.persona_presets
    assert "general_public" in presets
    assert "planner" in presets
    assert "regulator" in presets
    assert "developer" in presets
    assert "community" in presets
    assert presets["developer"]["weights"]["power"] == 50
    assert presets["community"]["weights"]["sensitive"] == 40
