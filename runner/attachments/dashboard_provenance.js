/* dashboard_provenance.js — authoritative source for __PROVENANCE_JS__
 *
 * Measured vs modeled provenance helpers (PR #2, 2026-08-28; Updated 2026-09-03).
 *
 * candidatesData carries an `is_simulated` boolean field set upstream
 * in runner/attachments/candidates.json:
 *
 *   is_simulated === false  →  micro-sited (measured against authoritative national/state
 *                              cadastral, infrastructure, and multi-hazard ground truth)
 *   is_simulated === true   →  modeled regional baseline / comparator where localized data is pending
 *
 * LMCC proposal sites carry project_id === 'LMCC_MacquarieCoal' or mb_code21 === 'NSW_MCC01'
 * or town_name === 'Teralba'.
 */

function isMicroSited(c) {
  return c != null && c.is_simulated === false;
}

function isEnhancedProject(c) {
  return c != null && (
    c.project_id === 'LMCC_MacquarieCoal' || 
    c.site_id === 'AURA-NSW-0001' || 
    c.mb_code21 === 'NSW_MCC01' || 
    (c.town_name === 'Teralba' && c.state_name === 'New South Wales')
  );
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

/* Renders a badge for an individual candidate row/popup/panel.
 * Only the LMCC proposal site receives the 'Enhanced Report' badge linking to the Site WebGIS App.
 * size: 'sm' for leaderboard rows, default for panels and popups. */
function provenanceBadge(c, size) {
  var fs = size === 'sm' ? '0.62rem' : '0.7rem';
  if (isEnhancedProject(c)) {
    var appUrl = (c && c.project_app_url) ? c.project_app_url : 'projects/index_LMCC_MacquarieCoal.html';
    return '<a href="' + appUrl + '" target="_blank" onclick="event.stopPropagation();" title="LMCC Transformation Precinct Proposal — Click to view Site WebGIS" style="display:inline-flex;align-items:center;gap:3px;margin-top:3px;padding:2px 8px;border-radius:999px;font-size:' + fs + ';font-weight:700;letter-spacing:0.04em;white-space:nowrap;background:linear-gradient(135deg, rgba(34,197,94,0.25) 0%, rgba(2,132,199,0.25) 100%);color:#38bdf8;border:1px solid rgba(56,189,248,0.6);box-shadow:0 0 8px rgba(56,189,248,0.25);text-decoration:none;cursor:pointer;">✨ Enhanced Report ↗</a>';
  }
  if (isMicroSited(c)) {
    return '<span title="Micro-sited: measured against verified national infrastructure, state cadastre, elevation, and environmental setback ground truth." style="display:inline-block;margin-top:3px;padding:1px 6px;border-radius:999px;font-size:' + fs + ';font-weight:700;letter-spacing:0.04em;white-space:nowrap;background:rgba(52,211,153,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.45);">MICRO-SITED</span>';
  }
  return '<span title="Simulated baseline: modeled regional comparator used where localized site cadastre is pending." style="display:inline-block;margin-top:3px;padding:1px 6px;border-radius:999px;font-size:' + fs + ';font-weight:700;letter-spacing:0.04em;white-space:nowrap;background:rgba(251,191,36,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.45);">SIMULATED BASELINE</span>';
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
