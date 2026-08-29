FROM python:3.11-slim

WORKDIR /app

# Install system geospatial libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev gdal-bin libproj-dev libgeos-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV AURA_REGION=national
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.Analysis.national_suitability_analysis"]
