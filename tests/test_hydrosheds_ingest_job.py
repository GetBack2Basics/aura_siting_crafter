"""Tests for the HydroSHEDS ingest job's pure logic (no network, no GDAL, no GCS)."""

import os
import sys

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOB_DIR = os.path.join(BASE_DIR, "jobs", "hydrosheds_ingest")
sys.path.insert(0, os.path.join(BASE_DIR, "src", "Ingestion_v2"))
sys.path.insert(0, JOB_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

import ingest  # noqa: E402
import stage_job_context  # noqa: E402


def test_pick_raster_requires_exactly_one():
    assert ingest.pick_raster(["a/readme.txt", "a/au_acc_3s.tif"]) == "a/au_acc_3s.tif"
    with pytest.raises(RuntimeError):
        ingest.pick_raster(["readme.txt"])
    with pytest.raises(RuntimeError):
        ingest.pick_raster(["a.tif", "b.tif"])


def test_raw_archives_use_a_different_bucket_than_the_public_outputs():
    assert ingest.RAW_BUCKET != ingest.BUCKET
    assert ingest.RAW_BUCKET == "aura-siting-crafter-private-raw"


def test_object_paths():
    assert ingest.raw_object("k", "https://h/x/au_acc_3s.zip") == "raw/k/au_acc_3s.zip"
    assert ingest.cog_object("k", "d/au_acc_3s.tif", "national") == "processed/k/au_acc_3s.tif"
    assert ingest.cog_object("k", "d/au_acc_3s.tif", "hunter") == "processed/k/regions/hunter/au_acc_3s.tif"


def test_overview_resampling_never_averages_counts():
    assert ingest.overview_resampling({"band_semantics": "flow accumulation: count of upstream contributing cells"}) == "NEAREST"
    assert ingest.overview_resampling({"band_semantics": "hydrologically conditioned elevation"}) == "AVERAGE"


def test_region_bbox_comes_from_repo_config(monkeypatch):
    stage_dir = stage_job_context.stage("hydrosheds_ingest")
    monkeypatch.setattr(ingest, "HERE", stage_dir)
    assert ingest.load_region_bbox("national") is None
    assert ingest.load_region_bbox("hunter") == [151.0, -33.2, 152.0, -32.5]


def test_manifest_entries_pass_gate_and_are_loadable(monkeypatch):
    stage_dir = stage_job_context.stage("hydrosheds_ingest")
    monkeypatch.setattr(ingest, "HERE", stage_dir)
    for key in ("hydrosheds_au_acc_3s_v1", "hydrosheds_au_con_3s_v1"):
        ingest.assert_publishable(ingest.load_manifest_entry(key))


def test_gate_blocks_unapproved_vector_dataset(monkeypatch):
    stage_dir = stage_job_context.stage("hydrosheds_ingest")
    monkeypatch.setattr(ingest, "HERE", stage_dir)
    entry = ingest.load_manifest_entry("qld_waterway_barriers_hydro_v2")
    with pytest.raises(ingest.PublishBlocked):
        ingest.assert_publishable(entry)

