FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    FLASK_APP=app.main:app

# Instalar dependencias del sistema y limpiar cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario y configurar permisos
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Instalar dependencias de Python
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY --chown=appuser:appuser . .

# Comando de inicio mejorado
CMD ["sh", "-c", "flask run --host=0.0.0.0 --port=8004 & celery -A app.tasks.notifications worker --loglevel=info"]