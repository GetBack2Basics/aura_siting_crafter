"""
Lint Test: Zero-Mock & Anti-Placeholder Enforcement Gate
Prevents AI agents and developers from introducing hardcoded mock data, synthetic coordinate arrays,
or placeholder dataset counts into source files.
"""

import os
import re
import glob
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# File patterns to audit
AUDIT_DIRS = [
    os.path.join(BASE_DIR, "docs", "qa", "*.html"),
    os.path.join(BASE_DIR, "src", "**", "*.html"),
    os.path.join(BASE_DIR, "src", "**", "*.js"),
    os.path.join(BASE_DIR, "src", "**", "*.py"),
    os.path.join(BASE_DIR, "tools", "*.py"),
]

# Patterns that indicate synthetic / mocked data
FORBIDDEN_PATTERNS = [
    (r"sampleFeatures\s*=\s*\[", "Hardcoded sample features array (sampleFeatures = [...])"),
    (r"mock_data\s*=\s*", "Explicit mock data variable (mock_data = ...)"),
    (r"dummy_records\s*=\s*", "Dummy records variable"),
    (r"placeholder_count\s*=\s*", "Placeholder record count"),
    (r"\[\s*\[\s*151\.\d+\s*,\s*-33\.\d+\s*\]\s*,\s*\[\s*151\.\d+\s*,\s*-33\.\d+\s*\]", "Hardcoded synthetic Sydney coordinates in general templates"),
]

def get_files_to_audit():
    files = []
    for pattern in AUDIT_DIRS:
        files.extend(glob.glob(pattern, recursive=True))
    return sorted(list(set(files)))

@pytest.mark.parametrize("filepath", get_files_to_audit())
def test_no_mock_or_placeholder_data_in_file(filepath):
    """Asserts that no audited source file contains forbidden mock or synthetic data patterns."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    rel_path = os.path.relpath(filepath, BASE_DIR)
    
    for pattern, description in FORBIDDEN_PATTERNS:
        match = re.search(pattern, content)
        assert not match, f"Zero-Mock Violation in {rel_path}: Found {description} (Match: '{match.group(0) if match else ''}')"
