import pandas as pd
from sklearn.neighbors import NearestNeighbors
from collections import defaultdict
from datetime import datetime
from app.database import mongo_client

class RecommendationEngine:
    def __init__(self):
        self.model = NearestNeighbors(n_neighbors=5, metric='cosine')
        self.user_product_matrix = defaultdict(lambda: defaultdict(int))
        self.product_ids = []
        self.last_updated = None
        
        # Cargar datos iniciales
        self.load_initial_data()
    
    def load_initial_data(self):
        # Obtener todos los productos existentes
        pipeline = [{"$group": {"_id": "$items.product_id"}}]
        results = mongo_client.db.orders.aggregate(pipeline)
        self.product_ids = [str(item["_id"]) for item in results]
        
        # Inicializar matriz con datos históricos
        orders = mongo_client.db.orders.find()
        for order in orders:
            user = str(order['user_id'])
            for item in order['items']:
                product = str(item['product_id'])
                self.user_product_matrix[user][product] += 1
        
    def train_model(self):
        # Obtener solo pedidos nuevos desde la última actualización
        last_update = self.last_updated or datetime.min
        orders = list(mongo_client.db.orders.find(
            {"created_at": {"$gt": last_update}},
            {'user_id': 1, 'items.product_id': 1}
        ))

        # Actualizar la matriz usuario-producto incrementalmente
        for order in orders:
            user = str(order['user_id'])
            for item in order['items']:
                product = str(item['product_id'])
                self.user_product_matrix[user][product] += 1

        df = pd.DataFrame.from_dict(self.user_product_matrix, orient='index').fillna(0)
        self.model.fit(df)
        self.last_updated = datetime.now()
        
    def get_recommendations(self, user_id):
        if not self.model:
            return self.get_popular_products()
            
        # Obtener datos del usuario
        user_data = mongo_client.db.orders.find_one(
            {'user_id': user_id}, 
            {'items.product_id': 1}
        )
        
        if not user_data:
            return self.get_popular_products()
            
        # Crear vector de usuario
        user_vector = {str(item['product_id']): 1 for item in user_data['items']}
        df_user = pd.DataFrame([user_vector], columns=self.product_ids).fillna(0)
        
        # Obtener recomendaciones
        _, indices = self.model.kneighbors(df_user)
        return [self.product_ids[i] for i in indices[0]]

    def get_popular_products(self, n=5):
        pipeline = [
            {"$unwind": "$items"},
            {"$group": {"_id": "$items.product_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": n}
        ]
        results = mongo_client.db.orders.aggregate(pipeline)
        return [str(item["_id"]) for item in results]