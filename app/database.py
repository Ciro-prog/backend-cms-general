# ================================
# ARCHIVO: app/database.py
# RUTA: app/database.py
# 🔧 CORREGIDO: Manejo de índices duplicados
# ================================

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

# Variables de entorno
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "cms_dinamico")

# Cliente global
_client: AsyncIOMotorClient = None
_database: AsyncIOMotorDatabase = None

async def connect_to_mongo():
    """Conectar a MongoDB"""
    global _client, _database
    
    try:
        _client = AsyncIOMotorClient(MONGODB_URL)
        _database = _client[MONGODB_DB_NAME]
        
        # Probar conexión
        await _database.command("ping")
        logger.info(f"✅ Conectado a MongoDB: {MONGODB_DB_NAME}")
        
        # Crear índices necesarios
        await create_indexes()
        
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    global _client
    if _client:
        _client.close()
        logger.info("🔌 Conexión a MongoDB cerrada")

def get_database() -> AsyncIOMotorDatabase:
    """Obtener instancia de la base de datos"""
    return _database

async def create_indexes():
    """Crear índices necesarios para optimizar consultas"""
    try:
        # 🔧 CORREGIDO: Limpiar documentos con valores null antes de crear índices
        
        # Limpiar documentos null en business_types
        await _database.business_types.delete_many({"business_type_id": None})
        await _database.business_types.delete_many({"business_type_id": ""})
        
        # Limpiar documentos null en business_instances  
        await _database.business_instances.delete_many({"business_id": None})
        await _database.business_instances.delete_many({"business_id": ""})
        
        # Limpiar documentos null en api_configurations
        await _database.api_configurations.delete_many({"api_id": None})
        await _database.api_configurations.delete_many({"api_id": ""})
        
        # Limpiar documentos null en dynamic_components
        await _database.dynamic_components.delete_many({"component_id": None})
        await _database.dynamic_components.delete_many({"component_id": ""})
        
        logger.info("✅ Documentos con valores null limpiados")
        
        # Ahora crear índices de forma segura
        index_operations = [
            # Índices para business_types
            (_database.business_types, "business_type_id", True),
            (_database.business_types, "name", False),
            
            # Índices para business_instances
            (_database.business_instances, "business_id", True),
            (_database.business_instances, "business_type_id", False),
            (_database.business_instances, "name", False),
            
            # Índices para api_configurations
            (_database.api_configurations, "api_id", True),
            (_database.api_configurations, "business_id", False),
            
            # Índices para dynamic_components
            (_database.dynamic_components, "component_id", True),
            (_database.dynamic_components, "business_id", False),
            (_database.dynamic_components, "api_id", False),
            
            # Índices para api_cache
            (_database.api_cache, "cache_key", True),
            (_database.api_cache, "api_id", False),
            (_database.api_cache, "expires_at", False),
            
            # Índices para api_logs
            (_database.api_logs, "log_id", True),
            (_database.api_logs, "api_id", False),
            (_database.api_logs, "timestamp", False),
            (_database.api_logs, "business_id", False),
        ]
        
        for collection, field_name, unique in index_operations:
            try:
                await collection.create_index(field_name, unique=unique)
                logger.info(f"✅ Índice creado: {collection.name}.{field_name} (unique={unique})")
            except Exception as e:
                if "already exists" in str(e) or "E11000" in str(e):
                    logger.info(f"ℹ️ Índice ya existe: {collection.name}.{field_name}")
                else:
                    logger.warning(f"⚠️ Error creando índice {collection.name}.{field_name}: {e}")
        
        logger.info("✅ Índices de base de datos verificados")
        
    except Exception as e:
        logger.warning(f"⚠️ Error en operación de índices: {e}")