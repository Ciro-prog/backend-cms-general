from typing import List, Optional
from datetime import datetime
import logging

from ..database import get_database
from ..models.entity import EntityConfig, EntityConfigCreate, EntityConfigUpdate

logger = logging.getLogger(__name__)

class EntityService:
    """Servicio para gestión de configuraciones de entidades"""
    
    def __init__(self):
        self.db = get_database()
    
    async def get_entity_configs_by_business(self, business_id: str) -> List[EntityConfig]:
        """Obtener todas las configuraciones de entidades de un business"""
        cursor = self.db.entities_config.find({"business_id": business_id}).sort("entidad", 1)
        configs = []
        
        async for doc in cursor:
            configs.append(EntityConfig(**doc))
        
        return configs
    
    async def get_entity_config(self, business_id: str, entidad: str) -> Optional[EntityConfig]:
        """Obtener configuración específica de entidad"""
        doc = await self.db.entities_config.find_one({
            "business_id": business_id,
            "entidad": entidad
        })
        return EntityConfig(**doc) if doc else None
    
    async def create_entity_config(self, config_data: EntityConfigCreate) -> EntityConfig:
        """Crear nueva configuración de entidad"""
        config = EntityConfig(**config_data.dict())
        
        result = await self.db.entities_config.insert_one(config.dict(by_alias=True))
        config.id = result.inserted_id
        
        logger.info(f"Configuración de entidad creada: {config.business_id}.{config.entidad}")
        return config
    
    async def update_entity_config(
        self, 
        business_id: str, 
        entidad: str, 
        config_update: EntityConfigUpdate
    ) -> Optional[EntityConfig]:
        """Actualizar configuración de entidad"""
        update_data = config_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.db.entities_config.find_one_and_update(
            {"business_id": business_id, "entidad": entidad},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            logger.info(f"Configuración actualizada: {business_id}.{entidad}")
            return EntityConfig(**result)
        
        return None