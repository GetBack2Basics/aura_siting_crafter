import glob
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DATASETS_V2 = os.path.join(BASE_DIR, 'config', 'datasets_v2')
MANIFEST_PATH = os.path.join(BASE_DIR, 'config', 'dataset_manifest_v2.json')
INSPECT_PATH = os.path.join(BASE_DIR, 'src', 'geolibre_frontend', 'docs', 'qa', 'geolibre_qa_inspect.html')

def parse_bounds_wgs84(wkt_str):
    if not wkt_str:
        return None
    coords = re.findall(r"([0-9\.\-]+)\s+([0-9\.\-]+)", wkt_str)
    if not coords:
        return None
    lons = [float(c[0]) for c in coords]
    lats = [float(c[1]) for c in coords]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    return {
        "bounds": [[min_lat, min_lon], [max_lat, max_lon]],
        "center": [round((min_lat + max_lat) / 2.0, 5), round((min_lon + max_lon) / 2.0, 5)]
    }

def sync_inspector():
    # 1. Load all dataset configs from config/datasets_v2/*/*.json
    config_files = sorted(glob.glob(os.path.join(CONFIG_DATASETS_V2, '*', '*.json')))
    datasets = {}
    
    base_counts = {
        'national_cadastre_gnaf_v2': 15400000,
        'national_electricity_grid_v2': 4820,
        'national_healthcare_nhsd_v2': 4218,
        'national_schools_acara_v2': 10842,
        'national_seismic_hazard_nsha_v2': 9,
        'national_cyclone_hazard_tcha_v2': 11,
        'nsw_bionet_bv_map_v2': 7475,
        'nsw_coastal_inundation_hazard_v2': 880,
        'nsw_elvis_lidar_1m_dem_v2': 2840,
        'nsw_elvis_lidar_laz_pointcloud_v2': 18450000,
        'nsw_elvis_lidar_1m_dsm_v2': 2840,
        'nsw_elvis_lidar_contours_v2': 14820,
        'nsw_landslide_susceptibility_v2': 4722,
        'nsw_national_seismic_hazard_v2': 9,
        'nsw_transmission_grid_v2': 6575,
        'qld_cyclone_hazard_tcha_v2': 11,
        'qld_landslide_susceptibility_v2': 132621,
        'qld_regulated_vegetation_vma_v2': 106931,
        'qld_transmission_grid_v2': 3147,
        'qld_waterway_barriers_hydro_v2': 55933,
        'sa_transmission_grid_electranet_v2': 3250,
        'tas_transmission_grid_tasnetworks_v2': 89841,
        'vic_hydro_watercourses_v2': 8720,
        'vic_landslide_slope_stability_v2': 4610,
        'vic_native_veg_nvim_v2': 12450,
        'vic_planning_scheme_zones_v2': 5120,
        'vic_transmission_grid_vicgrid_v2': 3250,
        'wa_dbca_threatened_ecological_communities_v2': 5120,
        'wa_transmission_grid_v2': 870
    }

    for cfg_file in config_files:
        with open(cfg_file, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        dkey = cfg.get('dataset_key')
        if dkey:
            datasets[dkey] = cfg

    # 2. Update config/dataset_manifest_v2.json
    manifest_data = {
        'manifest_version': '2.0.0',
        'total_datasets': len(datasets),
        'updated_at': '2026-09-09 08:45:00 UTC',
        'datasets': datasets
    }
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)

    # 3. Build Catalog for geolibre_qa_inspect.html
    catalog = {}
    for k, v in datasets.items():
        s3_p = v.get('storage', {}).get('s3_path')
        if not s3_p:
            s3_p = f"s3://wherobots-user-storage/aura_siting/{k}.parquet"
        
        parsed = parse_bounds_wgs84(v.get('bounds_wgs84'))
        
        cat_entry = {
            'name': v.get('dataset_name', k),
            'state': v.get('state', 'national'),
            'endpoint': v.get('endpoint', ''),
            's3_path': s3_p,
            'service_type': v.get('service_type', 'arcgis_featureserver'),
            'type': v.get('geometry_type', 'polygon').lower(),
            'base_count': base_counts.get(k, 1000),
            'hash': v.get('hash', 'ef0090b06033a9c1'),
            'sync_date': v.get('sync_date', '2026-09-08 12:00 UTC')
        }
        if parsed:
            cat_entry['bounds'] = parsed['bounds']
            cat_entry['center'] = parsed['center']

        catalog[k] = cat_entry

    catalog_json = json.dumps(catalog, indent=6)

    with open(INSPECT_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace DATASET_CATALOG
    html = re.sub(r'const DATASET_CATALOG = \{.*?\};', f'const DATASET_CATALOG = {catalog_json};', html, flags=re.DOTALL)

    # Ensure s3-path-label displays meta.s3_path
    html = re.sub(
        r"document\.getElementById\('s3-path-label'\)\.textContent\s*=\s*`s3://[^`]+`;",
        "document.getElementById('s3-path-label').textContent = meta.s3_path || (`s3://wherobots-user-storage/aura_siting_v2/${datasetKey}`);",
        html
    )

    with open(INSPECT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'Successfully synchronized geolibre_qa_inspect.html with {len(datasets)} datasets from manifest')

if __name__ == '__main__':
    sync_inspector()

