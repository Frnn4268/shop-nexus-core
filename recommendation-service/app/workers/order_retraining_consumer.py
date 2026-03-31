import json
import logging
import time

import pika

from app.clients.rabbitmq_client import RabbitMQClient
from app.core.config import settings
from app.services.model_service import train_model


LOGGER = logging.getLogger(__name__)


class OrderRetrainingConsumer:
    def __init__(self, rabbitmq_client: RabbitMQClient):
        self._rabbitmq_client = rabbitmq_client
        self._order_count = 0

    def start(self) -> None:
        while True:
            try:
                connection = self._rabbitmq_client.create_connection()
                channel = connection.channel()
                self._rabbitmq_client.declare_order_topology(channel)
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue=settings.order_queue,
                    on_message_callback=self._handle_message,
                    auto_ack=False,
                )
                LOGGER.info("Recommendation consumer connected to RabbitMQ")
                channel.start_consuming()
            except pika.exceptions.AMQPConnectionError as exc:
                LOGGER.warning("RabbitMQ unavailable for recommendation consumer: %s", exc)
                time.sleep(5)

    def _handle_message(self, channel, method, properties, body) -> None:
        try:
            payload = json.loads(body)
            if not self._is_supported_order_event(payload):
                LOGGER.warning("Skipping unsupported event payload: %s", payload)
                channel.basic_ack(delivery_tag=method.delivery_tag)
                return
            self._order_count += 1
            if self._order_count >= settings.train_interval:
                LOGGER.info("Training recommendation model after %s new orders", self._order_count)
                train_model()
                self._order_count = 0
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as exc:
            LOGGER.exception("Failed to process recommendation event: %s", exc)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    @staticmethod
    def _is_supported_order_event(payload: dict) -> bool:
        if payload.get("event_type") == "order.created" and isinstance(payload.get("data"), dict):
            data = payload["data"]
            return all(field in data for field in ("order_id", "user_id", "total"))

        return all(field in payload for field in ("ID", "UserID", "Total"))