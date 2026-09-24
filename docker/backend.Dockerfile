FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app
RUN chmod +x /app/docker/backend-entrypoint.sh \
    && mkdir -p /app/storage/uploads /app/storage/models /app/experiments/results

EXPOSE 8000
ENTRYPOINT ["/app/docker/backend-entrypoint.sh"]
