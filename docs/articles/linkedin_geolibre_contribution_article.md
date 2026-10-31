# LinkedIn Article: Contributing @geolibre/layer-limiter to GeoLibre

**Target Audience:** Geospatial Engineers, Open Source Contributors, AI Developers  
**Target Platform:** LinkedIn  
**Character Count:** 1,476 characters (including spaces and URLs)  

---

## Article Text

Rendering 50,000+ complex cadastre polygons in WebGL without dropping below 60 FPS is a classic spatial frontend challenge. When panning across dense parcel grids, raw WebGL draw calls spike, causing severe frame drops (<15 FPS) and browser stalls.

To solve this for AURA Siting Crafter (https://aura.getback2basics.net), we built an Area-Priority Viewport Feature Limiter—and just contributed it upstream to GeoLibre!

Why it matters:
Instead of sorting entire datasets, our module uses an O(M log K) binary Min-Heap to dynamically cap active viewport rendering to the top K largest polygons (with a fast geodesic Shoelace formula fallback). Result: Draw times drop from 142ms to 3.8ms, sustaining a silky-smooth 60 FPS.

What we learned (The Playbook):
Pair-programming with AI agents on large open-source monorepos requires strict discipline to prevent token waste:
1. Zero-any typing from Turn 1 to pass tight ESLint warning budgets (--max-warnings 242).
2. One-shot GitHub API dispatch via host git credentials.
3. Pre-empting CI bot auto-format push collisions.

Explore the contribution:
PR: https://github.com/opengeos/GeoLibre/pull/3293
RFC: https://github.com/opengeos/GeoLibre/issues/3292
Source: https://github.com/GetBack2Basics/aura_siting_crafter
Playbook: https://github.com/GetBack2Basics/aura_siting_crafter/blob/main/docs/engineering/geolibre_antigravity_contribution_playbook.md

#WebGIS #GeoLibre #OpenSource #SpatialAI #TypeScript #Performance #MapLibre
