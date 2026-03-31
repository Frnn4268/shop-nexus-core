from functools import lru_cache

from pymongo import MongoClient

from app.core.config import settings


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    return MongoClient(
        settings.mongodb_uri,
        maxPoolSize=settings.mongo_max_pool_size,
        serverSelectionTimeoutMS=settings.mongo_server_selection_timeout_ms,
        socketTimeoutMS=settings.mongo_socket_timeout_ms,
        connectTimeoutMS=settings.mongo_connect_timeout_ms,
    )


def get_db():
    return get_client()[settings.db_name]


def ping_database() -> bool:
    get_client().admin.command("ping")
    return True