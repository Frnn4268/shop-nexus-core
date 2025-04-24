from sklearn.neighbors import NearestNeighbors
from datetime import datetime, timedelta
import numpy as np
import joblib
from tenacity import retry, wait_exponential

class RecommendationEngine:
    def __init__(self):
        self.model = None
        self.product_mapping = {}
        self.last_trained = None
        self.load_initial_data()
        
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10))
    def load_initial_data(self):
        """Carga datos iniciales con reintentos"""
        pipeline = [{"$group": {"_id": "$items.product_id"}}]
        results = mongo_client.db.orders.aggregate(pipeline)
        self.product_ids = [str(item["_id"]) for item in results]
        self._create_initial_matrix()
        
    def _create_initial_matrix(self):
        """Crea matriz usuario-producto inicial"""
        self.user_matrix = {}
        orders = mongo_client.db.orders.find().sort("created_at", -1).limit(1000)
        for order in orders:
            user = str(order['user_id'])
            self.user_matrix.setdefault(user, defaultdict(int))
            for item in order['items']:
                self.user_matrix[user][str(item['product_id'])] += 1
                
        self._train_model()
    
    def _train_model(self):
        """Entrena el modelo de recomendación"""
        df = pd.DataFrame.from_dict(self.user_matrix, orient='index').fillna(0)
        if not df.empty:
            self.model = NearestNeighbors(
                n_neighbors=10, 
                metric='cosine', 
                algorithm='brute'
            ).fit(df)
            self.last_trained = datetime.now()
            
    def process_order(self, order_data):
        """Actualiza el modelo con nueva orden"""
        user = str(order_data['user_id'])
        self.user_matrix.setdefault(user, defaultdict(int))
        
        for item in order_data['items']:
            product = str(item['product_id'])
            self.user_matrix[user][product] += 1
            
        # Reentrenar cada hora o después de 100 nuevas órdenes
        if (datetime.now() - self.last_trained) > timedelta(hours=1):
            self._train_model()