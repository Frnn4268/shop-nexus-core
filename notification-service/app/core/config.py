import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    port: int = int(os.getenv("PORT", "8004"))
    flask_env: str = os.getenv("FLASK_ENV", "production")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    rabbitmq_uri: str = os.getenv("RABBITMQ_URI", "amqp://guest:guest@rabbitmq:5672/")
    rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_user: str = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_password: str = os.getenv("RABBITMQ_PASS", "guest")
    rabbitmq_heartbeat: int = int(os.getenv("RABBITMQ_HEARTBEAT", "600"))
    rabbitmq_retry_delay: int = int(os.getenv("RABBITMQ_RETRY_DELAY", "5"))
    rabbitmq_max_retries: int = int(os.getenv("RABBITMQ_MAX_RETRIES", "10"))
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672/")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "rpc://")
    order_queue: str = os.getenv("ORDER_EVENTS_QUEUE", "order_created")
    order_exchange: str = os.getenv("ORDER_EVENTS_EXCHANGE", "order_created")
    order_routing_key: str = os.getenv("ORDER_EVENTS_ROUTING_KEY", "order_created")
    notification_email_domain: str = os.getenv("NOTIFICATION_EMAIL_DOMAIN", "example.com")
    notification_phone_default: str = os.getenv("NOTIFICATION_PHONE_DEFAULT", "+1234567890")


settings = Settings()