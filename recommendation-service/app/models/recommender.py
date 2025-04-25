from sklearn.neighbors import NearestNeighbors
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import defaultdict
import logging
import time
from tenacity import retry, wait_exponential

logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self):
        self.model = None
        self.user_matrix = defaultdict(lambda: defaultdict(int)) 
        self.product_ids = []
        self.last_trained = None
        self._initial_load_done = False
    
    def initialize(self):
        """Carga datos de forma asincrónica solo una vez"""
        if not self._initial_load_done:
            self.load_initial_data()
            self._initial_load_done = True
        
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10))
    def load_initial_data(self):
        """Carga inicial con manejo de progreso"""
        try:
            logger.info("🏁 Iniciando carga de datos desde MongoDB...")
            
            # Paso 1: Obtener productos únicos
            pipeline = [{"$group": {"_id": "$items.product_id"}}]
            cursor = mongo_client.db.orders.aggregate(pipeline, allowDiskUse=True)
            self.product_ids = [str(item["_id"]) for item in cursor]
            logger.info(f"📦 Productos cargados: {len(self.product_ids)}")
            
            # Paso 2: Cargar órdenes recientes
            self._load_recent_orders()
            
            # Paso 3: Entrenar modelo inicial
            self._train_model()
            
        except Exception as e:
            logger.error(f"🔥 Error crítico en carga inicial: {str(e)}")
            raise
    
    def _load_recent_orders(self, limit=500):
        """Carga limitada de órdenes recientes"""
        logger.info(f"🔄 Cargando últimas {limit} órdenes...")
        self.user_matrix = defaultdict(lambda: defaultdict(int))
        
        orders = mongo_client.db.orders.find().sort("created_at", -1).limit(limit)
        for order in orders:
            user = str(order['user_id'])
            for item in order.get('items', []):
                product = str(item.get('product_id', ''))
                if product:  # Validación
                    self.user_matrix[user][product] += 1
    
    def _train_model(self):
        """Entrenamiento optimizado con pandas"""
        if not self.user_matrix:
            logger.warning("🤷 No hay datos para entrenar")
            return
            
        logger.info("🎓 Entrenando modelo...")
        start_time = time.time()
        
        # Convertir a DataFrame sparse
        df = pd.DataFrame.from_dict(self.user_matrix, orient='index').fillna(0)
        df = df.astype(pd.SparseDtype("float", 0))  # Optimización de memoria
        
        self.model = NearestNeighbors(
            n_neighbors=10, 
            metric='cosine', 
            algorithm='brute', 
            n_jobs=-1  # Usar todos los cores
        ).fit(df)
        
        self.last_trained = datetime.now()
        logger.info(f"✅ Modelo entrenado en {time.time() - start_time:.2f}s")
    
    def process_order(self, order_data):
        """Procesamiento optimizado con validación"""
        try:
            user = str(order_data.get('user_id', ''))
            items = order_data.get('items', [])
            
            if not user or not items:
                logger.warning("📭 Orden vacía o inválida")
                return
                
            # Actualizar matriz
            for item in items:
                product = str(item.get('product_id', ''))
                if product:
                    self.user_matrix[user][product] += 1
                    
            # Reentrenamiento condicional
            if (datetime.now() - self.last_trained) > timedelta(minutes=30):
                logger.info("🔄 Reentrenamiento programado")
                self._train_model()
                
        except Exception as e:
            logger.error(f"⚠️ Error procesando orden: {str(e)}")
        
    def get_recommendations(self, user_id):
        """Genera recomendaciones para un usuario específico"""
        if not self.model:
            logger.warning("Modelo no entrenado, no se pueden generar recomendaciones")
            return []
        
        try:
            logger.info(f"🧠 Generando recomendaciones para usuario: {user_id}")
            start_time = time.time()
            
            # 1. Crear vector de usuario
            user_data = self.user_matrix.get(str(user_id), {})
            user_vector = pd.DataFrame.from_dict(
                {str(user_id): user_data},
                orient='index'
            ).reindex(columns=self.product_ids, fill_value=0)
            
            # 2. Buscar vecinos más cercanos
            _, indices = self.model.kneighbors(user_vector)
            
            # 3. Obtener usuarios similares
            neighbor_indices = indices[0]
            neighbor_ids = [
                list(self.user_matrix.keys())[idx] 
                for idx in neighbor_indices
                if idx < len(self.user_matrix)
            ]
            
            # 4. Recomendar productos de vecinos
            recommendations = []
            for neighbor in neighbor_ids:
                neighbor_products = sorted(
                    self.user_matrix[neighbor].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]  # Top 5 productos por vecino
                recommendations.extend([p[0] for p in neighbor_products])
            
            # 5. Filtrar y ordenar
            unique_recommendations = list({
                p for p in recommendations 
                if p not in user_data  # Excluir productos ya comprados
            })
            
            logger.info(f"✅ Recomendaciones generadas en {time.time() - start_time:.2f}s")
            return unique_recommendations[:10]  # Top 10
            
        except Exception as e:
            logger.error(f"🚨 Error en get_recommendations: {str(e)}", exc_info=True)
            return []