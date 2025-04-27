import pika
import os
from threading import Thread
from .recommender import train_model

class RecommendationConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.order_count = 0
        self.TRAIN_INTERVAL = int(os.getenv("TRAIN_INTERVAL", 100))

    def connect(self):
        params = pika.URLParameters(os.getenv("RABBITMQ_URI"))
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        
        # Añadir los mismos parámetros que en order-service
        self.channel.queue_declare(
            queue='order_created',
            durable=True,
            arguments={
                'x-message-ttl': 86400000  # 24 horas en milisegundos
            }
        )

    def start_consuming(self):
        self.channel.basic_consume(
            queue='order_created',
            on_message_callback=self.process_message,
            auto_ack=True
        )
        self.channel.start_consuming()

    def process_message(self, ch, method, properties, body):
        self.order_count += 1
        if self.order_count >= self.TRAIN_INTERVAL:
            print("Entrenando nuevo modelo...")
            train_model()
            self.order_count = 0

def start_consumer():
    consumer = RecommendationConsumer()
    consumer.connect()
    consumer.start_consuming()