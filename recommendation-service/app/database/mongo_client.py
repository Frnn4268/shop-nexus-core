import os
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), 
       stop=stop_after_attempt(5),
       reraise=True)
def create_mongo_connection():
    """Crea una conexión robusta a MongoDB con reintentos"""
    client = MongoClient(
        os.getenv("MONGODB_URI"),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    try:
        client.admin.command('ping')
        
        # Crear índices solo si es la primera conexión exitosa
        db = client[os.getenv("DB_NAME")]
        
        # Índice para user_id (usado en las consultas de recomendaciones)
        db.orders.create_index([("user_id", ASCENDING)], background=True)
        
        # Índice para items.product_id (agregaciones frecuentes)
        db.orders.create_index([("items.product_id", ASCENDING)], background=True)
        
        print("✅ Índices creados/verificados correctamente")
        return client
        
    except (ConnectionFailure, OperationFailure) as e:
        print(f"❌ Error de conexión/operación en MongoDB: {str(e)}")
        raise

client = create_mongo_connection()
db = client[os.getenv("DB_NAME")]