/* dashboard_provenance.js — authoritative source for __PROVENANCE_JS__
 *
 * Measured vs modeled provenance helpers (PR #2, 2026-08-28).
 *
 * candidatesData now carries an `is_simulated` boolean field set upstream
 * in runner/attachments/candidates.json, so classification is a field read —
 * not an id-prefix inference.
 *
 *   is_simulated === false  →  micro-sited (measured against cadastral,
 *                              slope and setback ground truth)
 *   is_simulated === true   →  modeled regional comparator
 *
 * Aggregate rows (state/region tables) have no candidate id, so they DERIVE
 * from this helper rather than testing state names separately — one rule,
 * so a micro-sited site outside NSW can never desync the surfaces.
 */

function isMicroSited(c) {
  return c != null && c.is_simulated === false;
}

/* Cache of which state_name / region_name groups contain at least one
 * micro-sited candidate, so simulatedGroupTag() can tag pure-baseline groups. */
var _microSitedGroupCache = new Map();
function groupsWithMicroSited(key) {
  var cached = _microSitedGroupCache.get(key);
  if (cached) return cached;
  var out = new Set();
  candidatesData.forEach(function (c) {
    if (isMicroSited(c) && c[key] != null) out.add(c[key]);
  });
  _microSitedGroupCache.set(key, out);
  return out;
}
function isAllSimulatedGroup(value, key) {
  return !groupsWithMicroSited(key).has(value);
}

/* Renders a pill badge for an individual candidate row/popup/panel.
 * size: 'sm' for leaderboard rows, default for panels and popups. */
function provenanceBadge(c, size) {
  var micro = isMicroSited(c);
  var fs = size === 'sm' ? '0.62rem' : '0.7rem';
  return '<span title="' + (micro
      ? 'Micro-sited: measured against cadastral, slope and setback ground truth.'
      : 'Simulated baseline: a modeled regional comparator, not a measured site assessment.') +
    '" style="display:inline-block;margin-top:3px;padding:1px 6px;border-radius:999px;font-size:' + fs +
    ';font-weight:700;letter-spacing:0.04em;white-space:nowrap;' +
    (micro ? 'background:rgba(52,211,153,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.45);'
           : 'background:rgba(251,191,36,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.45);') +
    '">' + (micro ? 'MICRO-SITED' : 'SIMULATED BASELINE') + '</span>';
}

/* Renders a compact SIMULATED pill for state/region aggregate table rows
 * where every candidate in that group is a modeled baseline.
 * Returns empty string for groups that contain at least one micro-sited site. */
function simulatedGroupTag(value, key, title) {
  if (!isAllSimulatedGroup(value, key)) return '';
  return ' <span title="' + title + '" style="display:inline-block;padding:1px 6px;border-radius:999px;' +
    'font-size:0.6rem;font-weight:700;background:rgba(251,191,36,0.15);color:#fbbf24;' +
    'border:1px solid rgba(251,191,36,0.45);white-space:nowrap;">SIMULATED</span>';
}
