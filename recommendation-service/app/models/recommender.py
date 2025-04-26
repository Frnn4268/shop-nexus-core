from sklearn.neighbors import NearestNeighbors
from datetime import datetime, timedelta
import pandas as pd
from collections import defaultdict
import logging
import time

logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self):
        self.model = None
        self.user_data = defaultdict(lambda: defaultdict(int))
        self.last_trained = None
        self.is_ready = False

    def initialize(self):
        """Inicialización auto-reparadora"""
        logger.info("🔥 Iniciando motor de recomendaciones")
        while True:
            try:
                self._load_data()
                self._train()
                self.is_ready = True
                logger.info("✅ Motor listo con %d usuarios", len(self.user_data))
                return
            except Exception as e:
                logger.error("💥 Error crítico: %s. Reintentando en 10s...", str(e))
                time.sleep(10)

    def _load_data(self):
        """Carga datos esenciales con tolerancia a fallos"""
        # Paso 1: Cargar productos
        products = mongo_client.db.orders.distinct("items.product_id")
        self.products = [str(p) for p in products]
        logger.info("📦 %d productos encontrados", len(self.products))

        # Paso 2: Cargar órdenes recientes
        orders = mongo_client.db.orders.find(
            {}, 
            {"user_id": 1, "items.product_id": 1}
        ).limit(1000)
        
        for order in orders:
            user = str(order.get("user_id", ""))
            for item in order.get("items", []):
                product = str(item.get("product_id", ""))
                if user and product:
                    self.user_data[user][product] += 1

    def _train(self):
        """Entrenamiento con datos reales o dummy"""
        if len(self.user_data) >= 2:
            df = pd.DataFrame.from_dict(self.user_data, orient='index').fillna(0)
            self.model = NearestNeighbors(n_neighbors=5, metric='cosine').fit(df)
            logger.info("🎓 Modelo entrenado con %d usuarios", len(df))
        else:
            # Modelo de emergencia
            import numpy as np
            dummy_data = np.random.rand(2, len(self.products))
            self.model = NearestNeighbors().fit(dummy_data)
            logger.warning("⚠️ Modelo dummy creado por falta de datos")

        self.last_trained = datetime.now()

    def process_order(self, order):
        """Procesamiento simplificado"""
        try:
            user = str(order['user_id'])
            for item in order.get('items', []):
                product = str(item['product_id'])
                self.user_data[user][product] += 1
            
            if (datetime.now() - self.last_trained) > timedelta(minutes=5):
                self._train()
                
        except Exception as e:
            logger.error("❌ Error procesando orden: %s", str(e))

    def get_recommendations(self, user_id):
        """Recomendaciones con resultados garantizados"""
        if not self.is_ready:
            return {"status": "pending"}, 202
        
        try:
            user_vector = pd.DataFrame(
                {user_id: self.user_data.get(user_id, {})}, 
                columns=self.products
            ).fillna(0)
            
            _, indices = self.model.kneighbors(user_vector)
            recommendations = []
            
            for idx in indices[0]:
                neighbor = list(self.user_data.keys())[idx]
                top_products = sorted(
                    self.user_data[neighbor].items(),
                    key=lambda x: x[1], 
                    reverse=True
                )[:3]
                recommendations.extend([p[0] for p in top_products])
            
            return list(set(recommendations))[:5]
        
        except Exception as e:
            logger.error("🚨 Error generando recomendaciones: %s", str(e))
            return {"error": "internal_error"}, 500