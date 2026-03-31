from typing import Any

from app.clients.openrouter_client import OpenRouterClient
from app.core.config import settings
from app.services.catalog_document_service import CatalogDocumentService
from app.services.vector_index_service import VectorIndexService


class CatalogRAGService:
    def __init__(
        self,
        document_service: CatalogDocumentService,
        vector_index_service: VectorIndexService,
        openrouter_client: OpenRouterClient,
    ):
        self._document_service = document_service
        self._vector_index_service = vector_index_service
        self._openrouter_client = openrouter_client

    def build_index(self) -> dict[str, Any]:
        documents = self._document_service.build_documents()
        return self._vector_index_service.reindex(documents)

    def get_index_status(self) -> dict[str, Any]:
        return self._vector_index_service.get_status()

    def answer_query(self, question: str, top_k: int | None = None) -> dict[str, Any]:
        search_k = top_k or settings.default_top_k
        documents = self._vector_index_service.similarity_search(
            question,
            search_k,
            self._document_service.build_documents,
        )
        sources = self._serialize_sources(documents)

        if not sources:
            return {
                "mode": "retrieval_only",
                "answer": "No relevant catalog context was found for this question.",
                "sources": [],
            }

        if not self._openrouter_client.is_enabled():
            return {
                "mode": "retrieval_only",
                "answer": "Relevant products were retrieved, but OpenRouter is not configured. See the returned sources.",
                "sources": sources,
            }

        context = "\n\n".join(source["content"] for source in sources)
        return {
            "mode": "rag",
            "answer": self._openrouter_client.generate_answer(question, context),
            "sources": sources,
        }

    @staticmethod
    def _serialize_sources(documents: list[Any]) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []
        for document in documents:
            source = dict(document.metadata)
            source["content"] = document.page_content
            sources.append(source)
        return sources