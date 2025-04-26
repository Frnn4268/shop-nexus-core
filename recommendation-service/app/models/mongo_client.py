import os
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from tenacity import retry, wait_exponential, stop_after_attempt
import logging

logger = logging.getLogger(__name__)

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), 
       stop=stop_after_attempt(5),
       reraise=True)
def get_mongo_client():
    """Conexión mejorada a MongoDB con verificación de datos"""
    client = MongoClient(
        os.getenv("MONGODB_URI"),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
        uuidRepresentation='standard'
    )
    
    try:
        client.admin.command('ping')
        db = client[os.getenv("DB_NAME")]
        
        # Verificar datos esenciales
        if db.products.count_documents({}) == 0:
            logger.error("🚨 No hay productos en la base de datos")
            raise ValueError("La colección de productos está vacía")
            
        # Índices mejorados
        db.orders.create_index([
            ("user_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        db.products.create_index([("category", ASCENDING)])
        
        logger.info("✅ Conexión a MongoDB establecida correctamente")
        return client
        
    except (ConnectionFailure, OperationFailure) as e:
        logger.error(f"❌ Error de conexión: {str(e)}")
        raise

# Inicialización diferida
client = None
db = None

def initialize_mongo():
    global client, db
    client = get_mongo_client()
    db = client[os.getenv("DB_NAME")]