from app import create_app
from app.core.config import settings
from app.services.model_service import load_model


app = create_app()
load_model()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=settings.port, debug=settings.flask_debug)