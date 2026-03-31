from app.clients.rabbitmq_client import RabbitMQClient
from app.core.logging_config import configure_logging
from app.services.order_notification_service import OrderNotificationService
from app.workers.order_created_consumer import OrderCreatedConsumer


if __name__ == "__main__":
    configure_logging()
    consumer = OrderCreatedConsumer(RabbitMQClient(), OrderNotificationService())
    consumer.start()