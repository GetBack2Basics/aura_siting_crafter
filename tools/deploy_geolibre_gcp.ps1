# ==============================================================================
# Deploy GeoLibre WebGIS & FastAPI Spatial AI Proxy on Google Cloud Platform (GCP)
# ==============================================================================
param (
    [string]$GcpProjectId = $env:GCP_PROJECT_ID,
    [string]$GcpRegion = "australia-southeast1",
    [string]$ServiceName = "geolibre-spatial-ai-proxy"
)

if (-not $GcpProjectId) {
    $GcpProjectId = "aura-siting-crafter"
}

Write-Host "=== 1. Validating Environment & Credentials ===" -ForegroundColor Cyan
Write-Host "Active GCP Project: $GcpProjectId"
Write-Host "Target Region: $GcpRegion"

Write-Host "=== 2. Building & Deploying FastAPI Spatial AI Proxy to Cloud Run ===" -ForegroundColor Cyan
gcloud builds submit `
    --project="$GcpProjectId" `
    --config="cloudbuild_proxy.yaml" `
    --timeout="10m"

gcloud run deploy "$ServiceName" `
    --project="$GcpProjectId" `
    --region="$GcpRegion" `
    --image="gcr.io/$GcpProjectId/${ServiceName}:latest" `
    --platform="managed" `
    --allow-unauthenticated `
    --min-instances=0 `
    --max-instances=10 `
    --memory="512Mi" `
    --cpu="1" `
    --set-env-vars="AURA_REGION=national"

$ServiceUrl = gcloud run services describe "$ServiceName" --platform managed --region "$GcpRegion" --format 'value(status.url)'
Write-Host "Cloud Run Service URL: $ServiceUrl" -ForegroundColor Green

Write-Host "=== Deployment Complete ===" -ForegroundColor Green
