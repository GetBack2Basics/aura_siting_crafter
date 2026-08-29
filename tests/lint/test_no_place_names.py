import pathlib, pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BANNED_TERMS = ["hunter_spatial_crafter"]

def get_source_files():
    files = []
    target_dirs = ["src", "config", "runner", "notebooks"]
    for td in target_dirs:
        dir_path = ROOT / td
        if dir_path.exists():
            for ext in ["*.py", "*.html", "*.json"]:
                for p in dir_path.rglob(ext):
                    parts = p.parts
                    if not any(x in parts for x in [".venv", "__pycache__", ".git", ".pytest_cache"]):
                        files.append(p)
    return files

@pytest.mark.parametrize("filepath", get_source_files())
def test_no_banned_repo_names(filepath):
    text = filepath.read_text(encoding="utf-8", errors="ignore")
    for term in BANNED_TERMS:
        assert term not in text, f"Banned repo name '{term}' found in {filepath.relative_to(ROOT)}"
