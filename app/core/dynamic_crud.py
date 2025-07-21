# ================================
# app/core/dynamic_crud.py
# ================================

from typing import Dict, Any, List, Optional, Type
from fastapi import HTTPException
import logging
from datetime import datetime

from ..database import get_database
from ..models.entity import EntityConfig, CampoConfig
from ..models.user import User
from ..services.api_service import ApiService
from ..services.validation_service import ValidationService
from ..utils.exceptions import EntityNotFoundError, ValidationError, PermissionDeniedError
from ..utils.helpers import parse_filter_string

logger = logging.getLogger(__name__)

class DynamicCrudGenerator:
    """Generador de operaciones CRUD dinámicas basado en configuración"""
    
    def __init__(self):
        self.db = get_database()
        self.api_service = ApiService()
        self.validation_service = ValidationService()
    
    async def get_entity_config(self, business_id: str, entity_name: str) -> EntityConfig:
        """Obtener configuración de entidad"""
        config_doc = await self.db.entities_config.find_one({
            "business_id": business_id,
            "entidad": entity_name
        })
        
        if not config_doc:
            raise EntityNotFoundError(entity_name)
        
        return EntityConfig(**config_doc)
    
    async def list_entities(
        self,
        business_id: str,
        entity_name: str,
        user: User,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """Listar entidades con paginación y filtros"""
        
        config = await self.get_entity_config(business_id, entity_name)
        
        # Verificar permisos de lectura
        self._check_read_permission(user, config)
        
        # Obtener datos desde API externa si está configurada
        if hasattr(config.configuracion, 'api_config') and config.configuracion.get('api_config'):
            return await self._list_from_api(config, page, per_page, filters, sort_by, sort_order, user)
        else:
            # Obtener desde base de datos local
            return await self._list_from_db(config, page, per_page, filters, sort_by, sort_order, user)
    
    async def get_entity(
        self,
        business_id: str,
        entity_name: str,
        entity_id: str,
        user: User
    ) -> Dict[str, Any]:
        """Obtener una entidad específica"""
        
        config = await self.get_entity_config(business_id, entity_name)
        
        # Verificar permisos
        self._check_read_permission(user, config)
        
        if hasattr(config.configuracion, 'api_config') and config.configuracion.get('api_config'):
            return await self._get_from_api(config, entity_id, user)
        else:
            return await self._get_from_db(config, entity_id, user)
    
    async def create_entity(
        self,
        business_id: str,
        entity_name: str,
        data: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Crear nueva entidad"""
        
        config = await self.get_entity_config(business_id, entity_name)
        
        # Verificar permisos de creación
        self._check_create_permission(user, config)
        
        # Validar datos
        validated_data = await self._validate_entity_data(config, data, is_create=True)
        
        if hasattr(config.configuracion, 'api_config') and config.configuracion.get('api_config'):
            return await self._create_in_api(config, validated_data, user)
        else:
            return await self._create_in_db(config, validated_data, user)
    
    async def update_entity(
        self,
        business_id: str,
        entity_name: str,
        entity_id: str,
        data: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Actualizar entidad existente"""
        
        config = await self.get_entity_config(business_id, entity_name)
        
        # Verificar permisos de edición
        self._check_update_permission(user, config)
        
        # Validar datos
        validated_data = await self._validate_entity_data(config, data, is_create=False)
        
        if hasattr(config.configuracion, 'api_config') and config.configuracion.get('api_config'):
            return await self._update_in_api(config, entity_id, validated_data, user)
        else:
            return await self._update_in_db(config, entity_id, validated_data, user)
    
    async def delete_entity(
        self,
        business_id: str,
        entity_name: str,
        entity_id: str,
        user: User
    ) -> bool:
        """Eliminar entidad"""
        
        config = await self.get_entity_config(business_id, entity_name)
        
        # Verificar permisos de eliminación
        self._check_delete_permission(user, config)
        
        if hasattr(config.configuracion, 'api_config') and config.configuracion.get('api_config'):
            return await self._delete_in_api(config, entity_id, user)
        else:
            return await self._delete_in_db(config, entity_id, user)
    
    # === MÉTODOS PARA API EXTERNA ===
    
    async def _list_from_api(
        self,
        config: EntityConfig,
        page: int,
        per_page: int,
        filters: Optional[str],
        sort_by: Optional[str],
        sort_order: str,
        user: User
    ) -> Dict[str, Any]:
        """Listar desde API externa"""
        
        api_config = config.configuracion.get('api_config')
        if not api_config:
            raise ValueError("Configuración de API no encontrada")
        
        # Construir parámetros de consulta
        params = {
            "page": page,
            "per_page": per_page
        }
        
        # Agregar filtros
        if filters:
            filter_dict = parse_filter_string(filters)
            params.update(filter_dict)
        
        # Agregar ordenamiento
        if sort_by:
            params["sort_by"] = sort_by
            params["sort_order"] = sort_order
        
        # Realizar petición
        response = await self.api_service.make_request(
            config.business_id,
            api_config['fuente'],
            api_config['endpoint'],
            method="GET",
            params=params
        )
        
        # Mapear datos según configuración
        mapped_data = self._map_api_response(response, api_config.get('mapeo', {}))
        
        # Filtrar campos según permisos del usuario
        filtered_data = self._filter_fields_for_user(mapped_data, config, user)
        
        return {
            "items": filtered_data,
            "page": page,
            "per_page": per_page,
            "total": response.get("total", len(filtered_data))
        }
    
    async def _create_in_api(
        self,
        config: EntityConfig,
        data: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Crear en API externa"""
        
        api_config = config.configuracion.get('api_config')
        crud_config = config.configuracion.get('crud_config', {})
        
        if not crud_config.get('crear', {}).get('habilitado', False):
            raise PermissionDeniedError("Creación no permitida para esta entidad")
        
        # Mapear datos al formato de la API
        mapped_data = self._map_data_for_api(data, api_config.get('mapeo', {}))
        
        # Realizar petición de creación
        endpoint = crud_config['crear'].get('endpoint', api_config['endpoint'])
        
        response = await self.api_service.make_request(
            config.business_id,
            api_config['fuente'],
            endpoint,
            method="POST",
            data=mapped_data,
            use_cache=False
        )
        
        return self._map_api_response(response, api_config.get('mapeo', {}))
    
    # === MÉTODOS PARA BASE DE DATOS LOCAL ===
    
    async def _list_from_db(
        self,
        config: EntityConfig,
        page: int,
        per_page: int,
        filters: Optional[str],
        sort_by: Optional[str],
        sort_order: str,
        user: User
    ) -> Dict[str, Any]:
        """Listar desde base de datos local"""
        
        collection = self.db[f"{config.business_id}_{config.entidad}"]
        
        # Construir filtro
        filter_query = {}
        if filters:
            filter_query.update(parse_filter_string(filters))
        
        # Contar total
        total = await collection.count_documents(filter_query)
        
        # Construir pipeline de agregación
        pipeline = [{"$match": filter_query}]
        
        # Ordenamiento
        if sort_by:
            sort_direction = 1 if sort_order == "asc" else -1
            pipeline.append({"$sort": {sort_by: sort_direction}})
        
        # Paginación
        skip = (page - 1) * per_page
        pipeline.extend([
            {"$skip": skip},
            {"$limit": per_page}
        ])
        
        # Ejecutar consulta
        cursor = collection.aggregate(pipeline)
        items = []
        async for doc in cursor:
            items.append(self._convert_objectid_to_str(doc))
        
        # Filtrar campos según permisos
        filtered_items = self._filter_fields_for_user(items, config, user)
        
        return {
            "items": filtered_items,
            "page": page,
            "per_page": per_page,
            "total": total
        }
    
    async def _create_in_db(
        self,
        config: EntityConfig,
        data: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Crear en base de datos local"""
        
        collection = self.db[f"{config.business_id}_{config.entidad}"]
        
        # Agregar metadatos
        data.update({
            "created_at": datetime.utcnow(),
            "created_by": str(user.id),
            "updated_at": datetime.utcnow(),
            "updated_by": str(user.id)
        })
        
        # Insertar documento
        result = await collection.insert_one(data)
        data["_id"] = result.inserted_id
        
        return self._convert_objectid_to_str(data)
    
    # === MÉTODOS DE UTILIDAD ===
    
    def _check_read_permission(self, user: User, config: EntityConfig):
        """Verificar permisos de lectura"""
        if user.rol in ["super_admin", "admin"]:
            return True
        
        # TODO: Implementar verificación granular de permisos
        entity_perms = user.permisos.entidades_acceso
        if entity_perms and config.entidad not in entity_perms:
            raise PermissionDeniedError(f"Sin permisos para leer {config.entidad}")
    
    def _check_create_permission(self, user: User, config: EntityConfig):
        """Verificar permisos de creación"""
        if user.rol in ["super_admin", "admin"]:
            return True
        
        crud_config = config.configuracion.get('crud_config', {})
        create_roles = crud_config.get('crear', {}).get('roles', [])
        
        if user.rol not in create_roles:
            raise PermissionDeniedError(f"Sin permisos para crear en {config.entidad}")
    
    def _check_update_permission(self, user: User, config: EntityConfig):
        """Verificar permisos de actualización"""
        if user.rol in ["super_admin", "admin"]:
            return True
        
        crud_config = config.configuracion.get('crud_config', {})
        update_roles = crud_config.get('editar', {}).get('roles', [])
        
        if user.rol not in update_roles:
            raise PermissionDeniedError(f"Sin permisos para editar en {config.entidad}")
    
    def _check_delete_permission(self, user: User, config: EntityConfig):
        """Verificar permisos de eliminación"""
        if user.rol in ["super_admin", "admin"]:
            return True
        
        crud_config = config.configuracion.get('crud_config', {})
        delete_roles = crud_config.get('eliminar', {}).get('roles', [])
        
        if user.rol not in delete_roles:
            raise PermissionDeniedError(f"Sin permisos para eliminar en {config.entidad}")
    
    async def _validate_entity_data(
        self,
        config: EntityConfig,
        data: Dict[str, Any],
        is_create: bool = True
    ) -> Dict[str, Any]:
        """Validar datos de entidad según configuración"""
        
        campos = config.configuracion.get('campos', [])
        validated_data = {}
        
        for campo_config in campos:
            campo_name = campo_config['campo']
            campo_value = data.get(campo_name)
            
            # Verificar campos obligatorios
            if campo_config.get('obligatorio', False) and is_create:
                if campo_value is None or campo_value == "":
                    raise ValidationError(campo_name, "Campo obligatorio")
            
            # Validar solo si el campo está presente
            if campo_value is not None:
                validated_value = await self.validation_service.validate_field(
                    campo_value,
                    campo_config
                )
                validated_data[campo_name] = validated_value
        
        return validated_data
    
    def _map_api_response(self, response: Dict[str, Any], mapeo: Dict[str, str]) -> List[Dict[str, Any]]:
        """Mapear respuesta de API según configuración"""
        if not mapeo:
            return response
        
        # Si response es una lista
        if isinstance(response, list):
            return [self._map_single_item(item, mapeo) for item in response]
        
        # Si response tiene una clave 'data' o similar
        if isinstance(response, dict):
            if "data" in response:
                items = response["data"]
            elif "items" in response:
                items = response["items"]
            else:
                return [self._map_single_item(response, mapeo)]
            
            if isinstance(items, list):
                return [self._map_single_item(item, mapeo) for item in items]
        
        return response
    
    def _map_single_item(self, item: Dict[str, Any], mapeo: Dict[str, str]) -> Dict[str, Any]:
        """Mapear un solo item según configuración de mapeo"""
        mapped_item = {}
        
        for api_field, entity_field in mapeo.items():
            if api_field in item:
                mapped_item[entity_field] = item[api_field]
        
        # Conservar campos no mapeados
        for key, value in item.items():
            if key not in mapeo and key not in mapped_item:
                mapped_item[key] = value
        
        return mapped_item
    
    def _map_data_for_api(self, data: Dict[str, Any], mapeo: Dict[str, str]) -> Dict[str, Any]:
        """Mapear datos para envío a API (reverso del mapeo)"""
        if not mapeo:
            return data
        
        # Crear mapeo inverso
        reverse_mapeo = {v: k for k, v in mapeo.items()}
        
        mapped_data = {}
        for entity_field, value in data.items():
            api_field = reverse_mapeo.get(entity_field, entity_field)
            mapped_data[api_field] = value
        
        return mapped_data
    
    def _filter_fields_for_user(
        self,
        items: List[Dict[str, Any]],
        config: EntityConfig,
        user: User
    ) -> List[Dict[str, Any]]:
        """Filtrar campos según permisos del usuario"""
        
        campos = config.configuracion.get('campos', [])
        visible_fields = []
        
        for campo_config in campos:
            visible_roles = campo_config.get('visible_roles', ['*'])
            if '*' in visible_roles or user.rol in visible_roles:
                visible_fields.append(campo_config['campo'])
        
        # Si no hay configuración de campos, mostrar todos
        if not visible_fields:
            return items
        
        # Filtrar items
        filtered_items = []
        for item in items:
            filtered_item = {}
            for field in visible_fields:
                if field in item:
                    filtered_item[field] = item[field]
            # Siempre incluir ID si existe
            if 'id' in item:
                filtered_item['id'] = item['id']
            if '_id' in item:
                filtered_item['_id'] = item['_id']
            
            filtered_items.append(filtered_item)
        
        return filtered_items
    
    def _convert_objectid_to_str(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convertir ObjectId a string"""
        from bson import ObjectId
        
        if isinstance(doc, dict):
            converted = {}
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    converted[key] = str(value)
                elif isinstance(value, dict):
                    converted[key] = self._convert_objectid_to_str(value)
                elif isinstance(value, list):
                    converted[key] = [
                        self._convert_objectid_to_str(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    converted[key] = value
            return converted
        
        return doc