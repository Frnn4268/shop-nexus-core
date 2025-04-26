import logging

# Configuración base
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Crear logger raíz
logger = logging.getLogger(__name__)

def configure_logging():
    # Opcional: Configuraciones adicionales si son necesarias
    pass