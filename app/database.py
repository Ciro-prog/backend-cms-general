
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Crear conexión a MongoDB"""
    try:
        mongodb.client = AsyncIOMotorClient(settings.mongodb_url)
        mongodb.database = mongodb.client[settings.mongodb_db_name]
        
        # Verificar conexión
        await mongodb.client.admin.command('ping')
        logger.info("Conectado exitosamente a MongoDB")
        
        # Crear índices
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Error conectando a MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("Conexión MongoDB cerrada")

async def create_indexes():
    """Crear índices necesarios"""
    try:
        # Índices para business_instances
        await mongodb.database.business_instances.create_index("business_id", unique=True)
        await mongodb.database.business_instances.create_index("tipo_base")
        
        # Índices para users
        await mongodb.database.users.create_index("clerk_user_id", unique=True)
        await mongodb.database.users.create_index("business_id")
        
        # Índices para entities_config
        await mongodb.database.entities_config.create_index([("business_id", 1), ("entidad", 1)], unique=True)
        
        # Índices para views_config
        await mongodb.database.views_config.create_index([("business_id", 1), ("vista", 1)], unique=True)
        
        # Índices para api_configurations
        await mongodb.database.api_configurations.create_index([("business_id", 1), ("api_name", 1)], unique=True)
        
        # Índices para atencion_humana
        await mongodb.database.atencion_humana.create_index("business_id")
        await mongodb.database.atencion_humana.create_index("whatsapp_numero")
        await mongodb.database.atencion_humana.create_index("conversacion.estado")
        
        logger.info("Índices creados exitosamente")
        
    except Exception as e:
        logger.error(f"Error creando índices: {e}")

def get_database() -> AsyncIOMotorDatabase:
    """Obtener instancia de la base de datos"""
    return mongodb.database