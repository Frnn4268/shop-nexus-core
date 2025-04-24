from flask import Flask, jsonify
from app.handlers.notification_handler import start_consumer
from threading import Thread
import os
import pika
from app.tasks.notifications import celery

app = Flask(__name__)

# Configuración básica de logging
if os.getenv("FLASK_ENV") == "production":
    app.logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
else:
    app.logger.setLevel("DEBUG")

def check_rabbitmq_connection():
    """Verifica la conexión con RabbitMQ"""
    try:
        connection = pika.BlockingConnection(
            pika.URLParameters(os.getenv("RABBITMQ_URI")))
        connection.close()
        return {"status": "connected", "error": None}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}

def check_celery_status():
    """Verifica el estado de Celery"""
    try:
        insp = celery.control.inspect()
        return {"status": "active" if insp.ping() else "inactive", "error": None}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.route('/health')
def health_check():
    """Endpoint de health check para monitoreo"""
    services = {
        "rabbitmq": check_rabbitmq_connection(),
        "celery": check_celery_status()
    }
    return jsonify({
        "status": "OK",
        "version": "1.0.0",
        "services": services
    })

def start_background_consumer():
    """Inicia el consumidor en segundo plano con manejo de errores"""
    try:
        Thread(target=start_consumer, daemon=True).start()
        app.logger.info("Consumer de RabbitMQ iniciado en segundo plano")
    except Exception as e:
        app.logger.error(f"Error al iniciar el consumer: {str(e)}")

if __name__ == "__main__":
    start_background_consumer()
    app.run(
        host='0.0.0.0', 
        port=int(os.getenv("PORT", 8004)),
        use_reloader=False  # Importante para evitar doble ejecución en desarrollo
    )
else:
    # Para cuando se ejecuta con Gunicorn/uWSGI
    start_background_consumer()