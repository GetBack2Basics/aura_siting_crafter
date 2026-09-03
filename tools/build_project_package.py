#!/usr/bin/env python3
"""
AURA Siting Crafter — Project Package Builder
Builds standalone, high-precision site-specific WebGIS apps and statutory reports
from standardized project manifests (e.g. config/projects/LMCC_MacquarieCoal.json).
"""

import os
import sys
import json
import argparse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_manifest(manifest_path):
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_geojson_layer(rel_path):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"type": "FeatureCollection", "features": []}

def build_project_html_app(manifest, output_path):
    project_id = manifest['project_id']
    project_name = manifest['project_name']
    lga = manifest['lga']
    state = manifest['state']
    metrics = manifest['engineering_metrics']
    benchmarks = manifest['benchmarks']
    coords = manifest['coordinates']
    sectors = manifest['target_sectors']
    layers = manifest['spatial_layers']
    timestamp = datetime.now().strftime('%Y%m%d%H%M')

    # Load GeoJSON data directly to embed inline
    geo_boundary = load_geojson_layer(layers.get('precinct_boundary', ''))
    geo_pads = load_geojson_layer(layers.get('developable_pads', ''))
    geo_staging = load_geojson_layer(layers.get('staging_phases', ''))
    geo_phes = load_geojson_layer(layers.get('utilities_power_water', ''))
    geo_railroad = load_geojson_layer(layers.get('transport_rail_road', ''))
    geo_subsidence = load_geojson_layer(layers.get('geotechnical_subsidence', ''))
    geo_biolink = load_geojson_layer(layers.get('environmental_biolink', ''))
    geo_acoustic = load_geojson_layer(layers.get('acoustic_buffers_bunds', ''))

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} | AURA Site Assessment</title>
    <!-- MapLibre GL CSS -->
    <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
    <style>
        :root {{
            --bg-dark: #0f172a;
            --bg-panel: rgba(30, 41, 59, 0.94);
            --border-panel: rgba(255, 255, 255, 0.12);
            --primary: #38bdf8;
            --accent: #22c55e;
            --warning: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: var(--font-sans);
            background-color: var(--bg-dark);
            color: var(--text-main);
            overflow: hidden;
            height: 100vh;
            width: 100vw;
            display: flex;
        }}
        #map {{
            flex: 1;
            height: 100%;
            background: #090d16;
        }}
        .sidebar {{
            width: 440px;
            height: 100%;
            background: var(--bg-panel);
            backdrop-filter: blur(16px);
            border-right: 1px solid var(--border-panel);
            display: flex;
            flex-direction: column;
            z-index: 10;
            overflow-y: auto;
        }}
        .header {{
            padding: 24px 20px 20px 20px;
            border-bottom: 1px solid var(--border-panel);
            background: rgba(15, 23, 42, 0.7);
        }}
        h1 {{
            font-size: 20px;
            font-weight: 800;
            line-height: 1.3;
            margin-bottom: 6px;
            color: #ffffff;
        }}
        .subtitle {{
            font-size: 13px;
            color: var(--text-muted);
        }}
        .section {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-panel);
        }}
        .section-title {{
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--primary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }}
        .metric-card {{
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid var(--border-panel);
            padding: 10px 12px;
            border-radius: 6px;
        }}
        .metric-label {{
            font-size: 11px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }}
        .metric-value {{
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
        }}
        .metric-sub {{
            font-size: 10px;
            color: var(--accent);
        }}
        .layer-toggle {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 10px;
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid var(--border-panel);
            border-radius: 6px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .layer-toggle:hover {{
            background: rgba(56, 189, 248, 0.1);
            border-color: rgba(56, 189, 248, 0.4);
        }}
        .layer-info {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
        }}
        .layer-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }}
        .benchmark-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            margin-top: 8px;
        }}
        .benchmark-table th, .benchmark-table td {{
            padding: 6px 8px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }}
        .benchmark-table th {{
            color: var(--text-muted);
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 9px 12px;
            border-radius: 6px;
            font-size: 11.5px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
        }}
        .btn-primary {{
            background: #0284c7;
            color: #ffffff;
            width: 100%;
            margin-top: 6px;
        }}
        .btn-primary:hover {{
            background: #0369a1;
        }}
        .btn-outline {{
            background: rgba(30, 41, 59, 0.6);
            color: #93c5fd;
            border: 1px solid rgba(59, 130, 246, 0.3);
            width: 100%;
            margin-top: 6px;
        }}
        .btn-outline:hover {{
            background: rgba(59, 130, 246, 0.2);
            color: #ffffff;
        }}
    </style>
</head>
<body>

<div class="sidebar">
    <div class="header">
        <h1>{project_name}</h1>
        <div class="subtitle">{lga}, {state} | Proponent: DPHI, Lake Macquarie Council & Glencore</div>
    </div>

    <!-- Core Engineering Metrics -->
    <div class="section">
        <div class="section-title">Precinct Yield & Capacity</div>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Net Developable Area (NDA)</div>
                <div class="metric-value">{metrics['net_developable_area_ha']:.1f} ha</div>
                <div class="metric-sub">{metrics['immediate_phase1_ha']:.1f} ha Phase 1 Immediate</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">330kV Grid Reserve</div>
                <div class="metric-value">{metrics['power_capacity_mva']:.0f} MVA</div>
                <div class="metric-sub">Lines 21/22 Adjacent</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Pumped Hydro (PHES)</div>
                <div class="metric-value">{metrics['pumped_hydro_capacity_mwh']:.1f} MWh</div>
                <div class="metric-sub">120m Void Head</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Intermodal Rail Freight</div>
                <div class="metric-value">{metrics['rail_freight_capacity_tpa']:,.0f} t/yr</div>
                <div class="metric-sub">1.8km Active Siding</div>
            </div>
        </div>
    </div>

    <!-- Interactive Layer Controls -->
    <div class="section">
        <div class="section-title">Site-Level Micro-Layers</div>
        <div class="layer-toggle" onclick="toggleLayer('pads')">
            <div class="layer-info">
                <div class="layer-dot" style="background: #38bdf8;"></div>
                <span>10 Certified Developable Pads (NDPs)</span>
            </div>
            <input type="checkbox" id="chk-pads" checked>
        </div>
        <div class="layer-toggle" onclick="toggleLayer('phes')">
            <div class="layer-info">
                <div class="layer-dot" style="background: #eab308;"></div>
                <span>330kV Substation & 49 MWh PHES</span>
            </div>
            <input type="checkbox" id="chk-phes" checked>
        </div>
        <div class="layer-toggle" onclick="toggleLayer('railroad')">
            <div class="layer-info">
                <div class="layer-dot" style="background: #f97316;"></div>
                <span>Rail Intermodal Loop & 7.8km Haul Road</span>
            </div>
            <input type="checkbox" id="chk-railroad" checked>
        </div>
        <div class="layer-toggle" onclick="toggleLayer('subsidence')">
            <div class="layer-info">
                <div class="layer-dot" style="background: #ef4444;"></div>
                <span>Subsidence Advisory G1-G3 Zones</span>
            </div>
            <input type="checkbox" id="chk-subsidence" checked>
        </div>
        <div class="layer-toggle" onclick="toggleLayer('biolink')">
            <div class="layer-info">
                <div class="layer-dot" style="background: #22c55e;"></div>
                <span>Sugarloaf-Awaba C2 Koala Bio-Link</span>
            </div>
            <input type="checkbox" id="chk-biolink" checked>
        </div>
        <div class="layer-toggle" onclick="toggleLayer('acoustic')">
            <div class="layer-info">
                <div class="layer-dot" style="background: #a855f7;"></div>
                <span>6m-8m Acoustic Bunds & 500m Buffer</span>
            </div>
            <input type="checkbox" id="chk-acoustic" checked>
        </div>
    </div>

    <!-- Comparative Benchmark -->
    <div class="section">
        <div class="section-title">Benchmark vs National Baseline</div>
        <table class="benchmark-table">
            <thead>
                <tr>
                    <th>Domain</th>
                    <th>Site Value</th>
                    <th>National Avg</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Transmission Dist</td>
                    <td><b style="color:#22c55e;">{benchmarks['transmission_dist_km']} km</b></td>
                    <td>{benchmarks['national_avg_transmission_km']} km</td>
                </tr>
                <tr>
                    <td>Recycled Water Cooling</td>
                    <td><b style="color:#22c55e;">{benchmarks['water_recycled_pct']}%</b></td>
                    <td>{benchmarks['national_avg_water_recycled_pct']}%</td>
                </tr>
                <tr>
                    <td>NDA Net-to-Gross</td>
                    <td><b style="color:#38bdf8;">{benchmarks['net_to_gross_efficiency_pct']}%</b></td>
                    <td>{benchmarks['national_avg_net_to_gross_pct']}%</td>
                </tr>
                <tr>
                    <td>Data Depth Quality</td>
                    <td><b style="color:#22c55e;">{benchmarks['data_depth_tier']}</b></td>
                    <td>Tier-2 Regional</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Navigation & Reports Suite -->
    <div class="section" style="margin-top:auto;">
        <div class="section-title">Reports & Architecture Suite</div>
        <a href="report_{project_id}.html" target="_blank" class="btn btn-primary">
            📑 Statutory Site Siting Report ↗
        </a>
        <a href="../docs/macquarie_coal_precinct_site_enhancement_plan.html" target="_blank" class="btn btn-outline">
            🗺️ 6-Pillar Site Enhancement Plan ↗
        </a>
        <a href="../docs/project_specific_site_enhancement_architecture_plan.html" target="_blank" class="btn btn-outline">
            🏗️ Multi-Project Architecture Plan ↗
        </a>
        <a href="../national_suitability_report.html" target="_blank" class="btn btn-outline">
            🇦🇺 National Suitability Report ↗
        </a>
        <a href="../index.html" class="btn btn-outline">
            🌐 National Siting Overview ↗
        </a>
        <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 0.72rem; color: #94a3b8; line-height: 1.5; text-align: center;">
            &copy;&reg; 2026 GetBack2Basics - <a href="https://github.com/GetBack2Basics" target="_blank" style="color: #60a5fa; text-decoration: underline;">github.com/getback2basics</a> | This is an independent, personal research project exploring open data and modern cloud-native architectures. All (perceived) opinions are my own. The data tells the story, no matter what your driver is or isn't | {timestamp}
        </div>
    </div>
</div>

<div id="map"></div>

<!-- Embedded GeoJSON Datasets for Instant, Zero-Network Rendering -->
<script>
    const geoBoundary = {json.dumps(geo_boundary)};
    const geoPads = {json.dumps(geo_pads)};
    const geoStaging = {json.dumps(geo_staging)};
    const geoPhes = {json.dumps(geo_phes)};
    const geoRailroad = {json.dumps(geo_railroad)};
    const geoSubsidence = {json.dumps(geo_subsidence)};
    const geoBiolink = {json.dumps(geo_biolink)};
    const geoAcoustic = {json.dumps(geo_acoustic)};
</script>

<!-- MapLibre GL JS -->
<script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
<script>
    const map = new maplibregl.Map({{
        container: 'map',
        style: {{
            version: 8,
            sources: {{
                'osm-raster': {{
                    type: 'raster',
                    tiles: ['https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png'],
                    tileSize: 256,
                    attribution: '&copy; OpenStreetMap contributors'
                }}
            }},
            layers: [
                {{
                    id: 'osm-tiles',
                    type: 'raster',
                    source: 'osm-raster',
                    minzoom: 0,
                    maxzoom: 19
                }}
            ]
        }},
        center: [{coords['lon']}, {coords['lat']}],
        zoom: {coords['zoom']}
    }});

    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.on('load', () => {{
        // Add Boundary
        map.addSource('boundary', {{
            type: 'geojson',
            data: geoBoundary
        }});
        map.addLayer({{
            id: 'layer-boundary',
            type: 'line',
            source: 'boundary',
            paint: {{
                'line-color': '#ffffff',
                'line-width': 2,
                'line-dasharray': [4, 2]
            }}
        }});

        // Add Developable Pads
        map.addSource('pads', {{
            type: 'geojson',
            data: geoPads
        }});
        map.addLayer({{
            id: 'layer-pads-fill',
            type: 'fill',
            source: 'pads',
            paint: {{
                'fill-color': '#38bdf8',
                'fill-opacity': 0.4
            }}
        }});
        map.addLayer({{
            id: 'layer-pads-line',
            type: 'line',
            source: 'pads',
            paint: {{
                'line-color': '#0284c7',
                'line-width': 2
            }}
        }});

        // Add PHES & Substation
        map.addSource('phes', {{
            type: 'geojson',
            data: geoPhes
        }});
        map.addLayer({{
            id: 'layer-phes-fill',
            type: 'fill',
            source: 'phes',
            paint: {{
                'fill-color': '#eab308',
                'fill-opacity': 0.5
            }}
        }});
        map.addLayer({{
            id: 'layer-phes-line',
            type: 'line',
            source: 'phes',
            paint: {{
                'line-color': '#ca8a04',
                'line-width': 3
            }}
        }});

        // Add Rail & Road
        map.addSource('railroad', {{
            type: 'geojson',
            data: geoRailroad
        }});
        map.addLayer({{
            id: 'layer-railroad-line',
            type: 'line',
            source: 'railroad',
            paint: {{
                'line-color': '#f97316',
                'line-width': 4
            }}
        }});

        // Add Subsidence Zones
        map.addSource('subsidence', {{
            type: 'geojson',
            data: geoSubsidence
        }});
        map.addLayer({{
            id: 'layer-subsidence-fill',
            type: 'fill',
            source: 'subsidence',
            paint: {{
                'fill-color': ['get', 'color'],
                'fill-opacity': 0.25
            }}
        }});

        // Add Koala Bio-Link
        map.addSource('biolink', {{
            type: 'geojson',
            data: geoBiolink
        }});
        map.addLayer({{
            id: 'layer-biolink-fill',
            type: 'fill',
            source: 'biolink',
            paint: {{
                'fill-color': '#22c55e',
                'fill-opacity': 0.3
            }}
        }});

        // Add Acoustic Buffers
        map.addSource('acoustic', {{
            type: 'geojson',
            data: geoAcoustic
        }});
        map.addLayer({{
            id: 'layer-acoustic-fill',
            type: 'fill',
            source: 'acoustic',
            paint: {{
                'fill-color': '#a855f7',
                'fill-opacity': 0.2
            }}
        }});
        map.addLayer({{
            id: 'layer-acoustic-line',
            type: 'line',
            source: 'acoustic',
            paint: {{
                'line-color': '#9333ea',
                'line-width': 2,
                'line-dasharray': [2, 2]
            }}
        }});

        // Pad click popup
        map.on('click', 'layer-pads-fill', (e) => {{
            const props = e.features[0].properties;
            new maplibregl.Popup()
                .setLngLat(e.lngLat)
                .setHTML(`
                    <div style="font-family: sans-serif; font-size: 12px; color: #0f172a;">
                        <b style="font-size: 14px; color: #0284c7;">${{props.pad_id}}</b> (${{props.group}})<br>
                        <strong>Area:</strong> ${{props.area_ha}} ha | <strong>Phase:</strong> ${{props.phase}}<br>
                        <strong>Target:</strong> ${{props.target_use}}<br>
                        <strong>Bearing:</strong> ${{props.bearing_capacity_kpa}} kPa
                    </div>
                `)
                .addTo(map);
        }});
    }});

    function toggleLayer(layerKey) {{
        const chk = document.getElementById('chk-' + layerKey);
        const visible = chk.checked ? 'visible' : 'none';
        
        const layerMap = {{
            'pads': ['layer-pads-fill', 'layer-pads-line'],
            'phes': ['layer-phes-fill', 'layer-phes-line'],
            'railroad': ['layer-railroad-line'],
            'subsidence': ['layer-subsidence-fill'],
            'biolink': ['layer-biolink-fill'],
            'acoustic': ['layer-acoustic-fill', 'layer-acoustic-line']
        }};
        
        if (layerMap[layerKey]) {{
            layerMap[layerKey].forEach(lyr => {{
                if (map.getLayer(lyr)) {{
                    map.setLayoutProperty(lyr, 'visibility', visible);
                }}
            }});
        }}
    }}
</script>
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content.strip() + '\n')
    print(f"Generated Project App: {output_path}")

def build_project_statutory_report(manifest, output_path):
    project_id = manifest['project_id']
    project_name = manifest['project_name']
    lga = manifest['lga']
    state = manifest['state']
    metrics = manifest['engineering_metrics']
    benchmarks = manifest['benchmarks']
    sectors = manifest['target_sectors']
    timestamp = datetime.now().strftime('%Y%m%d%H%M')

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} | Comprehensive Statutory Siting & Resilience Report</title>
    <style>
        :root {{
            --bg-page: #f8fafc;
            --bg-card: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --primary: #0284c7;
            --primary-dark: #0369a1;
            --accent: #16a34a;
            --border: #e2e8f0;
            --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: var(--font-sans);
            background: var(--bg-page);
            color: var(--text-main);
            line-height: 1.6;
            padding: 0 0 60px 0;
        }}
        .top-nav {{
            background: #0f172a;
            color: white;
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .top-nav-brand {{
            font-size: 14px;
            font-weight: 700;
            color: #38bdf8;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .top-nav-links {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .top-nav-link {{
            color: #cbd5e1;
            text-decoration: none;
            font-size: 12px;
            font-weight: 600;
            padding: 5px 10px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.08);
            transition: all 0.2s;
        }}
        .top-nav-link:hover {{
            background: #0284c7;
            color: white;
        }}
        .container {{
            max-width: 1040px;
            margin: 32px auto 0 auto;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            padding: 44px;
        }}
        .header-tag {{
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            color: var(--primary);
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        h1 {{
            font-size: 28px;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 12px;
            line-height: 1.25;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            background: #f1f5f9;
            padding: 16px 20px;
            border-radius: 8px;
            margin: 24px 0 36px 0;
            font-size: 13px;
        }}
        .meta-item b {{
            color: #334155;
            display: block;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        h2 {{
            font-size: 18px;
            font-weight: 700;
            color: #0f172a;
            margin: 32px 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
        }}
        p, ul {{
            font-size: 14.5px;
            color: #334155;
            margin-bottom: 16px;
        }}
        ul {{ padding-left: 24px; }}
        li {{ margin-bottom: 8px; }}
        .table-custom {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 13.5px;
        }}
        .table-custom th, .table-custom td {{
            padding: 10px 14px;
            text-align: left;
            border: 1px solid var(--border);
        }}
        .table-custom th {{
            background: #f8fafc;
            color: #475569;
            font-weight: 600;
        }}
        .badge-pill {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 700;
        }}
        .pill-green {{ background: #dcfce7; color: #15803d; }}
        .pill-blue {{ background: #e0f2fe; color: #0369a1; }}
        .pill-orange {{ background: #ffedd5; color: #c2410c; }}
        .suite-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin: 24px 0;
        }}
        .suite-card {{
            background: #f8fafc;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .suite-card h4 {{
            font-size: 15px;
            color: #0f172a;
            margin-bottom: 6px;
        }}
        .suite-card p {{
            font-size: 12.5px;
            color: var(--text-muted);
            margin-bottom: 16px;
        }}
        .btn-card {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 8px 14px;
            background: #0284c7;
            color: white;
            border-radius: 6px;
            text-decoration: none;
            font-size: 12px;
            font-weight: 700;
        }}
        .btn-card:hover {{ background: #0369a1; }}
        .action-banner {{
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            color: white;
            padding: 24px;
            border-radius: 8px;
            margin-top: 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .action-banner h3 {{
            font-size: 18px;
            margin-bottom: 4px;
        }}
        .action-banner p {{
            color: #e0f2fe;
            margin: 0;
            font-size: 13px;
        }}
        .btn-banner {{
            background: white;
            color: var(--primary-dark);
            padding: 10px 18px;
            border-radius: 6px;
            font-weight: 700;
            text-decoration: none;
            font-size: 13px;
            white-space: nowrap;
        }}
    </style>
</head>
<body>

<div class="top-nav">
    <div class="top-nav-brand">
        AURA Siting Crafter | Statutory Site Report ({project_id})
    </div>
    <div class="top-nav-links">
        <a href="index_{project_id}.html" target="_blank" class="top-nav-link">🌐 Interactive Site WebGIS</a>
        <a href="../docs/macquarie_coal_precinct_site_enhancement_plan.html" target="_blank" class="top-nav-link">🗺️ Site Enhancement Plan</a>
        <a href="../docs/project_specific_site_enhancement_architecture_plan.html" target="_blank" class="top-nav-link">🏗️ Architecture Plan</a>
        <a href="../national_suitability_report.html" target="_blank" class="top-nav-link">🇦🇺 National Baseline</a>
        <a href="https://www.planningportal.nsw.gov.au/ppr/post-exhibition/macquarie-coal-complex-transformation-precinct" target="_blank" class="top-nav-link">🏛️ NSW Planning Portal ↗</a>
    </div>
</div>

<div class="container">
    <div class="header-tag">AURA Siting Crafter | Statutory Site Report</div>
    <h1>{project_name}</h1>
    <p style="font-size: 16px; color: var(--text-muted);">
        Comprehensive Statutory Siting & Resilience Report — State Significant Rezoning Assessment
    </p>

    <div class="meta-grid">
        <div class="meta-item">
            <b>Jurisdiction</b>
            {lga}, {state}
        </div>
        <div class="meta-item">
            <b>Gross Footprint</b>
            {metrics['gross_area_ha']:.0f} ha
        </div>
        <div class="meta-item">
            <b>Net Developable Area</b>
            {metrics['net_developable_area_ha']:.1f} ha ({metrics['immediate_phase1_ha']:.1f} ha Ph. 1)
        </div>
        <div class="meta-item">
            <b>High-Voltage Power</b>
            {metrics['power_capacity_mva']:.0f} MVA (330kV)
        </div>
    </div>

    <h2>1. Executive Summary & Statutory Siting Merits</h2>
    <p>
        The <strong>{project_name}</strong> represents one of the most strategically significant post-mining brownfield transition precincts in Australia. Located within the City of Lake Macquarie with direct frontage to <strong>Transgrid 330kV transmission lines</strong> and the Main Northern Railway, the precinct is primed for sovereign digital compute, clean energy firming, and advanced manufacturing.
    </p>
    <p>
        This site-specific report supplements the National Siting Baseline by detailing localized geotechnical certifications, 3-phase developable pad geometry, acoustic bund buffering, and closed-loop non-potable cooling integration.
    </p>

    <h2>2. Site vs. National Comparative Benchmark</h2>
    <table class="table-custom">
        <thead>
            <tr>
                <th>Planning & Infrastructure Metric</th>
                <th>Site Certified Value</th>
                <th>National Baseline Avg</th>
                <th>Strategic Advantage</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><b>Grid Transmission Proximity</b></td>
                <td><span class="badge-pill pill-green">{benchmarks['transmission_dist_km']} km (330kV)</span></td>
                <td>{benchmarks['national_avg_transmission_km']} km</td>
                <td>Top 5% nationwide; zero new long-range lines required</td>
            </tr>
            <tr>
                <td><b>Industrial Cooling Water Source</b></td>
                <td><span class="badge-pill pill-green">{benchmarks['water_recycled_pct']}% Tertiary Recycled</span></td>
                <td>{benchmarks['national_avg_water_recycled_pct']}% Recycled</td>
                <td>Saves 1.25 GL/yr drinking water via Edgeworth WWTW</td>
            </tr>
            <tr>
                <td><b>Net Developable Yield Ratio</b></td>
                <td><span class="badge-pill pill-blue">{benchmarks['net_to_gross_efficiency_pct']}% Net-to-Gross</span></td>
                <td>{benchmarks['national_avg_net_to_gross_pct']}% Net-to-Gross</td>
                <td>10 certified pads with staged civil earthworks</td>
            </tr>
            <tr>
                <td><b>Energy Storage & Peaking Asset</b></td>
                <td><span class="badge-pill pill-orange">49.0 MWh Micro-PHES + 100MW BESS</span></td>
                <td>Ad-hoc BESS only</td>
                <td>120m void head delivers synchronous green inertia</td>
            </tr>
        </tbody>
    </table>

    <h2>3. 3-Phase Net Developable Pad Staging Plan</h2>
    <table class="table-custom">
        <thead>
            <tr>
                <th>Phase</th>
                <th>Time Horizon</th>
                <th>Pads Included</th>
                <th>Area (ha)</th>
                <th>Target Industrial Clusters</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><b>Phase 1</b></td>
                <td>Years 0–3 (Immediate)</td>
                <td>Pads A1–A4 (MCPP Plateau), C1–C2 (Teralba Gateways)</td>
                <td>82.7 ha</td>
                <td>Sovereign AI Data Centres, Advanced Manufacturing, Rail Intermodal</td>
            </tr>
            <tr>
                <td><b>Phase 2</b></td>
                <td>Years 3–7 (Medium)</td>
                <td>Pads B1–B3 (Westside Void Floor & Pit)</td>
                <td>125.4 ha</td>
                <td>Heavy Transport Fleet, Modular Construction, Circular Economy</td>
            </tr>
            <tr>
                <td><b>Phase 3</b></td>
                <td>Years 7–12+ (Long)</td>
                <td>Pad D1 (Tailings Storage Facility Plateau)</td>
                <td>112.0 ha</td>
                <td>Solar PV Array, 100MW Grid-Scale BESS, Clean Tech Hardstand</td>
            </tr>
        </tbody>
    </table>

    <h2>4. Pre-Approved Subsidence Advisory Geotechnical Matrix</h2>
    <table class="table-custom">
        <thead>
            <tr>
                <th>Geotechnical Zone</th>
                <th>Mine Workings Profile</th>
                <th>Certified Foundation Standard</th>
                <th>DA Approval Pathway</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><b>Zone G1</b></td>
                <td>Intact bedrock, unmined ridge</td>
                <td>Standard spread footings (>300 kPa allowable bearing)</td>
                <td>Expedited 14-day signoff</td>
            </tr>
            <tr>
                <td><b>Zone G2</b></td>
                <td>Deep stable workings (>100m depth)</td>
                <td>Articulated stiffened raft slabs (3mm/m strain design)</td>
                <td>Standard 30-day compliance</td>
            </tr>
            <tr>
                <td><b>Zone G3</b></td>
                <td>Shallow bord-and-pillar workings (<50m depth)</td>
                <td>Pressure-grouted void consolidation or socketed piles</td>
                <td>Detailed geotechnical signoff</td>
            </tr>
        </tbody>
    </table>

    <h2>5. Site Enhancement & Architecture Documentation Suite</h2>
    <div class="suite-grid">
        <div class="suite-card">
            <div>
                <h4>🗺️ 6-Pillar Site Enhancement Plan</h4>
                <p>Complete statutory analysis covering 10 Net Developable Pads, 330kV substation pad, 49 MWh PHES, Koala bio-link corridor, and Hunter Water recycled cooling pipeline.</p>
            </div>
            <a href="../docs/macquarie_coal_precinct_site_enhancement_plan.html" target="_blank" class="btn-card">Read Site Enhancement Plan ↗</a>
        </div>
        <div class="suite-card">
            <div>
                <h4>🏗️ Multi-Project Siting Architecture</h4>
                <p>Engineering blueprint for project submission manifests, automated packaging pipelines, zero-mock spatial layers, and non-intrusive national deep linking.</p>
            </div>
            <a href="../docs/project_specific_site_enhancement_architecture_plan.html" target="_blank" class="btn-card">Read Architecture Plan ↗</a>
        </div>
        <div class="suite-card">
            <div>
                <h4>🌐 Interactive Site WebGIS</h4>
                <p>Live MapLibre WebGIS client featuring 3D topographic terrain, interactive layer filtering, and individual pad inspection.</p>
            </div>
            <a href="index_{project_id}.html" target="_blank" class="btn-card">Launch Site WebGIS ↗</a>
        </div>
    </div>

    <div class="action-banner">
        <div>
            <h3>Explore in Interactive 3D WebGIS</h3>
            <p>Inspect all 10 developable pads, live layer filters, and spatial constraints directly on the map.</p>
        </div>
        <a href="index_{project_id}.html" target="_blank" class="btn-banner">Launch Site WebGIS ↗</a>
    </div>
</div>

<!-- Standardized Universal Footer -->
<footer style="margin-top: 3rem; padding: 1.5rem 1rem; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 0.8rem; color: #94a3b8; text-align: center; line-height: 1.6;">
  &copy;&reg; 2026 GetBack2Basics - <a href="https://github.com/GetBack2Basics" target="_blank" style="color: #60a5fa; text-decoration: underline;">github.com/getback2basics</a> | This is an independent, personal research project exploring open data and modern cloud-native architectures. All (perceived) opinions are my own. The data tells the story, no matter what your driver is or isn't | {timestamp}
</footer>

</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content.strip() + '\n')
    print(f"Generated Project Statutory Report: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="AURA Project Package Builder")
    parser.add_argument("--manifest", required=True, help="Path to project manifest JSON")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    project_id = manifest["project_id"]

    # Generate inside both src/geolibre_frontend/projects AND runner/projects for direct web hosting
    app_out_frontend = os.path.join("src", "geolibre_frontend", "projects", f"index_{project_id}.html")
    report_out_runner = os.path.join("runner", "projects", f"report_{project_id}.html")

    # Also make a matching report in geolibre_frontend/projects and app in runner/projects so all links resolve relative
    app_out_runner = os.path.join("runner", "projects", f"index_{project_id}.html")
    report_out_frontend = os.path.join("src", "geolibre_frontend", "projects", f"report_{project_id}.html")

    os.makedirs(os.path.dirname(app_out_frontend), exist_ok=True)
    os.makedirs(os.path.dirname(report_out_runner), exist_ok=True)

    build_project_html_app(manifest, app_out_frontend)
    build_project_html_app(manifest, app_out_runner)
    build_project_statutory_report(manifest, report_out_runner)
    build_project_statutory_report(manifest, report_out_frontend)
    print(f"Project package for '{project_id}' built successfully in both frontend and runner suites.")

if __name__ == "__main__":
    main()
