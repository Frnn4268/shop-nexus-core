import pika
import json
import os
import time
from app.tasks.notifications import send_email, send_sms

def start_consumer():
    max_retries = 5
    retry_delay = 5  # segundos

    for attempt in range(max_retries):
        try:
            connection = pika.BlockingConnection(
                pika.URLParameters(os.getenv("RABBITMQ_URI"))
            )
            channel = connection.channel()
            channel.queue_declare(queue='order_created')
            
            def callback(ch, method, properties, body):
                # ... código existente

                channel.basic_consume(
                    queue='order_created',
                    on_message_callback=callback,
                    auto_ack=True
                )
                
                print("Escuchando eventos de pedidos...")
                channel.start_consuming()
            break
            
        except pika.exceptions.AMQPConnectionError:
            if attempt < max_retries - 1:
                print(f"Reintentando conexión ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                print("Error: No se pudo conectar a RabbitMQ")