# LinkedIn Article: Contributing to GeoLibre — Lessons Learned & Upstream Playbook

**Target Audience:** Geospatial Engineers, Open Source Contributors, AI Developers  
**Target Platform:** LinkedIn  
**Post Body Length:** 1,495 characters (under 1,500-character ceiling, zero in-post external URLs)  
**Style Standard:** First-person singular ("I"), provocative opening hook, ELI10 explanation, links placed in the first comment.  

---

## Main Post Body (Copy & Paste to LinkedIn)

Why do modern WebGIS maps still freeze and drop to 10 FPS the moment you look at a real-world city?

Because browsers choke trying to render 50,000 microscopic polygon slivers at once.

My contribution to GeoLibre (@geolibre/layer-limiter) was just merged into main and released in v3.6.0 to fix this.

ELI10: Imagine a 50,000-piece puzzle. Trying to look at every tiny speck of dust at once freezes your brain. My tool tells the map: 'Just pick the biggest, most important shapes in view and draw those first!' The map stays silky-smooth (60 FPS) and lag-free.

I built this for AURA Siting Crafter to map parcels across Australia. Contributing upstream taught me vital lessons on pairing with AI on open-source monorepos, which I turned into a Playbook:

1. Test Typecheck Ratchet: Node's runner (node --test) strips types at runtime. A test can pass while failing CI's typecheck gate (npm run typecheck:tests). I now always verify this locally!
2. Async Teardown: If a controller debounces panning, disable() must clear pending timers so delayed callbacks don't overwrite restored data.
3. Coordinate Math: For polygon area math, I measure relative to vertex 0 to prevent float errors, subtract holes, and test antimeridian wrapping.
4. Token Efficiency: I dispatch forks, RFCs, and PRs via host credentials in one shot instead of wasting AI tokens on retries.

👇 Links to the merged PR, live map, and open Playbook are in the first comment!

#OpenSource #GeoLibre #WebGIS #TypeScript #DevOps

---

## First Comment (Post Immediately After Publishing)

🔗 Here are the links referenced in the post:

• Merged Pull Request: https://github.com/opengeos/GeoLibre/pull/3293
• RFC Issue: https://github.com/opengeos/GeoLibre/issues/3292
• Upstream Contribution Playbook: https://github.com/GetBack2Basics/aura_siting_crafter/blob/main/docs/engineering/geolibre_antigravity_contribution_playbook.md
• Live Australian Siting Map (Showcase): https://aura.getback2basics.net
• Repository: https://github.com/GetBack2Basics/aura_siting_crafter
