FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GUNICORN_WORKERS=2 \
    GUNICORN_TIMEOUT=300 \
    GUNICORN_WORKER_CLASS=gevent

# Añadir más dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libopenblas-dev \
    libgomp1 \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:8003 --workers ${GUNICORN_WORKERS} --timeout ${GUNICORN_TIMEOUT} --worker-class ${GUNICORN_WORKER_CLASS} --access-logfile - app.main:app"]