# ================================
# app/core/logging_config.py - SIMPLE
# ================================

import logging
from pathlib import Path

def setup_logging():
    """Configurar logging básico"""
    
    # Crear directorio de logs
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configuración básica
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/cms-dinamico.log', encoding='utf-8')
        ]
    )
    
    # Configurar loggers específicos
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Sistema de logging configurado")
