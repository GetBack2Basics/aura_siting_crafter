"""Contract tests for the GeoLibre QA inspector page, layer registry, and parts index builder."""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

import build_parts_index  # noqa: E402
import stage_job_context  # noqa: E402


def _read(rel_path: str) -> str:
    with open(os.path.join(BASE_DIR, *rel_path.split("/")), encoding="utf-8") as f:
        return f.read()


def test_qa_page_uses_maplibre_and_real_where_filter():
    html = _read("src/geolibre_frontend/docs/qa/geolibre_qa_inspect.html")
    assert "maplibre-gl.js" in html
    assert "new maplibregl.Map(" in html
    assert "geotiff" in html
    for forbidden in ("leaflet.js", "leaflet.css", "L.map(", "L.markerClusterGroup(", "loadedFeatures.length / 2"):
        assert forbidden not in html, f"forbidden legacy token in QA page: {forbidden}"
    assert "qaCompileWhere(" in html
    assert "activeFilterPredicate" in html


def test_qa_layer_registry_exposes_controls_and_filter_compiler():
    js = _read("src/geolibre_frontend/js/geolibre-qa-layer-registry.js")
    for fn in (
        "function qaCompileWhere(",
        "function qaLoadVisibleParts(",
        "function qaRestackLayers(",
        "function qaMoveCard(",
        "function qaToggleLayerPanel(",
        "function qaInitPanelDrag(",
        "wfs_type_name",
    ):
        assert fn in js, f"missing expected symbol in geolibre-qa-layer-registry.js: {fn}"


def test_frontend_manifest_matches_root_and_has_wfs_type_names():
    root = json.loads(_read("config/dataset_manifest_v2.json"))
    front = json.loads(_read("src/geolibre_frontend/config/dataset_manifest_v2.json"))
    assert root == front
    wfs_entries = [e for e in root["datasets"].values() if e.get("service_type") == "geoserver_wfs"]
    assert len(wfs_entries) >= 5
    for entry in wfs_entries:
        assert entry.get("wfs_type_name"), f"{entry['dataset_key']} missing wfs_type_name"


class _FakeBlob:
    def __init__(self, name: str, size: int = 1024, text: str = ""):
        self.name = name
        self.size = size
        self._text = text

    def download_as_text(self) -> str:
        return self._text


class _FakeClient:
    def __init__(self, blobs):
        self._blobs = blobs

    def list_blobs(self, _bucket, prefix="", match_glob=None):
        out = [b for b in self._blobs if b.name.startswith(prefix)]
        if match_glob and match_glob.endswith("/legend.json"):
            out = [b for b in out if b.name.endswith("/legend.json")]
        return out


def test_build_parts_index_registers_regional_and_national_parts():
    legend_doc = json.dumps({
        "zooms": "8-12",
        "tiles_url_template": "https://storage.googleapis.com/test-bucket/tiles/hydrosheds_au_acc_3s_v1/hunter/{z}/{x}/{y}.png",
    })
    client = _FakeClient([
        _FakeBlob("processed/hydrosheds_au_acc_3s_v1/regions/hunter/au_acc_3s.tif", size=247514),
        _FakeBlob("processed/hydrosheds_au_acc_3s_v1/au_acc_3s.tif", size=999999),
        _FakeBlob("processed/hydrosheds_au_acc_3s_v1/regions/unknown_reg/au_acc_3s.tif", size=123),
        _FakeBlob("tiles/hydrosheds_au_acc_3s_v1/hunter/legend.json", text=legend_doc),
    ])
    indexes = build_parts_index.build(
        client,
        keys=["hydrosheds_au_acc_3s_v1", "aura_drainage_slope_deg_v1"],
        base_dir=BASE_DIR,
        bucket="test-bucket",
    )
    assert "aura_drainage_slope_deg_v1" not in indexes
    idx = indexes["hydrosheds_au_acc_3s_v1"]
    assert idx["part_count"] == 2
    by_id = {p["id"]: p for p in idx["parts"]}
    assert set(by_id) == {"hunter", "national"}
    assert by_id["hunter"]["cog_bytes"] == 247514
    assert by_id["hunter"]["minzoom"] == 8 and by_id["hunter"]["maxzoom"] == 12
    assert by_id["hunter"]["tiles_url_template"].endswith("/{z}/{x}/{y}.png")
    assert by_id["national"]["bbox"] == build_parts_index.NATIONAL_BBOX
    assert any("unknown_reg" in s for s in idx["skipped"])


def test_stage_job_context_includes_parts_index_builder():
    for job in ("hydrosheds_ingest", "hydrosheds_derive"):
        dest = stage_job_context.stage(job)
        assert os.path.isfile(os.path.join(dest, "build_parts_index.py"))
        assert os.path.isfile(os.path.join(dest, "publish_gate.py"))
        assert os.path.isfile(os.path.join(dest, "dataset_manifest_v2.json"))


def test_qa_report_pages_include_all_manifest_datasets_and_autopopulate():
    manifest = json.loads(_read("config/dataset_manifest_v2.json"))["datasets"]
    rel = "src/geolibre_frontend/docs/qa/index.html"
    html = _read(rel)
    assert "autopopulateFromManifest" in html
    for key in manifest:
        assert f"geolibre_qa_inspect.html?dataset={key}" in html, f"{rel} missing link for {key}"
    assert not os.path.exists(os.path.join(BASE_DIR, "src", "geolibre_frontend", "data_qa.html"))


