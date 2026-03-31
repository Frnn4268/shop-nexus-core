import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mongo_uri: str = os.getenv("MONGODB_URI", "mongodb://mongo:27017")
    db_name: str = os.getenv("DB_NAME", "shop-nexus-core")
    port: int = int(os.getenv("PORT", "8005"))
    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "/app/chroma")
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "catalog")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    default_top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    mongo_max_pool_size: int = int(os.getenv("MONGO_MAX_POOL_SIZE", "50"))
    mongo_server_selection_timeout_ms: int = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))
    mongo_connect_timeout_ms: int = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "5000"))
    mongo_socket_timeout_ms: int = int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "30000"))
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_referer: str = os.getenv("OPENROUTER_REFERER", "https://shop-nexus-core.local")
    openrouter_app_name: str = os.getenv("OPENROUTER_APP_NAME", "shop-nexus-core")


settings = Settings()