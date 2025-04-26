import pika
import json
from app.config import Config
from app.models.recommender import Recommender
from app.utils.logger import logger

recommender = Recommender()

def start_consumer():
    try:
        connection = pika.BlockingConnection(pika.URLParameters(Config.RABBITMQ_URI))
        channel = connection.channel()
        
        channel.queue_declare(queue='order_created', durable=True)
        
        def callback(ch, method, properties, body):
            try:
                order = json.loads(body)
                logger.info(f"Orden recibida: {order}")  # Debug
                
                # Extraer user_id correctamente (formato ObjectId de MongoDB)
                user_id = str(order['UserID']['$oid'])  # Asegurar formato string
                
                # Procesar todos los items de la orden
                for item in order['Items']:
                    product_id = item['product_id']
                    recommender.mongo.record_interaction(user_id, product_id)
                    logger.info(f"Interacción registrada: {user_id} - {product_id}")  # Confirmación
                
                recommender.increment_counter()
                
            except Exception as e:
                logger.error(f"Error procesando mensaje: {str(e)}")

        channel.basic_consume(
            queue='order_created',
            on_message_callback=callback,
            auto_ack=True
        )
        
        logger.info("Consumidor de RabbitMQ iniciado")
        channel.start_consuming()
        
    except Exception as e:
        logger.error(f"Error en el consumidor: {str(e)}")