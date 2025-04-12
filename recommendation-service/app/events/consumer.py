import pika
import json
import os
from app.database.mongo import get_purchase_history_collection

def start_consumer():
    max_retries = 5
    retry_delay = 10  # segundos
    
    for _ in range(max_retries):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.getenv("RABBITMQ_HOST"),
                    heartbeat=600
                )
            )
            break
        except pika.exceptions.AMQPConnectionError:
            time.sleep(retry_delay)
    else:
        raise Exception("No se pudo conectar a RabbitMQ después de varios intentos")
    
    channel = connection.channel()
    
    channel.queue_declare(queue='order_created')
    
    def callback(ch, method, properties, body):
        order = json.loads(body)
        user_id = order['user_id']
        product_ids = [item['product_id'] for item in order['items']]
        
        # Actualizar historial de compras en MongoDB
        collection = get_purchase_history_collection()
        collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"product_ids": {"$each": product_ids}}},
            upsert=True
        )
        
        # Re-entrenar modelo
        Recommender().update_model()
    
    channel.basic_consume(
        queue='order_created',
        on_message_callback=callback,
        auto_ack=True
    )
    
    channel.start_consuming()