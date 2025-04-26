import pika
import json
import logging
import time
from tenacity import retry, wait_exponential, stop_after_attempt
from app.models import mongo_client

logger = logging.getLogger(__name__)

class EnhancedMessageProcessor:
    def __init__(self, engine):
        self.engine = engine
        self._connection = None
        self._channel = None

    @retry(wait=wait_exponential(multiplier=1, max=60), stop=stop_after_attempt(10))
    def _connect(self):
        """Conexión persistente mejorada a RabbitMQ"""
        params = pika.URLParameters(os.getenv("RABBITMQ_URI"))
        params.heartbeat = 600
        params.blocked_connection_timeout = 300
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue='order_created', durable=True)
        logger.info("✅ Conexión a RabbitMQ establecida")

    def _process_order(self, order):
        """Procesamiento detallado de órdenes"""
        try:
            user_id = str(order["UserID"])
            items = order.get("Items", [])
            
            # Actualizar perfil de usuario
            user_profile = self.engine.user_profiles.get(user_id, {})
            
            for item in items:
                product_id = str(item["ProductID"])
                product_data = self.engine.product_features.get(product_id, {})
                
                # Actualizar estadísticas
                user_profile.setdefault('categories', set()).add(product_data.get('category'))
                user_profile['total_spent'] = user_profile.get('total_spent', 0) + product_data.get('price', 0)
                user_profile['purchase_count'] = user_profile.get('purchase_count', 0) + 1
                user_profile['average_rating'] = (
                    user_profile.get('average_rating', 0) * (user_profile.get('purchase_count', 0) - 1) + 
                    product_data.get('rating', 0)
                ) / user_profile.get('purchase_count', 1)
            
            self.engine.user_profiles[user_id] = user_profile
            
            # Entrenamiento incremental cada 100 órdenes
            if len(self.engine.user_profiles) % 100 == 0:
                self.engine._train()
                
            logger.debug("📥 Orden procesada para usuario %s", user_id)
            
        except Exception as e:
            logger.error("💣 Error procesando orden: %s", str(e))

    def _on_message(self, ch, method, properties, body):
        """Manejo robusto de mensajes"""
        try:
            start_time = time.time()
            order = json.loads(body)
            self._process_order(order)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("🕒 Procesado en %.2fs", time.time() - start_time)
        except json.JSONDecodeError:
            logger.error("📦 Mensaje inválido: %s", body)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error("💣 Error crítico: %s", str(e))
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start(self):
        """Bucle de ejecución con manejo de reconexión"""
        while True:
            try:
                if not self._connection or self._connection.is_closed:
                    self._connect()
                
                self._channel.basic_qos(prefetch_count=10)
                self._channel.basic_consume(
                    queue='order_created',
                    on_message_callback=self._on_message
                )
                logger.info("👂 Escuchando mensajes...")
                self._channel.start_consuming()
                
            except pika.exceptions.AMQPConnectionError:
                logger.warning("⚡ Reconectando a RabbitMQ...")
                time.sleep(5)
            except KeyboardInterrupt:
                logger.info("🛑 Deteniendo consumer...")
                self._connection.close()
                break
            except Exception as e:
                logger.error("🔥 Error inesperado: %s", str(e))
                time.sleep(10)