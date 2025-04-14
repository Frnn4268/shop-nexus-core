FROM python:3.11-slim-bullseye

WORKDIR /app

# Establecer PYTHONPATH para incluir el directorio actual
ENV PYTHONPATH="${PYTHONPATH}:/app"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app/main.py"]