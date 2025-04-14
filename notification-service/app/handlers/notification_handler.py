import pika
import json
import os
from app.tasks.notifications import send_email, send_sms

def start_consumer():
    connection = pika.BlockingConnection(
        pika.URLParameters(os.getenv("RABBITMQ_URI"))
    )
    channel = connection.channel()
    
    channel.queue_declare(queue='order_created')
    
    def callback(ch, method, properties, body):
        order_data = json.loads(body)
        user_email = "user@example.com"  # Simular datos de usuario
        user_phone = "+1234567890"
        
        # Enviar notificaciones asíncronas
        send_email.delay(user_email, f"Pedido creado: {order_data['id']}")
        send_sms.delay(user_phone, f"Pedido en proceso: {order_data['total']} USD")
        print("✅ Notificaciones en cola de tareas")
    
    channel.basic_consume(
        queue='order_created',
        on_message_callback=callback,
        auto_ack=True
    )
    
    print("Escuchando eventos de pedidos...")
    channel.start_consuming()