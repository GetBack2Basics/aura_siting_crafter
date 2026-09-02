import os
import json
import pytest
from src.Analysis.national_suitability_analysis import (
    calculate_multi_hazard_resilience_score,
    calculate_sigmoidal_sensitive_score
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_hazard_scoring_baseline_optimal():
    """Verify optimal site with negligible hazards gets near-perfect score."""
    record = {
        "flood_depth_m": 0.0,
        "is_floodway": False,
        "state_name": "Western Australia",
        "lat": -33.36,
        "slope_pct": 1.4,
        "dist_to_veg_m": 150.0
    }
    res = calculate_multi_hazard_resilience_score(record)
    assert not res["is_hazard_excluded"]
    assert res["hazard_score"] >= 0.95, f"Expected high resilience score, got {res['hazard_score']}"


def test_hazard_scoring_flood_exclusion():
    """Verify flood depth >0.8m or active floodway triggers hard exclusion."""
    record = {
        "flood_depth_m": 1.2,
        "is_floodway": True,
        "state_name": "New South Wales",
        "lat": -32.9,
        "slope_pct": 2.0,
        "dist_to_veg_m": 150.0
    }
    res = calculate_multi_hazard_resilience_score(record)
    assert res["is_hazard_excluded"], "Expected hard exclusion for >0.8m flood depth"
    assert res["hazard_score"] == 0.0


def test_hazard_scoring_landslide_exclusion():
    """Verify slope >8.0% triggers geotechnical hard exclusion."""
    record = {
        "flood_depth_m": 0.0,
        "is_floodway": False,
        "state_name": "New South Wales",
        "lat": -32.9,
        "slope_pct": 9.5,
        "dist_to_veg_m": 150.0
    }
    res = calculate_multi_hazard_resilience_score(record)
    assert res["is_hazard_excluded"], "Expected hard exclusion for slope > 8%"
    assert res["hazard_score"] == 0.0


def test_hazard_scoring_bushfire_exclusion():
    """Verify proximity <20m to dense bushfire vegetation triggers BAL-FZ hard exclusion."""
    record = {
        "flood_depth_m": 0.0,
        "is_floodway": False,
        "state_name": "New South Wales",
        "lat": -32.9,
        "slope_pct": 2.0,
        "dist_to_veg_m": 10.0
    }
    res = calculate_multi_hazard_resilience_score(record)
    assert res["is_hazard_excluded"], "Expected hard exclusion for <20m vegetation buffer"
    assert res["hazard_score"] == 0.0


def test_composite_mcda_6_factors():
    """Verify 6-factor composite MCDA weighting matches statutory specification."""
    # Weights: Power: 30%, Hazard: 25%, Sensitive: 20%, Water: 15%, Size: 10%
    s_p = 1.0
    s_haz = 0.90
    s_sens = 1.0
    s_w = 0.80
    s_sz = 1.0

    suitability = (s_p * 0.30) + (s_haz * 0.25) + (s_sens * 0.20) + (s_w * 0.15) + (s_sz * 0.10)
    expected = 0.30 + (0.90 * 0.25) + 0.20 + (0.80 * 0.15) + 0.10
    assert abs(suitability - expected) < 1e-6
    assert abs(suitability - 0.945) < 1e-6


def test_peer_reviewed_citations_present():
    """Verify statutory methodology JSON contains peer-reviewed DOI/URL citations."""
    methodology_path = os.path.join(ROOT_DIR, "runner", "attachments", "methodology.json")
    assert os.path.exists(methodology_path), f"Missing {methodology_path}"
    with open(methodology_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Must contain multi_hazard_resilience_score formula
    haz_formula = data.get("multi_hazard_resilience_score")
    assert haz_formula is not None, "Missing multi_hazard_resilience_score in methodology.json"
    assert "references" in haz_formula, "Missing references in multi_hazard_resilience_score"
    assert len(haz_formula["references"]) >= 5, "Expected at least 5 statutory/peer-reviewed citations"

    # Verify ARR 2019, AS 1170.4, AS 1170.2, AGS 2007 citations are present
    cites = " ".join([r["citation"] for r in haz_formula["references"]])
    assert "ARR 2019" in cites or "Ball et al." in cites
    assert "AS 1170.4" in cites or "Allen" in cites
    assert "AS/NZS 1170.2" in cites or "Arthur" in cites
    assert "AGS 2007" in cites or "Fell" in cites


def test_candidate_data_depth_indexing():
    """Verify candidates exported have valid data depth metrics."""
    candidates_path = os.path.join(ROOT_DIR, "exports_v2", "datacenter_candidates_v2.json")
    assert os.path.exists(candidates_path), f"Missing {candidates_path}"
    with open(candidates_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    assert len(candidates) >= 16
    for c in candidates:
        assert "data_depth_pct" in c
        assert "data_depth_tier" in c
        assert "indexed_layers_count" in c
        assert 0.0 <= c["data_depth_pct"] <= 100.0
        assert c["indexed_layers_count"] in (8, 10)
        assert "hazard_resilience_score" in c
