FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando para iniciar Flask y Celery Worker
CMD sh -c "celery -A app.tasks.notifications worker --loglevel=info & python app/main.py"