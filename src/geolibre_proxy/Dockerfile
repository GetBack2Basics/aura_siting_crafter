# Multi-stage lightweight Python container for GCP Cloud Run
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PORT=8080

COPY src/geolibre_proxy/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/
COPY config/ /app/config/
COPY runner/ /app/runner/

EXPOSE 8080

CMD exec uvicorn src.geolibre_proxy.main:app --host 0.0.0.0 --port ${PORT}
