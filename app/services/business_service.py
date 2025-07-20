from typing import List, Optional
from datetime import datetime
import logging

from ..database import get_database
from ..models.business import (
    BusinessType, BusinessTypeCreate, BusinessTypeUpdate,
    BusinessInstance, BusinessInstanceCreate, BusinessInstanceUpdate
)

logger = logging.getLogger(__name__)

class BusinessService:
    """Servicio para gestión de tipos de negocio e instancias"""
    
    def __init__(self):
        self.db = get_database()
    
    # === BUSINESS TYPES ===
    
    async def get_all_business_types(self) -> List[BusinessType]:
        """Obtener todos los tipos de negocio"""
        cursor = self.db.business_types.find().sort("nombre", 1)
        business_types = []
        
        async for doc in cursor:
            business_types.append(BusinessType(**doc))
        
        return business_types
    
    async def get_business_type_by_tipo(self, tipo: str) -> Optional[BusinessType]:
        """Obtener tipo de negocio por su identificador"""
        doc = await self.db.business_types.find_one({"tipo": tipo})
        return BusinessType(**doc) if doc else None
    
    async def create_business_type(self, business_type_data: BusinessTypeCreate) -> BusinessType:
        """Crear un nuevo tipo de negocio"""
        business_type = BusinessType(**business_type_data.dict())
        
        result = await self.db.business_types.insert_one(business_type.dict(by_alias=True))
        business_type.id = result.inserted_id
        
        logger.info(f"Tipo de negocio creado: {business_type.tipo}")
        return business_type
    
    async def update_business_type(
        self, 
        tipo: str, 
        business_type_update: BusinessTypeUpdate
    ) -> Optional[BusinessType]:
        """Actualizar un tipo de negocio"""
        update_data = business_type_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.db.business_types.find_one_and_update(
            {"tipo": tipo},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            logger.info(f"Tipo de negocio actualizado: {tipo}")
            return BusinessType(**result)
        
        return None
    
    async def delete_business_type(self, tipo: str) -> bool:
        """Eliminar un tipo de negocio"""
        result = await self.db.business_types.delete_one({"tipo": tipo})
        
        if result.deleted_count > 0:
            logger.info(f"Tipo de negocio eliminado: {tipo}")
            return True
        
        return False
    
    # === BUSINESS INSTANCES ===
    
    async def get_all_business_instances(
        self, 
        tipo_base: Optional[str] = None,
        activo: Optional[bool] = None
    ) -> List[BusinessInstance]:
        """Obtener todas las instancias de negocio"""
        filter_query = {}
        
        if tipo_base:
            filter_query["tipo_base"] = tipo_base
        if activo is not None:
            filter_query["activo"] = activo
        
        cursor = self.db.business_instances.find(filter_query).sort("nombre", 1)
        businesses = []
        
        async for doc in cursor:
            businesses.append(BusinessInstance(**doc))
        
        return businesses
    
    async def get_business_instance(self, business_id: str) -> Optional[BusinessInstance]:
        """Obtener instancia de negocio por ID"""
        doc = await self.db.business_instances.find_one({"business_id": business_id})
        return BusinessInstance(**doc) if doc else None
    
    async def get_businesses_by_type(self, tipo_base: str) -> List[BusinessInstance]:
        """Obtener negocios por tipo base"""
        return await self.get_all_business_instances(tipo_base=tipo_base)
    
    async def create_business_instance(
        self, 
        business_data: BusinessInstanceCreate
    ) -> BusinessInstance:
        """Crear una nueva instancia de negocio"""
        business = BusinessInstance(**business_data.dict())
        
        result = await self.db.business_instances.insert_one(business.dict(by_alias=True))
        business.id = result.inserted_id
        
        logger.info(f"Negocio creado: {business.business_id}")
        return business
    
    async def update_business_instance(
        self, 
        business_id: str, 
        business_update: BusinessInstanceUpdate
    ) -> Optional[BusinessInstance]:
        """Actualizar una instancia de negocio"""
        update_data = business_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.db.business_instances.find_one_and_update(
            {"business_id": business_id},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            logger.info(f"Negocio actualizado: {business_id}")
            return BusinessInstance(**result)
        
        return None
    
    async def delete_business_instance(self, business_id: str) -> bool:
        """Eliminar una instancia de negocio"""
        result = await self.db.business_instances.delete_one({"business_id": business_id})
        
        if result.deleted_count > 0:
            logger.info(f"Negocio eliminado: {business_id}")
            return True
        
        return False