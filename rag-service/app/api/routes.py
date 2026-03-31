from http import HTTPStatus

from flask import Blueprint, jsonify, request

from app.api.schemas import parse_query_request


def create_blueprint(rag_service, health_service) -> Blueprint:
    blueprint = Blueprint("rag", __name__)

    @blueprint.get("/health")
    def health():
        payload = health_service.get_health()
        status_code = HTTPStatus.OK if payload.get("status") == "healthy" else HTTPStatus.SERVICE_UNAVAILABLE
        return jsonify(payload), status_code

    @blueprint.post("/catalog/index")
    def catalog_index():
        return jsonify({"status": "indexed", **rag_service.build_index()}), 200

    @blueprint.post("/rag/query")
    def rag_query():
        try:
            query_request = parse_query_request(request.get_json(silent=True))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify(rag_service.answer_query(query_request.query, query_request.top_k)), 200

    return blueprint