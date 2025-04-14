from flask import Flask
from app.handlers.notification_handler import start_consumer
from threading import Thread
import os

app = Flask(__name__)

# Iniciar consumidor en segundo plano
Thread(target=start_consumer, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8004)