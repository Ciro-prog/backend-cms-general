import logging
from ..database import connect_to_mongo
from ..services.cache_service import CacheService

logger = logging.getLogger(__name__)

async def startup_events():
    """Eventos de inicio de la aplicación"""
    logger.info("🚀 Iniciando CMS Dinámico...")
    
    # Conectar a MongoDB
    await connect_to_mongo()
    
    # Conectar a Redis
    cache_service = CacheService()
    await cache_service.connect()
    
    logger.info("✅ CMS Dinámico iniciado correctamente")

async def shutdown_events():
    """Eventos de cierre de la aplicación"""
    logger.info("🔄 Cerrando CMS Dinámico...")
    
    # Cerrar conexiones
    cache_service = CacheService()
    await cache_service.close()
    
    logger.info("✅ CMS Dinámico cerrado correctamente")
