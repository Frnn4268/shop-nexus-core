import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from flask import Flask

from app.api.routes import create_blueprint
from app.api.schemas import parse_limit
from app.services import model_service


class ParseLimitTests(unittest.TestCase):
    def test_parse_limit_uses_default_when_missing(self):
        self.assertEqual(parse_limit(None), 5)

    def test_parse_limit_caps_to_supported_range(self):
        self.assertEqual(parse_limit("50"), 20)
        self.assertEqual(parse_limit("0"), 1)

    def test_parse_limit_rejects_non_numeric_values(self):
        with self.assertRaisesRegex(ValueError, "limit must be an integer"):
            parse_limit("invalid")


class RecommendationModelServiceTests(unittest.TestCase):
    def test_get_model_status_exposes_artifact_metadata(self):
        artifact = {
            "artifact_version": "1.1",
            "trained_at": "2026-03-30T00:00:00+00:00",
            "interactions_count": 12,
            "users_count": 3,
            "products_count": 4,
            "popular_product_ids": ["p1", "p2"],
            "ranking_weights": {
                "collaborative_filtering": 0.75,
                "popularity": 0.15,
                "category_affinity": 0.10,
            },
            "evaluation": {"precision_at_k": 0.2},
        }

        with patch("app.services.model_service.load_model", return_value=artifact):
            status = model_service.get_model_status()

        self.assertTrue(status["model_ready"])
        self.assertEqual(status["artifact_version"], "1.1")
        self.assertEqual(status["fallback_count"], 2)
        self.assertIn("ranking_weights", status)

    def test_list_model_artifacts_returns_manifest_payload(self):
        manifest = {
            "active_artifact_id": "artifact-2",
            "artifacts": [
                {"artifact_id": "artifact-2"},
                {"artifact_id": "artifact-1"},
            ],
        }

        with patch("app.services.model_service._read_manifest", return_value=manifest):
            payload = model_service.list_model_artifacts()

        self.assertEqual(payload["active_artifact_id"], "artifact-2")
        self.assertEqual(len(payload["artifacts"]), 2)

    def test_rollback_model_restores_selected_artifact(self):
        artifact = {
            "artifact_id": "artifact-1",
            "artifact_version": "1.1",
            "trained_at": "2026-03-30T00:00:00+00:00",
            "interactions_count": 5,
            "users_count": 2,
            "products_count": 3,
            "popular_product_ids": [],
            "ranking_weights": {},
            "evaluation": {},
            "artifact_path": "/tmp/artifact-1.joblib",
        }
        manifest = {"active_artifact_id": "artifact-2", "artifacts": [{"artifact_id": "artifact-2"}]}

        with patch("app.services.model_service._load_artifact_by_id", return_value=artifact), patch(
            "app.services.model_service.dump"
        ) as dump_mock, patch("app.services.model_service._read_manifest", return_value=manifest), patch(
            "app.services.model_service._write_manifest"
        ), patch("app.services.model_service.get_model_status", return_value={"artifact_id": "artifact-1", "model_ready": True}):
            payload = model_service.rollback_model("artifact-1")

        dump_mock.assert_called_once_with(artifact, model_service.settings.model_path)
        self.assertEqual(payload["status"], "rolled_back")
        self.assertEqual(payload["artifact_id"], "artifact-1")

    def test_train_model_persists_versioned_artifacts_and_prunes_old_ones(self):
        fake_payload = {
            "artifact_version": "1.1",
            "trained_at": "2026-03-30T00:00:00+00:00",
            "interactions_count": 10,
            "users_count": 2,
            "products_count": 3,
            "popular_product_ids": [],
            "ranking_weights": {},
            "evaluation": {},
        }

        with TemporaryDirectory() as tmp_dir, patch.object(model_service.settings, "model_path", str(Path(tmp_dir) / "model.joblib")), patch.object(
            model_service.settings,
            "model_registry_dir",
            str(Path(tmp_dir) / "artifacts"),
        ), patch.object(model_service.settings, "model_versions_to_keep", 1), patch(
            "app.services.model_service._build_training_payload",
            return_value=fake_payload,
        ), patch("app.services.model_service._new_artifact_id", return_value="artifact-1"), patch(
            "app.services.model_service.dump"
        ) as dump_mock, patch("app.services.model_service._write_manifest") as write_manifest_mock:
            payload = model_service.train_model()

        self.assertEqual(payload["artifact_id"], "artifact-1")
        self.assertEqual(dump_mock.call_count, 2)
        write_manifest_mock.assert_called_once()

    def test_get_recommendations_returns_popular_fallback_when_model_missing(self):
        with patch("app.services.model_service.load_model", return_value=None), patch(
            "app.services.model_service._popular_products",
            return_value=["p1", "p2"],
        ):
            recommendations = model_service.get_recommendations("user-1", num=2)

        self.assertEqual(
            recommendations,
            [
                {"product_id": "p1", "score": 0.0, "source": "popular_fallback"},
                {"product_id": "p2", "score": 0.0, "source": "popular_fallback"},
            ],
        )

    def test_empty_evaluation_contains_extended_metrics(self):
        evaluation = model_service._empty_evaluation()

        self.assertEqual(evaluation["hit_rate_at_k"], 0.0)
        self.assertEqual(evaluation["mrr_at_k"], 0.0)
        self.assertIn("top_k", evaluation)


class RecommendationRouteArtifactTests(unittest.TestCase):
    def test_artifacts_route_returns_payload(self):
        app = Flask(__name__)
        recommendation_service = type("RecommendationServiceStub", (), {"artifacts": staticmethod(lambda: {"artifacts": []}), "retrain": staticmethod(lambda: {}), "evaluation": staticmethod(lambda: {}), "get_recommendations_response": staticmethod(lambda user_id, limit: ({}, 200)), "rollback": staticmethod(lambda artifact_id: ({}, 200))})()
        health_service = type("HealthServiceStub", (), {"get_health": staticmethod(lambda: {"status": "healthy", "services": {}})})()
        app.register_blueprint(create_blueprint(recommendation_service, health_service))

        response = app.test_client().get("/recommendations/artifacts")

        self.assertEqual(response.status_code, 200)

    def test_rollback_route_requires_artifact_id(self):
        app = Flask(__name__)
        recommendation_service = type("RecommendationServiceStub", (), {"artifacts": staticmethod(lambda: {"artifacts": []}), "retrain": staticmethod(lambda: {}), "evaluation": staticmethod(lambda: {}), "get_recommendations_response": staticmethod(lambda user_id, limit: ({}, 200)), "rollback": staticmethod(lambda artifact_id: ({"error": "artifact_id is required"}, 400))})()
        health_service = type("HealthServiceStub", (), {"get_health": staticmethod(lambda: {"status": "healthy", "services": {}})})()
        app.register_blueprint(create_blueprint(recommendation_service, health_service))

        response = app.test_client().post("/recommendations/rollback", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "artifact_id is required")


if __name__ == "__main__":
    unittest.main()