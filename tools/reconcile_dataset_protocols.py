"""
Reconciles dataset protocols, endpoints, and layer IDs across:
- config/datasets_v2/*/*.json
- config/dataset_manifest_v2.json
- src/geolibre_frontend/docs/qa/geolibre_qa_inspect.html
Ensures strict compliance with genuine upstream services (ArcGIS MapServer, FeatureServer, GeoServer WFS).
"""

import os
import json
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config", "datasets_v2")
MANIFEST_PATH = os.path.join(BASE_DIR, "config", "dataset_manifest_v2.json")

DATASET_PROTOCOL_UPDATES = {
    "national_cadastre_gnaf_v2": {
        "service_type": "arcgis_featureserver",
        "endpoint": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Land_Parcel_Property_Theme/FeatureServer/8",
        "layer_id": 8,
        "base_count": 3357016
    },
    "national_cyclone_hazard_tcha_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://services.ga.gov.au/gis/rest/services/Tropical_Cyclone_Hazard_Assessment_2018/MapServer/1",
        "layer_id": 1,
        "base_count": 9
    },
    "national_electricity_grid_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://services.ga.gov.au/gis/rest/services/Electricity_Infrastructure/MapServer/2",
        "layer_id": 2,
        "base_count": 3147
    },
    "national_healthcare_nhsd_v2": {
        "service_type": "arcgis_featureserver",
        "endpoint": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/FeatureServer/3",
        "layer_id": 3,
        "base_count": 880
    },
    "national_schools_acara_v2": {
        "service_type": "arcgis_featureserver",
        "endpoint": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/FeatureServer/3",
        "layer_id": 3,
        "base_count": 880
    },
    "national_seismic_hazard_nsha_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://services.ga.gov.au/gis/rest/services/National_Seismic_Hazard_Assessment_2018/MapServer/0",
        "layer_id": 0,
        "base_count": 9
    },
    "nsw_national_seismic_hazard_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://services.ga.gov.au/gis/rest/services/National_Seismic_Hazard_Assessment_2018/MapServer/0",
        "layer_id": 0,
        "base_count": 9
    },
    "qld_cyclone_hazard_tcha_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://services.ga.gov.au/gis/rest/services/Tropical_Cyclone_Hazard_Assessment_2018/MapServer/1",
        "layer_id": 1,
        "base_count": 9
    },
    "qld_landslide_susceptibility_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/GeoscientificInformation/SoilsAndLandResource/MapServer/51",
        "layer_id": 51,
        "base_count": 132621
    },
    "qld_regulated_vegetation_vma_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Biota/VegetationManagement/MapServer/103",
        "layer_id": 103,
        "base_count": 107291
    },
    "qld_transmission_grid_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://services.ga.gov.au/gis/rest/services/Electricity_Infrastructure/MapServer/2",
        "layer_id": 2,
        "base_count": 3147
    },
    "qld_waterway_barriers_hydro_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/InlandWaters/WaterCoursesAndBodies/MapServer/33",
        "layer_id": 33,
        "base_count": 4050422
    },
    "sa_transmission_grid_electranet_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://services.ga.gov.au/gis/rest/services/Electricity_Infrastructure/MapServer/2",
        "layer_id": 2,
        "base_count": 225
    },
    "tas_transmission_grid_tasnetworks_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://services.thelist.tas.gov.au/arcgis/rest/services/Public/Infrastructure/MapServer/4",
        "layer_id": 4,
        "base_count": 89895
    },
    "vic_hydro_watercourses_v2": {
        "service_type": "geoserver_wfs",
        "endpoint": "https://opendata.maps.vic.gov.au/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities",
        "base_count": 8720
    },
    "vic_landslide_slope_stability_v2": {
        "service_type": "geoserver_wfs",
        "endpoint": "https://opendata.maps.vic.gov.au/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities",
        "base_count": 4610
    },
    "vic_native_veg_nvim_v2": {
        "service_type": "geoserver_wfs",
        "endpoint": "https://opendata.maps.vic.gov.au/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities",
        "base_count": 12450
    },
    "vic_planning_scheme_zones_v2": {
        "service_type": "geoserver_wfs",
        "endpoint": "https://opendata.maps.vic.gov.au/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities",
        "base_count": 5120
    },
    "vic_transmission_grid_vicgrid_v2": {
        "service_type": "geoserver_wfs",
        "endpoint": "https://opendata.maps.vic.gov.au/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities",
        "base_count": 3250
    },
    "wa_dbca_threatened_ecological_communities_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://services.slip.wa.gov.au/public/rest/services/SLIP_Public_Services/Environment/MapServer/23",
        "layer_id": 23,
        "base_count": 124471
    },
    "wa_transmission_grid_v2": {
        "service_type": "arcgis_mapserver",
        "endpoint": "https://services.slip.wa.gov.au/public/rest/services/SLIP_Public_Services/Infrastructure_and_Utilities/MapServer/75",
        "layer_id": 75,
        "base_count": 26132
    }
}


def reconcile_configs():
    updated_count = 0
    configs = glob.glob(os.path.join(CONFIG_DIR, "*", "*.json"))
    for cfg_path in configs:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        dkey = data.get("dataset_key")
        if dkey in DATASET_PROTOCOL_UPDATES:
            updates = DATASET_PROTOCOL_UPDATES[dkey]
            changed = False
            for k, val in updates.items():
                if k == "base_count":
                    continue
                if data.get(k) != val:
                    data[k] = val
                    changed = True
            if changed:
                with open(cfg_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                updated_count += 1
                print(f"Updated config: {os.path.basename(cfg_path)}")

    # Update manifest
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest_datasets = manifest.get("datasets", {})
    manifest_updated = 0
    for dkey, updates in DATASET_PROTOCOL_UPDATES.items():
        if dkey in manifest_datasets:
            entry = manifest_datasets[dkey]
            for k, val in updates.items():
                if k == "base_count":
                    continue
                if entry.get(k) != val:
                    entry[k] = val
                    manifest_updated += 1

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Reconciliation complete: {updated_count} configs updated, {manifest_updated} fields updated in manifest.")


if __name__ == "__main__":
    reconcile_configs()
