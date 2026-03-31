from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class QueryRequest:
    query: str
    top_k: int


def parse_query_request(payload: dict | None) -> QueryRequest:
    data = payload or {}
    query = str(data.get("query", "")).strip()
    if not query:
        raise ValueError("query is required")

    try:
        top_k = max(1, min(int(data.get("top_k", settings.default_top_k)), 10))
    except (TypeError, ValueError) as exc:
        raise ValueError("top_k must be an integer") from exc

    return QueryRequest(query=query, top_k=top_k)