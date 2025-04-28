from flask import Flask, jsonify, request
from bson import ObjectId  # Importación necesaria
from threading import Thread
import os 
from .rabbitmq import start_consumer
from .recommender import get_recommendations, load_model
from .database import get_db  # Importar la conexión a MongoDB

app = Flask(__name__)

# Iniciar consumidor en segundo plano
Thread(target=start_consumer, daemon=True).start()

# Cargar modelo al iniciar
try:
    load_model()
    print("✅ Modelo cargado exitosamente")
except Exception as e:
    print(f"❌ Error cargando el modelo: {str(e)}")

@app.route("/recommendations/<user_id>", methods=["GET"])
def recommendations(user_id):
    try:
        # Validar formato del user_id
        if not ObjectId.is_valid(user_id):
            return jsonify({"error": "ID de usuario inválido"}), 400
        
        # Obtener recomendaciones
        recommended_ids = get_recommendations(user_id)
        
        if not recommended_ids:
            return jsonify({"message": "No hay recomendaciones disponibles"}), 404
        
        # Convertir IDs a ObjectId
        object_ids = [ObjectId(id) for id in recommended_ids if ObjectId.is_valid(id)]
        
        # Obtener detalles de productos
        db = get_db()
        products = list(db.products.find(
            {"_id": {"$in": object_ids}},
            {"_id": 1, "name": 1, "price": 1, "categories": 1}
        ))
        
        # Formatear respuesta
        recommended_products = [{
            "id": str(product["_id"]),
            "name": product["name"],
            "price": product["price"],
            "categories": [str(cat_id) for cat_id in product.get("categories", [])]
        } for product in products]
        
        return jsonify(recommended_products), 200
        
    except Exception as e:
        app.logger.error(f"Error en recomendaciones: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "services": {
            "mongodb": "connected" if get_db().command('ping') else "disconnected",
            "rabbitmq": "connected" if app.extensions.get('rabbitmq') else "disconnected"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003, debug=os.getenv("FLASK_DEBUG", False))