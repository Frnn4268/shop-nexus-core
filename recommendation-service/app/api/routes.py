from http import HTTPStatus

from flask import Blueprint, jsonify, request

from app.api.schemas import parse_limit


def create_blueprint(recommendation_service, health_service) -> Blueprint:
    blueprint = Blueprint("recommendation", __name__)

    @blueprint.get("/recommendations/<string:user_id>")
    def recommendations(user_id: str):
        try:
            limit = parse_limit(request.args.get("limit"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        payload, status_code = recommendation_service.get_recommendations_response(user_id, limit)
        return jsonify(payload), status_code

    @blueprint.post("/recommendations/train")
    def retrain():
        return jsonify(recommendation_service.retrain()), 200

    @blueprint.get("/recommendations/evaluation")
    def evaluation():
        return jsonify(recommendation_service.evaluation()), 200

    @blueprint.get("/recommendations/artifacts")
    def artifacts():
        return jsonify(recommendation_service.artifacts()), 200

    @blueprint.post("/recommendations/rollback")
    def rollback():
        payload = request.get_json(silent=True) or {}
        response, status_code = recommendation_service.rollback(str(payload.get("artifact_id", "")).strip())
        return jsonify(response), status_code

    @blueprint.get("/health")
    def health():
        payload = health_service.get_health()
        status_code = HTTPStatus.OK if payload.get("status") == "healthy" else HTTPStatus.SERVICE_UNAVAILABLE
        return jsonify(payload), status_code

    return blueprint