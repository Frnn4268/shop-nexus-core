FROM python:3.11-slim

WORKDIR /app

# Configurar entorno para módulos Python
ENV PYTHONPATH="/app"

# Instalar dependencias del sistema (solo si son necesarias)
RUN apt-get update && apt-get install -y gcc

# Crear usuario no privilegiado desde el inicio
RUN adduser --disabled-password appuser && chown -R appuser /app
USER appuser

# Instalar todas las dependencias como usuario no root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando para iniciar Celery + Flask
CMD ["sh", "-c", "celery -A app.tasks.notifications worker --loglevel=info & python app/main.py"]