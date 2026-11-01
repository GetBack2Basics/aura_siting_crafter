# LinkedIn Article: Contributing to GeoLibre — Lessons Learned & Upstream Playbook

**Target Audience:** Geospatial Engineers, Open Source Contributors, AI Developers  
**Target Platform:** LinkedIn  
**Character Count:** 1,479 characters (including spaces and URLs)  

---

## Article Text

Our upstream contribution to GeoLibre (@geolibre/layer-limiter) was just merged into main and released in v3.6.0!

Engineered for AURA Siting Crafter (https://aura.getback2basics.net) to sustain 60 FPS across 50k+ parcels via an O(M log K) Min-Heap, this PR taught us vital lessons on contributing to large monorepos with AI coding agents.

To help other contributors, we documented our review learnings into an open Playbook:

1. Test Typecheck Ratchet: Node's native runner (node --test) strips types at runtime. A test can pass while failing CI's typecheck gate (npm run typecheck:tests). Always run the ratchet locally!
2. Async Teardown: If a controller debounces events, disable() MUST cancel pending timers (clearTimeout) and apply() must guard at entry to prevent race overwrites.
3. Spatial Precision: Measure Shoelace polygon math relative to the first vertex to prevent float cancellation, subtract hole rings, and test antimeridian wrapping (+-360 deg).
4. Token Efficiency: Don't burn LLM context on polling or sandbox retries. Programmatically dispatch GitHub forks, RFC issues, and PRs via host credentials.

Explore the contribution & playbook:
Merged PR: https://github.com/opengeos/GeoLibre/pull/3293
Playbook: https://github.com/GetBack2Basics/aura_siting_crafter/blob/main/docs/engineering/geolibre_antigravity_contribution_playbook.md
Source: https://github.com/GetBack2Basics/aura_siting_crafter

#OpenSource #GeoLibre #WebGIS #TypeScript #DevOps #SpatialAI
