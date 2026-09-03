import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

def check_all_links():
    broken = []
    for root, _, files in os.walk(BASE):
        if any(k in root for k in ['.venv', 'node_modules', '.git', '.pytest_cache', 'brain']):
            continue
        for f in files:
            if f.endswith('.html'):
                p = Path(root) / f
                content = p.read_text(encoding='utf-8', errors='ignore')
                for href in re.findall(r'href=["\']([^"\']+)["\']', content):
                    if href.startswith(('http://', 'https://', '#', 'javascript:', 'mailto:', 'tel:', 'data:')):
                        continue
                    clean = href.split('?')[0].split('#')[0]
                    if not clean:
                        continue
                    target = (p.parent / clean).resolve()
                    if not target.exists():
                        broken.append((p.relative_to(BASE), href, clean))
    return broken

if __name__ == '__main__':
    broken = check_all_links()
    print(f"Found {len(broken)} broken relative link occurrences:")
    for src, href, clean in broken:
        print(f"  {src} -> {href}")
