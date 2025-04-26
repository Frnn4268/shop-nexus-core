import pandas as pd
from pymongo import MongoClient
from app.config import Config
from app.utils.logger import logger

class MongoService:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client[Config.DB_NAME]
        logger.info("Conexión a MongoDB establecida")

    def get_interactions(self):
        """Obtener todas las interacciones usuario-producto"""
        interactions = list(self.db.user_interactions.find())
        return pd.DataFrame(interactions)

    def get_user_interactions(self, user_id):
        """Obtener interacciones de un usuario específico"""
        interactions = list(self.db.user_interactions.find({"user_id": user_id}))
        return pd.DataFrame(interactions)

    def record_interaction(self, user_id, product_id):
        self.db.user_interactions.update_one(
            {"user_id": user_id, "product_id": product_id},
            {"$inc": {"interaction": 1}},
            upsert=True
        )
        logger.info(f"Interacción registrada: {user_id} - {product_id}")