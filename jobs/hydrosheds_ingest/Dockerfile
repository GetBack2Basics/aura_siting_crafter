FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.2

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir --break-system-packages google-cloud-storage requests

WORKDIR /app
# Build context is assembled by tools/stage_job_context.py: ingest.py, publish_gate.py,
# dataset_manifest_v2.json and regions/*.json
COPY . /app

ENTRYPOINT ["python3", "/app/ingest.py"]

