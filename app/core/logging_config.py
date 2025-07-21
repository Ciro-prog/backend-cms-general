import logging
import logging.config
import os
from pathlib import Path

def setup_logging():
    """Configurar sistema de logging"""
    
    # Crear directorio de logs si no existe
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configurar logging desde archivo
    config_file = Path("logging.conf")
    if config_file.exists():
        logging.config.fileConfig(config_file, disable_existing_loggers=False)
    else:
        # Configuración básica si no existe el archivo
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/cms-dinamico.log')
            ]
        )
    
    # Configurar loggers específicos
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Sistema de logging configurado")