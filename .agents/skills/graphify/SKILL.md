---
name: graphify-aura
description: Run AST dependency analysis on aura_siting_crafter to map all imports, SQL table references, secret patterns, and place-name hits before any refactoring session.
---
# Graphify Analysis Skill

Run this at the start of any refactoring or onboarding session:

```bash
python tools/graphify_analysis.py
```

Output:
- Files with place-name references and hit counts
- Exposed credential patterns
- SQL table names referenced per file
- Cross-file import dependencies
- `_cfg()` call sites

Use the output as the checklist before and after modifications.
