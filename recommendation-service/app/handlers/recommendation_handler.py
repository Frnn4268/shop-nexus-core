import pika
import json
import os
import time
from app.models.recommender import RecommendationEngine

def start_consumer():
    engine = RecommendationEngine()
    connection = None
    
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.URLParameters(os.getenv("RABBITMQ_URI", "amqp://guest:guest@rabbitmq:5672/"))
            )
            channel = connection.channel()
            
            channel.queue_declare(queue='order_created', durable=True)
            
            def callback(ch, method, properties, body):
                try:
                    order_data = json.loads(body)
                    user_id = order_data['user_id']
                    engine.train_model()
                    print(f"Modelo actualizado con pedido de usuario {user_id}")
                except Exception as e:
                    print(f"Error procesando mensaje: {str(e)}")

            channel.basic_consume(
                queue='order_created',
                on_message_callback=callback,
                auto_ack=True
            )
            
            print("Escuchando eventos de RabbitMQ...")
            channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Error de conexión: {str(e)}. Reintentando en 10 segundos...")
            time.sleep(10)
            continue
        finally:
            if connection and not connection.is_closed:
                connection.close()