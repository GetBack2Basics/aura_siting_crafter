"""
Unit & Integration Test: Live Endpoint & Geometry Contract Auditing
Tests that all dataset configurations in config/datasets_v2/ point to live, reachable endpoints,
specifically loading from Google Cloud Storage or verified authoritative state/national APIs,
and ensures tests cleanly fail with actionable diagnostic messages if there is a data source issue.
"""

import os
import glob
import json
import requests
import pytest

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "datasets_v2")
MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "dataset_manifest_v2.json")

GEOMETRY_TYPE_MAP = {
    "esriGeometryPolygon": ["Polygon", "MultiPolygon"],
    "esriGeometryPoint": ["Point", "MultiPoint"],
    "esriGeometryPolyline": ["LineString", "MultiLineString", "Polyline"],
}

GCS_HOST = "storage.googleapis.com"
GCS_BUCKET = "aura-siting-crafter-geolibre-app"


def identify_storage_provider(url: str) -> str:
    """Classifies the endpoint storage provider or API gateway."""
    if GCS_HOST in url:
        return "Google Cloud Storage"
    elif "arcgis" in url.lower() or "featureserver" in url.lower() or "mapserver" in url.lower():
        return "ArcGIS REST Feature/Map Service"
    elif "wfs" in url.lower() or "ows" in url.lower():
        return "OGC WFS / OWS Service"
    elif "s3.amazonaws.com" in url.lower():
        return "AWS S3 (DEPRECATED / EXPIRED)"
    elif url.startswith("file://") or "localhost" in url or "127.0.0.1" in url:
        return "Local Filesystem / Mock (FORBIDDEN)"
    else:
        return "Authoritative Spatial Web Service"


def format_source_failure_message(
    dkey: str,
    endpoint: str,
    provider: str,
    issue: str,
    remediation: str,
    cfg_path: str = ""
) -> str:
    """Formats a clean, standardized, and actionable diagnostic failure message."""
    return (
        f"\n======================================================================\n"
        f"[DATASET SOURCE ERROR] Dataset: '{dkey}'\n"
        f"  - Provider:     {provider}\n"
        f"  - Target URL:   {endpoint}\n"
        f"  - Config File:  {cfg_path or 'N/A'}\n"
        f"  - Issue:        {issue}\n"
        f"  - Remediation:  {remediation}\n"
        f"======================================================================"
    )


@pytest.fixture(scope="module")
def dataset_configs():
    configs = sorted(glob.glob(os.path.join(CONFIG_DIR, "*", "*.json")))
    assert len(configs) > 0, "No dataset configurations found in config/datasets_v2/"
    return configs


def test_no_deprecated_s3_or_local_mocks_in_configs(dataset_configs):
    """
    Asserts that NO dataset configurations in config/datasets_v2/ reference
    expired AWS S3 URLs or local mock paths. All cloud assets must reference Google Cloud Storage.
    """
    forbidden_tokens = ["s3.amazonaws.com", "elvis-downloads.s3", "file://", "localhost", "127.0.0.1"]
    failures = []

    for cfg_path in dataset_configs:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dkey = data.get("dataset_key", "UNKNOWN")
        endpoint = data.get("endpoint", "")

        for token in forbidden_tokens:
            if token in endpoint.lower():
                provider = identify_storage_provider(endpoint)
                msg = format_source_failure_message(
                    dkey=dkey,
                    endpoint=endpoint,
                    provider=provider,
                    issue=f"Found forbidden token '{token}' in endpoint URL.",
                    remediation=(
                        "Migrate the asset to Google Cloud Storage (https://storage.googleapis.com/aura-siting-crafter-geolibre-app/...) "
                        "or point to the live authoritative state/national WFS/ArcGIS API endpoint."
                    ),
                    cfg_path=cfg_path
                )
                failures.append(msg)

    assert len(failures) == 0, "\n".join(failures)


def test_all_dataset_endpoints_reachable_and_geometry_contracts(dataset_configs):
    """
    Asserts that:
      1. Each configured live spatial endpoint returns HTTP 200 (or HTTP 206 for byte-range queries).
      2. Upstream ArcGIS / WFS geometryType strictly matches declared config geometry_type.
      3. Clean, actionable error messages are provided if any source fails.
    """
    failures = []
    headers = {
        "User-Agent": "AURA-Siting-Crafter/2.5 (Google-Cloud-Integration-Audit)"
    }

    for cfg_path in dataset_configs:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dkey = data.get("dataset_key", "UNKNOWN")
        endpoint = data.get("endpoint", "")
        declared_geom = data.get("geometry_type")
        provider = identify_storage_provider(endpoint)

        if not endpoint:
            failures.append(
                format_source_failure_message(
                    dkey=dkey,
                    endpoint="<EMPTY>",
                    provider=provider,
                    issue="Missing 'endpoint' field in dataset configuration.",
                    remediation="Add a valid Google Cloud Storage or authoritative API URL to this config.",
                    cfg_path=cfg_path
                )
            )
            continue

        try:
            # If Google Cloud binary pointcloud/mesh, probe with Range header to verify streaming
            req_headers = dict(headers)
            if endpoint.endswith(".laz") or endpoint.endswith(".copc.laz"):
                req_headers["Range"] = "bytes=0-1023"

            r = requests.get(endpoint, headers=req_headers, timeout=10, allow_redirects=True)
            valid_statuses = [200, 206] if "Range" in req_headers else [200]

            if r.status_code not in valid_statuses:
                remediation = (
                    f"Ensure the object exists in Google Cloud bucket '{GCS_BUCKET}' and public read access is enabled."
                    if provider == "Google Cloud Storage"
                    else "Check if the upstream state/national geospatial service is online or updated its REST layer ID."
                )
                failures.append(
                    format_source_failure_message(
                        dkey=dkey,
                        endpoint=endpoint,
                        provider=provider,
                        issue=f"Server returned HTTP {r.status_code} (expected {valid_statuses}).",
                        remediation=remediation,
                        cfg_path=cfg_path
                    )
                )
                continue

            # If it's an ArcGIS REST endpoint returning JSON metadata, probe geometryType
            if "f=json" in endpoint or r.headers.get("content-type", "").startswith("application/json") or "json" in r.text[:200]:
                try:
                    meta = r.json()
                    upstream_geom = meta.get("geometryType")
                    if upstream_geom:
                        valid_declared = GEOMETRY_TYPE_MAP.get(upstream_geom, [])
                        if declared_geom not in valid_declared:
                            failures.append(
                                format_source_failure_message(
                                    dkey=dkey,
                                    endpoint=endpoint,
                                    provider=provider,
                                    issue=(
                                        f"Geometry Mismatch: Upstream service declares '{upstream_geom}' "
                                        f"but dataset config expects '{declared_geom}'."
                                    ),
                                    remediation=f"Update config 'geometry_type' to one of {valid_declared}.",
                                    cfg_path=cfg_path
                                )
                            )
                except Exception:
                    pass

        except requests.exceptions.Timeout:
            failures.append(
                format_source_failure_message(
                    dkey=dkey,
                    endpoint=endpoint,
                    provider=provider,
                    issue="Connection timed out after 10 seconds.",
                    remediation="Verify network connectivity and ensure the upstream server or Google Cloud bucket is reachable.",
                    cfg_path=cfg_path
                )
            )
        except requests.exceptions.ConnectionError as ex:
            failures.append(
                format_source_failure_message(
                    dkey=dkey,
                    endpoint=endpoint,
                    provider=provider,
                    issue=f"Connection error: {type(ex).__name__}",
                    remediation="Check DNS resolution and endpoint host availability.",
                    cfg_path=cfg_path
                )
            )
        except Exception as ex:
            failures.append(
                format_source_failure_message(
                    dkey=dkey,
                    endpoint=endpoint,
                    provider=provider,
                    issue=f"Unexpected error: {type(ex).__name__} ({str(ex)})",
                    remediation="Investigate exception details and review configuration.",
                    cfg_path=cfg_path
                )
            )

    assert len(failures) == 0, (
        f"\nTotal Dataset Source Audit Failures: {len(failures)}\n" + "\n".join(failures)
    )


def test_google_cloud_storage_pointclouds_and_mesh_streaming():
    """
    Specifically asserts that all 3D Point Cloud, COPC, Potree octree, and DEM/DSM assets
    are hosted on Google Cloud Storage and support byte-range streaming queries for 3D viewers.
    """
    gcs_assets = [
        {
            "name": "Lake Macquarie ELVIS COPC LAZ Point Cloud",
            "url": "https://storage.googleapis.com/aura-siting-crafter-geolibre-app/potree/pointclouds/lake_macquarie_elvis.copc.laz",
            "check_range": True,
            "min_bytes": 1000
        },
        {
            "name": "Lake Macquarie Potree LOD Octree cloud.js",
            "url": "https://storage.googleapis.com/aura-siting-crafter-geolibre-app/potree/pointclouds/nsw_elvis_lidar_laz_pointcloud_v2/cloud.js",
            "check_range": False,
            "min_bytes": 50
        },
        {
            "name": "Lake Macquarie ELVIS Raw LAZ Tile",
            "url": "https://storage.googleapis.com/aura-siting-crafter-geolibre-app/potree/pointclouds/LakeMacquarie201409-LID1-C3-AHD_3666336_56_0002_0002.laz",
            "check_range": True,
            "min_bytes": 1000
        }
    ]

    failures = []
    for asset in gcs_assets:
        url = asset["url"]
        name = asset["name"]
        try:
            headers = {"Range": "bytes=0-1023"} if asset["check_range"] else {}
            r = requests.get(url, headers=headers, timeout=10)
            expected_status = 206 if asset["check_range"] else 200

            if r.status_code != expected_status and r.status_code != 200:
                failures.append(
                    format_source_failure_message(
                        dkey=name,
                        endpoint=url,
                        provider="Google Cloud Storage",
                        issue=f"HTTP {r.status_code} received (expected {expected_status} or 200).",
                        remediation=f"Ensure asset '{url}' is uploaded to Google Cloud Storage bucket '{GCS_BUCKET}' and permissions permit public read."
                    )
                )
            elif len(r.content) < asset["min_bytes"]:
                failures.append(
                    format_source_failure_message(
                        dkey=name,
                        endpoint=url,
                        provider="Google Cloud Storage",
                        issue=f"Payload size ({len(r.content)} bytes) was smaller than expected minimum ({asset['min_bytes']} bytes).",
                        remediation="Verify that the file in Google Cloud Storage is not corrupted or empty."
                    )
                )
        except Exception as ex:
            failures.append(
                format_source_failure_message(
                    dkey=name,
                    endpoint=url,
                    provider="Google Cloud Storage",
                    issue=f"Connection exception: {type(ex).__name__} ({str(ex)})",
                    remediation="Check Google Cloud Storage network connectivity."
                )
            )

    assert len(failures) == 0, (
        f"\nGoogle Cloud Storage Asset Verification Failures ({len(failures)}):\n" + "\n".join(failures)
    )
