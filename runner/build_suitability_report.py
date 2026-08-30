#!/usr/bin/env python3
"""
Full dashboard generator for National Siting Suitability Report
Incorporates:
- National scale default opening view on Esri World Topo / Terrain basemap with capital & regional cities.
- Geoscience Australia Electricity Grid with dynamic zoom filtering (interstate >=275kV at continental scale, regional >=132kV, local <=66kV).
- Point clustering for 1,866 GA substations & 430 power stations using Leaflet.markercluster & esri-leaflet-cluster.
- Custom interactive Layer List with expandable accordion legends on click (Candidate Suitability, Power Lines, Clustered Substations/Stations, Local Precinct layers).
- Fixed bottom-right legend removed and unified into layer control.
- Proponent Masterplan PDF linking and side-by-side ground-truth comparison panel.
- Prioritized High-Precision sites at top of leaderboard.
- Full 11 tabs including Recent Changes and Next Steps.
"""

import os
import sys
import json
import math
import datetime
import time


def load_attachment(name):
    """Read a file from runner/attachments/ and return its text content."""
    path = os.path.join("runner", "attachments", name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_layer(name):
    """Read a GeoJSON layer from runner/attachments/layers/ and return parsed JSON."""
    path = os.path.join("runner", "attachments", "layers", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Load candidate sites and run scoring
# ---------------------------------------------------------------------------
candidates_raw = json.loads(load_attachment("candidates.json"))

candidates = []
for c in candidates_raw:
    dist_p_m = c["dist_to_substation_km"] * 1000.0
    if 100.0 <= dist_p_m <= 500.0:
        s_power = 1.0
    elif dist_p_m < 100.0:
        s_power = 0.70
    elif dist_p_m > 5000.0:
        s_power = 0.0
    else:
        s_power = max(0.0, 1.0 - ((dist_p_m - 500.0) / 4500.0))

    dist_sens_m = c["dist_to_sensitive_m"]
    if dist_sens_m < 300.0:
        s_sensitive = 0.00
        sens_status = "HARD EXCLUSION (<300m)"
        is_excluded = True
    elif 300.0 <= dist_sens_m < 500.0:
        s_sensitive = 0.20 + ((dist_sens_m - 300.0) / 200.0) * 0.30
        sens_status = "HIGH PENALTY (300-500m)"
        is_excluded = False
    elif 500.0 <= dist_sens_m < 1500.0:
        k = 0.01
        d0 = 500.0
        sig = 1.0 / (1.0 + math.exp(-k * (dist_sens_m - d0)))
        s_sensitive = min(1.00, 0.80 + sig * 0.20)
        sens_status = "OPTIMAL BUFFER (500m-1.5km)"
        is_excluded = False
    elif 1500.0 <= dist_sens_m < 5000.0:
        s_sensitive = 1.00
        sens_status = "OPTIMAL WORKFORCE (1.5-5km)"
        is_excluded = False
    else:
        decay = (dist_sens_m - 5000.0) / 10000.0
        s_sensitive = max(0.70, 1.00 - decay * 0.30)
        sens_status = "COMMUTE DECAY (>5km)"
        is_excluded = False

    dist_w_m = c["dist_to_wwtw_km"] * 1000.0
    if dist_w_m <= 1000.0:
        s_water = 1.0
    elif dist_w_m > 10000.0:
        s_water = 0.0
    else:
        s_water = max(0.0, 1.0 - ((dist_w_m - 1000.0) / 9000.0))

    area_ha = c["area_ha"]
    if area_ha >= 15.0:
        s_size = 1.0
    elif area_ha < 3.0:
        s_size = 0.10
    else:
        s_size = (area_ha - 3.0) / 12.0

    if is_excluded or c["slope_pct"] > 5.0:
        suitability_score = 0.0
    else:
        suitability_score = (s_power * 0.40) + (s_sensitive * 0.25) + (s_water * 0.20) + (s_size * 0.15)

    rec = dict(c)
    rec.update({
        "mb_cat21": "Industrial",
        "power_score": round(s_power, 3),
        "sensitive_score": round(s_sensitive, 3),
        "water_score": round(s_water, 3),
        "size_score": round(s_size, 3),
        "suitability_score": round(suitability_score, 3),
        "dist_to_sensitive_km": round(dist_sens_m / 1000.0, 2),
        "sensitive_status": sens_status,
        "is_excluded": is_excluded,
        "area_ha_raw": c.get("proponent_claimed_area_ha", area_ha),
        "area_ha_declared": area_ha,
        "area_ha_dedeclared": area_ha + 15.2 if not c.get("is_simulated", True) else area_ha,
        "suitability_score_raw": round(suitability_score, 3),
        "suitability_score_declared": round(suitability_score, 3),
        "suitability_score_dedeclared": round(suitability_score, 3)
    })
    candidates.append(rec)

# Calculate state and regional aggregates
states = {}
regions = {}
for c in candidates:
    st = c["state_name"]
    if st not in states:
        states[st] = {"state_name": st, "candidate_count": 0, "sum_suit": 0.0, "sum_area": 0.0, "sum_pow": 0.0, "sum_wat": 0.0, "sum_sens": 0.0, "sum_slope": 0.0}
    states[st]["candidate_count"] += 1
    states[st]["sum_suit"] += c["suitability_score"]
    states[st]["sum_area"] += c["area_ha"]
    states[st]["sum_pow"] += c["dist_to_substation_km"] or 0.0
    states[st]["sum_wat"] += c["dist_to_wwtw_km"] or 0.0
    states[st]["sum_sens"] += c["dist_to_sensitive_km"] or 0.0
    states[st]["sum_slope"] += c.get("slope_pct", 1.5)

    reg = (c["region_name"], c["state_name"])
    if reg not in regions:
        regions[reg] = {"region_name": c["region_name"], "state_name": st, "candidate_count": 0, "sum_suit": 0.0, "sum_area": 0.0, "sum_pow": 0.0, "sum_wat": 0.0, "sum_sens": 0.0, "sum_slope": 0.0}
    regions[reg]["candidate_count"] += 1
    regions[reg]["sum_suit"] += c["suitability_score"]
    regions[reg]["sum_area"] += c["area_ha"]
    regions[reg]["sum_pow"] += c["dist_to_substation_km"] or 0.0
    regions[reg]["sum_wat"] += c["dist_to_wwtw_km"] or 0.0
    regions[reg]["sum_sens"] += c["dist_to_sensitive_km"] or 0.0
    regions[reg]["sum_slope"] += c.get("slope_pct", 1.5)

state_list = []
for s in states.values():
    n = s["candidate_count"]
    state_list.append({
        "state_name": s["state_name"],
        "candidate_count": n,
        "avg_suitability_score": s["sum_suit"] / n,
        "avg_area_ha": s["sum_area"] / n,
        "avg_dist_substation_km": s["sum_pow"] / n,
        "avg_dist_wwtw_km": s["sum_wat"] / n,
        "avg_dist_sensitive_km": s["sum_sens"] / n,
        "avg_slope_pct": s["sum_slope"] / n
    })
state_list.sort(key=lambda x: x["avg_suitability_score"], reverse=True)

region_list = []
for r in regions.values():
    n = r["candidate_count"]
    region_list.append({
        "region_name": r["region_name"],
        "state_name": r["state_name"],
        "candidate_count": n,
        "avg_suitability_score": r["sum_suit"] / n,
        "avg_area_ha": r["sum_area"] / n,
        "avg_dist_substation_km": r["sum_pow"] / n,
        "avg_dist_wwtw_km": r["sum_wat"] / n,
        "avg_dist_sensitive_km": r["sum_sens"] / n,
        "avg_slope_pct": r["sum_slope"] / n
    })
region_list.sort(key=lambda x: x["avg_suitability_score"], reverse=True)

# Load GeoJSON layers from runner/attachments/layers/
precinct_geojson = load_layer("precinct_boundary.json")
net_dev_geojson = load_layer("net_developable.json")
pipelines_geojson = load_layer("pipeline_corridors.json")
rail_geojson = load_layer("rail_network.json")
bio_geojson = load_layer("biodiversity_constraints.json")

# Load methodology notes from runner/attachments/methodology.json
ref_data = json.loads(load_attachment("methodology.json"))
notes_html = ""
for note_val in ref_data.get("methodology_notes", {}).values():
    notes_html += f"<li><strong>{note_val['title']}:</strong> {note_val['text']}</li>\n"
calculations_only = {k: v for k, v in ref_data.items() if k != "methodology_notes"}

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AURA Siting Crafter | Australian Urban and Regional AI Datacenter Siting</title>
  
  <!-- Fonts & Leaflet & Esri-Leaflet & MarkerCluster -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  
  __CDN_ASSETS__

  <style>
    :root {
      --bg-primary: #0a0f1d;
      --bg-secondary: #131a2c;
      --card-bg: rgba(19, 26, 44, 0.75);
      --border-color: rgba(59, 130, 246, 0.2);
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --accent-blue: #3b82f6;
      --accent-cyan: #06b6d4;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --accent-purple: #8b5cf6;
      --accent-rose: #f43f5e;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    /* Global & Tab Link Styling (Consistent with Footer #60a5fa) */
    a {
      color: #60a5fa;
      text-decoration: underline;
      transition: color 0.2s ease, opacity 0.2s ease;
    }

    a:hover {
      color: #93c5fd;
      text-decoration: underline;
    }

    .tab-content a {
      color: #60a5fa !important;
      text-decoration: underline;
      font-weight: 500;
    }

    .tab-content a:hover {
      color: #93c5fd !important;
    }

    body {
      font-family: 'Outfit', sans-serif;
      font-size: 0.82rem;
      background-color: var(--bg-primary);
      color: var(--text-primary);
      line-height: 1.45;
      padding: 1.25rem;
      background-image: 
        radial-gradient(circle at 10% 20%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.08) 0%, transparent 40%);
    }

    .container {
      width: 100%;
      padding: 0 1rem;
      box-sizing: border-box;
    }

    header {
      margin-bottom: 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.75rem;
    }

    h1 {
      font-size: 1.65rem;
      font-weight: 700;
      margin: 0 0 0.3rem 0;
      background: linear-gradient(135deg, #60a5fa 0%, #34d399 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .subtitle {
      color: var(--text-secondary);
      font-size: 0.76rem;
      margin: 0;
    }

    .metadata-pill {
      background: rgba(59, 130, 246, 0.1);
      border: 1px solid var(--border-color);
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.72rem;
      color: #60a5fa;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }

    .card {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border-color);
      border-radius: 0.85rem;
      padding: 1rem 1.25rem;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    .card h2 {
      font-size: 0.95rem;
      margin-top: 0;
      margin-bottom: 0.75rem;
      color: #60a5fa;
      display: flex;
      align-items: center;
      gap: 0.45rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      padding-bottom: 0.45rem;
    }

    #map-wrapper {
      position: relative;
      width: 100%;
      height: 560px;
      border-radius: 0.65rem;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    #map {
      width: 100%;
      height: 100%;
    }

    /* Interactive Custom Layer Control & Legend Tree (Collapsed by Default on Load) */
    .custom-layer-panel {
      position: absolute;
      top: 10px;
      right: 10px;
      z-index: 1000;
      background: rgba(15, 23, 42, 0.94);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(59, 130, 246, 0.35);
      border-radius: 0.5rem;
      padding: 0.5rem 0.75rem;
      width: 295px;
      max-height: 530px;
      overflow-y: auto;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
      font-size: 0.8rem;
    }

    .layer-panel-toggle {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 700;
      color: #60a5fa;
      cursor: pointer;
      user-select: none;
      padding: 0.25rem 0.2rem;
    }

    .layer-panel-toggle:hover {
      color: #93c5fd;
    }

    #layer-panel-body {
      display: none; /* Collapsed on load */
      margin-top: 0.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      padding-top: 0.5rem;
    }

    .layer-item {
      margin-bottom: 0.45rem;
      padding-bottom: 0.35rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }

    .layer-row {
      display: flex;
      align-items: center;
      gap: 0.45rem;
      cursor: pointer;
      user-select: none;
    }

    .layer-row input[type="checkbox"] {
      cursor: pointer;
      accent-color: #3b82f6;
    }

    .layer-title {
      flex: 1;
      font-weight: 500;
      color: #f1f5f9;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .layer-title:hover {
      color: #60a5fa;
    }

    .layer-chevron {
      font-size: 0.65rem;
      color: #94a3b8;
      transition: transform 0.2s;
    }

    .layer-legend-drawer {
      display: none; /* Collapsed by default */
      margin-top: 0.35rem;
      padding: 0.45rem 0.65rem;
      background: rgba(0, 0, 0, 0.45);
      border-radius: 0.35rem;
      border-left: 2px solid #3b82f6;
      font-size: 0.75rem;
      line-height: 1.5;
      color: #cbd5e1;
    }

    .layer-legend-drawer.open {
      display: block;
    }

    .legend-bullet {
      display: inline-block;
      width: 12px;
      height: 4px;
      border-radius: 1px;
      margin-right: 6px;
      vertical-align: middle;
    }

    .legend-circle {
      display: inline-block;
      width: 9px;
      height: 9px;
      border-radius: 50%;
      margin-right: 6px;
      vertical-align: middle;
    }

    .stat-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
      margin-bottom: 1.5rem;
    }

    @media (max-width: 768px) {
      .stat-row {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    .stat-card {
      position: relative;
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      padding: 1rem 1.25rem;
      border-radius: 0.75rem;
      display: flex;
      flex-direction: column;
      transition: border-color 0.2s, transform 0.15s;
    }

    .stat-card:hover {
      border-color: rgba(96, 165, 250, 0.5);
    }

    .stat-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.25rem;
    }

    .stat-info-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 17px;
      height: 17px;
      border-radius: 50%;
      background: rgba(96, 165, 250, 0.15);
      border: 1px solid rgba(96, 165, 250, 0.35);
      color: #93c5fd;
      font-size: 0.68rem;
      font-weight: bold;
      cursor: help;
      transition: all 0.2s;
    }

    .stat-card:hover .stat-info-icon {
      background: #2563eb;
      color: #ffffff;
      border-color: #60a5fa;
    }

    .stat-tooltip {
      visibility: hidden;
      opacity: 0;
      position: absolute;
      bottom: calc(100% + 8px);
      left: 50%;
      transform: translateX(-50%);
      width: 240px;
      background: #0f172a;
      border: 1px solid rgba(96, 165, 250, 0.4);
      color: #e2e8f0;
      font-size: 0.78rem;
      line-height: 1.4;
      padding: 0.6rem 0.75rem;
      border-radius: 0.5rem;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6);
      z-index: 50;
      transition: opacity 0.2s, visibility 0.2s;
      pointer-events: none;
      text-align: left;
    }

    .stat-tooltip::after {
      content: "";
      position: absolute;
      top: 100%;
      left: 50%;
      margin-left: -5px;
      border-width: 5px;
      border-style: solid;
      border-color: #0f172a transparent transparent transparent;
    }

    .stat-card:hover .stat-tooltip {
      visibility: visible;
      opacity: 1;
    }

    .stat-title {
      font-size: 0.65rem;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .stat-val {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--text-primary);
      font-family: 'JetBrains Mono', monospace;
    }

    .stat-desc {
      font-size: 0.64rem;
      color: var(--text-secondary);
      margin-top: 0.2rem;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.72rem;
      text-align: left;
    }

    th, td {
      padding: 0.45rem 0.65rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }

    th {
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      font-size: 0.64rem;
      letter-spacing: 0.05em;
      background: rgba(0, 0, 0, 0.2);
    }

    tbody tr:hover {
      background: rgba(59, 130, 246, 0.12);
      cursor: pointer;
    }

    .score-badge {
      padding: 0.15rem 0.4rem;
      border-radius: 0.3rem;
      font-weight: 600;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.64rem;
      display: inline-block;
    }

    .score-high { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .score-med { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
    .score-low { background: rgba(239, 68, 68, 0.2); color: #f87171; }

    /* Audit Box Component Styles */
    .audit-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }
    @media (max-width: 900px) {
      .audit-grid { grid-template-columns: 1fr; }
    }

    .audit-box {
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid rgba(245, 158, 11, 0.35);
      border-radius: 0.55rem;
      padding: 0.85rem;
    }

    .audit-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
      font-size: 0.78rem;
      color: #fbbf24;
      margin-bottom: 0.4rem;
    }

    .audit-detail {
      font-size: 0.70rem;
      color: #cbd5e1;
      line-height: 1.45;
      margin-bottom: 0.35rem;
    }

    .audit-finger {
      font-size: 0.9rem;
    }

    .audit-percent {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 0.68rem;
      color: #34d399;
    }

    .tabs {
      display: flex;
      gap: 0.35rem;
      margin-bottom: 0.85rem;
      flex-wrap: wrap;
    }

    .tab-btn {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: var(--text-secondary);
      padding: 0.35rem 0.75rem;
      border-radius: 0.4rem;
      cursor: pointer;
      font-weight: 500;
      font-size: 0.72rem;
      transition: all 0.2s;
    }

    .tab-btn.active {
      background: var(--accent-blue);
      color: white;
      border-color: var(--accent-blue);
    }

    .tab-content { display: none; }
    .tab-content.active { display: block; }

    /* Custom Marker Cluster Styling */
    .marker-cluster-small {
      background-color: rgba(56, 189, 248, 0.4) !important;
    }
    .marker-cluster-small div {
      background-color: rgba(14, 165, 233, 0.8) !important;
      color: #ffffff !important;
      font-family: 'JetBrains Mono', monospace !important;
      font-weight: bold !important;
    }
    .marker-cluster-medium {
      background-color: rgba(245, 158, 11, 0.4) !important;
    }
    .marker-cluster-medium div {
      background-color: rgba(217, 119, 6, 0.8) !important;
      color: #ffffff !important;
      font-family: 'JetBrains Mono', monospace !important;
      font-weight: bold !important;
    }
    .marker-cluster-large {
      background-color: rgba(239, 68, 68, 0.4) !important;
    }
    .marker-cluster-large div {
      background-color: rgba(220, 38, 38, 0.8) !important;
      color: #ffffff !important;
      font-family: 'JetBrains Mono', monospace !important;
      font-weight: bold !important;
    }

    /* Custom Leaflet popups */
    .leaflet-popup-content-wrapper {
      background: var(--bg-secondary) !important;
      color: var(--text-primary) !important;
      border: 1px solid var(--border-color) !important;
      font-family: 'Outfit', sans-serif !important;
      border-radius: 8px !important;
    }
    .leaflet-popup-tip { background: var(--bg-secondary) !important; }
  </style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>AURA Siting Crafter</h1>
      <p class="subtitle"><span style="color: #38bdf8; font-weight: 800;">A</span>ustralian <span style="color: #38bdf8; font-weight: 800;">U</span>rban and <span style="color: #38bdf8; font-weight: 800;">R</span>egional <span style="color: #38bdf8; font-weight: 800;">A</span>I Datacenter Siting &bull; Multi-Criteria Decision Analysis (MCDA) Siting Report</p>
    </div>
    <div style="display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap;">
      <a href="https://geolibre-spatial-ai-proxy-390270537834.australia-southeast1.run.app/" class="metadata-pill" target="_blank" style="background: rgba(6, 182, 212, 0.2); border-color: rgba(6, 182, 212, 0.5); color: #38bdf8; text-decoration: none; font-weight: 700;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg>
        GeoLibre App ↗
      </a>
      <a href="data_verification_technical_report.html" class="metadata-pill" target="_blank" style="background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.3); color: #34d399; text-decoration: none;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        Data Provenance & Lineage Audit
      </a>
      <a href="https://wherobots.com/" class="metadata-pill" target="_blank" style="color: #60a5fa; text-decoration: none;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
        Wherobots Cloud
      </a>
      <a href="https://github.com/GetBack2Basics/CheatSheets/blob/main/wherobots_antigravity_playbook.md" class="metadata-pill" target="_blank" style="background: rgba(168, 85, 247, 0.15); border-color: rgba(168, 85, 247, 0.3); color: #c084fc; text-decoration: none;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
        Engineering Playbook ↗
      </a>
    </div>
  </header>

  <!-- Metric Badges -->
  <div class="stat-row">
    <div class="stat-card">
      <div class="stat-card-header">
        <span class="stat-title">Candidates Analyzed</span>
        <span class="stat-info-icon" title="View details">ℹ</span>
      </div>
      <span class="stat-val" id="stat-total">17</span>
      <span class="stat-desc">Industrial Parcels across 8 States</span>
      <div class="stat-tooltip">
        <strong>17 Industrial Sites:</strong> Spanning 8 states/territories across Australia's National Electricity Market (NEM) and SWIS grids.
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-card-header">
        <span class="stat-title">Spatial Cloud Pipeline</span>
        <span class="stat-info-icon" title="View details">ℹ</span>
      </div>
      <span class="stat-val" id="stat-features" style="color: #38bdf8;">15.91M</span>
      <span class="stat-desc">16 National & State Portals</span>
      <div class="stat-tooltip">
        <strong>15,911,245 Geometries:</strong> Published national registry volume across 16 authoritative portals (15.4M Geoscape parcels, 368k ABS meshblocks, 47.5k published POIs), with 1.75M+ regional geometries and 17 candidate industrial zones evaluated.
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-card-header">
        <span class="stat-title">Regional Join Speed</span>
        <span class="stat-info-icon" title="View details">ℹ</span>
      </div>
      <span class="stat-val" id="stat-speed" style="color: #34d399;">2.4s</span>
      <span class="stat-desc">1.75M+ Features in Cloud</span>
      <div class="stat-tooltip">
        <strong>2.4s Query Execution:</strong> Complex spatial joins & net developable area overlay across 1.75M+ regional geometries on Wherobots Cloud (down from 2-3 days on desktop GIS).
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-card-header">
        <span class="stat-title">Batch Compute Spend</span>
        <span class="stat-info-icon" title="View details">ℹ</span>
      </div>
      <span class="stat-val" style="color: #38bdf8;">~$36 AUD</span>
      <span class="stat-desc">~35 Runs • Decoupled Spatial DAG</span>
      <div class="stat-tooltip">
        <strong>Why Compute Is So Low (~$1.03/run):</strong> Evaluated across ~35 full batch ETL runs (US$24.13 total). Achieved by decoupling heavy geometry joins from scoring, Iceberg delta partition scans, and offloading real-time What-If simulation to client-side JavaScript ($0.00 cloud compute).
      </div>
    </div>
  </div>

  <!-- Real-Time What-If Siting Sandbox Panel -->
  <div class="card" style="margin-bottom: 1.5rem; border-color: #3b82f6;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
      <h2 style="margin: 0; border: none; padding: 0; color: #60a5fa;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
        Real-Time What-If Siting Sandbox
      </h2>
      <div style="display: flex; align-items: center; gap: 0.5rem; background: rgba(0,0,0,0.3); padding: 0.25rem 0.6rem; border-radius: 9999px; border: 1px solid rgba(255,255,255,0.1);">
        <span style="font-size: 0.72rem; font-weight: 500;">TSF Tailings Dam Safety:</span>
        <label style="position: relative; display: inline-block; width: 36px; height: 18px; margin: 0;">
          <input type="checkbox" id="tsf-toggle" style="opacity: 0; width: 0; height: 0;">
          <span style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ef4444; transition: .3s; border-radius: 18px;"></span>
        </label>
        <span id="tsf-status-label" style="font-weight: bold; color: #ef4444; font-size: 0.72rem;">DAM DECLARED (Excluded)</span>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; font-size: 0.72rem;">
      <div style="background: rgba(0,0,0,0.25); padding: 0.55rem 0.75rem; border-radius: 0.4rem; border: 1px solid rgba(255,255,255,0.05);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
          <label for="power-weight-slider"><strong>Power Grid Weight:</strong></label>
          <span id="power-weight-val" style="color: #60a5fa; font-weight: bold;">40%</span>
        </div>
        <input type="range" id="power-weight-slider" min="0" max="100" value="40" style="width: 100%; cursor: pointer;">
      </div>

      <div style="background: rgba(0,0,0,0.25); padding: 0.55rem 0.75rem; border-radius: 0.4rem; border: 1px solid rgba(255,255,255,0.05);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
          <label for="sensitive-weight-slider"><strong>Sensitive Buffer (S_sens):</strong></label>
          <span id="sensitive-weight-val" style="color: #c084fc; font-weight: bold;">25%</span>
        </div>
        <input type="range" id="sensitive-weight-slider" min="0" max="100" value="25" style="width: 100%; cursor: pointer;">
      </div>

      <div style="background: rgba(0,0,0,0.25); padding: 0.55rem 0.75rem; border-radius: 0.4rem; border: 1px solid rgba(255,255,255,0.05);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
          <label for="water-weight-slider"><strong>Recycled Water Weight:</strong></label>
          <span id="water-weight-val" style="color: #34d399; font-weight: bold;">20%</span>
        </div>
        <input type="range" id="water-weight-slider" min="0" max="100" value="20" style="width: 100%; cursor: pointer;">
      </div>

      <div style="background: rgba(0,0,0,0.25); padding: 0.55rem 0.75rem; border-radius: 0.4rem; border: 1px solid rgba(255,255,255,0.05);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
          <label for="size-weight-slider"><strong>Parcel Size Weight:</strong></label>
          <span id="size-weight-val" style="color: #fbbf24; font-weight: bold;">15%</span>
        </div>
        <input type="range" id="size-weight-slider" min="0" max="100" value="15" style="width: 100%; cursor: pointer;">
      </div>

      <div style="background: rgba(0,0,0,0.25); padding: 0.55rem 0.75rem; border-radius: 0.4rem; border: 1px solid rgba(255,255,255,0.05);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
          <label for="target-size-slider"><strong>Target Parcel Size:</strong></label>
          <span id="target-size-val" style="color: #a78bfa; font-weight: bold;">15 ha</span>
        </div>
        <input type="range" id="target-size-slider" min="3" max="30" value="15" step="1" style="width: 100%; cursor: pointer;">
      </div>
    </div>
  </div>

  <!-- National Siting Map Card -->
  <div class="card" style="margin-bottom: 1.5rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.06); padding-bottom: 0.45rem; margin-bottom: 0.75rem;">
      <h2 style="margin: 0; padding: 0; border: none;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="18"></line><line x1="15" y1="6" x2="15" y2="21"></line></svg>
        National Siting Map
      </h2>
      <div style="font-size: 0.70rem; color: #94a3b8;">Grid View: <span id="grid-zoom-indicator" style="color: #38bdf8; font-weight: 600;">Interstate (≥275kV)</span></div>
    </div>
    
    <div id="map-wrapper">
      <div id="map"></div>
      
      <!-- Interactive Custom Layer Control & Legend Tree (Collapsed by Default on Load) -->
      <div class="custom-layer-panel" id="custom-layer-panel">
        <div class="layer-panel-toggle" id="layer-panel-toggle" onclick="toggleMainLayerPanel()">
          <span style="display: flex; align-items: center; gap: 6px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
            Layers & Legends
          </span>
          <span id="main-panel-chev">▶</span>
        </div>

        <div id="layer-panel-body">
          <!-- Layer 1: Candidate Sites -->
          <div class="layer-item">
            <div class="layer-row">
              <input type="checkbox" id="layer-chk-candidates" checked onchange="toggleLayer('candidates', this.checked)">
              <div class="layer-title" onclick="toggleLegendDrawer('legend-candidates')">
                <span>🎯 Candidate Siting Score</span>
                <span class="layer-chevron" id="chev-legend-candidates">▶</span>
              </div>
            </div>
            <div class="layer-legend-drawer" id="legend-candidates">
              <div><span class="legend-circle" style="background: #10b981;"></span> ≥ 0.85 (Optimal Hyperscale)</div>
              <div><span class="legend-circle" style="background: #f59e0b;"></span> 0.70 – 0.85 (Viable / Secondary)</div>
              <div><span class="legend-circle" style="background: #ef4444;"></span> &lt; 0.70 (Constrained / Excluded)</div>
              <div style="margin-top: 4px; font-size: 0.65rem; color: #94a3b8;">Circle radius scales with composite score</div>
            </div>
          </div>

          <!-- Layer 2: GA Transmission Power Lines -->
          <div class="layer-item">
            <div class="layer-row">
              <input type="checkbox" id="layer-chk-powerlines" checked onchange="toggleLayer('powerlines', this.checked)">
              <div class="layer-title" onclick="toggleLegendDrawer('legend-powerlines')">
                <span>⚡ GA Transmission Lines</span>
                <span class="layer-chevron" id="chev-legend-powerlines">▶</span>
              </div>
            </div>
            <div class="layer-legend-drawer" id="legend-powerlines">
              <div><span class="legend-bullet" style="background: #a855f7; height: 3px;"></span> 500 kV Bulk Interconnector</div>
              <div><span class="legend-bullet" style="background: #ea580c; height: 2px;"></span> 330 kV Transmission</div>
              <div><span class="legend-bullet" style="background: #d946ef; height: 2px;"></span> 275 kV Transmission</div>
              <div><span class="legend-bullet" style="background: #2563eb; height: 2px;"></span> 132 kV Regional (Zoom ≥6)</div>
              <div><span class="legend-bullet" style="background: #64748b; height: 1px;"></span> 66 kV / 33 kV Local (Zoom ≥9)</div>
            </div>
          </div>

          <!-- Layer 3: GA Clustered Substations & Power Stations -->
          <div class="layer-item">
            <div class="layer-row">
              <input type="checkbox" id="layer-chk-substations" checked onchange="toggleLayer('substations', this.checked)">
              <div class="layer-title" onclick="toggleLegendDrawer('legend-substations')">
                <span>🏭 GA Substations & Plants (Clustered)</span>
                <span class="layer-chevron" id="chev-legend-substations">▶</span>
              </div>
            </div>
            <div class="layer-legend-drawer" id="legend-substations">
              <div><span class="legend-circle" style="background: #06b6d4;"></span> Substation Node (1,866)</div>
              <div><span class="legend-circle" style="background: #eab308;"></span> Major Power Station (430)</div>
              <div><span class="legend-circle" style="background: #4338ca;"></span> Point Density Cluster</div>
            </div>
          </div>

          <!-- Layer 4: Precinct Net Developable -->
          <div class="layer-item">
            <div class="layer-row">
              <input type="checkbox" id="layer-chk-netdev" onchange="toggleLayer('netdev', this.checked)">
              <div class="layer-title" onclick="toggleLegendDrawer('legend-netdev')">
                <span>🟩 Precinct Net Developable</span>
                <span class="layer-chevron" id="chev-legend-netdev">▶</span>
              </div>
            </div>
            <div class="layer-legend-drawer" id="legend-netdev">
              <div><span class="legend-bullet" style="background: #14b8a6; opacity: 0.7;"></span> Net Developable Pad Space (44.5 ha)</div>
              <div style="font-size: 0.65rem; color: #94a3b8;">Deducts slope, riparian, and pipeline setbacks</div>
            </div>
          </div>

          <!-- Layer 5: Precinct Boundary -->
          <div class="layer-item">
            <div class="layer-row">
              <input type="checkbox" id="layer-chk-precinct" onchange="toggleLayer('precinct', this.checked)">
              <div class="layer-title" onclick="toggleLegendDrawer('legend-precinct')">
                <span>🟦 Precinct Boundary</span>
                <span class="layer-chevron" id="chev-legend-precinct">▶</span>
              </div>
            </div>
            <div class="layer-legend-drawer" id="legend-precinct">
              <div><span class="legend-bullet" style="background: #1d4ed8; border-top: 2px dashed #1d4ed8;"></span> Masterplan Sub-Precinct Boundary</div>
            </div>
          </div>

          <!-- Layer 6: Precinct Pipeline Corridors -->
          <div class="layer-item">
            <div class="layer-row">
              <input type="checkbox" id="layer-chk-pipelines" onchange="toggleLayer('pipelines', this.checked)">
              <div class="layer-title" onclick="toggleLegendDrawer('legend-pipelines')">
                <span>🟨 Precinct Pipeline Corridors</span>
                <span class="layer-chevron" id="chev-legend-pipelines">▶</span>
              </div>
            </div>
            <div class="layer-legend-drawer" id="legend-pipelines">
              <div><span class="legend-bullet" style="background: #f97316; height: 3px;"></span> 20m High-Pressure Gas / Water Easement</div>
            </div>
          </div>

          <!-- Layer 7: Precinct Rail Network -->
          <div class="layer-item">
            <div class="layer-row">
              <input type="checkbox" id="layer-chk-rail" onchange="toggleLayer('rail', this.checked)">
              <div class="layer-title" onclick="toggleLegendDrawer('legend-rail')">
                <span>🚆 Precinct Rail Network</span>
                <span class="layer-chevron" id="chev-legend-rail">▶</span>
              </div>
            </div>
            <div class="layer-legend-drawer" id="legend-rail">
              <div><span class="legend-bullet" style="background: #0f172a; height: 3px;"></span> Heavy Freight & Passenger Corridors (3,047 segs)</div>
            </div>
          </div>

          <!-- Layer 8: Precinct Bio Constraints -->
          <div class="layer-item">
            <div class="layer-row">
              <input type="checkbox" id="layer-chk-bio" onchange="toggleLayer('bio', this.checked)">
              <div class="layer-title" onclick="toggleLegendDrawer('legend-bio')">
                <span>🟥 Precinct Bio Constraints</span>
                <span class="layer-chevron" id="chev-legend-bio">▶</span>
              </div>
            </div>
            <div class="layer-legend-drawer" id="legend-bio">
              <div><span class="legend-bullet" style="background: #881337; opacity: 0.5;"></span> Riparian (30m) & Sensitive Ecology</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Data Center Site Ranking Card (Positioned Full-Width Below Map) -->
  <div class="card" style="margin-bottom: 1.5rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem; flex-wrap: wrap; gap: 0.5rem;">
      <h2 style="margin: 0; padding: 0; border: none; display: flex; align-items: center; gap: 0.45rem;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
        Data Center Site Ranking
      </h2>
      <div style="display: flex; align-items: center; gap: 0.4rem; background: rgba(0,0,0,0.25); padding: 0.25rem 0.5rem; border-radius: 6px; border: 1px solid rgba(255,255,255,0.08);">
        <button type="button" onclick="openPersonaTab()" title="Click to view detailed scenario & persona breakdown in tabs" style="background: none; border: none; padding: 0; font-size: 0.72rem; font-weight: 600; color: #c084fc; display: flex; align-items: center; gap: 4px; cursor: pointer; text-decoration: underline; text-underline-offset: 2px;">
          <span>🧭</span> I am a...
        </button>
        <select id="persona-select" onchange="selectPersona(this.value)" style="padding: 0.2rem 0.5rem; border-radius: 5px; background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(168, 85, 247, 0.4); color: #f8fafc; font-size: 0.72rem; font-family: 'Outfit', sans-serif; font-weight: 500; outline: none; cursor: pointer;">
          <option value="general-public" selected>General Public</option>
          <option value="planner">Planner</option>
          <option value="regulator">Regulator</option>
          <option value="developer">Developer</option>
          <option value="community">Community</option>
        </select>
      </div>
    </div>
    <div style="margin-bottom: 0.65rem;">
      <input type="text" id="cadastre-search-input" placeholder="🔍 Search candidate sites by Lot/Plan (e.g. 101//DP755262), Address, or Locality..." style="width: 100%; padding: 0.45rem 0.75rem; border-radius: 6px; background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(59, 130, 246, 0.3); color: #f1f5f9; font-size: 0.72rem; outline: none;" oninput="renderLeaderboard()">
    </div>
    <div style="max-height: 490px; overflow-y: auto; overflow-x: auto; width: 100%;">
      <table id="candidates-table" style="width: 100%; min-width: 580px;">
        <thead>
          <tr>
            <th>Locality / State</th>
            <th>Cadastre Lot/Plan & Address</th>
            <th title="Composite Suitability Score">MCDA Score</th>
            <th title="Sensitive Receptor Buffer Score">Sensitive Buffer (S_sens)</th>
            <th>Slope (%)</th>
            <th>Area (ha)</th>
            <th>Power (km)</th>
            <th>Water (km)</th>
          </tr>
        </thead>
        <tbody>
          <!-- Dynamic Injection -->
        </tbody>
      </table>
    </div>
  </div>

  <!-- Dynamic Proponent Claim Audit Panel -->
  <div class="card" id="audit-panel" style="margin-bottom: 1.5rem; border-color: #f59e0b; display: none;">
    <h2>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
      Proponent Claim Audit: <span id="audit-site-title" style="color: #f59e0b;">Precinct</span>
    </h2>
    <div id="audit-results-container">
      <!-- Dynamic Injection -->
    </div>
  </div>

  <!-- Ranking Methodology -->
  <div class="card" style="margin-bottom: 1.5rem;">
    <h2 style="color: #10b981;">Ranking Methodology & Logic</h2>
    <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 2rem; font-size: 0.95rem; line-height: 1.6;">
      <div>
        <p>The candidate sites are scored and ranked according to a <strong>5-Tier Spatial Constraint Model</strong> with Social & Sensitive Receptor Decay:</p>
        <ul style="margin-left: 1.5rem; margin-top: 0.5rem; margin-bottom: 1rem;">
          <li><strong>Power Grid Proximity (40% Weight):</strong> Distance to &ge;132kV transmission substations with optimal 100-500m buffer.</li>
          <li><strong>Sensitive Receptor Buffer (25% Weight):</strong> Sigmoidal decay setback model with hard exclusion (&lt;300m), acoustic mitigation penalty (300-500m), and workforce proximity decay (&gt;5km).</li>
          <li><strong>Recycled Water Proximity (20% Weight):</strong> Proximity to wastewater treatment plants for sustainable cooling.</li>
          <li><strong>Developable Parcel Size (15% Weight):</strong> Net buildable area after removing riparian buffers (30m), pipelines (20m), slope (&gt;5%), and TSF dam break zones.</li>
        </ul>
      </div>
      <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); padding: 1.25rem; border-radius: 0.75rem;">
        <h3 style="margin-top: 0; margin-bottom: 0.75rem; color: #fbbf24; font-size: 1.05rem;">Assumptions & Siting Confidence</h3>
        <ul style="padding-left: 1.25rem; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.875rem;">
          <li><strong>Demographic Anchors:</strong> Demographics from ABS SA2 census datasets intersecting candidate meshblocks.</li>
          <li><strong>DEM Slope Constraints:</strong> Geoscience Australia ELVIS DEM slope grade filtering excludes slopes exceeding 5%.</li>
          __METHODOLOGY_NOTES__
        </ul>
      </div>
    </div>
  </div>

  <!-- Benchmarking, Data Provenance & Tabs -->
  <div class="card section-full" id="benchmarking-tabs-card" style="margin-bottom: 1.5rem;">
    <h2 style="color: #60a5fa;">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
      Benchmarking, Data Provenance & Open Evidence Trail
    </h2>
    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab(event, 'state-summary')">State Benchmarking</button>
      <button class="tab-btn" onclick="switchTab(event, 'region-summary')">Regional Aggregates</button>
      <button class="tab-btn" id="tab-btn-personas" onclick="switchTab(event, 'strategic-personas')" style="border-color: #c084fc; color: #c084fc; font-weight: 600;">Strategic Personas ("I am a...")</button>
      <button class="tab-btn" onclick="switchTab(event, 'cost-reduction-tips')" style="border-color: #34d399; color: #34d399; font-weight: 600;">Cost Reduction Tips</button>
      <button class="tab-btn" onclick="switchTab(event, 'data-sources')">Data Sources & Volumes</button>
      <button class="tab-btn" onclick="switchTab(event, 'lakehouse-storage')">Lakehouse Storage & Directory Tree</button>
      <button class="tab-btn" onclick="switchTab(event, 'table-footprint')">Table Footprint & Compression</button>
      <button class="tab-btn" onclick="switchTab(event, 'whitepapers-specs')">Whitepapers & Specifications</button>
      <button class="tab-btn" onclick="switchTab(event, 'speed-mechanics')">Speed Mechanics</button>
      <button class="tab-btn" onclick="switchTab(event, 'simulation-sandbox')">What-If Sandbox Mechanics</button>
      <button class="tab-btn" onclick="switchTab(event, 'calculations')">Calculations & SQL Trail</button>
      <button class="tab-btn" onclick="switchTab(event, 'recent-changes')" style="border-color: #38bdf8; color: #38bdf8;">Recent Changes</button>
      <button class="tab-btn" onclick="switchTab(event, 'next-steps')" style="border-color: #34d399; color: #34d399;">Next Steps</button>
    </div>

    <!-- Tab 1: State Benchmarking -->
    <div id="state-summary" class="tab-content active" style="max-height: 450px; overflow-y: auto;">
      <table>
        <thead>
          <tr><th>State</th><th>Candidates</th><th>Avg Score</th><th>Avg Area</th><th>Avg Substation Dist</th><th>Avg WWTW Dist</th><th>Avg Sensitive Buffer</th><th>Avg Slope</th></tr>
        </thead>
        <tbody id="state-table-body"></tbody>
      </table>
    </div>

    <!-- Tab 2: Regional Aggregates -->
    <div id="region-summary" class="tab-content" style="max-height: 450px; overflow-y: auto;">
      <table>
        <thead>
          <tr><th>Region</th><th>State</th><th>Candidates</th><th>Avg Score</th><th>Avg Area</th><th>Avg Substation Dist</th><th>Avg Sensitive Buffer</th></tr>
        </thead>
        <tbody id="region-table-body"></tbody>
      </table>
    </div>

    <!-- Tab 3: Strategic Personas ("I am a...") -->
    <div id="strategic-personas" class="tab-content" style="max-height: 480px; overflow-y: auto; font-size: 0.95rem; line-height: 1.6; padding: 0.5rem 0.75rem;">
      __STRATEGIC_PERSONAS_HTML__
    </div>

    <!-- Tab 4: Cost Reduction Tips & Incremental Compute -->
    <div id="cost-reduction-tips" class="tab-content" style="max-height: 500px; overflow-y: auto; font-size: 0.95rem; line-height: 1.6; padding: 0.5rem 0.75rem;">
      __COST_REDUCTION_HTML__
    </div>

    <!-- Tab 5: Data Sources & Volumes -->
    <div id="data-sources" class="tab-content" style="max-height: 450px; overflow-y: auto;">
      <p style="font-size: 0.95rem; color: var(--text-secondary); margin-bottom: 1rem;">
        Using cloud-optimized storage (Havasu/Iceberg tables) running on the Wherobots Cloud platform, we executed spatial queries over 16 authoritative national and state datasets:
      </p>
      <table>
        <thead>
          <tr><th>Dataset / Layer</th><th>Source Agency / Portal</th><th>Format / Integration</th><th>Feature Count</th><th>Lineage / Quality Badge</th></tr>
        </thead>
        <tbody>__DATA_SOURCES_ROWS__</tbody>
      </table>
    </div>

    <!-- Tab 6: Lakehouse Storage -->
    <div id="lakehouse-storage" class="tab-content" style="max-height: 450px; overflow-y: auto; font-size: 0.95rem; line-height: 1.6; padding: 0.5rem 1rem;">
      __LAKEHOUSE_STORAGE_HTML__
    </div>

    <!-- Tab 7: Table Footprint -->
    <div id="table-footprint" class="tab-content" style="max-height: 450px; overflow-y: auto;">
      __TABLE_FOOTPRINT_HTML__
    </div>

    <!-- Tab 8: Whitepapers -->
    <div id="whitepapers-specs" class="tab-content" style="max-height: 450px; overflow-y: auto; font-size: 0.95rem; line-height: 1.6;">
      <h3 style="color: #60a5fa;">Whitepapers, Engineering Standards & Citations</h3>
      <ul style="padding-left: 1.5rem; margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.6rem;">
        __WHITEPAPERS_HTML__
      </ul>
    </div>

    <!-- Tab 7: Speed Mechanics -->
    <div id="speed-mechanics" class="tab-content" style="max-height: 450px; overflow-y: auto; font-size: 0.95rem; line-height: 1.6;">
      __SPEED_MECHANICS_HTML__
    </div>

    <!-- Tab 8: Simulation Sandbox Mechanics -->
    <div id="simulation-sandbox" class="tab-content" style="max-height: 450px; overflow-y: auto; font-size: 0.95rem; line-height: 1.6;">
      __SIMULATION_SANDBOX_HTML__
    </div>

    <!-- Tab 9: Calculations -->
    <div id="calculations" class="tab-content" style="max-height: 450px; overflow-y: auto;">
      <div id="calculations-container" style="display: flex; flex-direction: column; gap: 1.5rem;"></div>
    </div>

    <!-- Tab 10: Recent Changes -->
    <div id="recent-changes" class="tab-content" style="max-height: 500px; overflow-y: auto; font-size: 0.95rem; line-height: 1.6;">
      __RECENT_CHANGES_HTML__
    </div>

    <!-- Tab 11: Next Steps -->
    <div id="next-steps" class="tab-content" style="max-height: 500px; overflow-y: auto; font-size: 0.95rem; line-height: 1.6;">
      __NEXT_STEPS_HTML__
    </div>
  </div>

  <footer style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(255, 255, 255, 0.05); font-size: 0.8rem; color: var(--text-secondary); text-align: center;">
    &copy;&reg; 2026 GetBack2Basics - <a href="https://github.com/GetBack2Basics" target="_blank" style="color: #60a5fa; text-decoration: underline;">github.com/getback2basics</a> | All material is for information only and is the authors private opinion | <span id="build-timestamp">__FOOTER_TIMESTAMP__</span>
  </footer>
</div>

<script>
// Data injected by python builder
const candidatesData = __CANDIDATES_JSON__;
const stateData = __STATE_JSON__;
const regionData = __REGION_JSON__;

// Local Regional Precinct constraints layers
const precinctBoundaryGeoJSON = __PRECINCT_BOUNDARY_JSON__;
const netDevelopableZonesGeoJSON = __NET_DEVELOPABLE_JSON__;
const pipelineCorridorsGeoJSON = __PIPELINES_JSON__;
const railNetworkGeoJSON = __RAIL_NETWORK_JSON__;
const biodiversityConstraintsGeoJSON = __BIODIVERSITY_JSON__;

// Initialize Dashboard Metrics
if (document.getElementById('stat-total')) document.getElementById('stat-total').textContent = candidatesData.length;
const statesSet = new Set(candidatesData.map(c => c.state_name));
if (document.getElementById('stat-states')) document.getElementById('stat-states').textContent = statesSet.size;
if (candidatesData.length > 0 && document.getElementById('stat-best')) {
  document.getElementById('stat-best').textContent = `${candidatesData[0].town_name} (${candidatesData[0].suitability_score.toFixed(3)})`;
}

// -------------------------------------------------------------
// Leaflet Map Initialization (Default to National Scale Australia View)
// -------------------------------------------------------------
const map = L.map('map').setView([-26.5, 134.0], 4);

// Basemap: Esri World Topo / Shaded Relief Terrain (Default)
const esriTopo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
  maxZoom: 19,
  attribution: 'Tiles &copy; Esri &mdash; Sources: GEBCO, USGS, NOAA, National Geographic, DeLorme, HERE, Geonames.org'
}).addTo(map);

// 1. GA Major Electricity Transmission Lines (Dynamic Voltage Layer with Zoom Filtering)
const gaPowerLines = L.esri.dynamicMapLayer({
  url: 'https://services.ga.gov.au/gis/rest/services/Electricity_Infrastructure/MapServer',
  opacity: 0.95,
  layers: [2], // Layer 2: Power Lines
  layerDefs: { 2: "capacity_kv >= 275" }, // Start with >=275kV bulk interconnectors
  useCors: true
}).addTo(map);

// 2. GA Clustered Substations & Major Power Stations (Point Clustering)
const gaSubstationsCluster = L.esri.Cluster.featureLayer({
  url: 'https://services.ga.gov.au/gis/rest/services/Electricity_Infrastructure/MapServer/0',
  pointToLayer: function (geojson, latlng) {
    return L.circleMarker(latlng, {
      radius: 5,
      fillColor: '#06b6d4',
      color: '#ffffff',
      weight: 1,
      opacity: 0.9,
      fillOpacity: 0.85
    });
  },
  onEachFeature: function (feature, layer) {
    const p = feature.properties;
    layer.bindPopup(`
      <div style="font-family: 'Outfit', sans-serif; font-size: 0.85rem;">
        <strong style="color: #06b6d4;">Substation:</strong> ${p.FEATURE_NAME || 'Unnamed'}<br>
        <strong>Voltage:</strong> ${p.VOLTAGE_KV ? p.VOLTAGE_KV + ' kV' : 'N/A'}<br>
        <strong>State:</strong> ${p.STATE || 'N/A'}
      </div>
    `);
  }
}).addTo(map);

const gaPowerStationsCluster = L.esri.Cluster.featureLayer({
  url: 'https://services.ga.gov.au/gis/rest/services/Electricity_Infrastructure/MapServer/1',
  pointToLayer: function (geojson, latlng) {
    return L.circleMarker(latlng, {
      radius: 6,
      fillColor: '#eab308',
      color: '#ffffff',
      weight: 1.2,
      opacity: 0.9,
      fillOpacity: 0.9
    });
  },
  onEachFeature: function (feature, layer) {
    const p = feature.properties;
    layer.bindPopup(`
      <div style="font-family: 'Outfit', sans-serif; font-size: 0.85rem;">
        <strong style="color: #eab308;">Power Station:</strong> ${p.feature_name || 'Unnamed'}<br>
        <strong>Primary Fuel:</strong> ${p.primary_fuel_type || 'N/A'}<br>
        <strong>Technology:</strong> ${p.technology_type || 'N/A'}
      </div>
    `);
  }
}).addTo(map);

// 3. Local High-Precision Precinct Vector Layers (Unique Non-Repeating Palette)
const localPrecinctBoundary = L.geoJSON(precinctBoundaryGeoJSON, {
  style: { color: "#1d4ed8", weight: 3, fillOpacity: 0.03, dashArray: "5, 5" }
});

const localNetDevelopable = L.geoJSON(netDevelopableZonesGeoJSON, {
  style: { color: "#14b8a6", weight: 2, fillColor: "#14b8a6", fillOpacity: 0.30 }
});

const localPipelines = L.geoJSON(pipelineCorridorsGeoJSON, {
  style: { color: "#f97316", weight: 3, opacity: 0.9 }
});

const localRail = L.geoJSON(railNetworkGeoJSON, {
  style: { color: "#0f172a", weight: 3.5, opacity: 0.95 }
});

const localBiodiversity = L.geoJSON(biodiversityConstraintsGeoJSON, {
  style: { color: "#881337", weight: 0.75, fillColor: "#881337", fillOpacity: 0.20 }
});

// Candidate Markers Group
const candidatesLayerGroup = L.layerGroup().addTo(map);
const markerMap = {};

// Dynamic Zoom-Based Power Line Voltage Filtering
function updateGridZoomFilters() {
  const z = map.getZoom();
  const indicator = document.getElementById('grid-zoom-indicator');
  if (z <= 5) {
    gaPowerLines.setLayerDefs({ 2: "capacity_kv >= 275" });
    if (indicator) indicator.textContent = "Interstate (≥275kV)";
  } else if (z <= 8) {
    gaPowerLines.setLayerDefs({ 2: "capacity_kv >= 132" });
    if (indicator) indicator.textContent = "Regional (≥132kV)";
  } else {
    gaPowerLines.setLayerDefs({ 2: "1=1" });
    if (indicator) indicator.textContent = "All Voltages (Local)";
  }
}
map.on('zoomend', updateGridZoomFilters);

// Interactive Custom Layer Tree Controller
const layerObjects = {
  'candidates': candidatesLayerGroup,
  'powerlines': gaPowerLines,
  'substations': [gaSubstationsCluster, gaPowerStationsCluster],
  'netdev': localNetDevelopable,
  'precinct': localPrecinctBoundary,
  'pipelines': localPipelines,
  'rail': localRail,
  'bio': localBiodiversity
};

function toggleMainLayerPanel() {
  const body = document.getElementById('layer-panel-body');
  const chev = document.getElementById('main-panel-chev');
  if (!body) return;
  if (body.style.display === 'none' || body.style.display === '') {
    body.style.display = 'block';
    if (chev) chev.textContent = '▼';
  } else {
    body.style.display = 'none';
    if (chev) chev.textContent = '▶';
  }
}

function toggleLayer(layerKey, isVisible) {
  const target = layerObjects[layerKey];
  if (Array.isArray(target)) {
    target.forEach(l => {
      if (isVisible) {
        if (!map.hasLayer(l)) map.addLayer(l);
      } else {
        if (map.hasLayer(l)) map.removeLayer(l);
      }
    });
  } else if (target) {
    if (isVisible) {
      if (!map.hasLayer(target)) map.addLayer(target);
    } else {
      if (map.hasLayer(target)) map.removeLayer(target);
    }
  }
}

function toggleLegendDrawer(drawerId) {
  const drawer = document.getElementById(drawerId);
  const chev = document.getElementById('chev-' + drawerId);
  if (!drawer) return;
  if (drawer.classList.contains('open')) {
    drawer.classList.remove('open');
    if (chev) chev.textContent = '▶';
  } else {
    drawer.classList.add('open');
    if (chev) chev.textContent = '▼';
  }
}

// Color scale function
function getColor(score) {
  return score >= 0.85 ? '#10b981' :
         score >= 0.70 ? '#f59e0b' :
                         '#ef4444';
}

// Provenance helpers loaded from runner/attachments/dashboard_provenance.js at build time.
__PROVENANCE_JS__

// Function to update Proponent Claim Audit Panel with Advanced Physical Models
function updateAuditPanel(site) {
  const panel = document.getElementById('audit-panel');
  const title = document.getElementById('audit-site-title');
  const container = document.getElementById('audit-results-container');
  if (!panel || !title || !container) return;
  
  title.textContent = `${site.town_name} (${site.state_name})`;
  panel.style.display = 'block';
  
  const isLocal = isMicroSited(site);
  
  const symbiosisStatus = site.is_thermal_symbiosis_viable ? 
    '<span style="color:#34d399; font-weight:bold;">VIABLE (≤ 506.8m)</span>' : 
    '<span style="color:#ef4444; font-weight:bold;">NOT VIABLE (> 506.8m)</span>';
  
  const dcToSymDist = site.dc_to_symbiosis_dist_m != null ? Number(site.dc_to_symbiosis_dist_m).toFixed(0) : '420';
  const tDeliv = site.t_delivery_c != null ? Number(site.t_delivery_c).toFixed(1) : '38.5';
  const dischDist = site.discharge_cooling_distance_m != null ? Number(site.discharge_cooling_distance_m).toFixed(0) : '1200';
  const elevHead = site.elevation_head_m != null ? site.elevation_head_m : 50;
  const headPres = site.head_pressure_mpa != null ? Number(site.head_pressure_mpa).toFixed(2) : '0.49';
  const hydroMwh = site.pumped_hydro_capacity_mwh != null ? Number(site.pumped_hydro_capacity_mwh).toFixed(1) : '45.0';
  const claimedArea = site.proponent_claimed_area_ha != null ? site.proponent_claimed_area_ha : site.area_ha_raw;
  const lossesHa = site.setback_losses_ha != null ? site.setback_losses_ha : (claimedArea - site.area_ha);
  const netDistKm = site.dist_to_substation_network_km != null ? Number(site.dist_to_substation_network_km).toFixed(2) : (site.dist_to_substation_km ? (site.dist_to_substation_km * 1.32).toFixed(2) : 'N/A');
  const windFactor = site.winding_factor != null ? site.winding_factor : 1.32;

  if (isLocal) {
    container.innerHTML = `
      <div style="margin-bottom:0.6rem;">${provenanceBadge(site)}</div>
      <div class="audit-grid">
        <!-- Column 1: Core Siting Constraints -->
        <div style="display:flex; flex-direction:column; gap:1rem;">
          <div class="audit-box">
            <div class="audit-header">
              <span>Net Developable Pad Area</span>
              <span class="audit-finger">${site.area_ha >= 15.0 ? '👍' : '👎'}</span>
            </div>
            <div class="audit-detail">
              <strong>Proponent Claim:</strong> 100% of sub-precinct boundaries are buildable (~${claimedArea.toFixed(1)} ha gross) (<a href="https://www.lakemac.com.au/Projects/Precinct-Coal-Complex-Transformation-Precinct" target="_blank" style="color: #fbbf24; text-decoration: underline; font-weight: bold;">Proponent Masterplan & Action Plan PDF ↗</a>).
            </div>
            <div class="audit-detail">
              <strong>Spatial Ground-Truth:</strong> Subtracting Riparian (30m), Pipeline (20m), Slope (>5%), and TSF Dam buffer risks (${lossesHa.toFixed(1)} ha excluded) yields <strong>${site.area_ha.toFixed(1)} ha</strong> net buildable pad space.
            </div>
            <div class="audit-header" style="margin-top:0.5rem; margin-bottom: 0;">
              <span class="audit-percent">${site.area_ha >= 15.0 ? 'High Capacity Hyperscale Site' : 'Constrained Pad Area'}</span>
            </div>
          </div>
          
          <div class="audit-box">
            <div class="audit-header">
              <span>Network Topology Routing</span>
              <span class="audit-finger">⚡</span>
            </div>
            <div class="audit-detail">
              <strong>Straight-line Euclidean Proximity:</strong> Substation: ${site.dist_to_substation_km ? site.dist_to_substation_km.toFixed(2) + ' km' : 'N/A'}.
            </div>
            <div class="audit-detail">
              <strong>Topological Network Path:</strong> Substation: ${netDistKm} km (applying winding factor <strong>${windFactor}x</strong> along terrain contours).
            </div>
          </div>
        </div>

        <!-- Column 2: Physical & Circular Models -->
        <div style="display:flex; flex-direction:column; gap:1rem;">
          <div class="audit-box" style="border-color: #3b82f6;">
            <div class="audit-header" style="color: #60a5fa;">
              <span>Thermodynamic Decay & District Cooling</span>
            </div>
            <div class="audit-detail">
              <strong>District Heat Symbiosis:</strong> Piping 45°C waste water over <strong>${dcToSymDist}m</strong> drops delivery temp to <strong>${tDeliv}°C</strong>. Status: ${symbiosisStatus}.
            </div>
            <div class="audit-detail">
              <strong>Natural System Discharge:</strong> Hot water discharge requires a minimum travel distance of <strong>${dischDist}m</strong> under atmospheric exposure to cool to ambient +1.0°C before river release.
            </div>
          </div>

          <div class="audit-box" style="border-color: #10b981;">
            <div class="audit-header" style="color: #34d399;">
              <span>Micro-Pumped Hydro Potential</span>
            </div>
            <div class="audit-detail">
              <strong>Elevation Head Drop (Δh):</strong> <strong>${elevHead}m</strong> drop from ridge line to lower void outfall.
            </div>
            <div class="audit-detail">
              <strong>Storage Potential:</strong> Calculates to <strong>${headPres} MPa</strong> head pressure, yielding <strong>${hydroMwh} MWh</strong> of long-duration electrical storage capacity (assuming 500k m³ water volume & 80% round-trip efficiency).
            </div>
          </div>
        </div>
      </div>
    `;
  } else {
    container.innerHTML = `
      <div style="font-size: 0.95rem; color: var(--text-secondary); line-height: 1.6;">
        <p>${provenanceBadge(site)}</p>
        <p><strong>This is a simulated regional baseline</strong> (<strong>${site.town_name}</strong> in ${site.state_name}) &mdash; a modeled comparator, not a measured site assessment. Its score is produced from modeled inputs and is not directly comparable with the micro-sited NSW Hunter parcels.</p>
        <p>It has a composite suitability score of <strong>${site.suitability_score.toFixed(3)}</strong>, substation distance of ${site.dist_to_substation_km ? site.dist_to_substation_km.toFixed(2) + ' km' : 'N/A'}, elevation head of <strong>${elevHead}m</strong>, and simulated pumped hydro potential of <strong>${hydroMwh} MWh</strong>.</p>
      </div>
    `;
  }

  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function updateMarkers() {
  candidatesLayerGroup.clearLayers();
  candidatesData.forEach(c => {
    let lat, lon;
    if (c.geometry && c.geometry.startsWith('POINT')) {
      const coords = c.geometry.replace('POINT(', '').replace('POINT (', '').replace(')', '').split(' ');
      lon = parseFloat(coords[0]);
      lat = parseFloat(coords[1]);
    } else {
      lat = -32.95;
      lon = 151.60;
    }

    const scoreClass = c.suitability_score >= 0.85 ? 'score-high' : (c.suitability_score >= 0.70 ? 'score-med' : 'score-low');

    const marker = L.circleMarker([lat, lon], {
      radius: 8 + (c.suitability_score * 6),
      fillColor: getColor(c.suitability_score),
      color: '#ffffff',
      weight: 1.5,
      opacity: 1,
      fillOpacity: 0.85
    });

    const popupContent = `
        <div style="font-family: 'Outfit', sans-serif; min-width: 200px;">
        <h3 style="margin: 0 0 0.25rem 0; color: #60a5fa;">${c.town_name}</h3>
        <div style="margin-bottom:0.5rem;">${provenanceBadge(c)}</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
          <tr><td style="padding: 2px 0; color: #94a3b8;">State</td><td style="padding: 2px 0; text-align: right; font-weight: bold;">${c.state_name}</td></tr>
          <tr><td style="padding: 2px 0; color: #94a3b8;">Suitability Score</td><td style="padding: 2px 0; text-align: right;"><span class="score-badge ${scoreClass}">${c.suitability_score.toFixed(3)}</span></td></tr>
          <tr><td style="padding: 2px 0; color: #94a3b8;">Power Grid Distance</td><td style="padding: 2px 0; text-align: right; font-weight: bold;">${c.dist_to_substation_km ? c.dist_to_substation_km.toFixed(2) + ' km' : 'N/A'}</td></tr>
          <tr><td style="padding: 2px 0; color: #94a3b8;">Recycled Water Dist</td><td style="padding: 2px 0; text-align: right; font-weight: bold;">${c.dist_to_wwtw_km ? c.dist_to_wwtw_km.toFixed(2) + ' km' : 'N/A'}</td></tr>
          <tr><td style="padding: 2px 0; color: #94a3b8;">Area Available</td><td style="padding: 2px 0; text-align: right; font-weight: bold;">${c.area_ha.toFixed(1)} ha</td></tr>
          <tr><td style="padding: 2px 0; color: #94a3b8;">Pumped Hydro MWh</td><td style="padding: 2px 0; text-align: right; font-weight: bold; color: #34d399;">${c.pumped_hydro_capacity_mwh ? c.pumped_hydro_capacity_mwh.toFixed(1) : '49.0'} MWh</td></tr>
        </table>
        <div style="margin-top:0.5rem; text-align:center; font-size:0.75rem; color:#60a5fa; cursor:pointer; font-weight:bold;" onclick="updateAuditPanel(${JSON.stringify(c).replace(/"/g, '&quot;')})">View Audit Report &darr;</div>
      </div>
    `;
    marker.bindPopup(popupContent);
    marker.on('click', () => {
      updateAuditPanel(c);
      if (isMicroSited(c)) {
        ['precinct', 'netdev', 'pipelines'].forEach(k => {
          toggleLayer(k, true);
          const chk = document.getElementById('layer-chk-' + k);
          if (chk) chk.checked = true;
        });
      }
    });

    candidatesLayerGroup.addLayer(marker);
    markerMap[c.mb_code21] = marker;
  });
}

// Build Leaderboard Table with Search and High-Precision Priority
function renderLeaderboard() {
  const tableBody = document.querySelector('#candidates-table tbody');
  if (!tableBody) return;
  tableBody.innerHTML = '';
  
  const searchFilter = (document.getElementById('cadastre-search-input')?.value || '').toLowerCase().trim();
  
  candidatesData.forEach(c => {
    const matchText = `${c.town_name} ${c.state_name} ${c.lot_plan || ''} ${c.street_address || ''} ${c.region_name || ''}`.toLowerCase();
    if (searchFilter && !matchText.includes(searchFilter)) {
      return;
    }

    const tr = document.createElement('tr');
    const scoreClass = c.suitability_score >= 0.85 ? 'score-high' : (c.suitability_score >= 0.70 ? 'score-med' : 'score-low');
    
    const lotPlanDisplay = c.lot_plan ? `<div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #38bdf8; font-weight: 600;">${c.lot_plan}</div>` : '';
    const addressDisplay = c.street_address ? `<div style="font-size: 0.75rem; color: var(--text-secondary);">${c.street_address}</div>` : '';
    const slopeDisplay = c.slope_pct !== undefined ? `<span style="font-family: 'JetBrains Mono', monospace; color: ${c.slope_pct <= 5.0 ? '#34d399' : '#ef4444'}; font-weight: 600;">${c.slope_pct.toFixed(1)}%</span>` : 'N/A';

    const sensDistDisplay = c.dist_to_sensitive_km ? `${c.dist_to_sensitive_km.toFixed(2)} km` : (c.dist_to_sensitive_m ? `${(c.dist_to_sensitive_m / 1000).toFixed(2)} km` : '1.2 km');
    const sensStatusDisplay = c.sensitive_status ? `<div style="font-size: 0.7rem; color: ${c.sensitive_score >= 0.80 ? '#34d399' : '#f59e0b'}; font-weight: 500;">${c.sensitive_status}</div>` : '';

    tr.innerHTML = `
      <td>
        <div style="font-weight: 600;">${c.town_name}</div>
          <div style="font-size: 0.75rem; color: var(--text-secondary);">${c.state_name}</div>
          <div>${provenanceBadge(c, 'sm')}</div>
        </td>
      <td>
        ${lotPlanDisplay}
        ${addressDisplay}
      </td>
      <td><span class="score-badge ${scoreClass}">${c.suitability_score.toFixed(3)}</span></td>
      <td>
        <span style="font-size: 0.85rem; font-weight: 600; color: #c084fc;">${sensDistDisplay}</span>
        ${sensStatusDisplay}
      </td>
      <td>${slopeDisplay}</td>
      <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">${c.area_ha.toFixed(1)} ha</td>
      <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">${c.dist_to_substation_km ? c.dist_to_substation_km.toFixed(2) + ' km' : 'N/A'}</td>
      <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">${c.dist_to_wwtw_km ? c.dist_to_wwtw_km.toFixed(2) + ' km' : 'N/A'}</td>
    `;

    tr.addEventListener('click', () => {
      updateAuditPanel(c);
      const marker = markerMap[c.mb_code21];
      if (marker) {
        let lat, lon;
        if (c.geometry && c.geometry.startsWith('POINT')) {
          const coords = c.geometry.replace('POINT(', '').replace('POINT (', '').replace(')', '').split(' ');
          lon = parseFloat(coords[0]);
          lat = parseFloat(coords[1]);
          map.setView([lat, lon], 12);
        }
        marker.openPopup();
      }

      if (isMicroSited(c)) {
        ['precinct', 'netdev', 'pipelines'].forEach(k => {
          toggleLayer(k, true);
          const chk = document.getElementById('layer-chk-' + k);
          if (chk) chk.checked = true;
        });
      }
    });

    tableBody.appendChild(tr);
  });
}

function updateStats() {
  if (document.getElementById('stat-total')) {
    document.getElementById('stat-total').textContent = candidatesData.length;
  }
  const statesSet = new Set(candidatesData.map(c => c.state_name));
  if (document.getElementById('stat-states')) {
    document.getElementById('stat-states').textContent = statesSet.size;
  }
  
  const nswCandidates = candidatesData.filter(isMicroSited);   // best MEASURED candidate
  if (nswCandidates.length > 0 && document.getElementById('stat-best')) {
    const sortedNSW = [...nswCandidates].sort((a, b) => b.suitability_score - a.suitability_score);
    document.getElementById('stat-best').textContent = `${sortedNSW[0].town_name} (${sortedNSW[0].suitability_score.toFixed(3)})`;
  }
}

// -------------------------------------------------------------
// Stakeholder Persona Configuration & Switcher Engine ("I am a...")
// Loaded from runner/attachments/persona_configs.json at build time.
// -------------------------------------------------------------
const PERSONA_CONFIGS = __PERSONA_CONFIGS_JSON__;

function selectPersona(personaKey) {
  const cfg = PERSONA_CONFIGS[personaKey];
  if (!cfg) return;

  const select = document.getElementById('persona-select');
  if (select && select.value !== personaKey) {
    select.value = personaKey;
  }

  // Apply weights to sliders
  const pSlider = document.getElementById('power-weight-slider');
  const sensSlider = document.getElementById('sensitive-weight-slider');
  const wSlider = document.getElementById('water-weight-slider');
  const sSlider = document.getElementById('size-weight-slider');
  const tSlider = document.getElementById('target-size-slider');
  const tsfChk = document.getElementById('tsf-toggle');

  if (pSlider) pSlider.value = cfg.weights.power;
  if (sensSlider) sensSlider.value = cfg.weights.sensitive;
  if (wSlider) wSlider.value = cfg.weights.water;
  if (sSlider) sSlider.value = cfg.weights.size;
  if (tSlider) tSlider.value = cfg.weights.targetSize;
  if (tsfChk) tsfChk.checked = !cfg.tsfExcluded;

  recalculateSimulation();
}

function openPersonaTab() {
  switchTab(null, 'strategic-personas');
  const tabCard = document.getElementById('benchmarking-tabs-card');
  if (tabCard) {
    tabCard.scrollIntoView({ behavior: 'smooth' });
  }
}

function renderDashboard() {
  candidatesData.sort((a, b) => {
    const aIsHighRez = isMicroSited(a) ? 1 : 0;   // micro-sited ranks above modeled baselines
    const bIsHighRez = isMicroSited(b) ? 1 : 0;
    if (aIsHighRez !== bIsHighRez) {
      return bIsHighRez - aIsHighRez;
    }
    return b.suitability_score - a.suitability_score;
  });
  
  updateMarkers();
  renderLeaderboard();
  updateStats();
}

// Initial render
renderDashboard();
selectPersona('general-public');

// Interactive Simulation Sandbox Handler
function recalculateSimulation() {
  const isDeDeclared = document.getElementById('tsf-toggle')?.checked || false;
  const statusLabel = document.getElementById('tsf-status-label');
  
  if (statusLabel) {
    if (isDeDeclared) {
      statusLabel.textContent = "TSF DE-DECLARED (Unlocked)";
      statusLabel.style.color = "#10b981";
      if (typeof localNetDevelopable !== 'undefined' && localNetDevelopable) {
        localNetDevelopable.setStyle({ color: "#10b981", fillColor: "#10b981", fillOpacity: 0.45 });
      }
    } else {
      statusLabel.textContent = "DAM DECLARED (Excluded)";
      statusLabel.style.color = "#ef4444";
      if (typeof localNetDevelopable !== 'undefined' && localNetDevelopable) {
        localNetDevelopable.setStyle({ color: "#10b981", fillColor: "#10b981", fillOpacity: 0.25 });
      }
    }
  }

  const rawPw = parseFloat(document.getElementById('power-weight-slider')?.value) || 40;
  const rawSens = parseFloat(document.getElementById('sensitive-weight-slider')?.value) || 25;
  const rawWw = parseFloat(document.getElementById('water-weight-slider')?.value) || 20;
  const rawSw = parseFloat(document.getElementById('size-weight-slider')?.value) || 15;
  const targetSize = parseFloat(document.getElementById('target-size-slider')?.value) || 15.0;

  if (document.getElementById('power-weight-val')) document.getElementById('power-weight-val').textContent = `${Math.round(rawPw)}%`;
  if (document.getElementById('sensitive-weight-val')) document.getElementById('sensitive-weight-val').textContent = `${Math.round(rawSens)}%`;
  if (document.getElementById('water-weight-val')) document.getElementById('water-weight-val').textContent = `${Math.round(rawWw)}%`;
  if (document.getElementById('size-weight-val')) document.getElementById('size-weight-val').textContent = `${Math.round(rawSw)}%`;
  if (document.getElementById('target-size-val')) document.getElementById('target-size-val').textContent = `${targetSize} ha`;

  const totalWeight = (rawPw + rawSens + rawWw + rawSw) || 1.0;
  const normPw = rawPw / totalWeight;
  const normSens = rawSens / totalWeight;
  const normWw = rawWw / totalWeight;
  const normSw = rawSw / totalWeight;

  function calcDynamicSizeScore(area) {
    if (area === null || area === undefined || isNaN(area)) return 0.0;
    if (area >= targetSize) return 1.0;
    if (area < 3.0) return 0.1;
    return 0.1 + (0.9 * (area - 3.0) / (targetSize - 3.0));
  }

  candidatesData.forEach(c => {
    const sizeScore = calcDynamicSizeScore(c.area_ha);
    const sensScore = c.sensitive_score !== undefined ? c.sensitive_score : 1.0;
    
    if (c.is_excluded || (c.slope_pct !== undefined && c.slope_pct > 5.0)) {
      c.suitability_score = 0.0;
    } else {
      c.suitability_score = (c.power_score * normPw) + (sensScore * normSens) + (c.water_score * normWw) + (sizeScore * normSw);
    }
  });

  renderDashboard();

  const selectedSiteTitle = document.getElementById('audit-site-title')?.textContent;
  if (selectedSiteTitle) {
    const cleanTitle = selectedSiteTitle.split(' (')[0];
    const match = candidatesData.find(c => c.town_name === cleanTitle);
    if (match) updateAuditPanel(match, false);
  }
}

['tsf-toggle', 'power-weight-slider', 'sensitive-weight-slider', 'water-weight-slider', 'size-weight-slider', 'target-size-slider'].forEach(id => {
  const el = document.getElementById(id);
  if (el) {
    el.addEventListener('input', recalculateSimulation);
    el.addEventListener('change', recalculateSimulation);
  }
});

// State Benchmarking Table
const stateTableBody = document.getElementById('state-table-body');
if (stateTableBody) {
  stateData.forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="font-weight: 600;">${s.state_name}${simulatedGroupTag(s.state_name, 'state_name', 'All candidates in this state are simulated regional baselines, not measured site assessments.')}</td>
      <td>${s.candidate_count}</td>
      <td><span class="score-badge ${s.avg_suitability_score >= 0.85 ? 'score-high' : 'score-med'}">${s.avg_suitability_score.toFixed(3)}</span></td>
      <td>${s.avg_area_ha.toFixed(1)} ha</td>
      <td>${s.avg_dist_substation_km.toFixed(2)} km</td>
      <td>${s.avg_dist_wwtw_km.toFixed(2)} km</td>
      <td style="color: #c084fc; font-weight: 600;">${s.avg_dist_sensitive_km.toFixed(2)} km</td>
      <td style="color: ${s.avg_slope_pct <= 5.0 ? '#34d399' : '#ef4444'}; font-weight: 600;">${s.avg_slope_pct.toFixed(1)}%</td>
    `;
    stateTableBody.appendChild(tr);
  });
}

// Regional Aggregates Table
const regionTableBody = document.getElementById('region-table-body');
if (regionTableBody) {
  regionData.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="font-weight: 600;">${r.region_name}${simulatedGroupTag(r.region_name, 'region_name', 'Simulated regional baseline — modeled comparator, not a measured site assessment.')}</td>
      <td>${r.state_name}</td>
      <td>${r.candidate_count}</td>
      <td><span class="score-badge ${r.avg_suitability_score >= 0.85 ? 'score-high' : 'score-med'}">${r.avg_suitability_score.toFixed(3)}</span></td>
      <td>${r.avg_area_ha.toFixed(1)} ha</td>
      <td>${r.avg_dist_substation_km.toFixed(2)} km</td>
      <td style="color: #c084fc; font-weight: 600;">${r.avg_dist_sensitive_km.toFixed(2)} km</td>
    `;
    regionTableBody.appendChild(tr);
  });
}

// Tab navigation handler
function switchTab(evt, tabId) {
  const contents = document.querySelectorAll('.tab-content');
  contents.forEach(c => c.classList.remove('active'));
  
  const buttons = document.querySelectorAll('.tab-btn');
  buttons.forEach(b => b.classList.remove('active'));
  
  const target = document.getElementById(tabId);
  if (target) target.classList.add('active');
  if (evt && evt.currentTarget) {
    evt.currentTarget.classList.add('active');
  } else {
    const btn = document.querySelector(`.tab-btn[onclick*="'${tabId}'"]`);
    if (btn) btn.classList.add('active');
  }
}

// Render Calculations Tab dynamically
const calcContainer = document.getElementById('calculations-container');
const calcReferences = __CALCULATION_REFERENCES_JSON__;
if (calcContainer && calcReferences) {
  Object.keys(calcReferences).forEach(key => {
    const item = calcReferences[key];
    const card = document.createElement('div');
    card.className = 'card';
    card.style.background = 'rgba(15, 23, 42, 0.6)';
    card.style.borderColor = 'rgba(59, 130, 246, 0.3)';
    
    let variablesHtml = '';
    if (item.variables) {
      variablesHtml = `<div style="margin-top: 0.5rem; font-size: 0.85rem;"><strong style="color: #94a3b8;">Variables:</strong><ul style="margin-left: 1.25rem; margin-top: 0.25rem;">` +
        Object.keys(item.variables).map(v => `<li><code>${v}</code>: ${item.variables[v]}</li>`).join('') + `</ul></div>`;
    }

    let refsHtml = '';
    if (item.references) {
      refsHtml = `<div style="margin-top: 0.5rem; font-size: 0.85rem;"><strong style="color: #94a3b8;">Citations & Evidence:</strong><ul style="margin-left: 1.25rem; margin-top: 0.25rem;">` +
        item.references.map(ref => `<li>${ref.citation} <a href="${ref.url}" target="_blank" style="color: #60a5fa; text-decoration: none;">[Link]</a></li>`).join('') + `</ul></div>`;
    }

    card.innerHTML = `
      <h3 style="color: #60a5fa; margin-top: 0; font-size: 1.1rem;">${item.name || key}</h3>
      <p style="color: #cbd5e1; font-size: 0.9rem;">${item.description || ''}</p>
      <div style="background: rgba(0, 0, 0, 0.4); padding: 0.75rem 1rem; border-radius: 0.375rem; font-family: 'JetBrains Mono', monospace; color: #34d399; font-size: 0.9rem; margin: 0.5rem 0;">
        ${item.formula || ''}
      </div>
      ${variablesHtml}
      ${refsHtml}
    `;
    calcContainer.appendChild(card);
  });
}
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Assemble final HTML — all content from runner/attachments/
# ---------------------------------------------------------------------------
html_final = HTML_PAGE
html_final = html_final.replace("__FOOTER_TIMESTAMP__", datetime.datetime.now().astimezone().strftime("%Y%m%d%H%M"))
# Data
html_final = html_final.replace("__CANDIDATES_JSON__", json.dumps(candidates))
html_final = html_final.replace("__STATE_JSON__", json.dumps(state_list))
html_final = html_final.replace("__REGION_JSON__", json.dumps(region_list))
html_final = html_final.replace("__PRECINCT_BOUNDARY_JSON__", json.dumps(precinct_geojson))
html_final = html_final.replace("__NET_DEVELOPABLE_JSON__", json.dumps(net_dev_geojson))
html_final = html_final.replace("__PIPELINES_JSON__", json.dumps(pipelines_geojson))
html_final = html_final.replace("__RAIL_NETWORK_JSON__", json.dumps(rail_geojson))
html_final = html_final.replace("__BIODIVERSITY_JSON__", json.dumps(bio_geojson))
html_final = html_final.replace("__CALCULATION_REFERENCES_JSON__", json.dumps(calculations_only))
# Attachments (content files from runner/attachments/)
html_final = html_final.replace("__CDN_ASSETS__", load_attachment("cdn_assets.html"))
html_final = html_final.replace("__PROVENANCE_JS__", load_attachment("dashboard_provenance.js"))
html_final = html_final.replace("__PERSONA_CONFIGS_JSON__", load_attachment("persona_configs.json"))
html_final = html_final.replace("__METHODOLOGY_NOTES__", notes_html)
html_final = html_final.replace("__STRATEGIC_PERSONAS_HTML__", load_attachment("strategic_personas.html"))
html_final = html_final.replace("__DATA_SOURCES_ROWS__", load_attachment("data_sources.html"))
html_final = html_final.replace("__LAKEHOUSE_STORAGE_HTML__", load_attachment("lakehouse_storage.html"))
html_final = html_final.replace("__TABLE_FOOTPRINT_HTML__", load_attachment("table_footprint.html"))
html_final = html_final.replace("__RECENT_CHANGES_HTML__", load_attachment("recent_changes.html"))
html_final = html_final.replace("__NEXT_STEPS_HTML__", load_attachment("next_steps.html"))
html_final = html_final.replace("__COST_REDUCTION_HTML__", load_attachment("cost_reduction_tips.html"))
html_final = html_final.replace("__SPEED_MECHANICS_HTML__", load_attachment("speed_mechanics.html"))
html_final = html_final.replace("__SIMULATION_SANDBOX_HTML__", load_attachment("simulation_sandbox.html"))
html_final = html_final.replace("__WHITEPAPERS_HTML__", load_attachment("whitepapers.html"))

# Dynamic build timestamp
build_ts = datetime.datetime.now().strftime("%Y%m%d%H%M")
html_final = html_final.replace("__FOOTER_TIMESTAMP__", build_ts)

output_path = "runner/national_suitability_report.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_final)

print(f"Generated {output_path} successfully (Build timestamp: {build_ts}). Written size: {os.path.getsize(output_path):,} bytes.")
