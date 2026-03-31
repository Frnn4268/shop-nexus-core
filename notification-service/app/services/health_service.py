from app.clients.rabbitmq_client import RabbitMQClient
from app.tasks.notifications import celery


class HealthService:
    def __init__(self, rabbitmq_client: RabbitMQClient):
        self._rabbitmq_client = rabbitmq_client

    def get_health(self) -> dict:
        rabbitmq_status = self._check_rabbitmq_connection()
        celery_status = self._check_celery_status()
        overall_status = self._resolve_overall_status(rabbitmq_status, celery_status)
        return {
            "status": overall_status,
            "version": "1.0.0",
            "services": {
                "rabbitmq": rabbitmq_status,
                "celery": celery_status,
            },
        }

    @staticmethod
    def _resolve_overall_status(rabbitmq_status: dict, celery_status: dict) -> str:
        if rabbitmq_status.get("status") != "connected":
            return "degraded"
        if celery_status.get("status") != "active":
            return "degraded"
        return "healthy"

    def _check_rabbitmq_connection(self) -> dict:
        try:
            connection = self._rabbitmq_client.create_url_connection()
            connection.close()
            return {"status": "connected", "error": None}
        except Exception as exc:
            return {"status": "disconnected", "error": str(exc)}

    @staticmethod
    def _check_celery_status() -> dict:
        try:
            inspector = celery.control.inspect()
            return {"status": "active" if inspector and inspector.ping() else "inactive", "error": None}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}