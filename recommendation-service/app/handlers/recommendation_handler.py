import pika
import json
import logging
import time
from tenacity import retry, wait_exponential, stop_after_attempt
from app.models.recommender import RecommendationEngine

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(self):
        self.engine = RecommendationEngine()
        self._connection = None
        self._channel = None
        self._should_reconnect = False
        
    def initialize(self):
        """Inicialización controlada"""
        logger.info("🚀 Inicializando motor de recomendaciones...")
        start_time = time.time()
        self.engine.initialize()
        logger.info(f"🕒 Tiempo de inicialización: {time.time() - start_time:.2f}s")
        
    @retry(wait=wait_exponential(multiplier=1, min=2, max=30), 
           stop=stop_after_attempt(10))
    def connect(self):
        """Conexión robusta con manejo de errores"""
        logger.info("🔗 Conectando a RabbitMQ...")
        self._connection = pika.BlockingConnection(
            pika.URLParameters(os.getenv("RABBITMQ_URI"))
        )
        self._channel = self._connection.channel()
        self._channel.queue_declare(
            queue='order_created',
            durable=True,
            arguments={'x-max-priority': 10}
        )
        self._channel.basic_qos(prefetch_count=10)
        
    def on_message(self, ch, method, properties, body):
        """Callback async para procesamiento no bloqueante"""
        try:
            order_data = json.loads(body)
            logger.debug(f"📥 Mensaje recibido: {order_data['order_id']}")
            self.engine.process_order(order_data)
        except json.JSONDecodeError:
            logger.error("📦 Error decodificando JSON")
        except Exception as e:
            logger.error(f"⚠️ Error procesando mensaje: {str(e)}")
            
    def run(self):
        """Bucle principal de consumo"""
        while True:
            try:
                self.connect()
                self._channel.basic_consume(
                    queue='order_created',
                    on_message_callback=self.on_message,
                    auto_ack=True
                )
                logger.info("👂 Escuchando eventos...")
                self._channel.start_consuming()
            except pika.exceptions.ConnectionClosedByBroker:
                logger.warning("🔌 Conexión cerrada por el broker")
                self._should_reconnect = True
            except Exception as e:
                logger.error(f"💥 Error crítico: {str(e)}")
                self._should_reconnect = True
                
            if self._should_reconnect:
                logger.info("🔄 Reconectando en 10s...")
                time.sleep(10)
                self._should_reconnect = False

def start_consumer():
    consumer = RabbitMQConsumer()
    consumer.initialize()
    consumer.run()