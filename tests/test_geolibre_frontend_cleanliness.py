"""
Integration & Architecture Test: GeoLibre Frontend Cleanliness & Structure
Ensures that:
  1. src/geolibre_frontend/ root and projects/ contain only production GIS web assets.
  2. All testbeds, test HTML files, and validation harnesses reside within src/geolibre_frontend/tests/ and tests/frontend/.
  3. All required production 3D engines and viewers exist and are properly structured.
"""

import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "src", "geolibre_frontend")
FRONTEND_TESTS_DIR = os.path.join(FRONTEND_DIR, "tests")
TESTS_FRONTEND_DIR = os.path.join(BASE_DIR, "tests", "frontend")


def test_no_loose_test_pages_in_production_root():
    """Asserts that no test html files exist loose in src/geolibre_frontend or its projects folder."""
    assert os.path.exists(FRONTEND_DIR), "src/geolibre_frontend directory must exist"

    forbidden_filenames = ["cesium_test.html", "cesium_3d_test.html"]
    production_roots = [
        FRONTEND_DIR,
        os.path.join(FRONTEND_DIR, "projects")
    ]

    for prod_dir in production_roots:
        if not os.path.exists(prod_dir):
            continue
        for f in os.listdir(prod_dir):
            full_path = os.path.join(prod_dir, f)
            if os.path.isfile(full_path):
                assert f not in forbidden_filenames, (
                    f"Found loose test file '{f}' in production directory '{prod_dir}'. "
                    f"All testbeds must reside in src/geolibre_frontend/tests/."
                )
                if (f.endswith("_test.html") or f.startswith("test_")) and f != "test.html":
                    raise AssertionError(
                        f"Test file '{f}' found in production directory '{prod_dir}'. "
                        f"Move all test pages to src/geolibre_frontend/tests/."
                    )


def test_test_pages_exist_in_frontend_tests_directories():
    """Asserts that test HTML pages reside in src/geolibre_frontend/tests/ and tests/frontend/."""
    target_dirs = [FRONTEND_TESTS_DIR, TESTS_FRONTEND_DIR]
    expected_test_files = ["cesium_test.html", "cesium_3d_test.html"]

    for d in target_dirs:
        assert os.path.exists(d), f"Test directory '{d}' must exist"
        for tf in expected_test_files:
            path = os.path.join(d, tf)
            assert os.path.exists(path), f"Expected test page '{tf}' missing from {d}"
            assert os.path.getsize(path) > 1000, f"Test page '{tf}' in {d} is empty or invalid"


def test_production_viewers_exist():
    """Asserts that all core production viewers exist in src/geolibre_frontend."""
    required_viewers = [
        "geolibre_cesium_3d_viewer.html",
        "potree_3d_viewer.html",
        "copc_3d_viewer.html",
        "cesium_wireframe_tin.html",
        "map.html",
        "index.html",
        "data_qa.html",
        "data_lineage_audit.html",
    ]
    for v in required_viewers:
        path = os.path.join(FRONTEND_DIR, v)
        assert os.path.exists(path), f"Required production viewer '{v}' missing from {FRONTEND_DIR}"
