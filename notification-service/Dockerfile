FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    FLASK_APP=app.main:app

# Install system dependencies and clean package cache.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and grant ownership of the app directory.
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Install Python dependencies.
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY --chown=appuser:appuser . .

CMD ["python", "-m", "app.main"]