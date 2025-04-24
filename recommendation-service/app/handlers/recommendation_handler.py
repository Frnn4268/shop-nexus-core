import pika
import json
import logging
from tenacity import retry, wait_exponential, stop_after_attempt
from app.models.recommender import RecommendationEngine

logger = logging.getLogger(__name__)

@retry(wait=wait_exponential(multiplier=1, min=2, max=30), 
       stop=stop_after_attempt(10))
def create_rabbitmq_connection():
    """Crea conexión a RabbitMQ con política de reintentos"""
    return pika.BlockingConnection(
        pika.URLParameters(os.getenv("RABBITMQ_URI"))
    )

def start_consumer():
    engine = RecommendationEngine()
    
    while True:
        try:
            with create_rabbitmq_connection() as connection:
                channel = connection.channel()
                channel.queue_declare(
                    queue='order_created',
                    durable=True,
                    arguments={'x-max-priority': 10}
                )
                
                def callback(ch, method, properties, body):
                    try:
                        order_data = json.loads(body)
                        engine.process_order(order_data)
                        logger.info(f"Orden procesada: {order_data['order_id']}")
                    except Exception as e:
                        logger.error(f"Error procesando orden: {str(e)}")

                channel.basic_consume(
                    queue='order_created',
                    on_message_callback=callback,
                    auto_ack=True
                )
                
                logger.info("Escuchando eventos de RabbitMQ...")
                channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Deteniendo consumidor...")
            break
        except Exception as e:
            logger.error(f"Error crítico: {str(e)}. Reiniciando en 10 segundos...")
            time.sleep(10)