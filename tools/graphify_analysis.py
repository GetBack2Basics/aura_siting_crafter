#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graphify AST & Security analysis for aura_siting_crafter.
"""
import sys, io, ast, os, re, json, pathlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = pathlib.Path(__file__).resolve().parent.parent
BANNED_TERMS = ["hunter_spatial_crafter"]
SECRET_PATTERNS = [
    r"wbk_user_[a-zA-Z0-9]+",
    r"0mpjf[a-zA-Z0-9]+",
    r"ltq5l3[a-zA-Z0-9]+",
]
SQL_TABLE_RE = re.compile(r"org_catalog\.fgsdb\.([\w]+)")
IMPORT_RE    = re.compile(r"(?:from|import)\s+(src\.[^\s;,]+)")

report = {
    "imports": {},
    "banned_refs": {},
    "sql_tables": {},
    "secrets": {},
    "summary": {}
}

def should_skip(p):
    parts = p.parts
    return any(x in parts for x in [".venv", "__pycache__", ".git", "scratch", ".pytest_cache"])

all_text_files = []
for ext, ftype in [("*.py", "py"), ("*.html", "html"), ("*.ipynb", "ipynb"), ("*.json", "json"), ("*.md", "md")]:
    for p in ROOT.rglob(ext):
        if not should_skip(p):
            all_text_files.append((p, ftype))

for filepath, ftype in all_text_files:
    rel = str(filepath.relative_to(ROOT))
    if rel.startswith("docs" + os.sep + "dphi_"):
        continue  # historical formal submission context
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    lines = text.splitlines()

    banned_hits = []
    for i, line in enumerate(lines, 1):
        for term in BANNED_TERMS:
            if term in line.lower():
                banned_hits.append(f"L{i}: {line.strip()[:120]}")
                break
    if banned_hits:
        report["banned_refs"][rel] = banned_hits

    secret_hits = []
    for i, line in enumerate(lines, 1):
        for pat in SECRET_PATTERNS:
            if re.search(pat, line):
                secret_hits.append(f"L{i}: {line.strip()[:120]}")
                break
    if secret_hits:
        report["secrets"][rel] = secret_hits

    sql_tables = SQL_TABLE_RE.findall(text)
    if sql_tables:
        report["sql_tables"][rel] = sorted(set(sql_tables))

    imports = IMPORT_RE.findall(text)
    if imports:
        report["imports"][rel] = sorted(set(imports))

print("=" * 70)
print("GRAPHIFY ANALYSIS - aura_siting_crafter")
print("=" * 70)

print(f"\n[SECRETS DETECTED]: {len(report['secrets'])}")
for f, hits in report["secrets"].items():
    print(f"  {f}: {len(hits)} hits")

print(f"\n[BANNED REPO REFERENCES]: {len(report['banned_refs'])}")
for f, hits in report["banned_refs"].items():
    print(f"  {f}: {len(hits)} hits")

print(f"\n[SQL TABLES REFERENCED]:")
unique_tables = set(t for tbls in report["sql_tables"].values() for t in tbls)
for t in sorted(unique_tables):
    print(f"  - {t}")

print(f"\n[IMPORTS FROM src/]:")
for f, imps in report["imports"].items():
    print(f"  {f} -> {imps}")

print("=" * 70)
