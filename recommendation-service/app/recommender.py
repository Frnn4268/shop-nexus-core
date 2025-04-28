import pandas as pd
from implicit.als import AlternatingLeastSquares
from joblib import dump, load
import numpy as np
from .database import get_db
import os

MODEL_PATH = "/app/model.joblib"

def prepare_data():
    db = get_db()
    
    # Obtener órdenes
    orders = list(db.orders.aggregate([
        {"$unwind": "$items"},
        {"$project": {
            "user_id": "$user_id",
            "product_id": "$items.product_id",
            "quantity": "$items.quantity"
        }}
    ]))
    
    # Obtener productos
    products = {str(p["_id"]): p["category_ids"] for p in db.products.find()}
    
    # Crear matriz usuario-producto
    df = pd.DataFrame(orders)
    user_ids = df['user_id'].astype('category').cat.codes
    product_ids = df['product_id'].astype('category').cat.codes
    
    return {
        'user_ids': user_ids,
        'product_ids': product_ids,
        'interactions': df['quantity'].values,
        'product_map': dict(enumerate(df['product_id'].astype('category').cat.categories)),
        'user_map': dict(enumerate(df['user_id'].astype('category').cat.categories)),
        'products': products
    }

def train_model():
    data = prepare_data()
    
    # Crear matriz sparse
    matrix = np.zeros((data['user_ids'].max()+1, data['product_ids'].max()+1))
    for u, p, q in zip(data['user_ids'], data['product_ids'], data['interactions']):
        matrix[u, p] += q
    
    # Entrenar modelo ALS
    model = AlternatingLeastSquares(factors=50, iterations=20)
    model.fit(matrix.T)
    
    # Guardar modelo
    dump({
        'model': model,
        'product_map': data['product_map'],
        'user_map': data['user_map'],
        'products': data['products']
    }, MODEL_PATH)

def load_model():
    print(f"🔍 Intentando cargar modelo desde: {MODEL_PATH}")
    try:
        if os.path.exists(MODEL_PATH):
            model_data = joblib.load(MODEL_PATH)
            print("✅ Modelo cargado exitosamente")
            return model_data
        else:
            print("⚠️ Archivo de modelo no encontrado")
            return None
    except Exception as e:
        print(f"🔥 Error cargando modelo: {str(e)}")
        return None

def get_recommendations(user_id, num=5):
    print(f"🔍 Buscando recomendaciones para user_id: {user_id}")
    model_data = load_model()
    if not model_data:
        print("⚠️ Modelo no cargado!")
        return []
    
    # Convertir user_id a índice
    user_idx = [k for k, v in model_data['user_map'].items() if v == user_id]
    if not user_idx:
        return []
    
    # Obtener recomendaciones
    ids, scores = model_data['model'].recommend(
        user_idx[0],
        model_data['model'].item_users,
        N=num
    )
    
    return [model_data['product_map'][i] for i in ids]