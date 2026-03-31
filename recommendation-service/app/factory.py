from flask import Flask

from app.api.routes import create_blueprint
from app.services.health_service import HealthService
from app.services.recommendation_service import RecommendationService


def create_app() -> Flask:
    app = Flask(__name__)
    recommendation_service = RecommendationService()
    health_service = HealthService()
    app.register_blueprint(create_blueprint(recommendation_service, health_service))
    return app