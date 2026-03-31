from app.core.database import ping_database
from app.services.catalog_rag_service import CatalogRAGService


class HealthService:
    def __init__(self, rag_service: CatalogRAGService, llm_enabled_provider):
        self._rag_service = rag_service
        self._llm_enabled_provider = llm_enabled_provider

    def get_health(self) -> dict:
        try:
            ping_database()
            mongo_status = "connected"
        except Exception:
            mongo_status = "disconnected"

        try:
            index_status = self._rag_service.get_index_status()
            vector_store_status = "ready"
        except Exception as exc:
            index_status = {"error": str(exc)}
            vector_store_status = "degraded"

        return {
            "status": "healthy" if mongo_status == "connected" and vector_store_status == "ready" else "degraded",
            "services": {
                "mongodb": mongo_status,
                "vector_store": vector_store_status,
                "openrouter": "configured" if self._llm_enabled_provider() else "disabled",
            },
            "index": index_status,
        }