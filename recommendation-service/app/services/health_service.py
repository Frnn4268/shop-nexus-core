from app.core.database import ping_database
from app.services.model_service import get_model_status


class HealthService:
    @staticmethod
    def get_health() -> dict:
        model_status = get_model_status()
        try:
            ping_database()
            mongo_status = "connected"
        except Exception:
            mongo_status = "disconnected"

        return {
            "status": "healthy" if mongo_status == "connected" else "degraded",
            "services": {
                "mongodb": mongo_status,
                "recommendation_model": model_status,
            },
        }