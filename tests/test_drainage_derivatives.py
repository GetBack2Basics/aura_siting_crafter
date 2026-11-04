"""Tests for the drainage derivative maths and the derive job's manifest/gate wiring (no GDAL, no GCS)."""

import json
import os
import sys

import numpy as np
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "jobs", "hydrosheds_derive"))
sys.path.insert(0, os.path.join(BASE_DIR, "src", "Ingestion_v2"))

import derive_lib as lib  # noqa: E402
from publish_gate import assert_publishable  # noqa: E402

with open(os.path.join(BASE_DIR, "config", "scoring", "s_drainage_params.json"), "r", encoding="utf-8") as f:
    PARAMS = json.load(f)
with open(os.path.join(BASE_DIR, "config", "dataset_manifest_v2.json"), "r", encoding="utf-8") as f:
    MANIFEST = json.load(f)["datasets"]


def test_params_are_marked_experimental_and_weights_sum_to_one():
    assert PARAMS["status"] == "experimental_uncalibrated"
    assert sum(PARAMS["weights"].values()) == pytest.approx(1.0)


def test_sigmoid_midpoint_and_bounds():
    assert lib.sigmoid(3.0, 2.0, 3.0) == pytest.approx(0.5)
    assert 0.0 <= float(lib.sigmoid(-1e9, 2.0, 3.0)) < 1e-6
    assert float(lib.sigmoid(1e9, 2.0, 3.0)) > 1 - 1e-6


def test_stream_mask_threshold_and_nan():
    acc = np.array([[5.0, 1000.0], [np.nan, 5000.0]])
    assert lib.stream_mask(acc, 1000).tolist() == [[False, True], [False, True]]


def test_height_above_drainage_uses_nearest_stream_elevation():
    dem = np.array([[10.0, 12.0, 20.0, 30.0]])
    streams = np.array([[True, False, False, False]])
    hand = lib.height_above_drainage(dem, streams)
    assert hand.tolist() == [[0.0, 2.0, 10.0, 20.0]]


def test_height_above_drainage_without_streams_is_nan():
    dem = np.ones((2, 2))
    assert np.isnan(lib.height_above_drainage(dem, np.zeros((2, 2), dtype=bool))).all()


def test_s_drainage_bounds_and_monotonic_behaviour():
    acc = np.array([10.0, 1e5])
    hand = np.array([30.0, 0.0])
    slope = np.array([20.0, 0.5])
    score = lib.s_drainage(acc, hand, slope, PARAMS)
    assert ((score >= 0) & (score <= 1)).all()
    assert score[1] > score[0]  # big catchment, low and flat is more drainage-prone


def test_percentile_stops_ignore_nan_and_fail_on_empty():
    stops = lib.percentile_stops(np.array([np.nan, 1.0, 2.0, 3.0, 4.0, 5.0]))
    assert stops == sorted(stops) and stops[0] >= 1.0 and stops[-1] <= 5.0
    with pytest.raises(ValueError):
        lib.percentile_stops(np.array([np.nan]))


@pytest.mark.parametrize("key", ["aura_drainage_slope_deg_v1", "aura_drainage_hand_euclid_m_v1",
                                 "aura_drainage_streams_mask_v1", "aura_drainage_s_drainage_v1"])
def test_derived_manifest_entries_pass_gate_and_trace_sources(key):
    entry = MANIFEST[key]
    assert_publishable(entry)
    assert entry["derived"] is True
    assert all(src in MANIFEST for src in entry["derived_from"])

