from flask import Flask

from app.api.routes import create_blueprint
from app.clients.openrouter_client import OpenRouterClient
from app.repositories.catalog_repository import CatalogRepository
from app.services.catalog_document_service import CatalogDocumentService
from app.services.catalog_rag_service import CatalogRAGService
from app.services.health_service import HealthService
from app.services.vector_index_service import VectorIndexService


def create_app() -> Flask:
    app = Flask(__name__)

    catalog_repository = CatalogRepository()
    document_service = CatalogDocumentService(catalog_repository)
    vector_index_service = VectorIndexService()
    openrouter_client = OpenRouterClient()
    rag_service = CatalogRAGService(document_service, vector_index_service, openrouter_client)
    health_service = HealthService(rag_service, openrouter_client.is_enabled)

    app.register_blueprint(create_blueprint(rag_service, health_service))
    return app