from typing import List, Dict, Any, Optional
import logging

from ..database import get_database
from ..models.user import User
from ..core.dynamic_crud import DynamicCrudGenerator
from ..utils.exceptions import PermissionDeniedError, EntityNotFoundError

logger = logging.getLogger(__name__)

class DynamicCrudService:
    """Servicio que utiliza el generador de CRUD dinámico"""
    
    def __init__(self):
        self.db = get_database()
        self.crud_generator = DynamicCrudGenerator()
    
    async def get_entity_data(
        self,
        business_id: str,
        entidad: str,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[str] = None,
        user: User = None
    ) -> List[Dict[str, Any]]:
        """Obtener datos de una entidad con paginación y filtros"""
        
        try:
            result = await self.crud_generator.list_entities(
                business_id=business_id,
                entity_name=entidad,
                user=user,
                page=page,
                per_page=per_page,
                filters=filters
            )
            return result.get("items", [])
            
        except EntityNotFoundError:
            logger.error(f"Entidad no encontrada: {entidad}")
            raise
        except PermissionDeniedError:
            logger.error(f"Permisos insuficientes para {entidad}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo datos de entidad {entidad}: {e}")
            raise
    
    async def create_entity_item(
        self,
        business_id: str,
        entidad: str,
        item_data: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Crear nuevo item en entidad"""
        
        try:
            return await self.crud_generator.create_entity(
                business_id=business_id,
                entity_name=entidad,
                data=item_data,
                user=user
            )
            
        except Exception as e:
            logger.error(f"Error creando item en {entidad}: {e}")
            raise
    
    async def update_entity_item(
        self,
        business_id: str,
        entidad: str,
        item_id: str,
        item_data: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Actualizar item en entidad"""
        
        try:
            return await self.crud_generator.update_entity(
                business_id=business_id,
                entity_name=entidad,
                entity_id=item_id,
                data=item_data,
                user=user
            )
            
        except Exception as e:
            logger.error(f"Error actualizando item {item_id} en {entidad}: {e}")
            raise
    
    async def delete_entity_item(
        self,
        business_id: str,
        entidad: str,
        item_id: str,
        user: User
    ) -> bool:
        """Eliminar item de entidad"""
        
        try:
            return await self.crud_generator.delete_entity(
                business_id=business_id,
                entity_name=entidad,
                entity_id=item_id,
                user=user
            )
            
        except Exception as e:
            logger.error(f"Error eliminando item {item_id} de {entidad}: {e}")
            raise