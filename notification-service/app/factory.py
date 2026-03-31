from flask import Flask

from app.api.routes import create_blueprint
from app.clients.rabbitmq_client import RabbitMQClient
from app.core.logging_config import configure_logging
from app.services.health_service import HealthService


def create_app() -> Flask:
    configure_logging()

    app = Flask(__name__)
    rabbitmq_client = RabbitMQClient()
    health_service = HealthService(rabbitmq_client)
    app.register_blueprint(create_blueprint(health_service))
    return app