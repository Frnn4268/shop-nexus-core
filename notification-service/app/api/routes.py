from http import HTTPStatus

from flask import Blueprint, jsonify


def create_blueprint(health_service) -> Blueprint:
    blueprint = Blueprint("notification", __name__)

    @blueprint.get("/health")
    def health_check():
        payload = health_service.get_health()
        status_code = HTTPStatus.OK if payload.get("status") == "healthy" else HTTPStatus.SERVICE_UNAVAILABLE
        return jsonify(payload), status_code

    return blueprint