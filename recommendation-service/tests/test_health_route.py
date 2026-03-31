import unittest
from unittest.mock import Mock

from flask import Flask

from app.api.routes import create_blueprint


class RecommendationRouteTests(unittest.TestCase):
    def test_health_route_returns_503_when_degraded(self):
        app = Flask(__name__)
        recommendation_service = Mock()
        health_service = Mock()
        health_service.get_health.return_value = {"status": "degraded", "services": {}}
        app.register_blueprint(create_blueprint(recommendation_service, health_service))

        response = app.test_client().get("/health")

        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()