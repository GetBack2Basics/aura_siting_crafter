import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def check_links():
    broken = []
    checked = 0
    for root, _, files in os.walk(BASE_DIR):
        if any(ig in root for ig in ['.venv', 'node_modules', '.git', '.pytest_cache', 'brain', 'archive', 'docs/archive', 'docs\\archive']):
            continue
        for f in files:
            if f.endswith('.html'):
                p = Path(root) / f
                with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                    for line_num, line in enumerate(fh, 1):
                        for href in re.findall(r'href=["\']([^"\']+)["\']', line):
                            if href.startswith(('http://', 'https://', '#', 'javascript:', 'mailto:', 'tel:', 'data:', '${')):
                                continue
                            clean = href.split('?')[0].split('#')[0]
                            if not clean or '${' in clean:
                                continue
                            checked += 1
                            target = (p.parent / clean).resolve()
                            if not target.exists():
                                broken.append((str(p.relative_to(BASE_DIR)), line_num, href, str(target)))

    print(f"Total checked links: {checked}")
    print(f"Total broken local links: {len(broken)}")
    for src, line_num, href, tgt in broken:
        print(f"  {src}:{line_num} -> {href}\n    (Resolved to: {tgt})")

if __name__ == '__main__':
    check_links()
