from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..database import get_database
from ..models.view import ViewConfig, ViewConfigCreate, ViewConfigUpdate
from ..models.user import User
from ..auth.permissions import PermissionManager

logger = logging.getLogger(__name__)

class ViewService:
    """Servicio para gestión de configuraciones de vistas"""
    
    def __init__(self):
        self.db = get_database()
    
    async def get_view_configs_by_business(self, business_id: str) -> List[ViewConfig]:
        """Obtener todas las configuraciones de vistas de un business"""
        cursor = self.db.views_config.find({"business_id": business_id}).sort("vista", 1)
        configs = []
        
        async for doc in cursor:
            configs.append(ViewConfig(**doc))
        
        return configs
    
    async def get_view_config(self, business_id: str, vista: str) -> Optional[ViewConfig]:
        """Obtener configuración específica de vista"""
        doc = await self.db.views_config.find_one({
            "business_id": business_id,
            "vista": vista
        })
        return ViewConfig(**doc) if doc else None
    
    async def get_view_config_for_user(
        self, 
        business_id: str, 
        vista: str, 
        user: User
    ) -> Optional[Dict[str, Any]]:
        """Obtener configuración de vista filtrada por permisos de usuario"""
        config = await self.get_view_config(business_id, vista)
        if not config:
            return None
        
        # Verificar si el usuario puede acceder a la vista
        if not PermissionManager.can_access_view(user, vista):
            return None
        
        # Filtrar componentes según permisos
        filtered_components = []
        for component in config.configuracion.componentes:
            if "*" in component.permisos_rol or user.rol in component.permisos_rol:
                filtered_components.append(component)
        
        # Filtrar navegación
        filtered_navigation = []
        for nav_item in config.configuracion.navegacion:
            if "*" in nav_item.permisos_rol or user.rol in nav_item.permisos_rol:
                filtered_navigation.append(nav_item)
        
        # Crear configuración filtrada
        filtered_config = config.dict()
        filtered_config["configuracion"]["componentes"] = filtered_components
        filtered_config["configuracion"]["navegacion"] = filtered_navigation
        
        return filtered_config
    
    async def create_view_config(self, config_data: ViewConfigCreate) -> ViewConfig:
        """Crear nueva configuración de vista"""
        config = ViewConfig(**config_data.dict())
        
        result = await self.db.views_config.insert_one(config.dict(by_alias=True))
        config.id = result.inserted_id
        
        logger.info(f"Configuración de vista creada: {config.business_id}.{config.vista}")
        return config
    
    async def update_view_config(
        self, 
        business_id: str, 
        vista: str, 
        config_update: ViewConfigUpdate
    ) -> Optional[ViewConfig]:
        """Actualizar configuración de vista"""
        update_data = config_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.db.views_config.find_one_and_update(
            {"business_id": business_id, "vista": vista},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            logger.info(f"Configuración de vista actualizada: {business_id}.{vista}")
            return ViewConfig(**result)
        
        return None
    
    async def delete_view_config(self, business_id: str, vista: str) -> bool:
        """Eliminar configuración de vista"""
        result = await self.db.views_config.delete_one({
            "business_id": business_id,
            "vista": vista
        })
        
        if result.deleted_count > 0:
            logger.info(f"Configuración de vista eliminada: {business_id}.{vista}")
            return True
        
        return False