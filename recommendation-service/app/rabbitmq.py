import pika
import os
import time
from threading import Thread
from .recommender import train_model

class RecommendationConsumer:
    def __init__(self):
        # Añadir esta sección faltante
        self.QUEUE_CONFIG = {
            'queue': 'order_created',
            'durable': True,
            'arguments': {
                'x-message-ttl': 86400000,
                'x-queue-type': 'classic',
                'x-dead-letter-exchange': ''
            }
        }
        
        self.connection = None
        self.channel = None
        self.order_count = 0
        self.TRAIN_INTERVAL = int(os.getenv("TRAIN_INTERVAL", 10))

    def connect(self):
        for attempt in range(3):
            try:
                self.connection = pika.BlockingConnection(
                    pika.URLParameters(os.getenv("RABBITMQ_URI"))
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(**self.QUEUE_CONFIG)
                print("✅ Cola configurada correctamente")
                return
            except pika.exceptions.ChannelClosedByBroker as e:
                if e.reply_code == 406:
                    print("⚠️ Reconfigurando cola...")
                    self.channel = self.connection.channel()
                    self.channel.queue_delete(queue=self.QUEUE_CONFIG['queue'])
                    self.channel.queue_declare(**self.QUEUE_CONFIG)
                else:
                    raise
            time.sleep(2)

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