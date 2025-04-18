from flask import Flask
from app.handlers.notification_handler import start_consumer
from threading import Thread
import os

# La variable 'app' debe estar en el nivel superior del módulo
app = Flask(__name__)

# Iniciar consumidor de RabbitMQ en segundo plano
Thread(target=start_consumer, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8004))