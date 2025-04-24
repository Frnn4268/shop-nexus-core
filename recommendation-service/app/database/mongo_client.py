import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
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
        return client
    except ConnectionFailure as e:
        print(f"Error de conexión a MongoDB: {str(e)}")
        raise

client = create_mongo_connection()
db = client[os.getenv("DB_NAME")]