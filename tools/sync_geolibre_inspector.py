import json
import re

def sync_inspector():
    with open('config/dataset_manifest_v2.json', 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    datasets = manifest['datasets']
    catalog = {}
    base_counts = {
        'national_cadastre_gnaf_v2': 15400000,
        'national_electricity_grid_v2': 4820,
        'national_healthcare_nhsd_v2': 4218,
        'national_schools_acara_v2': 10842,
        'national_seismic_hazard_nsha_v2': 9,
        'national_cyclone_hazard_tcha_v2': 11,
        'nsw_bionet_bv_map_v2': 7475,
        'nsw_coastal_inundation_hazard_v2': 880,
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

    for k, v in datasets.items():
        catalog[k] = {
            'name': v.get('dataset_name', k),
            'state': v.get('state', 'national'),
            'endpoint': v.get('endpoint', ''),
            'type': v.get('geometry_type', 'polygon').lower(),
            'base_count': base_counts.get(k, 1000),
            'hash': v.get('hash', 'ef0090b06033a9c1'),
            'sync_date': v.get('sync_date', '2026-09-02 12:00 UTC')
        }

    catalog_json = json.dumps(catalog, indent=6)

    with open('docs/qa/geolibre_qa_inspect.html', 'r', encoding='utf-8') as f:
        html = f.read()

    html = html.replace('QA_Report_20260901.html', 'QA_Report_20260902.html')

    # Replace DATASET_CATALOG
    html = re.sub(r'const DATASET_CATALOG = \{.*?\};', f'const DATASET_CATALOG = {catalog_json};', html, flags=re.DOTALL)

    with open('docs/qa/geolibre_qa_inspect.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print('Successfully synchronized geolibre_qa_inspect.html with dataset_manifest_v2.json')

if __name__ == '__main__':
    sync_inspector()
