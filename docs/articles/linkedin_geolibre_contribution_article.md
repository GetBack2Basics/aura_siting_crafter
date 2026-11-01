# LinkedIn Article: Contributing to GeoLibre — Lessons Learned & Upstream Playbook

**Target Audience:** Geospatial Engineers, Open Source Contributors, AI Developers  
**Target Platform:** LinkedIn  
**Character Count:** 1,474 characters (including spaces and URLs)  

---

## Article Text

My contribution to GeoLibre (@geolibre/layer-limiter) was just merged into main and released in v3.6.0!

ELI10: Imagine a giant puzzle with 50,000 tiny pieces. If your browser tries to draw every grain of sand all at once, it freezes. My module tells the map: 'Just pick the biggest, most important shapes in view and draw those first!' The map stays silky-smooth (60 FPS) and lag-free.

I built this for AURA Siting Crafter (https://aura.getback2basics.net) to map land parcels across Australia. Contributing upstream taught me vital lessons on pairing with AI on large monorepos, which I turned into a Playbook:

1. Test Typecheck Ratchet: Node's native runner (node --test) strips types at runtime. A test can pass while failing CI's typecheck gate (npm run typecheck:tests). I now always check this locally!
2. Async Teardown: If a controller debounces panning, disable() must clear pending timers so delayed callbacks don't overwrite restored data.
3. Coordinate Math: For polygon area math, I measure relative to vertex 0 to prevent float errors, subtract holes, and test antimeridian wrapping.
4. Token Efficiency: I dispatch forks, RFCs, and PRs via host credentials in one shot instead of wasting AI tokens on retries.

Merged PR: https://github.com/opengeos/GeoLibre/pull/3293
Playbook: https://github.com/GetBack2Basics/aura_siting_crafter/blob/main/docs/engineering/geolibre_antigravity_contribution_playbook.md

#OpenSource #GeoLibre #WebGIS #TypeScript #DevOps
