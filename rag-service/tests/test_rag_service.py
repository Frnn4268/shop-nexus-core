import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from flask import Flask

from app.api.routes import create_blueprint
from app.api.schemas import parse_query_request
from app.services.catalog_rag_service import CatalogRAGService


class ParseQueryRequestTests(unittest.TestCase):
    def test_parse_query_request_requires_query(self):
        with self.assertRaisesRegex(ValueError, "query is required"):
            parse_query_request({})

    def test_parse_query_request_clamps_top_k(self):
        request_model = parse_query_request({"query": "desk setup", "top_k": 50})
        self.assertEqual(request_model.top_k, 10)


class CatalogRAGServiceTests(unittest.TestCase):
    def test_answer_query_returns_retrieval_only_when_no_sources(self):
        document_service = Mock()
        vector_index_service = Mock()
        openrouter_client = Mock()
        vector_index_service.similarity_search.return_value = []
        service = CatalogRAGService(document_service, vector_index_service, openrouter_client)

        response = service.answer_query("chair")

        self.assertEqual(response["mode"], "retrieval_only")
        self.assertEqual(response["sources"], [])

    def test_answer_query_returns_retrieval_only_when_openrouter_disabled(self):
        document_service = Mock()
        vector_index_service = Mock()
        openrouter_client = Mock()
        openrouter_client.is_enabled.return_value = False
        vector_index_service.similarity_search.return_value = [
            SimpleNamespace(metadata={"product_id": "p1"}, page_content="Product: Chair")
        ]
        service = CatalogRAGService(document_service, vector_index_service, openrouter_client)

        response = service.answer_query("chair")

        self.assertEqual(response["mode"], "retrieval_only")
        self.assertEqual(len(response["sources"]), 1)

    def test_answer_query_returns_rag_when_openrouter_enabled(self):
        document_service = Mock()
        vector_index_service = Mock()
        openrouter_client = Mock()
        openrouter_client.is_enabled.return_value = True
        openrouter_client.generate_answer.return_value = "Grounded answer"
        vector_index_service.similarity_search.return_value = [
            SimpleNamespace(metadata={"product_id": "p1"}, page_content="Product: Chair")
        ]
        service = CatalogRAGService(document_service, vector_index_service, openrouter_client)

        response = service.answer_query("chair")

        self.assertEqual(response["mode"], "rag")
        self.assertEqual(response["answer"], "Grounded answer")


class RAGRouteTests(unittest.TestCase):
    def test_health_route_returns_503_when_degraded(self):
        app = Flask(__name__)
        rag_service = Mock()
        health_service = Mock()
        health_service.get_health.return_value = {"status": "degraded", "services": {}}
        app.register_blueprint(create_blueprint(rag_service, health_service))

        response = app.test_client().get("/health")

        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()