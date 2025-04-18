FROM python:3.11-slim

WORKDIR /app

ENV FLASK_APP=app.main:app

# Instalar dependencias del sistema + Celery
RUN apt-get update && apt-get install -y gcc python3-dev curl 

# Instalar Celery explícitamente
RUN pip install celery==5.3.6

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "celery -A app.tasks.notifications worker --loglevel=info & flask run --host=0.0.0.0 --port=8004"]