from flask import Blueprint, request, jsonify
from app.models.recommender import Recommender
from app.config import Config
from app.utils.logger import logger

recommendations_bp = Blueprint('recommendations', __name__)
recommender = Recommender()

@recommendations_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@recommendations_bp.route('/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    # Validar API key
    api_key = request.headers.get('X-API-KEY')
    if api_key not in Config.API_KEYS:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        recommendations = recommender.get_recommendations(user_id)
        return jsonify({
            "user_id": user_id,
            "recommendations": recommendations
        }), 200
    except Exception as e:
        logger.error(f"Error generando recomendaciones: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500