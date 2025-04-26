from flask import Flask
from app.routes.recommendations import recommendations_router  # Nombre corregido
from app.services.queue_service import start_consumer
from app.utils.logger import configure_logging
import threading

def create_app():
    app = Flask(__name__)
    app.register_blueprint(recommendations_router)  # Usar el router corregido
    configure_logging()
    return app

app = create_app()

if __name__ == "__main__":
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    app.run(host='0.0.0.0', port=8003)