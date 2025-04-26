from flask import Blueprint
from app.handlers.recommendations import recommendations_bp

# Crear el blueprint principal
recommendations_router = Blueprint('recommendations', __name__)

# Registrar el blueprint de handlers
recommendations_router.register_blueprint(recommendations_bp, url_prefix='/recommendations')