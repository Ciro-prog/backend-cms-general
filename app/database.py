# ================================
# app/database.py - Conexión MongoDB
# ================================

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = Database()

async def connect_to_mongo():
    """Conectar a MongoDB"""
    try:
        # URL de MongoDB desde env o default
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "cms_dinamico")
        
        logger.info(f"Conectando a MongoDB: {mongodb_url}")
        
        # Crear cliente
        db.client = AsyncIOMotorClient(mongodb_url)
        db.database = db.client[db_name]
        
        # Test de conexión
        await db.client.admin.command('ping')
        logger.info("✅ Conectado a MongoDB exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Cerrar conexión MongoDB"""
    if db.client is not None:
        db.client.close()
        logger.info("🔌 Conexión MongoDB cerrada")

def get_database():
    """Obtener instancia de la base de datos"""
    if db.database is None:
        raise Exception("Database no inicializada. Ejecuta connect_to_mongo() primero")
    return db.database

# ================================
# FUNCIONES DE UTILIDAD
# ================================

async def ping_database():
    """Ping a la base de datos para verificar conexión"""
    try:
        if db.database is None:
            return False
        await db.database.command("ping")
        return True
    except Exception as e:
        logger.error(f"Ping fallido: {e}")
        return False

async def create_indexes():
    """Crear índices necesarios"""
    try:
        if db.database is None:
            logger.error("Database no inicializada")
            return
            
        database = db.database
        
        # Índices para api_configurations
        await database.api_configurations.create_index([
            ("business_id", 1), 
            ("api_name", 1)
        ], unique=True)
        
        # Índices para entities_config
        await database.entities_config.create_index([
            ("business_id", 1), 
            ("entidad", 1)
        ], unique=True)
        
        # Índices para business_types
        await database.business_types.create_index("tipo", unique=True)
        
        # Índices para business_instances
        await database.business_instances.create_index("business_id", unique=True)
        
        logger.info("✅ Índices creados exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error creando índices: {e}")
        raise