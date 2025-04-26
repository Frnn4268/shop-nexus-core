import joblib
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from app.config import Config
from app.services.mongo_service import MongoService
from app.utils.logger import logger

class Recommender:
    def __init__(self):
        self.model = None
        self.data = None
        self.counter = 0
        self.mongo = MongoService()
        self.load_data()
        self.train_model()

    def load_data(self):
        """Cargar datos de interacciones usuario-producto de MongoDB"""
        self.data = self.mongo.get_interactions()
        logger.info(f"Datos cargados: {len(self.data)} registros")

    def train_model(self):
        if len(self.data) < 2:
            self.model = None
            logger.warning("No hay suficientes datos para entrenar el modelo")
            return

        pivot_table = pd.pivot_table(
            self.data,
            values='interaction',
            index='user_id',
            columns='product_id',
            fill_value=0
        ).reset_index()

        self.model = NearestNeighbors(
            n_neighbors=Config.MODEL_NEIGHBORS,
            metric=Config.MODEL_METRIC
        )
        self.model.fit(pivot_table.drop('user_id', axis=1))
        joblib.dump(self.model, 'model.joblib')
        logger.info("Modelo reentrenado exitosamente")

    def increment_counter(self):
        """Manejar contador de órdenes para reentrenamiento"""
        self.counter += 1
        if self.counter >= 10:
            self.load_data()
            self.train_model()
            self.counter = 0
            logger.info("Contador de reentrenamiento reiniciado")

    def get_recommendations(self, user_id):
        """Generar recomendaciones para un usuario"""
        if not self.model:
            return []

        user_data = self.mongo.get_user_interactions(user_id)
        if user_data.empty:
            return []

        _, indices = self.model.kneighbors(user_data)
        product_ids = self.data.iloc[indices[0]]['product_id'].unique()
        return product_ids.tolist()