from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import pandas as pd
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta
import logging
import time
from joblib import dump, load
import os
from .mongo_client import db

logger = logging.getLogger(__name__)

class EnhancedRecommendationEngine:
    def __init__(self):
        self.model = None
        self.user_profiles = defaultdict(dict)
        self.product_features = {}
        self.products = []  # Necesario para el endpoint /health
        self.last_trained = datetime.min
        self.is_ready = False  # Bandera de estado
        self.scaler = None
        self.preprocessor = None
    
    def _load_user_behavior(self):
        pipeline = [...]
        user_data = db.orders.aggregate(pipeline)  # Corregido
    
    def _analyze_similar_users(self, user_ids):
        products = db.products.find(query, {  # Corregido
            "_id": 1,
            "name": 1,
            "category": 1,
            "price": 1,
            "rating": 1
        }).sort("rating", -1).limit(10)
        
    def initialize(self):
        """Inicialización mejorada con reintentos inteligentes"""
        retry_count = 0
        max_retries = 5
        
        while not self.is_ready and retry_count < max_retries:
            try:
                self._load_product_features()
                self._load_user_behavior()
                self._build_preprocessor()
                self._train()
                self.is_ready = True
                logger.info("✅ Motor listo con %d usuarios y %d productos", 
                           len(self.user_profiles), len(self.product_features))
                return
            except Exception as e:
                logger.error("💥 Error de inicialización: %s (Intento %d/%d)", 
                            str(e), retry_count+1, max_retries)
                retry_count += 1
                time.sleep(10 * retry_count)
        
        raise RuntimeError("No se pudo inicializar el motor de recomendaciones")

    def _load_product_features(self):
        try:
            products = list(db.products.find({}, {  # Convertir a lista
                "_id": 1,
                "category": 1,
                "price": 1,
                "rating": 1,
                "tags": 1
            }))
            
            self.products = [str(p["_id"]) for p in products]
            self.product_features = {str(p["_id"]): {
                "category": p.get("category", "unknown"),
                "price": float(p.get("price", 0)),
                "rating": float(p.get("rating", 0)),
                "tags": p.get("tags", [])
            } for p in products}
            
            if not self.product_features:
                raise ValueError("No hay productos en la base de datos")
                
        except Exception as e:
            logger.error("🔥 Error cargando productos: %s", str(e))
            raise

    def _load_user_behavior(self):
        """Carga el comportamiento de usuario con agregaciones complejas"""
        pipeline = [
            {"$match": {"created_at": {"$gte": datetime.now() - timedelta(days=30)}}},
            {"$unwind": "$items"},
            {"$lookup": {
                "from": "products",
                "localField": "items.product_id",
                "foreignField": "_id",
                "as": "product_data"
            }},
            {"$unwind": "$product_data"},
            {"$group": {
                "_id": "$user_id",
                "total_spent": {"$sum": "$product_data.price"},
                "categories": {"$addToSet": "$product_data.category"},
                "average_rating": {"$avg": "$product_data.rating"},
                "purchase_count": {"$sum": 1}
            }}
        ]
        
        user_data = db.orders.aggregate(pipeline)
        
        for user in user_data:
            user_id = str(user["_id"])
            self.user_profiles[user_id] = {
                "total_spent": user.get("total_spent", 0),
                "categories": list(user.get("categories", [])),
                "average_rating": user.get("average_rating", 0),
                "purchase_count": user.get("purchase_count", 0)
            }

    def _build_preprocessor(self):
        """Preprocesamiento de características combinadas"""
        numeric_features = ['total_spent', 'average_rating', 'purchase_count']
        categorical_features = ['categories']
        
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numeric_features),
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
            ])
        
    def _train(self):
        """Entrenamiento mejorado con validación de datos"""
        if len(self.user_profiles) < 10:
            logger.warning("⚠️ Insuficientes datos para entrenamiento (%d usuarios)", 
                          len(self.user_profiles))
            return
            
        df = pd.DataFrame.from_dict(self.user_profiles, orient='index')
        try:
            processed_data = self.preprocessor.fit_transform(df)
            
            self.model = NearestNeighbors(
                n_neighbors=5,
                metric='cosine',
                algorithm='brute'
            ).fit(processed_data)
            
            self.last_trained = datetime.now()
            logger.info("🎓 Modelo entrenado con %d usuarios", len(df))
            
            # Guardar modelo
            model_dir = "models"
            os.makedirs(model_dir, exist_ok=True)
            dump(self.model, os.path.join(model_dir, 'recommender.joblib'))
            
        except Exception as e:
            logger.error("🚨 Error en entrenamiento: %s", str(e))
            raise

    def get_recommendations(self, user_id):
        """Genera recomendaciones basadas en múltiples factores"""
        if not self.is_ready:
            return {"status": "initializing"}, 503
            
        try:
            user_profile = self.user_profiles.get(user_id, {})
            
            if not user_profile:
                return self._get_fallback_recommendations()
                
            df = pd.DataFrame([user_profile])
            processed_data = self.preprocessor.transform(df)
            
            _, indices = self.model.kneighbors(processed_data)
            similar_users = [list(self.user_profiles.keys())[i] for i in indices[0]]
            
            recommendations = self._analyze_similar_users(similar_users)
            return recommendations[:5]
            
        except Exception as e:
            logger.error("🚨 Error generando recomendaciones: %s", str(e))
            return self._get_fallback_recommendations()

    def _analyze_similar_users(self, user_ids):
        """Analiza usuarios similares para obtener recomendaciones"""
        category_scores = defaultdict(float)
        price_range = []
        ratings = []
        
        for uid in user_ids:
            user = self.user_profiles.get(uid, {})
            for cat in user.get('categories', []):
                category_scores[cat] += 1
            price_range.append(user.get('total_spent', 0))
            ratings.append(user.get('average_rating', 0))
            
        avg_price = np.mean(price_range) if price_range else 0
        avg_rating = np.mean(ratings) if ratings else 0
        
        # Obtener productos que coincidan con los criterios
        query = {
            "category": {"$in": list(category_scores.keys())},
            "price": {"$lte": avg_price * 1.2},
            "rating": {"$gte": avg_rating - 1}
        }
        
        products = db.products.find(query, {
            "_id": 1,
            "name": 1,
            "category": 1,
            "price": 1,
            "rating": 1
        }).sort("rating", -1).limit(10)
        
        return [str(p["_id"]) for p in products]

    def _get_fallback_recommendations(self):
        """Recomendaciones de respaldo basadas en tendencias generales"""
        pipeline = [
            {"$group": {
                "_id": "$category",
                "avgRating": {"$avg": "$rating"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1, "avgRating": -1}},
            {"$limit": 3}
        ]
        
        top_categories = [c["_id"] for c in db.products.aggregate(pipeline)]
        
        products = db.products.find.find(
            {"category": {"$in": top_categories}},
            {"_id": 1}
        ).sort([("rating", -1), ("price", 1)]).limit(5)
        
        return [str(p["_id"]) for p in products]