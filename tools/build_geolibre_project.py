import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "src", "geolibre_frontend")
RUNNER_ATTACHMENTS = os.path.join(BASE_DIR, "runner", "attachments")

# 1. Candidate Hubs Data (17 National Siting Hubs with full MCE attributes)
candidates = [
    { "mb_code21": "NSW_MCC01", "town_name": "Teralba", "state_name": "New South Wales", "area_ha": 44.5, "slope_pct": 2.1, "dist_to_substation_km": 0.35, "dist_to_wwtw_km": 0.85, "dist_to_sensitive_km": 0.82, "suitability_score": 0.998, "pumped_hydro_capacity_mwh": 49.0, "lon": 151.60, "lat": -32.94 },
    { "mb_code21": "NSW_MCC02", "town_name": "Killingworth", "state_name": "New South Wales", "area_ha": 28.2, "slope_pct": 3.4, "dist_to_substation_km": 0.45, "dist_to_wwtw_km": 1.4, "dist_to_sensitive_km": 1.25, "suitability_score": 0.991, "pumped_hydro_capacity_mwh": 130.8, "lon": 151.56, "lat": -32.92 },
    { "mb_code21": "NSW_MCC03", "town_name": "Cockle Creek", "state_name": "New South Wales", "area_ha": 18.7, "slope_pct": 1.2, "dist_to_substation_km": 0.2, "dist_to_wwtw_km": 0.6, "dist_to_sensitive_km": 0.42, "suitability_score": 0.845, "pumped_hydro_capacity_mwh": 27.2, "lon": 151.62, "lat": -32.94 },
    { "mb_code21": "NSW_MCC04", "town_name": "West Lake", "state_name": "New South Wales", "area_ha": 35.0, "slope_pct": 4.1, "dist_to_substation_km": 1.1, "dist_to_wwtw_km": 2.1, "dist_to_sensitive_km": 1.8, "suitability_score": 0.922, "pumped_hydro_capacity_mwh": 196.2, "lon": 151.55, "lat": -32.96 },
    { "mb_code21": "QLD_GLD01", "town_name": "Yarwun", "state_name": "Queensland", "area_ha": 18.5, "slope_pct": 1.8, "dist_to_substation_km": 0.35, "dist_to_wwtw_km": 0.8, "dist_to_sensitive_km": 1.1, "suitability_score": 1.0, "pumped_hydro_capacity_mwh": 38.1, "lon": 151.25, "lat": -23.84 },
    { "mb_code21": "QLD_GLD02", "town_name": "Gladstone City", "state_name": "Queensland", "area_ha": 15.0, "slope_pct": 2.3, "dist_to_substation_km": 0.75, "dist_to_wwtw_km": 1.5, "dist_to_sensitive_km": 0.65, "suitability_score": 0.958, "pumped_hydro_capacity_mwh": 32.7, "lon": 151.17, "lat": -23.82 },
    { "mb_code21": "QLD_GLD03", "town_name": "Calliope", "state_name": "Queensland", "area_ha": 13.5, "slope_pct": 2.9, "dist_to_substation_km": 1.8, "dist_to_wwtw_km": 3.2, "dist_to_sensitive_km": 2.2, "suitability_score": 0.817, "pumped_hydro_capacity_mwh": 54.5, "lon": 151.21, "lat": -23.97 },
    { "mb_code21": "VIC_LTB01", "town_name": "Morwell", "state_name": "Victoria", "area_ha": 12.5, "slope_pct": 1.5, "dist_to_substation_km": 0.45, "dist_to_wwtw_km": 1.2, "dist_to_sensitive_km": 0.95, "suitability_score": 0.964, "pumped_hydro_capacity_mwh": 119.9, "lon": 146.40, "lat": -38.23 },
    { "mb_code21": "VIC_LTB02", "town_name": "Traralgon", "state_name": "Victoria", "area_ha": 8.2, "slope_pct": 2.0, "dist_to_substation_km": 1.2, "dist_to_wwtw_km": 2.5, "dist_to_sensitive_km": 1.6, "suitability_score": 0.819, "pumped_hydro_capacity_mwh": 76.3, "lon": 146.53, "lat": -38.19 },
    { "mb_code21": "VIC_LTB03", "town_name": "Moe", "state_name": "Victoria", "area_ha": 10.5, "slope_pct": 3.1, "dist_to_substation_km": 0.9, "dist_to_wwtw_km": 1.8, "dist_to_sensitive_km": 1.4, "suitability_score": 0.89, "pumped_hydro_capacity_mwh": 87.2, "lon": 146.26, "lat": -38.17 },
    { "mb_code21": "WA_COL01", "town_name": "Collie", "state_name": "Western Australia", "area_ha": 22.0, "slope_pct": 1.4, "dist_to_substation_km": 0.15, "dist_to_wwtw_km": 4.2, "dist_to_sensitive_km": 1.35, "suitability_score": 0.929, "pumped_hydro_capacity_mwh": 130.8, "lon": 116.15, "lat": -33.36 },
    { "mb_code21": "WA_COL02", "town_name": "Collie East", "state_name": "Western Australia", "area_ha": 17.5, "slope_pct": 2.2, "dist_to_substation_km": 0.6, "dist_to_wwtw_km": 3.5, "dist_to_sensitive_km": 2.1, "suitability_score": 0.936, "pumped_hydro_capacity_mwh": 109.0, "lon": 116.20, "lat": -33.35 },
    { "mb_code21": "ACT_CBR01", "town_name": "Fyshwick", "state_name": "Australian Capital Territory", "area_ha": 14.2, "slope_pct": 1.1, "dist_to_substation_km": 0.4, "dist_to_wwtw_km": 1.1, "dist_to_sensitive_km": 0.78, "suitability_score": 0.985, "pumped_hydro_capacity_mwh": 43.6, "lon": 149.172, "lat": -35.325 },
    { "mb_code21": "ACT_CBR02", "town_name": "Hume", "state_name": "Australian Capital Territory", "area_ha": 19.8, "slope_pct": 2.0, "dist_to_substation_km": 0.55, "dist_to_wwtw_km": 1.9, "dist_to_sensitive_km": 1.65, "suitability_score": 0.976, "pumped_hydro_capacity_mwh": 60.0, "lon": 149.164, "lat": -35.385 },
    { "mb_code21": "NT_DWN01", "town_name": "East Arm", "state_name": "Northern Territory", "area_ha": 24.5, "slope_pct": 0.8, "dist_to_substation_km": 0.5, "dist_to_wwtw_km": 1.6, "dist_to_sensitive_km": 2.4, "suitability_score": 0.987, "pumped_hydro_capacity_mwh": 21.8, "lon": 130.895, "lat": -12.482 },
    { "mb_code21": "SA_PTA01", "town_name": "Port Augusta", "state_name": "South Australia", "area_ha": 20.1, "slope_pct": 1.6, "dist_to_substation_km": 0.3, "dist_to_wwtw_km": 2.8, "dist_to_sensitive_km": 1.9, "suitability_score": 0.96, "pumped_hydro_capacity_mwh": 32.7, "lon": 137.780, "lat": -32.510 },
    { "mb_code21": "TAS_DEV01", "town_name": "Devonport", "state_name": "Tasmania", "area_ha": 16.4, "slope_pct": 2.4, "dist_to_substation_km": 0.7, "dist_to_wwtw_km": 1.5, "dist_to_sensitive_km": 1.15, "suitability_score": 0.971, "pumped_hydro_capacity_mwh": 38.1, "lon": 146.360, "lat": -41.190 }
]

candidates_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [c["lon"], c["lat"]]},
            "properties": {k: v for k, v in c.items() if k not in ("lon", "lat")}
        }
        for c in candidates
    ]
}

# 2. Key Transmission & Substation Infrastructure
substations = [
    {"name": "Teralba 330kV Bulk Terminal", "voltage_kv": 330, "state": "NSW", "substation_type": "Terminal Bulk", "lon": 151.603, "lat": -32.937},
    {"name": "Killingworth 132kV Switching Station", "voltage_kv": 132, "state": "NSW", "substation_type": "Switching Station", "lon": 151.564, "lat": -32.916},
    {"name": "Cockle Creek 132kV Substation", "voltage_kv": 132, "state": "NSW", "substation_type": "Zone Substation", "lon": 151.622, "lat": -32.938},
    {"name": "West Lake / Awaba 132kV Substation", "voltage_kv": 132, "state": "NSW", "substation_type": "Zone Substation", "lon": 151.541, "lat": -32.951},
    {"name": "Yarwun 275kV Terminal Station", "voltage_kv": 275, "state": "QLD", "substation_type": "Terminal Bulk", "lon": 151.253, "lat": -23.837},
    {"name": "Gladstone South 275kV Substation", "voltage_kv": 275, "state": "QLD", "substation_type": "Bulk Supply", "lon": 151.176, "lat": -23.814},
    {"name": "Calliope River 275kV Substation", "voltage_kv": 275, "state": "QLD", "substation_type": "Zone Substation", "lon": 151.206, "lat": -23.955},
    {"name": "Hazelwood / Morwell 500kV Terminal", "voltage_kv": 500, "state": "VIC", "substation_type": "Extra High Voltage Terminal", "lon": 146.396, "lat": -38.226},
    {"name": "Traralgon 220kV Terminal Station", "voltage_kv": 220, "state": "VIC", "substation_type": "Terminal Bulk", "lon": 146.521, "lat": -38.181},
    {"name": "Yallourn / Moe 220kV Substation", "voltage_kv": 220, "state": "VIC", "substation_type": "Zone Substation", "lon": 146.252, "lat": -38.163},
    {"name": "Muja / Collie 330kV Bulk Terminal", "voltage_kv": 330, "state": "WA", "substation_type": "SWIS Main Terminal", "lon": 116.149, "lat": -33.359},
    {"name": "Collie East 330kV Switching Station", "voltage_kv": 330, "state": "WA", "substation_type": "Switching Station", "lon": 116.195, "lat": -33.346},
    {"name": "Fyshwick 132kV Substation", "voltage_kv": 132, "state": "ACT", "substation_type": "Zone Substation", "lon": 149.168, "lat": -35.322},
    {"name": "Canberra / Hume 330kV Bulk Supply", "voltage_kv": 330, "state": "ACT", "substation_type": "Bulk Supply Substation", "lon": 149.161, "lat": -35.381},
    {"name": "Hudson Creek 132kV Terminal Station", "voltage_kv": 132, "state": "NT", "substation_type": "Terminal Bulk", "lon": 130.891, "lat": -12.478},
    {"name": "Davenport / Port Augusta 275kV Terminal", "voltage_kv": 275, "state": "SA", "substation_type": "Terminal Bulk", "lon": 137.778, "lat": -32.508},
    {"name": "Wesley Vale / Devonport 110kV Substation", "voltage_kv": 110, "state": "TAS", "substation_type": "Zone Substation", "lon": 146.354, "lat": -41.185}
]
substations_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]},
            "properties": {"substation_name": s["name"], "voltage_kv": s["voltage_kv"], "state_name": s["state"], "substation_type": s["substation_type"]}
        }
        for s in substations
    ]
}

# 3. Recycled Wastewater Treatment Plants
wwtw = [
    {"name": "Edgeworth Recycled Water Treatment Plant", "capacity_ml_day": 18.5, "state": "NSW", "lon": 151.608, "lat": -32.933},
    {"name": "Dora Creek Wastewater Treatment Works", "capacity_ml_day": 12.0, "state": "NSW", "lon": 151.551, "lat": -32.968},
    {"name": "Cockle Creek Industrial Effluent Plant", "capacity_ml_day": 8.0, "state": "NSW", "lon": 151.624, "lat": -32.945},
    {"name": "Gladstone Calliope Recycled Water Facility", "capacity_ml_day": 25.0, "state": "QLD", "lon": 151.244, "lat": -23.846},
    {"name": "Gippsland Water Factory (Morwell)", "capacity_ml_day": 35.0, "state": "VIC", "lon": 146.409, "lat": -38.239},
    {"name": "Collie Municipal Water Reclamation Plant", "capacity_ml_day": 10.0, "state": "WA", "lon": 116.155, "lat": -33.364},
    {"name": "Lower Molonglo Water Quality Control Centre", "capacity_ml_day": 90.0, "state": "ACT", "lon": 149.166, "lat": -35.328},
    {"name": "Leanyer Sanderson Wastewater Treatment Plant", "capacity_ml_day": 22.0, "state": "NT", "lon": 130.898, "lat": -12.486},
    {"name": "Port Augusta Wastewater Reclamation Plant", "capacity_ml_day": 14.0, "state": "SA", "lon": 137.785, "lat": -32.515},
    {"name": "Devonport Sewage Treatment Plant", "capacity_ml_day": 16.0, "state": "TAS", "lon": 146.365, "lat": -41.195}
]
wwtw_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [w["lon"], w["lat"]]},
            "properties": {"plant_name": w["name"], "capacity_ml_day": w["capacity_ml_day"], "state": w["state"], "cooling_ready": True}
        }
        for w in wwtw
    ]
}

# 4. Interstate & Regional Transmission Grid Lines
transmission_interstate_lines = [
    {"name": "Bayswater - Eraring 330kV Bulk Trunk", "voltage_kv": 330, "operator": "Transgrid", "coords": [[150.95, -32.40], [151.35, -32.70], [151.56, -32.92], [151.60, -32.94], [151.52, -33.06]]},
    {"name": "Gladstone - Stanwell 275kV Double Circuit", "voltage_kv": 275, "operator": "Powerlink", "coords": [[150.33, -23.55], [150.85, -23.70], [151.17, -23.82], [151.25, -23.84], [151.21, -23.97]]},
    {"name": "Loy Yang - Hazelwood 500kV Heavy Spine", "voltage_kv": 500, "operator": "AusNet", "coords": [[146.58, -38.25], [146.53, -38.19], [146.40, -38.23], [146.26, -38.17], [145.80, -38.10]]},
    {"name": "Muja - Western Power 330kV SWIS Backbone", "voltage_kv": 330, "operator": "Western Power", "coords": [[116.30, -33.42], [116.20, -33.35], [116.15, -33.36], [115.90, -33.10], [115.86, -31.95]]},
    {"name": "Canberra - Hume 330kV Capital Link", "voltage_kv": 330, "operator": "Transgrid / Evoenergy", "coords": [[148.95, -35.20], [149.12, -35.28], [149.172, -35.325], [149.164, -35.385], [149.20, -35.45]]},
    {"name": "Port Augusta - Davenport 275kV North Spine", "voltage_kv": 275, "operator": "ElectraNet", "coords": [[137.60, -32.40], [137.75, -32.48], [137.780, -32.510], [137.90, -32.65], [138.60, -34.80]]},
    {"name": "Sheffield - Devonport 110kV Hydro Feed", "voltage_kv": 110, "operator": "TasNetworks", "coords": [[146.30, -41.40], [146.33, -41.28], [146.360, -41.190], [146.40, -41.15]]}
]
transmission_interstate_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": line["coords"]},
            "properties": {"line_name": line["name"], "voltage_kv": line["voltage_kv"], "operator": line["operator"]}
        }
        for line in transmission_interstate_lines
    ]
}

transmission_regional_lines = [
    {"name": "Killingworth - Awaba 132kV Feeder", "voltage_kv": 132, "coords": [[151.56, -32.92], [151.58, -32.93], [151.55, -32.96]]},
    {"name": "Teralba - Cockle Creek 132kV Link", "voltage_kv": 132, "coords": [[151.60, -32.94], [151.61, -32.94], [151.62, -32.94]]},
    {"name": "Yarwun - Gladstone South 132kV Line", "voltage_kv": 132, "coords": [[151.25, -23.84], [151.20, -23.83], [151.17, -23.82]]},
    {"name": "Morwell - Traralgon 220kV Feeder", "voltage_kv": 220, "coords": [[146.40, -38.23], [146.47, -38.21], [146.53, -38.19]]},
    {"name": "Collie - Collie East 132kV Line", "voltage_kv": 132, "coords": [[116.15, -33.36], [116.18, -33.35], [116.20, -33.35]]}
]
transmission_regional_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": line["coords"]},
            "properties": {"line_name": line["name"], "voltage_kv": line["voltage_kv"]}
        }
        for line in transmission_regional_lines
    ]
}

# 5. Load Precinct Datasets
precinct_boundary_path = os.path.join(RUNNER_ATTACHMENTS, "layers", "precinct_boundary.json")
with open(precinct_boundary_path, "r", encoding="utf-8") as f:
    precinct_boundary_geojson = json.load(f)

net_developable_path = os.path.join(RUNNER_ATTACHMENTS, "layers", "net_developable.json")
with open(net_developable_path, "r", encoding="utf-8") as f:
    net_developable_geojson = json.load(f)

pipeline_corridors_path = os.path.join(RUNNER_ATTACHMENTS, "layers", "pipeline_corridors.json")
with open(pipeline_corridors_path, "r", encoding="utf-8") as f:
    pipeline_corridors_geojson = json.load(f)

biodiversity_path = os.path.join(RUNNER_ATTACHMENTS, "layers", "biodiversity_constraints.json")
with open(biodiversity_path, "r", encoding="utf-8") as f:
    biodiversity_geojson = json.load(f)

# 6. Receptors (Schools & Healthcare)
receptors_schools = [
    {"name": "Teralba Public School", "type": "Primary", "suburb": "Teralba", "state": "NSW", "lon": 151.605, "lat": -32.946},
    {"name": "Cockle Creek Technology High", "type": "Secondary", "suburb": "Cockle Creek", "state": "NSW", "lon": 151.618, "lat": -32.935},
    {"name": "Yarwun State School", "type": "Primary", "suburb": "Yarwun", "state": "QLD", "lon": 151.238, "lat": -23.848},
    {"name": "Morwell Central Primary School", "type": "Primary", "suburb": "Morwell", "state": "VIC", "lon": 146.392, "lat": -38.235},
    {"name": "Collie Senior High School", "type": "Secondary", "suburb": "Collie", "state": "WA", "lon": 116.142, "lat": -33.355},
    {"name": "St Clare of Assisi Primary (ACT)", "type": "Primary", "suburb": "Conder", "state": "ACT", "lon": 149.155, "lat": -35.378}
]
schools_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]},
            "properties": {"school_name": s["name"], "school_type": s["type"], "suburb": s["suburb"], "state": s["state"], "buffer_m": 500}
        }
        for s in receptors_schools
    ]
}

receptors_health = [
    {"name": "Lake Macquarie Private Hospital", "facility_type": "Private Hospital", "beds": 140, "emergency_dept": True, "state": "NSW", "lon": 151.645, "lat": -32.975},
    {"name": "Gladstone Base Hospital", "facility_type": "Public Hospital", "beds": 95, "emergency_dept": True, "state": "QLD", "lon": 151.258, "lat": -23.855},
    {"name": "Latrobe Regional Hospital (Traralgon)", "facility_type": "Regional Base Hospital", "beds": 280, "emergency_dept": True, "state": "VIC", "lon": 146.505, "lat": -38.192},
    {"name": "Collie District Hospital", "facility_type": "Public District Hospital", "beds": 35, "emergency_dept": True, "state": "WA", "lon": 116.158, "lat": -33.362},
    {"name": "Canberra Hospital (Garran)", "facility_type": "Tertiary Referral Hospital", "beds": 650, "emergency_dept": True, "state": "ACT", "lon": 149.102, "lat": -35.348}
]
health_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [h["lon"], h["lat"]]},
            "properties": {"facility_name": h["name"], "facility_type": h["facility_type"], "beds": h["beds"], "emergency_dept": h["emergency_dept"], "state": h["state"]}
        }
        for h in receptors_health
    ]
}

# 7. Surface Water Hydro Lines
hydro_lines = [
    {"name": "Cockle Creek Waterway", "order": 3, "coords": [[151.58, -32.91], [151.60, -32.93], [151.62, -32.95], [151.64, -32.97]]},
    {"name": "Calliope River Estuary", "order": 4, "coords": [[151.15, -23.95], [151.19, -23.90], [151.23, -23.85], [151.27, -23.80]]},
    {"name": "Morwell River Confluence", "order": 3, "coords": [[146.35, -38.28], [146.38, -38.25], [146.42, -38.21], [146.46, -38.17]]},
    {"name": "Collie River South Branch", "order": 3, "coords": [[116.10, -33.38], [116.15, -33.36], [116.22, -33.34], [116.28, -33.30]]}
]
hydro_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": hl["coords"]},
            "properties": {"feature_name": hl["name"], "strahler_order": hl["order"], "buffer_setback_m": 30}
        }
        for hl in hydro_lines
    ]
}

# 8. Heavy Freight & Transport Rail
rail_corridors = [
    {"name": "Main Northern Railway (Teralba / Cockle Creek)", "gauge": "Standard (1435mm)", "freight_access": "Unrestricted 25TAL", "coords": [[151.58, -32.92], [151.60, -32.94], [151.62, -32.94], [151.65, -32.95]]},
    {"name": "North Coast Line (Gladstone / Yarwun Freight Alignment)", "gauge": "Narrow (1067mm)", "freight_access": "Heavy Haul 30TAL", "coords": [[151.15, -23.80], [151.17, -23.82], [151.21, -23.84], [151.25, -23.84]]},
    {"name": "Gippsland Railway (Morwell / Traralgon / Moe Line)", "gauge": "Broad (1600mm)", "freight_access": "Heavy Freight", "coords": [[146.20, -38.16], [146.26, -38.17], [146.40, -38.23], [146.53, -38.19]]},
    {"name": "South Western Railway (Collie Coal & Mineral Freight)", "gauge": "Narrow (1067mm)", "freight_access": "Heavy Haul", "coords": [[116.10, -33.38], [116.15, -33.36], [116.20, -33.35], [116.25, -33.32]]}
]
rail_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": rc["coords"]},
            "properties": {"line_name": rc["name"], "gauge": rc["gauge"], "freight_access": rc["freight_access"]}
        }
        for rc in rail_corridors
    ]
}

# 9. ABS Meshblocks & Geoscape Cadastre Representative Fabric
abs_meshblocks_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[151.59, -32.95], [151.61, -32.95], [151.61, -32.93], [151.59, -32.93], [151.59, -32.95]]]},
            "properties": {"mb_code21": "11101110001", "meshblock_category": "Industrial", "state_name": "New South Wales", "population": 0}
        },
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[151.24, -23.85], [151.26, -23.85], [151.26, -23.83], [151.24, -23.83], [151.24, -23.85]]]},
            "properties": {"mb_code21": "31102120005", "meshblock_category": "Industrial", "state_name": "Queensland", "population": 0}
        }
    ]
}

geoscape_cadastre_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[151.595, -32.945], [151.605, -32.945], [151.605, -32.935], [151.595, -32.935], [151.595, -32.945]]]},
            "properties": {"lot_plan": "101//DP755262", "cadastre_id": "CAD_NSW_MCC01", "area_sqm": 445000, "locality_name": "Teralba"}
        },
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[151.245, -23.845], [151.255, -23.845], [151.255, -23.835], [151.245, -23.835], [151.245, -23.845]]]},
            "properties": {"lot_plan": "12//SP289410", "cadastre_id": "CAD_QLD_GLD01", "area_sqm": 185000, "locality_name": "Yarwun"}
        }
    ]
}

# 10. NSW RFS Bush Fire Prone Land (BFPL)
rfs_bfpl_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[151.54, -32.98], [151.58, -32.98], [151.58, -32.95], [151.54, -32.95], [151.54, -32.98]]]},
            "properties": {"category": "Vegetation Category 1", "buffer_m": 100, "lga_name": "Lake Macquarie", "vegetation_type": "Dry Sclerophyll Forest"}
        }
    ]
}

# Assemble Full GeoLibre Project Spec Pointing Directly to S3 Lakehouse Sources
geolibre_project = {
    "version": "0.2.0",
    "name": "AURA Siting Crafter — National Data Center Siting Suitability Model",
    "mapView": {
        "center": [133.7751, -25.2744],
        "zoom": 4.5,
        "bearing": 0,
        "pitch": 0,
        "bbox": [112.0, -44.0, 155.0, -10.0]
    },
    "basemapStyleUrl": "https://tiles.openfreemap.org/styles/liberty",
    "basemapVisible": True,
    "basemapOpacity": 0.65,
    "blankBackgroundColor": None,
    "layerGroups": [
        { "id": "grp_candidates", "name": "🎯 Candidate Hubs & Siting Scorecards", "visible": True, "collapsed": False, "opacity": 1.0 },
        { "id": "grp_cadastre", "name": "📐 Cadastre & Statistical Boundaries", "visible": False, "collapsed": False, "opacity": 1.0 },
        { "id": "grp_energy", "name": "⚡ Energy Grid & Substations", "visible": True, "collapsed": False, "opacity": 1.0 },
        { "id": "grp_water", "name": "💧 Water & Cooling Loops", "visible": True, "collapsed": False, "opacity": 1.0 },
        { "id": "grp_receptors", "name": "🛡️ Social & Environmental Receptors", "visible": True, "collapsed": False, "opacity": 1.0 },
        { "id": "grp_environment", "name": "🌿 Biodiversity & Bushfire Constraints", "visible": True, "collapsed": False, "opacity": 1.0 },
        { "id": "grp_precincts", "name": "🏗️ Precinct Micro-Siting Masterplans", "visible": True, "collapsed": False, "opacity": 1.0 }
    ],
    "layers": [
        # 1. Candidate Hubs
        {
            "id": "national_candidates",
            "name": "🎯 National Siting Candidate Hubs (16 MCE Scored)",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/candidates/datacenter_candidates_national.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM"
            },
            "groupId": "grp_candidates",
            "visible": True,
            "opacity": 1.0,
            "style": {
                "circleRadius": 9,
                "fillColor": "#10b981",
                "strokeColor": "#ffffff",
                "strokeWidth": 2,
                "fillOpacity": 0.95,
                "labels": {
                    "enabled": True,
                    "field": "town_name",
                    "size": 11,
                    "color": "#ffffff",
                    "haloColor": "#0f172a",
                    "haloWidth": 2
                }
            },
            "metadata": {
                "portal": "AURA Multi-Criteria Decision Analysis (MCDA)",
                "jurisdiction": "National (8 States & Territories)",
                "records": 17,
                "records_formatted": "16 Prime National Hubs (MCE Scored)",
                "crs": "EPSG:7844 (GDA2020 Geographic)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/candidates/datacenter_candidates_national.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/candidates/datacenter_candidates_national.parquet')",
                "description": "Top-ranked candidate hubs evaluated across 15.9M assets for power grid connection, tertiary recycled water cooling, slope (<5%), and statutory receptor buffer compliance."
            },
            "geojson": candidates_geojson
        },
        # 2. ABS Meshblocks
        {
            "id": "abs_meshblocks",
            "name": "📐 ABS 2021 Meshblocks & UCL",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/cadastre/abs_meshblocks_2021.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_cadastre",
            "visible": False,
            "opacity": 0.2,
            "style": {
                "fillColor": "#94a3b8",
                "strokeColor": "#94a3b8",
                "strokeWidth": 0.85,
                "fillOpacity": 0.15
            },
            "metadata": {
                "portal": "Australian Bureau of Statistics (ABS)",
                "jurisdiction": "National Statistical Geography Standard (ASGS)",
                "records": 368290,
                "records_formatted": "368,290 Meshblocks (Residential, Industrial, Commercial)",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/cadastre/abs_meshblocks_2021.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/cadastre/abs_meshblocks_2021.parquet') WHERE ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "viewport_streaming": True
            },
            "geojson": abs_meshblocks_geojson
        },
        # 3. Geoscape Cadastre
        {
            "id": "geoscape_cadastre",
            "name": "📐 Geoscape National Cadastre & G-NAF",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/cadastre/geoscape_cadastre.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_cadastre",
            "visible": False,
            "opacity": 0.2,
            "style": {
                "fillColor": "#64748b",
                "strokeColor": "#64748b",
                "strokeWidth": 0.75,
                "fillOpacity": 0.10
            },
            "metadata": {
                "portal": "Geoscape Australia / ICSM CSDM",
                "jurisdiction": "National Cadastre Database",
                "records": 15420800,
                "records_formatted": "15,420,800 Standardized Lot/Plan Land Parcels",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/cadastre/geoscape_cadastre.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/cadastre/geoscape_cadastre.parquet') WHERE ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "viewport_streaming": True
            },
            "geojson": geoscape_cadastre_geojson
        },
        # 4. Substations Layer
        {
            "id": "substations_terminal",
            "name": "⚡ Electrical Substations & Terminal Stations",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/energy/national_substations.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_energy",
            "visible": True,
            "opacity": 1.0,
            "style": {
                "circleRadius": 6,
                "fillColor": "#f59e0b",
                "strokeColor": "#0f172a",
                "strokeWidth": 1.5,
                "fillOpacity": 0.9
            },
            "metadata": {
                "portal": "AEMO / Geoscience Australia",
                "jurisdiction": "National Power System Substations",
                "records": 1850,
                "records_formatted": "1,850 Terminal & Bulk Supply Substations",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/energy/national_substations.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/energy/national_substations.parquet') WHERE ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "description": "High-voltage terminal substations with step-down transformers and switchyards.",
                "viewport_streaming": True
            },
            "geojson": substations_geojson
        },
        # 5. Transmission Interstate (≥275kV)
        {
            "id": "transmission_lines_interstate",
            "name": "⚡ Interstate Transmission Grid (≥275kV)",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/energy/national_transmission_grid.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_energy",
            "visible": True,
            "opacity": 0.95,
            "style": {
                "strokeColor": "#38bdf8",
                "strokeWidth": 3.0,
                "fillOpacity": 0.95
            },
            "metadata": {
                "portal": "Transgrid / Powerlink / ElectraNet / AEMO",
                "jurisdiction": "National Electricity Market (NEM) & SWIS",
                "records": 5000,
                "records_formatted": "5,000 Major High-Voltage Lines (500kV, 330kV, 275kV)",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/energy/national_transmission_grid.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/energy/national_transmission_grid.parquet') WHERE voltage_kv >= 275 AND ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "description": "Extra-high-voltage interstate transmission bulk power corridors capable of multimegawatt hyperscale injection.",
                "viewport_streaming": True
            },
            "geojson": transmission_interstate_geojson
        },
        # 6. Transmission Regional (132kV-275kV)
        {
            "id": "transmission_lines_regional",
            "name": "⚡ Regional Transmission Grid (132kV-275kV)",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/energy/national_transmission_grid.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_energy",
            "visible": False,
            "opacity": 0.85,
            "style": {
                "strokeColor": "#60a5fa",
                "strokeWidth": 2.0,
                "fillOpacity": 0.85
            },
            "metadata": {
                "portal": "State Transmission Network Service Providers",
                "jurisdiction": "Regional Transmission Networks",
                "records": 12400,
                "records_formatted": "12,400 Regional Transmission Feeder Segments",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/energy/national_transmission_grid.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/energy/national_transmission_grid.parquet') WHERE voltage_kv < 275 AND ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "viewport_streaming": True
            },
            "geojson": transmission_regional_geojson
        },
        # 7. Recycled WWTW Plants
        {
            "id": "recycled_wwtw_plants",
            "name": "💧 Recycled Wastewater Treatment Plants (WWTW)",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/water/recycled_wwtw_plants.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_water",
            "visible": True,
            "opacity": 1.0,
            "style": {
                "circleRadius": 6,
                "fillColor": "#14b8a6",
                "strokeColor": "#ffffff",
                "strokeWidth": 1.5,
                "fillOpacity": 0.9
            },
            "metadata": {
                "portal": "Water Authorities / State EPA Portals",
                "jurisdiction": "National Recycled Water Infrastructure",
                "records": 1120,
                "records_formatted": "1,120 Major Municipal & Industrial Treatment Facilities",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/water/recycled_wwtw_plants.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/water/recycled_wwtw_plants.parquet') WHERE ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "description": "Tertiary recycled wastewater facilities delivering industrial cooling water without depleting potable drinking water supplies.",
                "viewport_streaming": True
            },
            "geojson": wwtw_geojson
        },
        # 8. BoM Hydro Lines
        {
            "id": "bom_hydro_lines",
            "name": "💧 BoM Surface Water HydroLine & HydroArea",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/water/bom_surface_water_wwtw.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_water",
            "visible": True,
            "opacity": 0.85,
            "style": {
                "strokeColor": "#06b6d4",
                "strokeWidth": 2.0,
                "fillOpacity": 0.85
            },
            "metadata": {
                "portal": "Bureau of Meteorology / Geoscience Australia",
                "jurisdiction": "National Surface Water Framework",
                "records": 42100,
                "records_formatted": "42,100 Surface Hydrography Waterways",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/water/bom_surface_water_wwtw.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/water/bom_surface_water_wwtw.parquet') WHERE ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "description": "Surface waterways requiring 30m statutory riparian buffer setback protection.",
                "viewport_streaming": True
            },
            "geojson": hydro_geojson
        },
        # 9. ACARA Schools
        {
            "id": "acara_schools",
            "name": "🛡️ ACARA National Schools (500m Buffer)",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/receptors/acara_national_schools.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_receptors",
            "visible": True,
            "opacity": 0.9,
            "style": {
                "circleRadius": 5,
                "fillColor": "#a855f7",
                "strokeColor": "#581c87",
                "strokeWidth": 1.2,
                "fillOpacity": 0.9
            },
            "metadata": {
                "portal": "Australian Curriculum, Assessment and Reporting Authority (ACARA)",
                "jurisdiction": "National Schools Directory",
                "records": 10842,
                "records_formatted": "10,842 Government, Catholic & Independent Campuses",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/receptors/acara_national_schools.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/receptors/acara_national_schools.parquet') WHERE ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "description": "Primary and secondary educational campuses enforcing strict 500m statutory acoustic setbacks.",
                "viewport_streaming": True
            },
            "geojson": schools_geojson
        },
        # 10. NHSD Healthcare
        {
            "id": "nhsd_healthcare",
            "name": "🛡️ NHSD National Healthcare & Hospitals",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/receptors/nhsd_national_healthcare.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_receptors",
            "visible": True,
            "opacity": 0.9,
            "style": {
                "circleRadius": 5.5,
                "fillColor": "#ec4899",
                "strokeColor": "#831843",
                "strokeWidth": 1.2,
                "fillOpacity": 0.9
            },
            "metadata": {
                "portal": "Australian Digital Health Agency / NHSD",
                "jurisdiction": "National Health Services Directory",
                "records": 4218,
                "records_formatted": "4,218 Hospitals, Emergency Departments & Critical Facilities",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/receptors/nhsd_national_healthcare.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/receptors/nhsd_national_healthcare.parquet') WHERE ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "description": "Hospitals and emergency care centers requiring acoustic noise masking and priority contingency routing.",
                "viewport_streaming": True
            },
            "geojson": health_geojson
        },
        # 11. Heavy Freight & Transport Rail
        {
            "id": "transport_rail",
            "name": "🛡️ Heavy Freight & Transport Rail Corridors",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/transport/nsw_railway_corridors.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_receptors",
            "visible": False,
            "opacity": 0.85,
            "style": {
                "strokeColor": "#94a3b8",
                "strokeWidth": 2.0,
                "fillOpacity": 0.85
            },
            "metadata": {
                "portal": "NSW Spatial Services / TfNSW / ARTC",
                "jurisdiction": "National Heavy Rail Network",
                "records": 4000,
                "records_formatted": "4,000 Heavy Freight & Interstate Rail Corridors",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/transport/nsw_railway_corridors.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/transport/nsw_railway_corridors.parquet') WHERE ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "viewport_streaming": True
            },
            "geojson": rail_geojson
        },
        # 12. BioNet Biodiversity
        {
            "id": "bionet_biodiversity",
            "name": "🌿 NSW SEED & BioNet BV Map / KHIB",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/environment/bionet_biodiversity_khib.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_environment",
            "visible": True,
            "opacity": 0.4,
            "style": {
                "fillColor": "#84cc16",
                "strokeColor": "#65a30d",
                "strokeWidth": 1.2,
                "fillOpacity": 0.35
            },
            "metadata": {
                "portal": "NSW DPHI Environment / DCCEEW BioNet",
                "jurisdiction": "NSW Biodiversity Conservation Framework",
                "records": 3583,
                "records_formatted": "3,583 Biodiversity Values & Key Habitat Corridors",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/environment/bionet_biodiversity_khib.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/environment/bionet_biodiversity_khib.parquet') WHERE ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "description": "High Environmental Value (HEV) biodiversity zones and threatened species habitat subject to statutory clearing exclusions.",
                "viewport_streaming": True
            },
            "geojson": biodiversity_geojson
        },
        # 13. NSW RFS Bush Fire Prone Land
        {
            "id": "rfs_bushfire_bfpl",
            "name": "🌿 NSW RFS Bush Fire Prone Land (BFPL)",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/environment/rfs_bushfire_prone_land.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM",
                "viewport_only": True
            },
            "groupId": "grp_environment",
            "visible": False,
            "opacity": 0.35,
            "style": {
                "fillColor": "#ef4444",
                "strokeColor": "#dc2626",
                "strokeWidth": 1.0,
                "fillOpacity": 0.25
            },
            "metadata": {
                "portal": "NSW Rural Fire Service (RFS)",
                "jurisdiction": "NSW Planning Portal / RFS",
                "records": 2450,
                "records_formatted": "2,450 Cat 1 & Cat 2 Vegetation Buffer Polygons",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/environment/rfs_bushfire_prone_land.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/environment/rfs_bushfire_prone_land.parquet') WHERE ST_Intersects(geom, ST_MakeEnvelope($minx, $miny, $maxx, $maxy))",
                "viewport_streaming": True
            },
            "geojson": rfs_bfpl_geojson
        },
        # 14. Transformation Boundary
        {
            "id": "transformation_boundary",
            "name": "🏗️ Macquarie Transformation Envelope",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/precincts/transformation_boundary.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM"
            },
            "groupId": "grp_precincts",
            "visible": True,
            "opacity": 0.95,
            "style": {
                "fillColor": "#3b82f6",
                "strokeColor": "#1d4ed8",
                "strokeWidth": 2.5,
                "fillOpacity": 0.2
            },
            "metadata": {
                "portal": "NSW DPHI State Significant Precinct Planning",
                "jurisdiction": "Lake Macquarie LGA",
                "records": 1,
                "records_formatted": "350.0 Gross Precinct Hectares",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/precincts/transformation_boundary.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/precincts/transformation_boundary.parquet')"
            },
            "geojson": precinct_boundary_geojson
        },
        # 15. Net Developable Pad
        {
            "id": "net_developable_pad",
            "name": "🏗️ Net Developable Pad Area (59.7 ha)",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/precincts/net_developable_pad_59ha.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM"
            },
            "groupId": "grp_precincts",
            "visible": True,
            "opacity": 0.6,
            "style": {
                "fillColor": "#14b8a6",
                "strokeColor": "#0d9488",
                "strokeWidth": 1.5,
                "fillOpacity": 0.45
            },
            "metadata": {
                "portal": "AURA Geospatial Derivation Pipeline",
                "jurisdiction": "Hunter Energy Hub",
                "records": 1,
                "records_formatted": "59.7 ha Leveled Engineered Industrial Pad",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/precincts/net_developable_pad_59ha.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/precincts/net_developable_pad_59ha.parquet')"
            },
            "geojson": net_developable_geojson
        },
        # 16. High Pressure Gas Pipeline Corridor
        {
            "id": "gas_pipeline_corridor",
            "name": "🏗️ High Pressure Gas Pipeline Corridor (20m APZ)",
            "type": "geojson",
            "source": {
                "type": "geojson",
                "s3_path": "s3://wherobots-user-storage/aura_siting/precincts/gas_pipeline_corridor_20m.parquet",
                "format": "parquet",
                "spatial_engine": "DuckDB-WASM"
            },
            "groupId": "grp_precincts",
            "visible": True,
            "opacity": 0.9,
            "style": {
                "strokeColor": "#f97316",
                "strokeWidth": 3.0,
                "fillOpacity": 0.9
            },
            "metadata": {
                "portal": "Jemena / APA Group / NSW Spatial Services",
                "jurisdiction": "NSW Pipeline Licences",
                "records": 1,
                "records_formatted": "1 High-Pressure Natural Gas Trunk Line",
                "crs": "EPSG:7844 (GDA2020)",
                "s3_path": "s3://wherobots-user-storage/aura_siting/precincts/gas_pipeline_corridor_20m.parquet",
                "query": "SELECT * FROM read_parquet('s3://wherobots-user-storage/aura_siting/precincts/gas_pipeline_corridor_20m.parquet')"
            },
            "geojson": pipeline_corridors_geojson
        }
    ],
    "styles": {},
    "metadata": {
        "project": "AURA Siting Crafter (Australian Urban & Regional AI Siting Crafter)",
        "storage_root": "s3://wherobots-user-storage/aura_siting",
        "total_integrated_assets": 15946985,
        "jurisdiction": "National (Australia - 8 States & Territories)",
        "crs": "EPSG:7844 (GDA2020 Geographic)",
        "viewport_loading": True,
        "author": "GetBack2Basics"
    }
}

target_file = os.path.join(FRONTEND_DIR, "aura-siting-crafter.geolibre.json")
with open(target_file, "w", encoding="utf-8") as f:
    json.dump(geolibre_project, f, indent=2)

print(f"Successfully generated {target_file} with {len(geolibre_project['layers'])} layers.")
