import pika
import json
import logging
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger(__name__)

class MessageProcessor:
    def __init__(self):
        self.engine = RecommendationEngine()
        self.engine.initialize()

    @retry(wait=wait_exponential(multiplier=1, max=60))
    def connect_rabbitmq(self):
        """Conexión persistente a RabbitMQ"""
        return pika.BlockingConnection(
            pika.URLParameters(os.getenv("RABBITMQ_URI"))
        )

    def process_message(self, ch, method, properties, body):
        """Manejo robusto de mensajes"""
        try:
            order = json.loads(body)
            self.engine.process_order({
                "user_id": str(order["UserID"]),
                "items": [
                    {"product_id": str(item["ProductID"])}
                    for item in order.get("Items", [])
                ]
            })
            logger.info("📥 Orden procesada: %s", order["ID"])
        except Exception as e:
            logger.error("💣 Error fatal en mensaje: %s", str(e))

    def start(self):
        """Bucle principal de ejecución"""
        while True:
            try:
                with self.connect_rabbitmq() as connection:
                    channel = connection.channel()
                    channel.basic_consume(
                        queue='order_created',
                        on_message_callback=self.process_message,
                        auto_ack=True
                    )
                    logger.info("👂 Escuchando mensajes...")
                    channel.start_consuming()
            except Exception as e:
                logger.error("⚡ Reconectando en 5s... Error: %s", str(e))
                time.sleep(5)

if __name__ == "__main__":
    processor = MessageProcessor()
    processor.start()