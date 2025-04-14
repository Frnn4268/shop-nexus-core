import pandas as pd
from sklearn.neighbors import NearestNeighbors
from app.database import mongo_client

class RecommendationEngine:
    def __init__(self):
        self.model = None
        self.product_ids = []
        
    def train_model(self):
        # Obtener datos históricos de pedidos
        orders = list(mongo_client.db.orders.find({}, {
            'user_id': 1,
            'items.product_id': 1
        }))
        
        # Crear matriz usuario-producto
        data = {}
        for order in orders:
            user = str(order['user_id'])
            for item in order['items']:
                product = str(item['product_id'])
                data.setdefault(user, {})[product] = data.get(user, {}).get(product, 0) + 1
                
        df = pd.DataFrame.from_dict(data, orient='index').fillna(0)
        self.product_ids = df.columns.tolist()
        
        # Entrenar modelo KNN
        self.model = NearestNeighbors(n_neighbors=5, metric='cosine')
        self.model.fit(df)
        
    def get_recommendations(self, user_id):
        if not self.model:
            return []
            
        # Obtener datos del usuario
        user_data = mongo_client.db.orders.find_one(
            {'user_id': user_id}, 
            {'items.product_id': 1}
        )
        
        if not user_data:
            return []
            
        # Crear vector de usuario
        user_vector = {str(item['product_id']): 1 for item in user_data['items']}
        df_user = pd.DataFrame([user_vector], columns=self.product_ids).fillna(0)
        
        # Obtener recomendaciones
        _, indices = self.model.kneighbors(df_user)
        return [self.product_ids[i] for i in indices[0]]