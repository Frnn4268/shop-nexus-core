import logging
import json
import os
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from joblib import dump, load

from app.core.config import settings
from app.core.database import get_db


LOGGER = logging.getLogger(__name__)

_MODEL_CACHE: dict[str, Any] | None = None
_MODEL_LOCK = threading.Lock()
_ARTIFACT_VERSION = "1.1"
_MANIFEST_NAME = "manifest.json"
_RANKING_WEIGHTS = {
    "collaborative_filtering": 0.75,
    "popularity": 0.15,
    "category_affinity": 0.10,
}


def _ensure_model_dir() -> None:
    os.makedirs(os.path.dirname(settings.model_path), exist_ok=True)
    os.makedirs(settings.model_registry_dir, exist_ok=True)


def _manifest_path() -> str:
    return os.path.join(settings.model_registry_dir, _MANIFEST_NAME)


def _artifact_file_name(artifact_id: str) -> str:
    return f"recommendation-model-{artifact_id}.joblib"


def _artifact_path(artifact_id: str) -> str:
    return os.path.join(settings.model_registry_dir, _artifact_file_name(artifact_id))


def _new_artifact_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _default_manifest() -> dict[str, Any]:
    return {"active_artifact_id": None, "artifacts": []}


def _read_manifest() -> dict[str, Any]:
    path = _manifest_path()
    if not os.path.exists(path):
        return _default_manifest()

    with open(path, "r", encoding="utf-8") as manifest_file:
        payload = json.load(manifest_file)

    if not isinstance(payload, dict):
        return _default_manifest()

    payload.setdefault("active_artifact_id", None)
    payload.setdefault("artifacts", [])
    return payload


def _write_manifest(manifest: dict[str, Any]) -> None:
    with open(_manifest_path(), "w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, indent=2, sort_keys=True)


def _artifact_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": payload.get("artifact_id"),
        "artifact_version": payload.get("artifact_version"),
        "trained_at": payload.get("trained_at"),
        "interactions_count": payload.get("interactions_count", 0),
        "users_count": payload.get("users_count", 0),
        "products_count": payload.get("products_count", 0),
        "evaluation": payload.get("evaluation"),
        "path": payload.get("artifact_path"),
    }


def _upsert_manifest_entry(manifest: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    artifact_id = payload.get("artifact_id")
    artifacts = [entry for entry in manifest.get("artifacts", []) if entry.get("artifact_id") != artifact_id]
    artifacts.insert(0, _artifact_summary(payload))
    manifest["artifacts"] = artifacts
    manifest["active_artifact_id"] = artifact_id
    return manifest


def _prune_old_artifacts(manifest: dict[str, Any]) -> dict[str, Any]:
    retained = manifest.get("artifacts", [])[: settings.model_versions_to_keep]
    removed = manifest.get("artifacts", [])[settings.model_versions_to_keep :]
    for artifact in removed:
        artifact_path = artifact.get("path")
        if artifact_path and os.path.exists(artifact_path):
            os.remove(artifact_path)
    manifest["artifacts"] = retained
    if manifest.get("active_artifact_id") not in {entry.get("artifact_id") for entry in retained}:
        manifest["active_artifact_id"] = retained[0].get("artifact_id") if retained else None
    return manifest


def _persist_active_artifact(payload: dict[str, Any], artifact_id: str) -> None:
    payload["artifact_id"] = artifact_id
    payload["artifact_path"] = _artifact_path(artifact_id)
    dump(payload, payload["artifact_path"])
    dump(payload, settings.model_path)


def _load_artifact_by_id(artifact_id: str) -> dict[str, Any]:
    artifact_path = _artifact_path(artifact_id)
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"artifact {artifact_id} does not exist")
    payload = load(artifact_path)
    payload.setdefault("artifact_id", artifact_id)
    payload.setdefault("artifact_path", artifact_path)
    return payload


def list_model_artifacts() -> dict[str, Any]:
    manifest = _read_manifest()
    return {
        "active_artifact_id": manifest.get("active_artifact_id"),
        "artifacts": manifest.get("artifacts", []),
        "retention_limit": settings.model_versions_to_keep,
    }


def rollback_model(artifact_id: str) -> dict[str, Any]:
    global _MODEL_CACHE

    with _MODEL_LOCK:
        payload = _load_artifact_by_id(artifact_id)
        dump(payload, settings.model_path)
        _MODEL_CACHE = payload

        manifest = _read_manifest()
        manifest["active_artifact_id"] = artifact_id
        manifest = _upsert_manifest_entry(manifest, payload)
        _write_manifest(manifest)

        LOGGER.info("Recommendation model rolled back to artifact %s", artifact_id)
        return {
            "status": "rolled_back",
            "artifact_id": artifact_id,
            **get_model_status(),
        }


def _serialize_mongo_value(value: Any) -> str:
    return str(value)


def _normalize_score_map(raw_scores: dict[str, float]) -> dict[str, float]:
    if not raw_scores:
        return {}

    values = list(raw_scores.values())
    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        return {key: 1.0 for key in raw_scores}
    return {key: (value - minimum) / (maximum - minimum) for key, value in raw_scores.items()}


def _empty_evaluation() -> dict[str, Any]:
    return {
        "evaluated_users": 0,
        "precision_at_k": 0.0,
        "recall_at_k": 0.0,
        "coverage_at_k": 0.0,
        "hit_rate_at_k": 0.0,
        "mrr_at_k": 0.0,
        "top_k": settings.evaluation_top_k,
    }


def _build_training_metadata(
    interactions_count: int,
    users_count: int,
    products_count: int,
) -> dict[str, Any]:
    return {
        "artifact_version": _ARTIFACT_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "interactions_count": interactions_count,
        "users_count": users_count,
        "products_count": products_count,
        "ranking_weights": dict(_RANKING_WEIGHTS),
    }


def _build_product_category_map() -> dict[str, list[str]]:
    db = get_db()
    category_map: dict[str, list[str]] = {}
    for product in db.products.find({}, {"category_ids": 1}):
        category_map[str(product["_id"])] = [str(category_id) for category_id in product.get("category_ids", [])]
    return category_map


def _build_user_category_affinity(
    interactions: list[dict[str, Any]],
    product_category_map: dict[str, list[str]],
) -> dict[str, dict[str, float]]:
    affinity_totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for interaction in interactions:
        user_id = _serialize_mongo_value(interaction["user_id"])
        product_id = _serialize_mongo_value(interaction["product_id"])
        quantity = max(float(interaction.get("quantity", 1)), 1.0)
        for category_id in product_category_map.get(product_id, []):
            affinity_totals[user_id][category_id] += quantity

    affinity_scores: dict[str, dict[str, float]] = {}
    for user_id, category_scores in affinity_totals.items():
        maximum = max(category_scores.values()) if category_scores else 1.0
        affinity_scores[user_id] = {
            category_id: score / maximum
            for category_id, score in category_scores.items()
        }
    return affinity_scores


def _category_affinity_score(
    user_id: str,
    product_id: str,
    user_category_affinity: dict[str, dict[str, float]],
    product_category_map: dict[str, list[str]],
) -> float:
    categories = product_category_map.get(product_id, [])
    if not categories:
        return 0.0
    affinity = user_category_affinity.get(user_id, {})
    if not affinity:
        return 0.0
    return max((affinity.get(category_id, 0.0) for category_id in categories), default=0.0)


def _build_sparse_matrix(interactions: list[dict[str, Any]]) -> tuple[Any, dict[str, int], dict[str, int]]:
    from scipy.sparse import coo_matrix

    user_to_index: dict[str, int] = {}
    item_to_index: dict[str, int] = {}
    rows: list[int] = []
    cols: list[int] = []
    weights: list[float] = []

    for interaction in interactions:
        user_id = _serialize_mongo_value(interaction["user_id"])
        product_id = _serialize_mongo_value(interaction["product_id"])
        quantity = max(float(interaction.get("quantity", 1)), 1.0)

        user_index = user_to_index.setdefault(user_id, len(user_to_index))
        item_index = item_to_index.setdefault(product_id, len(item_to_index))

        rows.append(user_index)
        cols.append(item_index)
        weights.append(quantity)

    matrix = coo_matrix(
        (weights, (rows, cols)),
        shape=(len(user_to_index), len(item_to_index)),
    ).tocsr()
    return matrix, user_to_index, item_to_index


def _train_als_model(user_items) -> Any | None:
    from implicit.als import AlternatingLeastSquares

    if user_items.shape[0] == 0 or user_items.shape[1] == 0:
        return None

    model = AlternatingLeastSquares(
        factors=min(settings.model_factors, max(8, user_items.shape[1])),
        iterations=settings.model_iterations,
        regularization=settings.model_regularization,
    )
    model.fit((user_items * settings.model_alpha).T.tocsr())
    return model


def _split_train_test(interactions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    interactions_by_user: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for interaction in interactions:
        interactions_by_user[_serialize_mongo_value(interaction["user_id"])].append(interaction)

    train_interactions: list[dict[str, Any]] = []
    test_items_by_user: dict[str, set[str]] = {}
    for user_id, user_interactions in interactions_by_user.items():
        if len(user_interactions) < 2:
            train_interactions.extend(user_interactions)
            continue

        holdout = user_interactions[-1]
        train_interactions.extend(user_interactions[:-1])
        test_items_by_user[user_id] = {_serialize_mongo_value(holdout["product_id"])}

    return train_interactions, test_items_by_user


def _evaluate_model(interactions: list[dict[str, Any]]) -> dict[str, Any]:
    train_interactions, test_items_by_user = _split_train_test(interactions)
    if not test_items_by_user:
        return _empty_evaluation()

    user_items, user_to_index, item_to_index = _build_sparse_matrix(train_interactions)
    model = _train_als_model(user_items)
    if model is None:
        return _empty_evaluation()

    index_to_item = {index: product_id for product_id, index in item_to_index.items()}
    hits = 0
    evaluated_users = 0
    reciprocal_rank_sum = 0.0
    unique_recommended_items: set[str] = set()

    for user_id, expected_items in test_items_by_user.items():
        user_index = user_to_index.get(user_id)
        if user_index is None:
            continue
        item_ids, _ = model.recommend(
            user_index,
            user_items[user_index],
            N=settings.evaluation_top_k,
            filter_already_liked_items=True,
        )
        recommended_items = {
            index_to_item[int(item_index)]
            for item_index in item_ids
            if int(item_index) in index_to_item
        }
        if not recommended_items:
            continue
        evaluated_users += 1
        matching_items = recommended_items & expected_items
        hits += len(matching_items)
        unique_recommended_items.update(recommended_items)

        for rank, item_id in enumerate(item_ids, start=1):
            product_id = index_to_item.get(int(item_id))
            if product_id in expected_items:
                reciprocal_rank_sum += 1 / rank
                break

    denominator = max(evaluated_users, 1)
    return {
        "evaluated_users": evaluated_users,
        "precision_at_k": round(hits / (denominator * settings.evaluation_top_k), 4),
        "recall_at_k": round(hits / denominator, 4),
        "coverage_at_k": round(len(unique_recommended_items) / max(len(item_to_index), 1), 4),
        "hit_rate_at_k": round(hits / denominator, 4),
        "mrr_at_k": round(reciprocal_rank_sum / denominator, 4),
        "top_k": settings.evaluation_top_k,
    }


def _popular_products(limit: int = settings.popular_fallback_size) -> list[str]:
    db = get_db()
    pipeline = [
        {"$unwind": "$items"},
        {"$group": {"_id": "$items.product_id", "score": {"$sum": "$items.quantity"}}},
        {"$sort": {"score": -1}},
        {"$limit": limit},
    ]
    return [_serialize_mongo_value(row["_id"]) for row in db.orders.aggregate(pipeline)]


def _build_training_payload() -> dict[str, Any]:
    db = get_db()
    interactions = list(
        db.orders.aggregate(
            [
                {"$unwind": "$items"},
                {
                    "$project": {
                        "user_id": "$user_id",
                        "product_id": "$items.product_id",
                        "quantity": "$items.quantity",
                        "created_at": "$created_at",
                    }
                },
                {"$sort": {"created_at": 1}},
            ]
        )
    )

    popular_product_ids = _popular_products()
    product_category_map = _build_product_category_map()
    if not interactions:
        metadata = _build_training_metadata(
            interactions_count=0,
            users_count=0,
            products_count=0,
        )
        return {
            "model": None,
            "user_items": None,
            "user_to_index": {},
            "index_to_item": {},
            "popular_product_ids": popular_product_ids,
            "popularity_scores": {},
            "product_category_map": product_category_map,
            "user_category_affinity": {},
            "evaluation": _empty_evaluation(),
            **metadata,
        }

    user_items, user_to_index, item_to_index = _build_sparse_matrix(interactions)
    model = _train_als_model(user_items)

    index_to_item = {index: product_id for product_id, index in item_to_index.items()}
    popularity_totals: dict[str, float] = defaultdict(float)
    for interaction in interactions:
        popularity_totals[_serialize_mongo_value(interaction["product_id"])] += max(float(interaction.get("quantity", 1)), 1.0)

    popularity_scores = _normalize_score_map(dict(popularity_totals))
    user_category_affinity = _build_user_category_affinity(interactions, product_category_map)
    evaluation = _evaluate_model(interactions)
    metadata = _build_training_metadata(
        interactions_count=len(interactions),
        users_count=len(user_to_index),
        products_count=len(item_to_index),
    )

    return {
        "model": model,
        "user_items": user_items,
        "user_to_index": user_to_index,
        "index_to_item": index_to_item,
        "popular_product_ids": popular_product_ids,
        "popularity_scores": popularity_scores,
        "product_category_map": product_category_map,
        "user_category_affinity": user_category_affinity,
        "evaluation": evaluation,
        **metadata,
    }


def train_model() -> dict[str, Any]:
    global _MODEL_CACHE

    with _MODEL_LOCK:
        payload = _build_training_payload()
        _ensure_model_dir()

        artifact_id = _new_artifact_id()
        _persist_active_artifact(payload, artifact_id)

        manifest = _read_manifest()
        manifest = _upsert_manifest_entry(manifest, payload)
        manifest = _prune_old_artifacts(manifest)
        _write_manifest(manifest)

        _MODEL_CACHE = payload
        LOGGER.info(
            "Recommendation model trained with %s interactions as artifact %s",
            payload["interactions_count"],
            payload["artifact_id"],
        )
        return payload


def load_model(force_reload: bool = False) -> dict[str, Any] | None:
    global _MODEL_CACHE

    if _MODEL_CACHE is not None and not force_reload:
        return _MODEL_CACHE

    if not os.path.exists(settings.model_path):
        LOGGER.warning("Recommendation model file not found at %s", settings.model_path)
        return None

    with _MODEL_LOCK:
        if _MODEL_CACHE is not None and not force_reload:
            return _MODEL_CACHE
        _MODEL_CACHE = load(settings.model_path)
        if _MODEL_CACHE is not None:
            manifest = _read_manifest()
            active_artifact_id = manifest.get("active_artifact_id")
            if active_artifact_id and not _MODEL_CACHE.get("artifact_id"):
                _MODEL_CACHE["artifact_id"] = active_artifact_id
                _MODEL_CACHE["artifact_path"] = _artifact_path(active_artifact_id)
        return _MODEL_CACHE


def get_model_status() -> dict[str, Any]:
    artifact = load_model()
    manifest = _read_manifest()
    return {
        "model_ready": artifact is not None,
        "artifact_id": artifact.get("artifact_id") if artifact else manifest.get("active_artifact_id"),
        "artifact_version": artifact.get("artifact_version") if artifact else None,
        "model_path": settings.model_path,
        "model_registry_dir": settings.model_registry_dir,
        "trained_at": artifact.get("trained_at") if artifact else None,
        "interactions_count": artifact.get("interactions_count", 0) if artifact else 0,
        "users_count": artifact.get("users_count", 0) if artifact else 0,
        "products_count": artifact.get("products_count", 0) if artifact else 0,
        "fallback_count": len(artifact.get("popular_product_ids", [])) if artifact else 0,
        "ranking_weights": artifact.get("ranking_weights") if artifact else None,
        "evaluation": artifact.get("evaluation") if artifact else None,
        "artifact_history_count": len(manifest.get("artifacts", [])),
    }


def get_recommendations(user_id: str, num: int = 5) -> list[dict[str, Any]]:
    artifact = load_model()
    if artifact is None:
        return [{"product_id": product_id, "score": 0.0, "source": "popular_fallback"} for product_id in _popular_products(num)]

    popular_candidates = artifact.get("popular_product_ids", [])
    model = artifact.get("model")
    user_items = artifact.get("user_items")
    user_to_index = artifact.get("user_to_index", {})
    index_to_item = artifact.get("index_to_item", {})
    popularity_scores = artifact.get("popularity_scores", {})
    product_category_map = artifact.get("product_category_map", {})
    user_category_affinity = artifact.get("user_category_affinity", {})

    if model is None or user_items is None or user_id not in user_to_index:
        cold_start = []
        for product_id in popular_candidates[:num]:
            cold_start.append(
                {
                    "product_id": product_id,
                    "score": popularity_scores.get(product_id, 0.0),
                    "source": "popular_fallback",
                }
            )
        return cold_start

    user_index = user_to_index[user_id]
    item_ids, scores = model.recommend(
        user_index,
        user_items[user_index],
        N=max(num * 4, 20),
        filter_already_liked_items=True,
    )

    raw_cf_scores: dict[str, float] = {}
    for item_index, score in zip(item_ids, scores):
        product_id = index_to_item.get(int(item_index))
        if product_id:
            raw_cf_scores[product_id] = max(float(score), 0.0)

    normalized_cf_scores = _normalize_score_map(raw_cf_scores)

    recommendations: list[dict[str, Any]] = []
    seen_product_ids: set[str] = set()
    for item_index in item_ids:
        product_id = index_to_item.get(int(item_index))
        if not product_id or product_id in seen_product_ids:
            continue
        cf_score = normalized_cf_scores.get(product_id, 0.0)
        popularity_score = popularity_scores.get(product_id, 0.0)
        affinity_score = _category_affinity_score(
            user_id,
            product_id,
            user_category_affinity,
            product_category_map,
        )
        final_score = round(
            (cf_score * _RANKING_WEIGHTS["collaborative_filtering"])
            + (popularity_score * _RANKING_WEIGHTS["popularity"])
            + (affinity_score * _RANKING_WEIGHTS["category_affinity"]),
            4,
        )
        recommendations.append(
            {
                "product_id": product_id,
                "score": final_score,
                "source": "hybrid_cf_popularity_category",
            }
        )
        seen_product_ids.add(product_id)
        if len(recommendations) >= num:
            return recommendations

    for product_id in popular_candidates:
        if product_id in seen_product_ids:
            continue
        recommendations.append(
            {
                "product_id": product_id,
                "score": round(popularity_scores.get(product_id, 0.0), 4),
                "source": "popular_fallback",
            }
        )
        seen_product_ids.add(product_id)
        if len(recommendations) >= num:
            break

    return recommendations