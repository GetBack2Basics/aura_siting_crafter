import re, pathlib, pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SECRET_PATTERNS = [
    r"wbk_user_[a-zA-Z0-9]+",
    r"0mpjf[a-zA-Z0-9]+",
    r"ltq5l3[a-zA-Z0-9]+",
]

def get_files():
    files = []
    for ext in ["*.py", "*.html", "*.json", "*.md"]:
        for p in ROOT.rglob(ext):
            parts = p.parts
            if not any(x in parts for x in [".venv", "__pycache__", ".git", ".pytest_cache"]):
                files.append(p)
    return files

@pytest.mark.parametrize("filepath", get_files())
def test_no_secrets_in_file(filepath):
    text = filepath.read_text(encoding="utf-8", errors="ignore")
    for pat in SECRET_PATTERNS:
        match = re.search(pat, text)
        assert not match, f"Secret pattern '{pat}' detected in {filepath.relative_to(ROOT)}: {match.group(0)}"
