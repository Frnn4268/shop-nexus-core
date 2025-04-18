from flask import Flask, jsonify
from app.models.recommender import RecommendationEngine
from app.handlers.recommendation_handler import start_consumer
from threading import Thread
import requests as request
import os

app = Flask(__name__)
engine = RecommendationEngine()

# Iniciar consumidor de RabbitMQ en segundo plano
Thread(target=start_consumer, daemon=True).start()

API_KEYS = os.getenv("API_KEYS", "").split(",")

@app.route('/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    recommendations = engine.get_recommendations(user_id)
    return jsonify({
        "user_id": user_id,
        "recommendations": recommendations
    })

@app.before_request
def check_auth():
    if request.endpoint == 'get_recommendations':
        api_key = request.headers.get("X-API-Key")
        if api_key not in API_KEYS:
            return jsonify({"error": "Unauthorized"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8003))