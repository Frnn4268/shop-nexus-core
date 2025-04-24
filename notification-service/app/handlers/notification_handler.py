import pika
import json
import os
import time
import logging
from app.tasks.notifications import send_email, send_sms

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_rabbitmq_connection():
    """Crea una conexión robusta a RabbitMQ con reconexión automática"""
    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER", "guest"),
        os.getenv("RABBITMQ_PASS", "guest")
    )
    parameters = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
        port=int(os.getenv("RABBITMQ_PORT", 5672)),
        virtual_host='/',
        credentials=credentials,
        connection_attempts=10,
        retry_delay=5,
        socket_timeout=10,
        heartbeat=600
    )
    return pika.BlockingConnection(parameters)

def start_consumer():
    """Consumidor mejorado con manejo de errores y reconexión"""
    while True:
        try:
            connection = create_rabbitmq_connection()
            channel = connection.channel()
            
            # Configurar exchange y cola
            channel.exchange_declare(
                exchange='order_created',
                exchange_type='direct',
                durable=True
            )
            channel.queue_declare(
                queue='order_created',
                durable=True,
                arguments={
                    'x-message-ttl': 86400000  # 24h en ms
                }
            )
            channel.queue_bind(
                exchange='order_created',
                queue='order_created',
                routing_key='order_created'
            )

            # QoS para evitar sobrecarga
            channel.basic_qos(prefetch_count=1)

            def callback(ch, method, properties, body):
                try:
                    order_data = json.loads(body)
                    logger.info(f"📨 Mensaje recibido: {order_data}")
                    
                    # Validación básica
                    required_fields = ['ID', 'Total', 'UserID']
                    if not all(field in order_data for field in required_fields):
                        raise ValueError("Datos incompletos en el mensaje")
                    
                    # Simular obtención de datos de usuario (debería venir del mensaje)
                    user_email = f"user{order_data['UserID']}@example.com"
                    user_phone = "+1234567890"
                    
                    # Encolar tareas
                    send_email.delay(
                        user_email, 
                        f"Pedido {order_data['ID']} confirmado!",
                        f"Detalles del pedido: ${order_data['Total']}"
                    )
                    send_sms.delay(
                        user_phone,
                        f"Gracias por tu pedido de ${order_data['Total']}"
                    )
                    
                    logger.info("✅ Notificaciones programadas correctamente")
                    
                except json.JSONDecodeError:
                    logger.error("❌ Error decodificando mensaje JSON")
                except Exception as e:
                    logger.error(f"⚠️ Error procesando mensaje: {str(e)}")

            channel.basic_consume(
                queue='order_created',
                on_message_callback=callback,
                auto_ack=True
            )

            logger.info("👂 Escuchando eventos en 'order_created'...")
            channel.start_consuming()

        except pika.exceptions.ConnectionClosedByBroker:
            logger.warning("Conexión cerrada por el broker. Reintentando...")
            time.sleep(5)
        except pika.exceptions.AMQPChannelError:
            logger.error("Error de canal. Reiniciando conexión...")
            time.sleep(10)
        except pika.exceptions.AMQPConnectionError:
            logger.error("Error de conexión. Reintentando en 10 segundos...")
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Deteniendo consumidor...")
            connection.close()
            break