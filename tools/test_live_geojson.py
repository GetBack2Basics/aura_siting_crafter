import requests
import json

# Test ArcGIS REST GeoJSON query
test_urls = [
    ("NSW BioNet (ArcGIS)", "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/FeatureServer/1/query?where=1=1&outFields=*&f=geojson&resultRecordCount=5"),
    ("GA Grid (ArcGIS)", "https://services.ga.gov.au/gis/rest/services/Electricity_Infrastructure/MapServer/0/query?where=1=1&outFields=*&f=geojson&resultRecordCount=5"),
    ("GA Seismic (ArcGIS)", "https://services.ga.gov.au/gis/rest/services/National_Seismic_Hazard_Assessment_2018/MapServer/0/query?where=1=1&outFields=*&f=geojson&resultRecordCount=5"),
    ("QLD Powerlink (ArcGIS)", "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Energy/ElectricityInfrastructure/MapServer/2/query?where=1=1&outFields=*&f=geojson&resultRecordCount=5"),
    ("QLD Watercourses (ArcGIS)", "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/InlandWaters/Watercourses/MapServer/0/query?where=1=1&outFields=*&f=geojson&resultRecordCount=5"),
    ("VIC Geoserver WFS", "https://opendata.maps.vic.gov.au/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=datavic:VMFEAT_POWER_TRANSMISSION_LINE&outputFormat=application/json&count=5"),
]

for name, url in test_urls:
    try:
        r = requests.get(url, timeout=8)
        data = r.json()
        features = data.get("features", [])
        geom_type = features[0]["geometry"]["type"] if features else "None"
        sample_coord = features[0]["geometry"]["coordinates"] if features else "None"
        print(f"[OK 200] {name} -> {len(features)} features, geom: {geom_type}")
        if features:
            print(f"   Sample coords: {str(sample_coord)[:60]}...")
    except Exception as ex:
        print(f"[ERR] {name} -> {ex}")
