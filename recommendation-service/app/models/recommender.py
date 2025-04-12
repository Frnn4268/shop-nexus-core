import pandas as pd
from sklearn.decomposition import NMF
import numpy as np
from app.database.mongo import get_purchase_history_collection

class Recommender:
    def __init__(self):
        self.model = NMF(n_components=10, init='random', random_state=42)
        self.user_product_matrix = None
        self.product_ids = []
        
    def update_model(self):
        collection = get_purchase_history_collection()
        data = list(collection.find())

        if not data:
            self.user_product_matrix = pd.DataFrame()
            return

        try:
            df = pd.DataFrame(data).explode('product_ids')
            if 'product_ids' not in df.columns:
                raise KeyError("Campo 'product_ids' no encontrado en los datos")
                
            user_product = pd.crosstab(df['user_id'], df['product_ids'])

        except KeyError as e:
            print(f"Error en la estructura de datos: {str(e)}")
            self.user_product_matrix = pd.DataFrame()
        
    def recommend(self, user_id, n=5):
        """Genera recomendaciones para un usuario"""
        collection = get_purchase_history_collection()
        user_data = collection.find_one({"user_id": user_id})
        
        if not user_data:
            return []
            
        # Obtener factorización de matrices
        W = self.model.transform(user_product)
        H = self.model.components_
        
        # Predecir ratings
        predicted = np.dot(W, H)
        
        # Obtener productos no comprados
        user_products = set(user_data['product_ids'])
        recommendations = []
        
        for idx, product in enumerate(self.product_ids):
            if product not in user_products:
                recommendations.append((product, predicted[user_idx][idx]))
                
        return [p[0] for p in sorted(recommendations, key=lambda x: -x[1])[:n]]