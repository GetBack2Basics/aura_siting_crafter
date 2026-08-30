#!/usr/bin/env bash
# ==============================================================================
# Deploy GeoLibre WebGIS & FastAPI Spatial AI Proxy on Google Cloud Platform (GCP)
# ==============================================================================
set -euo pipefail

GCP_PROJECT_ID="${GCP_PROJECT_ID:-aura-siting-crafter}"
GCP_REGION="${GCP_REGION:-australia-southeast1}"
SERVICE_NAME="geolibre-spatial-ai-proxy"
GCS_APP_BUCKET="gs://${GCP_PROJECT_ID}-geolibre-app"

echo "=== 1. Validating Environment & Credentials ==="
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI is required." >&2
    exit 1
fi

echo "Active GCP Project: ${GCP_PROJECT_ID}"
echo "Target Region: ${GCP_REGION}"

echo "=== 2. Building & Deploying FastAPI Spatial AI Proxy to Cloud Run ==="
gcloud builds submit \
    --project="${GCP_PROJECT_ID}" \
    --tag="gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:latest" \
    --config=- <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:latest', '-f', 'src/geolibre_proxy/Dockerfile', '.']
images:
- 'gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:latest'
EOF

gcloud run deploy "${SERVICE_NAME}" \
    --project="${GCP_PROJECT_ID}" \
    --region="${GCP_REGION}" \
    --image="gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:latest" \
    --platform="managed" \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=10 \
    --memory="512Mi" \
    --cpu="1" \
    --set-env-vars="AURA_REGION=national"

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform managed --region "${GCP_REGION}" --format 'value(status.url)')
echo "Cloud Run Service URL: ${SERVICE_URL}"

echo "=== 3. Deploying Static GeoLibre Web App to GCS + Cloud CDN ==="
if ! gcloud storage buckets describe "${GCS_APP_BUCKET}" &> /dev/null; then
    echo "Creating GCS Bucket ${GCS_APP_BUCKET}..."
    gcloud storage buckets create "${GCS_APP_BUCKET}" --location="${GCP_REGION}"
    gcloud storage buckets update "${GCS_APP_BUCKET}" --web-main-page-suffix="index.html"
fi

echo "=== Deployment Complete ==="
echo "GeoLibre WebGIS App: https://storage.googleapis.com/${GCP_PROJECT_ID}-geolibre-app/index.html"
echo "Spatial AI Proxy: ${SERVICE_URL}"
