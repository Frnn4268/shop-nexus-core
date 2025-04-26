# mongo_client.py (modificado)
import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from tenacity import retry, wait_exponential, stop_after_attempt
import logging

logger = logging.getLogger(__name__)

class MongoDBConnection:
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        self.client = None
        self.db = None
        self.connect()
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), 
           stop=stop_after_attempt(5),
           reraise=True)
    def connect(self):
        self.client = MongoClient(
            os.getenv("MONGODB_URI"),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        try:
            self.client.admin.command('ping')
            self.db = self.client[os.getenv("DB_NAME")]
            
            # Crear colecciones básicas si no existen
            if 'products' not in self.db.list_collection_names():
                self.db.create_collection('products')
                logger.warning("⚠️ Colección 'products' creada")
                
            # Índices
            self.db.products.create_index([("category", ASCENDING)])
            self.db.orders.create_index([
                ("user_id", ASCENDING),
                ("created_at", DESCENDING)
            ])
            
            logger.info("✅ MongoDB conectado")
            
        except Exception as e:
            logger.error(f"❌ Error MongoDB: {str(e)}")
            raise

# Singleton accesible globalmente
mongodb = MongoDBConnection()