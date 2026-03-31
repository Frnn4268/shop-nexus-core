import os
from dataclasses import dataclass


@dataclass
class Settings:
    port: int = int(os.getenv("PORT", "8003"))
    flask_debug: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    mongodb_uri: str = os.getenv("MONGODB_URI", os.getenv("MONGO_URI", "mongodb://mongo:27017"))
    db_name: str = os.getenv("DB_NAME", "shop-nexus-core")
    mongo_max_pool_size: int = int(os.getenv("MONGO_MAX_POOL_SIZE", "50"))
    mongo_server_selection_timeout_ms: int = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))
    mongo_socket_timeout_ms: int = int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "30000"))
    mongo_connect_timeout_ms: int = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "5000"))
    rabbitmq_uri: str = os.getenv("RABBITMQ_URI", "amqp://guest:guest@rabbitmq:5672/")
    order_exchange: str = os.getenv("ORDER_EVENTS_EXCHANGE", "order_created")
    order_queue: str = os.getenv("ORDER_EVENTS_QUEUE", "order_created")
    order_routing_key: str = os.getenv("ORDER_EVENTS_ROUTING_KEY", "order_created")
    train_interval: int = int(os.getenv("TRAIN_INTERVAL", "10"))
    model_path: str = os.getenv("MODEL_PATH", "/app/model/model.joblib")
    model_registry_dir: str = os.getenv("MODEL_REGISTRY_DIR", "/app/model/artifacts")
    model_versions_to_keep: int = int(os.getenv("MODEL_VERSIONS_TO_KEEP", "5"))
    model_factors: int = int(os.getenv("MODEL_FACTORS", "32"))
    model_iterations: int = int(os.getenv("MODEL_ITERATIONS", "20"))
    model_regularization: float = float(os.getenv("MODEL_REGULARIZATION", "0.1"))
    model_alpha: float = float(os.getenv("MODEL_ALPHA", "20"))
    popular_fallback_size: int = int(os.getenv("POPULAR_FALLBACK_SIZE", "20"))
    evaluation_top_k: int = int(os.getenv("EVALUATION_TOP_K", "10"))


settings = Settings()