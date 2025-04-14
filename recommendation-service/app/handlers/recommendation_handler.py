import pika
import json
import os
import time
from app.models.recommender import RecommendationEngine

def start_consumer():
    engine = RecommendationEngine()
    
    max_retries = 5
    retry_delay = 10  # segundos
    
    for i in range(max_retries):
        try:
            connection = pika.BlockingConnection(
                pika.URLParameters(os.getenv("RABBITMQ_URI"))
            )
            break
        except pika.exceptions.AMQPConnectionError:
            if i < max_retries - 1:
                print(f"Reintentando conexión a RabbitMQ ({i+1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                print("Error: No se pudo conectar a RabbitMQ después de varios intentos")
                return
    
    channel = connection.channel()
    channel.queue_declare(queue='order_created')
    
    def callback(ch, method, properties, body):
        order_data = json.loads(body)
        user_id = order_data['user_id']
        engine.train_model()
        print(f"Modelo actualizado con pedido de usuario {user_id}")
    
    channel.basic_consume(
        queue='order_created',
        on_message_callback=callback,
        auto_ack=True
    )
    
    print("Escuchando eventos de RabbitMQ...")
    channel.start_consuming()