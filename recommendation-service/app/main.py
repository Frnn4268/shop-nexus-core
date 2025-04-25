from flask import Flask, jsonify, request
import os
import threading
import logging
from app.models.recommender import RecommendationEngine

app = Flask(__name__)
engine = RecommendationEngine()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

API_KEYS = os.getenv("API_KEYS", "").split(",")

@app.route('/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    try:
        recommendations = engine.get_recommendations(user_id)
        return jsonify({
            "user_id": user_id,
            "recommendations": recommendations
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.before_request
def check_auth():
    if request.endpoint == 'get_recommendations':
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key not in API_KEYS:
            return jsonify({"error": "Unauthorized"}), 401

def run_consumer():
    """Ejecuta el consumer en un hilo separado"""
    from app.handlers.recommendation_handler import start_consumer
    logger.info("🧵 Iniciando consumer en segundo plano...")
    start_consumer()

if __name__ == '__main__':
    # Inicialización del engine
    logger.info("🚀 Inicializando motor de recomendaciones...")
    
    try:
        engine.initialize()
        logger.info("✅ Modelo inicial entrenado!")
    except Exception as e:
        logger.error(f"🔥 Error inicializando modelo: {str(e)}")
        exit(1)
    
    # Hilo para RabbitMQ
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()
    
    # Iniciar Flask
    app.run(
        host='0.0.0.0', 
        port=int(os.getenv("PORT", 8003)),
        use_reloader=False
    )