"""Tests: dual-store manifest fields, publish gate and sync reconciliation (no network, no mock data).

Reconciliation tests use tiny in-test listings of the shape the real stores return; they check logic only,
and never write anything back to the real manifest.
"""

import copy
import json
import os
import sys

import jsonschema
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))
sys.path.insert(0, os.path.join(BASE_DIR, "src", "Ingestion_v2"))

import sync_manifest_locations as sync  # noqa: E402
from publish_gate import PublishBlocked, assert_publishable, assert_safe_object_name  # noqa: E402

with open(os.path.join(BASE_DIR, "config", "dataset_manifest_v2.json"), "r", encoding="utf-8") as f:
    MANIFEST = json.load(f)
with open(os.path.join(BASE_DIR, "config", "schemas", "dataset_locations_schema.json"), "r", encoding="utf-8") as f:
    SCHEMA = json.load(f)


def test_every_dataset_has_valid_location_fields():
    for key, entry in MANIFEST["datasets"].items():
        try:
            jsonschema.validate(instance=entry, schema=SCHEMA)
        except jsonschema.ValidationError as exc:
            pytest.fail(f"{key}: {exc.message}")


def test_total_datasets_matches_count():
    assert MANIFEST["total_datasets"] == len(MANIFEST["datasets"])


def test_gcs_locations_only_point_at_the_aura_bucket():
    for key, entry in MANIFEST["datasets"].items():
        gcs = entry["locations"]["gcs"]
        if gcs:
            assert gcs["uri"].startswith(f"gs://{sync.BUCKET}/"), key


def test_backfill_is_idempotent_and_never_overwrites():
    m = copy.deepcopy(MANIFEST)
    first = sync.backfill(m)
    snapshot = copy.deepcopy(m)
    assert sync.backfill(m) == 0
    assert m == snapshot
    assert first == 0  # committed manifest is already backfilled


def test_gate_blocks_unverified_licence():
    with pytest.raises(PublishBlocked):
        assert_publishable({"dataset_key": "x", "access": "public", "licence": {"redistribution": None}})
    with pytest.raises(PublishBlocked):
        assert_publishable({"dataset_key": "x", "access": "public"})


def test_gate_allows_verified_public_dataset():
    assert_publishable({"dataset_key": "x", "access": "public",
                        "licence": {"name": "CC-BY-4.0", "attribution": "Example", "redistribution": True}})


def test_gate_blocks_private_and_missing_attribution():
    with pytest.raises(PublishBlocked):
        assert_publishable({"dataset_key": "x", "access": "private",
                            "licence": {"name": "CC-BY-4.0", "attribution": "A", "redistribution": True}})
    with pytest.raises(PublishBlocked):
        assert_publishable({"dataset_key": "x", "access": "public",
                            "licence": {"name": "CC-BY-4.0", "attribution": None, "redistribution": True}})


@pytest.mark.parametrize("name", [".env", "config/.env.local", "creds/credentials.json",
                                  "application_default_credentials.json", "k/service_account_a.json", "a.pem",
                                  "audit_logs/telemetry_latest.json"])
def test_gate_blocks_secret_like_names(name):
    with pytest.raises(PublishBlocked):
        assert_safe_object_name(name)


def test_gate_allows_normal_names():
    assert_safe_object_name("raster/hydrosheds/au_acc_3s.tif")


def test_gcs_uri_and_prefix_helpers():
    uri = sync.gcs_uri_from_https(f"https://storage.googleapis.com/{sync.BUCKET}/potree/pc/cloud.js")
    assert uri == f"gs://{sync.BUCKET}/potree/pc/cloud.js"
    assert sync.gcs_prefix_for(uri) == "potree/pc/"
    assert sync.gcs_prefix_for(f"gs://{sync.BUCKET}/a/b.copc.laz") == "a/b.copc.laz"
    assert sync.gcs_uri_from_https("https://example.com/x") is None


def test_reconcile_gcs_reports_present_missing_orphans():
    m = {"datasets": {
        "a": {"locations": {"gcs": {"uri": "gs://b/a/cloud.js", "present": None}}},
        "b": {"locations": {"gcs": {"uri": "gs://b/nothing/file.tif", "present": None}}},
    }}
    objs = [{"name": "a/cloud.js", "size": 10, "updated": "2026-01-01"},
            {"name": "a/data/0.bin", "size": 20, "updated": "2026-02-01"},
            {"name": "stray/x/y.txt", "size": 5, "updated": "2026-01-01"}]
    rep = sync.reconcile_gcs(m, objs)
    assert rep["present"] == ["a"] and rep["missing"] == ["b"]
    assert rep["orphans"] == {"stray/x/y.txt": 1}
    assert m["datasets"]["a"]["locations"]["gcs"]["bytes"] == 30
    assert m["datasets"]["b"]["locations"]["gcs"]["present"] is False


def test_reconcile_wherobots_reports_present_missing_orphans():
    m = {"datasets": {
        "a": {"locations": {"wherobots": {"uri": "wherobots://fgsdb/aura_siting/t_a", "present": None, "snapshot_id": None}}},
        "b": {"locations": {"wherobots": {"uri": "wherobots://fgsdb/aura_siting/t_b", "present": None, "snapshot_id": None}}},
    }}
    rep = sync.reconcile_wherobots(m, [{"name": "t_a", "snapshot_id": "123"}, {"name": "t_extra"}])
    assert rep["present"] == ["a"] and rep["missing"] == ["b"] and rep["orphans"] == ["t_extra"]
    assert m["datasets"]["a"]["locations"]["wherobots"]["snapshot_id"] == "123"

