from flask import Flask, jsonify
from app.models.recommender import RecommendationEngine
from app.handlers.recommendation_handler import start_consumer
from threading import Thread
import os

app = Flask(__name__)
engine = RecommendationEngine()

# Iniciar consumidor de RabbitMQ en segundo plano
Thread(target=start_consumer, daemon=True).start()

@app.route('/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    recommendations = engine.get_recommendations(user_id)
    return jsonify({
        "user_id": user_id,
        "recommendations": recommendations
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003)