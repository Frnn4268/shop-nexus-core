from flask import Flask, jsonify
from .rabbitmq import start_consumer
from threading import Thread
from .recommender import get_recommendations, load_model
import os

app = Flask(__name__)

# Iniciar consumidor en segundo plano
Thread(target=start_consumer, daemon=True).start()

# Cargar modelo al iniciar
load_model()

@app.route('/recommendations', methods=['GET'])
def recommendations():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id parameter is required"}), 400
    
    recommended_ids = get_recommendations(user_id)
    
    # Obtener detalles de productos
    db = get_db()
    products = list(db.products.find({"_id": {"$in": [ObjectId(id) for id in recommended_ids]}}))
    
    return jsonify([{
        "id": str(p["_id"]),
        "name": p["name"],
        "price": p["price"]
    } for p in products])

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003)