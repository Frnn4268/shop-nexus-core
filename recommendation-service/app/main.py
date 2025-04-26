from flask import Flask, jsonify
import os
import logging  # Importación correcta
from logging import getLogger
from app.models.mongo_client import initialize_mongo
from app.models.recommender import EnhancedRecommendationEngine
from app.handlers.recommendation_handler import EnhancedMessageProcessor
import threading

app = Flask(__name__)

# Configuración avanzada de logging
logger = getLogger(__name__) 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('recommendation_service.log')
    ]
)

# Inicialización diferida de recursos
def initialize_services():
    logger.info("🚀 Inicializando servicios...")
    
    # 1. MongoDB
    try:
        initialize_mongo()
        logger.info("✅ MongoDB inicializado")
    except Exception as e:
        logger.error("🔥 Error MongoDB: %s", str(e))
        raise
    
    # 2. Motor de recomendaciones
    engine = EnhancedRecommendationEngine()
    try:
        engine.initialize()
        logger.info("✅ Motor de recomendaciones listo")
    except Exception as e:
        logger.error("🔥 Error inicializando motor: %s", str(e))
        raise
    
    # 3. RabbitMQ Consumer
    processor = EnhancedMessageProcessor(engine)
    mq_thread = threading.Thread(
        target=processor.start,
        daemon=True,
        name="RabbitMQ-Consumer"
    )
    mq_thread.start()
    
    return engine

engine = initialize_services()

@app.route('/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    try:
        if not engine.is_ready:
            return jsonify({
                "status": "initializing",
                "progress": f"{len(engine.user_profiles)} users loaded"
            }), 503
            
        recommendations = engine.get_recommendations(user_id)
        return jsonify({
            "user_id": user_id,
            "recommendations": recommendations,
            "model_version": engine.last_trained.isoformat()
        })
    except Exception as e:
        logger.error("🚨 Error en recomendación: %s", str(e))
        return jsonify({"error": "processing_error"}), 500

@app.route('/health')
def health():
    return jsonify({
        "status": "ready" if engine.is_ready else "initializing",
        "users": len(engine.user_profiles),
        "products": len(engine.product_features),
        "last_trained": engine.last_trained.isoformat() if engine.last_trained else None
    })

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv("PORT", 8003)),
        use_reloader=False,
        threaded=True
    )