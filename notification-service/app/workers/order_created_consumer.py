import json
import logging
import time

import pika

from app.clients.rabbitmq_client import RabbitMQClient
from app.core.config import settings
from app.services.order_notification_service import OrderNotificationService


LOGGER = logging.getLogger(__name__)


class OrderCreatedConsumer:
    def __init__(self, rabbitmq_client: RabbitMQClient, notification_service: OrderNotificationService):
        self._rabbitmq_client = rabbitmq_client
        self._notification_service = notification_service

    def start(self) -> None:
        while True:
            connection = None
            try:
                connection = self._rabbitmq_client.create_worker_connection()
                channel = connection.channel()
                self._rabbitmq_client.declare_order_topology(channel)
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue=settings.order_queue,
                    on_message_callback=self._handle_message,
                    auto_ack=False,
                )
                LOGGER.info("Listening for order_created events")
                channel.start_consuming()
            except pika.exceptions.ConnectionClosedByBroker:
                LOGGER.warning("Connection closed by broker, retrying")
                time.sleep(settings.rabbitmq_retry_delay)
            except pika.exceptions.AMQPChannelError:
                LOGGER.error("Channel error detected, reconnecting")
                time.sleep(settings.rabbitmq_retry_delay)
            except pika.exceptions.AMQPConnectionError:
                LOGGER.error("Connection error detected, retrying")
                time.sleep(settings.rabbitmq_retry_delay)
            except KeyboardInterrupt:
                LOGGER.info("Stopping notification consumer")
                if connection is not None and connection.is_open:
                    connection.close()
                break

    def _handle_message(self, channel, method, properties, body) -> None:
        try:
            payload = json.loads(body)
            LOGGER.info("Received order_created event: %s", payload)
            order_event = self._notification_service.parse_order_event(payload)
            self._notification_service.schedule_notifications(order_event)
            LOGGER.info("Notification tasks scheduled successfully")
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except json.JSONDecodeError:
            LOGGER.error("Failed to decode JSON event payload")
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as exc:
            LOGGER.error("Failed to process notification event: %s", exc)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)