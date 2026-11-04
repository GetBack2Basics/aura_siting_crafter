FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.2

# numpy comes from the base image (Debian package); scipy from apt keeps them compatible
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip python3-scipy \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir --break-system-packages google-cloud-storage requests

WORKDIR /app
# Build context is assembled by tools/stage_job_context.py
COPY . /app

ENTRYPOINT ["python3", "/app/derive.py"]
