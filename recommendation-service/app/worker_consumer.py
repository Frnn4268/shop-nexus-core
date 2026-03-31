from app.clients.rabbitmq_client import RabbitMQClient
from app.services.model_service import load_model, train_model
from app.workers.order_retraining_consumer import OrderRetrainingConsumer


if __name__ == "__main__":
    if load_model() is None:
        train_model()
    OrderRetrainingConsumer(RabbitMQClient()).start()