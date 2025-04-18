FROM python:3.11-slim

WORKDIR /app

ENV FLASK_APP=app.main:app

RUN apt-get update && apt-get install -y gcc python3-dev curl 
RUN pip install celery==5.3.6

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear usuario no-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

COPY . .

CMD ["sh", "-c", "celery -A app.tasks.notifications worker --loglevel=info -Q order_created & flask run --host=0.0.0.0 --port=8004"]