from bson import ObjectId

from app.core.database import get_db
from app.services.model_service import get_model_status, get_recommendations, list_model_artifacts, rollback_model, train_model


class RecommendationService:
    def get_recommendations_response(self, user_id: str, limit: int) -> tuple[dict | list[dict], int]:
        if not ObjectId.is_valid(user_id):
            return {"error": "Invalid user ID"}, 400

        recommendations_payload = get_recommendations(user_id, num=limit)
        if not recommendations_payload:
            return {"message": "No recommendations available"}, 404

        product_ids = [item["product_id"] for item in recommendations_payload if ObjectId.is_valid(item["product_id"])]
        products = list(
            get_db().products.find(
                {"_id": {"$in": [ObjectId(product_id) for product_id in product_ids]}},
                {"name": 1, "price": 1, "description": 1, "category_ids": 1},
            )
        )
        products_by_id = {str(product["_id"]): product for product in products}

        response = []
        for recommendation in recommendations_payload:
            product = products_by_id.get(recommendation["product_id"])
            if not product:
                continue
            response.append(
                {
                    "id": str(product["_id"]),
                    "name": product.get("name"),
                    "description": product.get("description"),
                    "price": product.get("price"),
                    "category_ids": [str(category_id) for category_id in product.get("category_ids", [])],
                    "score": recommendation["score"],
                    "source": recommendation["source"],
                }
            )

        return response, 200

    @staticmethod
    def retrain() -> dict:
        artifact = train_model()
        return {
            "status": "trained",
            **get_model_status(),
            "artifacts": {
                "artifact_version": artifact.get("artifact_version"),
                "popular_product_ids": artifact.get("popular_product_ids", [])[:5],
                "evaluation": artifact.get("evaluation"),
            },
        }

    @staticmethod
    def evaluation() -> dict:
        model_status = get_model_status()
        return {
            "model_ready": model_status["model_ready"],
            "artifact_id": model_status.get("artifact_id"),
            "artifact_version": model_status.get("artifact_version"),
            "ranking_weights": model_status.get("ranking_weights"),
            "evaluation": model_status.get("evaluation"),
        }

    @staticmethod
    def artifacts() -> dict:
        return list_model_artifacts()

    @staticmethod
    def rollback(artifact_id: str) -> tuple[dict, int]:
        if not artifact_id:
            return {"error": "artifact_id is required"}, 400

        try:
            return rollback_model(artifact_id), 200
        except FileNotFoundError as exc:
            return {"error": str(exc)}, 404

    @staticmethod
    def health() -> dict:
        return {
            "services": {
                "recommendation_model": get_model_status(),
            }
        }