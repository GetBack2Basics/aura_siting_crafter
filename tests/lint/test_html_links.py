import os
import re
from pathlib import Path
import pytest
import urllib.request

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Define the canonical deployment mapping of source directories to GCS web root
DEPLOY_MAPPINGS = [
    # (source_dir_relative, gcs_web_prefix)
    ("src/geolibre_frontend", ""),
    ("src/geolibre_frontend/projects", "projects"),
    ("docs", "docs"),
    ("docs/qa", "docs/qa"),
    ("runner", ""),
    ("runner/projects", "projects"),
]

def find_html_files():
    html_files = []
    for root, _, files in os.walk(BASE_DIR):
        if any(ignored in root for virt in ['.venv', 'node_modules', '.git', '.pytest_cache', 'brain'] if (ignored := virt)):
            continue
        for f in files:
            if f.endswith('.html'):
                html_files.append(Path(root) / f)
    return html_files

def resolve_gcs_path(source_file: Path, clean_href: str) -> str:
    """
    Simulates browser URL resolution in the deployed GCS bucket.
    """
    rel_source = source_file.relative_to(BASE_DIR).as_posix()
    
    # Determine the web prefix of this file in the deployed bucket
    web_dir = ""
    for src_dir, prefix in DEPLOY_MAPPINGS:
        if rel_source.startswith(src_dir + "/"):
            remainder = rel_source[len(src_dir) + 1:]
            parent_remainder = "/".join(remainder.split("/")[:-1])
            web_dir = f"{prefix}/{parent_remainder}".strip("/")
            break
        elif rel_source == src_dir or rel_source == f"{src_dir}/{source_file.name}":
            web_dir = prefix
            break

    # Resolve relative href from web_dir
    parts = [p for p in web_dir.split('/') if p]
    for seg in clean_href.split('/'):
        if seg == '.' or not seg:
            continue
        elif seg == '..':
            if parts:
                parts.pop()
        else:
            parts.append(seg)
    return "/".join(parts)

@pytest.mark.parametrize("html_file", find_html_files())
def test_html_internal_links_valid(html_file):
    """
    Verifies that all internal relative links in HTML files resolve to existing files
    locally or mapped in the deployment schema.
    """
    content = html_file.read_text(encoding='utf-8', errors='ignore')
    # Match href="..." attributes (excluding templated ${...} expressions)
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', content)

    for href in hrefs:
        # Ignore external links, anchor targets, javascript, tel/mailto, template literals
        if href.startswith(('http://', 'https://', '#', 'javascript:', 'mailto:', 'tel:', 'data:', '${')):
            continue
        
        # Remove query strings and hashes
        clean_href = href.split('?')[0].split('#')[0]
        if not clean_href or '${' in clean_href:
            continue

        # 1. Direct local file check
        target_path = (html_file.parent / clean_href).resolve()
        if target_path.exists():
            continue

        # 2. Check if it resolves in the deployed GCS bucket structure
        deployed_web_path = resolve_gcs_path(html_file, clean_href)
        
        # Check if deployed_web_path corresponds to any source file in repo
        found_in_deployment = False
        for src_dir, prefix in DEPLOY_MAPPINGS:
            if prefix and deployed_web_path.startswith(prefix + "/"):
                candidate = BASE_DIR / src_dir / deployed_web_path[len(prefix) + 1:]
                if candidate.exists():
                    found_in_deployment = True
                    break
            elif not prefix:
                candidate = BASE_DIR / src_dir / deployed_web_path
                if candidate.exists():
                    found_in_deployment = True
                    break
            
            # Direct root and alias checks
            if (BASE_DIR / deployed_web_path).exists() or (BASE_DIR / 'docs' / deployed_web_path).exists():
                found_in_deployment = True
                break

            # Handle root-level and cross-directory report aliases
            if deployed_web_path.endswith('national_suitability_report.html') and (BASE_DIR / 'runner' / 'national_suitability_report.html').exists():
                found_in_deployment = True
                break
            if deployed_web_path.endswith('QA_Report_20260902.html') and (BASE_DIR / 'docs' / 'qa' / 'QA_Report_20260902.html').exists():
                found_in_deployment = True
                break

        assert found_in_deployment, (
            f"Broken relative link in {html_file.relative_to(BASE_DIR)}: "
            f"href='{href}' (resolved web path: '{deployed_web_path}') does not exist locally or in deployment mapping."
        )
