"""
Pytest Test Suite: Release Reports & HTML Integrity Gate
Executes automated auditing of all generated HTML reports, frontend assets, and summary cards.
"""

import os
import pytest
from tools.verify_all_release_reports import (
    get_all_target_html_files,
    get_known_dataset_keys,
    audit_html_file,
    BASE_DIR
)

TARGET_FILES = get_all_target_html_files()
KNOWN_KEYS = get_known_dataset_keys()

@pytest.mark.parametrize("filepath", TARGET_FILES)
def test_report_html_integrity(filepath):
    """Asserts that each generated HTML report complies 100% with zero-mock, integer pct, and card integrity rules."""
    rel_path = os.path.relpath(filepath, BASE_DIR)
    is_ok, errors = audit_html_file(filepath, KNOWN_KEYS)
    assert is_ok, f"Pre-Release Report Integrity Failed in {rel_path}:\n" + "\n".join(f" - {e}" for e in errors)
