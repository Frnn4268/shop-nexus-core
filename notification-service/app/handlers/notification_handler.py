import pika
import json
import os
import time
from app.tasks.notifications import send_email, send_sms

def start_consumer():
    max_retries = 5
    retry_delay = 5  # segundos
    connection = None

    # Intentar conexión con reintentos
    for attempt in range(max_retries):
        try:
            print(f"🔄 Intento {attempt+1}/{max_retries}: Conectando a RabbitMQ...")
            connection = pika.BlockingConnection(
                pika.URLParameters(os.getenv("RABBITMQ_URI"))
            )
            break
        except pika.exceptions.AMQPConnectionError:
            if attempt < max_retries - 1:
                print(f"Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                print("❌ Error: No se pudo conectar a RabbitMQ")
                return

    channel = connection.channel()
    channel.exchange_declare(
        exchange='order_created',  
        exchange_type='direct',
        durable=True
    )
    channel.queue_declare(queue='order_created', durable=True)
    channel.queue_bind(
        queue='order_created',
        exchange='order_events',
        routing_key='order_created'  # Asegúrate que order-service use este routing key
    )

    # Función de callback
    def callback(ch, method, properties, body):
        try:
            order_data = json.loads(body)
            print(f"[DEBUG] Mensaje recibido: {order_data}")  # Log completo
            
            user_email = "user@example.com"
            user_phone = "+1234567890"
            
            # Verifica campos obligatorios
            if 'ID' not in order_data or 'Total' not in order_data:
                raise KeyError("Campos faltantes en el mensaje")
            
            send_email.delay(user_email, f"Pedido {order_data['ID']} confirmado!")
            send_sms.delay(user_phone, f"Gracias por tu pedido de ${order_data['Total']}")
            print("✅ Notificaciones encoladas")

        except KeyError as e:
            print(f"❌ Error en los datos: {str(e)}")
        except Exception as e:
            print(f"⚠️ Error inesperado: {str(e)}")

    # Configurar consumidor
    channel.basic_consume(
        queue='order_created',
        on_message_callback=callback,
        auto_ack=True  # ✔️ Confirmación automática
    )

    print("👂 Escuchando eventos en la cola 'order_created'...")
    channel.start_consuming()