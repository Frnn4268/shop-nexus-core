import pika

from app.core.config import settings


class RabbitMQClient:
    def create_url_connection(self):
        return pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_uri))

    def create_worker_connection(self):
        credentials = pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password)
        parameters = pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            virtual_host="/",
            credentials=credentials,
            connection_attempts=settings.rabbitmq_max_retries,
            retry_delay=settings.rabbitmq_retry_delay,
            socket_timeout=10,
            heartbeat=settings.rabbitmq_heartbeat,
        )
        return pika.BlockingConnection(parameters)

    def declare_order_topology(self, channel) -> None:
        channel.exchange_declare(
            exchange=settings.order_exchange,
            exchange_type="direct",
            durable=True,
        )
        channel.queue_declare(
            queue=settings.order_queue,
            durable=True,
            arguments={"x-message-ttl": 86400000},
        )
        channel.queue_bind(
            exchange=settings.order_exchange,
            queue=settings.order_queue,
            routing_key=settings.order_routing_key,
        )