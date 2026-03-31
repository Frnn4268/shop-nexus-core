import pika

from app.core.config import settings


class RabbitMQClient:
    def create_connection(self):
        return pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_uri))

    def declare_order_topology(self, channel) -> None:
        channel.exchange_declare(
            exchange=settings.order_exchange,
            exchange_type="direct",
            durable=True,
        )
        channel.queue_declare(
            queue=settings.order_queue,
            durable=True,
            arguments={"x-message-ttl": 86400000, "x-queue-type": "classic"},
        )
        channel.queue_bind(
            queue=settings.order_queue,
            exchange=settings.order_exchange,
            routing_key=settings.order_routing_key,
        )