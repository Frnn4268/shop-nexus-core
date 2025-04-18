FROM python:3.11-slim-bullseye

WORKDIR /app

# Instalar dependencias del sistema para pandas y scikit-learn
RUN apt-get update && apt-get install -y gcc python3-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:8003 --workers 4 app.main:app"]