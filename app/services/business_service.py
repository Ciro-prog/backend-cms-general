# ================================
# app/services/business_service.py
# ================================

from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from datetime import datetime
import logging

from ..models.business import (
    BusinessType, BusinessTypeCreate, BusinessTypeUpdate,
    BusinessInstance, BusinessInstanceCreate, BusinessInstanceUpdate,
    DEFAULT_ISP_BUSINESS_TYPE, DEFAULT_TELCONORTE_BUSINESS
)

logger = logging.getLogger(__name__)

class BusinessService:
    """Servicio para gestionar Business Types e Instances"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.business_types_collection = db.business_types
        self.business_instances_collection = db.business_instances
    
    # ================================
    # BUSINESS TYPES
    # ================================
    
    async def create_business_type(self, business_type_data: BusinessTypeCreate, created_by: Optional[str] = None) -> BusinessType:
        """Crear un nuevo Business Type"""
        # Generar ID único
        business_type_id = f"{business_type_data.name.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"
        
        # Crear documento
        business_type = BusinessType(
            business_type_id=business_type_id,
            **business_type_data.dict(),
            created_by=created_by
        )
        
        # Guardar en base de datos
        await self.business_types_collection.insert_one(business_type.dict())
        
        logger.info(f"✅ Business Type creado: {business_type_id}")
        return business_type
    
    async def get_business_type(self, business_type_id: str) -> Optional[BusinessType]:
        """Obtener un Business Type por ID"""
        doc = await self.business_types_collection.find_one({"business_type_id": business_type_id})
        if doc:
            return BusinessType(**doc)
        return None
    
    async def list_business_types(self, skip: int = 0, limit: int = 100) -> List[BusinessType]:
        """Listar Business Types"""
        cursor = self.business_types_collection.find({}).sort("created_at", DESCENDING).skip(skip).limit(limit)
        business_types = []
        async for doc in cursor:
            business_types.append(BusinessType(**doc))
        return business_types
    
    async def update_business_type(self, business_type_id: str, update_data: BusinessTypeUpdate) -> Optional[BusinessType]:
        """Actualizar un Business Type"""
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        result = await self.business_types_collection.update_one(
            {"business_type_id": business_type_id},
            {"$set": update_dict}
        )
        
        if result.modified_count > 0:
            return await self.get_business_type(business_type_id)
        return None
    
    async def delete_business_type(self, business_type_id: str) -> bool:
        """Eliminar un Business Type"""
        # Verificar que no tenga business instances asociados
        instances_count = await self.business_instances_collection.count_documents({"business_type_id": business_type_id})
        if instances_count > 0:
            raise ValueError(f"No se puede eliminar: {instances_count} business instances asociados")
        
        result = await self.business_types_collection.delete_one({"business_type_id": business_type_id})
        return result.deleted_count > 0
    
    # ================================
    # BUSINESS INSTANCES
    # ================================
    
    async def create_business_instance(self, business_data: BusinessInstanceCreate, created_by: Optional[str] = None) -> BusinessInstance:
        """Crear una nueva Business Instance"""
        # Verificar que el business_type existe
        business_type = await self.get_business_type(business_data.business_type_id)
        if not business_type:
            raise ValueError(f"Business Type no encontrado: {business_data.business_type_id}")
        
        # Generar ID único
        business_id = f"{business_data.name.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"
        
        # Crear documento
        business_instance = BusinessInstance(
            business_id=business_id,
            **business_data.dict(),
            created_by=created_by
        )
        
        # Guardar en base de datos
        await self.business_instances_collection.insert_one(business_instance.dict())
        
        logger.info(f"✅ Business Instance creado: {business_id}")
        return business_instance
    
    async def get_business_instance(self, business_id: str) -> Optional[BusinessInstance]:
        """Obtener una Business Instance por ID"""
        doc = await self.business_instances_collection.find_one({"business_id": business_id})
        if doc:
            return BusinessInstance(**doc)
        return None
    
    async def list_business_instances(self, business_type_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[BusinessInstance]:
        """Listar Business Instances"""
        filter_dict = {}
        if business_type_id:
            filter_dict["business_type_id"] = business_type_id
        
        cursor = self.business_instances_collection.find(filter_dict).sort("created_at", DESCENDING).skip(skip).limit(limit)
        business_instances = []
        async for doc in cursor:
            business_instances.append(BusinessInstance(**doc))
        return business_instances
    
    async def update_business_instance(self, business_id: str, update_data: BusinessInstanceUpdate) -> Optional[BusinessInstance]:
        """Actualizar una Business Instance"""
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        result = await self.business_instances_collection.update_one(
            {"business_id": business_id},
            {"$set": update_dict}
        )
        
        if result.modified_count > 0:
            return await self.get_business_instance(business_id)
        return None
    
    async def delete_business_instance(self, business_id: str) -> bool:
        """Eliminar una Business Instance"""
        result = await self.business_instances_collection.delete_one({"business_id": business_id})
        return result.deleted_count > 0
    
    # ================================
    # UTILIDADES
    # ================================
    
    async def get_business_with_type(self, business_id: str) -> Optional[Dict[str, Any]]:
        """Obtener Business Instance con su Business Type"""
        business = await self.get_business_instance(business_id)
        if not business:
            return None
        
        business_type = await self.get_business_type(business.business_type_id)
        
        return {
            "business": business,
            "business_type": business_type
        }
    
    async def get_business_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas generales"""
        total_types = await self.business_types_collection.count_documents({})
        total_instances = await self.business_instances_collection.count_documents({})
        active_instances = await self.business_instances_collection.count_documents({"status": "active"})
        
        return {
            "total_business_types": total_types,
            "total_business_instances": total_instances,
            "active_business_instances": active_instances,
            "inactive_business_instances": total_instances - active_instances
        }
    
    # ================================
    # INICIALIZACIÓN CON DATOS DE EJEMPLO
    # ================================
    
    async def initialize_default_data(self):
        """Inicializar con datos de ejemplo si no existen"""
        # Verificar si ya existe el ISP business type
        existing_isp = await self.business_types_collection.find_one({"name": "ISP Provider"})
        if not existing_isp:
            logger.info("🔧 Creando Business Type ISP por defecto...")
            isp_type = await self.create_business_type(DEFAULT_ISP_BUSINESS_TYPE, "system")
            
            logger.info("🔧 Creando Business Instance TelcoNorte por defecto...")
            telconorte_data = BusinessInstanceCreate(
                name="TelcoNorte ISP",
                business_type_id=isp_type.business_type_id,  # Usar el ID generado
                branding=DEFAULT_TELCONORTE_BUSINESS.branding,
                active_components=DEFAULT_TELCONORTE_BUSINESS.active_components
            )
            await self.create_business_instance(telconorte_data, "system")
            
            logger.info("✅ Datos por defecto inicializados")
        else:
            logger.info("✅ Datos por defecto ya existen")

# ================================
# app/services/api_service.py
# ================================

import aiohttp
import asyncio
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from ..models.api_integration import (
    APIConfiguration, AuthType, DynamicComponent,
    APICallLog, APICacheEntry
)

logger = logging.getLogger(__name__)

class APIService:
    """Servicio para gestionar APIs externas"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.api_configs_collection = db.api_configurations
        self.components_collection = db.dynamic_components
        self.cache_collection = db.api_cache
        self.logs_collection = db.api_logs
    
    # ================================
    # CONFIGURACIÓN DE APIS
    # ================================
    
    async def create_api_config(self, api_config: APIConfiguration) -> APIConfiguration:
        """Crear nueva configuración de API"""
        # Encriptar datos sensibles antes de guardar
        encrypted_config = await self._encrypt_sensitive_data(api_config)
        
        await self.api_configs_collection.insert_one(encrypted_config.dict())
        logger.info(f"✅ API Config creada: {api_config.api_id}")
        return api_config
    
    async def get_api_config(self, api_id: str) -> Optional[APIConfiguration]:
        """Obtener configuración de API"""
        doc = await self.api_configs_collection.find_one({"api_id": api_id})
        if doc:
            config = APIConfiguration(**doc)
            # Desencriptar datos sensibles
            return await self._decrypt_sensitive_data(config)
        return None
    
    # ================================
    # LLAMADAS A APIS EXTERNAS
    # ================================
    
    async def call_api(self, api_id: str, component_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Realizar llamada a API externa con cache y logging"""
        api_config = await self.get_api_config(api_id)
        if not api_config:
            raise ValueError(f"API config no encontrada: {api_id}")
        
        # Verificar cache primero
        cache_key = self._generate_cache_key(api_config)
        cached_data = await self._get_cached_data(cache_key)
        
        if cached_data:
            logger.info(f"📊 Cache hit para API: {api_id}")
            return {
                "success": True,
                "data": cached_data["data"],
                "cached": True,
                "cached_at": cached_data["cached_at"]
            }
        
        # Realizar llamada HTTP
        start_time = datetime.utcnow()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Preparar headers
                headers = dict(api_config.default_headers)
                headers.update(await self._get_auth_headers(api_config))
                
                # Preparar URL completa
                full_url = f"{api_config.base_url.rstrip('/')}/{api_config.endpoint.lstrip('/')}"
                
                # Realizar request
                async with session.request(
                    method=api_config.method.value,
                    url=full_url,
                    headers=headers,
                    params=api_config.default_params,
                    timeout=aiohttp.ClientTimeout(total=api_config.timeout_seconds)
                ) as response:
                    
                    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    response_text = await response.text()
                    
                    # Procesar respuesta
                    if response.status == 200:
                        data = await self._process_response(response_text, api_config)
                        
                        # Guardar en cache
                        if api_config.cache_config.enabled:
                            await self._save_to_cache(cache_key, data, api_config)
                        
                        # Log exitoso
                        await self._log_api_call(
                            api_config, component_id, user_id, True,
                            response.status, response_time, len(data) if isinstance(data, list) else 1
                        )
                        
                        return {
                            "success": True,
                            "data": data,
                            "cached": False,
                            "response_time_ms": response_time
                        }
                    else:
                        # Log error
                        await self._log_api_call(
                            api_config, component_id, user_id, False,
                            response.status, response_time, error_message=f"HTTP {response.status}"
                        )
                        
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {response_text[:200]}",
                            "response_time_ms": response_time
                        }
        
        except asyncio.TimeoutError:
            await self._log_api_call(
                api_config, component_id, user_id, False,
                error_message="Timeout", error_type="timeout"
            )
            return {"success": False, "error": "Timeout en la llamada a la API"}
        
        except Exception as e:
            await self._log_api_call(
                api_config, component_id, user_id, False,
                error_message=str(e), error_type="connection"
            )
            return {"success": False, "error": f"Error de conexión: {str(e)}"}
    
    # ================================
    # MÉTODOS PRIVADOS
    # ================================
    
    async def _encrypt_sensitive_data(self, config: APIConfiguration) -> APIConfiguration:
        """Encriptar datos sensibles - SIMPLE para MVP"""
        # Para MVP, solo marcamos que está encriptado
        # En producción aquí iría encriptación real
        return config
    
    async def _decrypt_sensitive_data(self, config: APIConfiguration) -> APIConfiguration:
        """Desencriptar datos sensibles - SIMPLE para MVP"""
        return config
    
    async def _get_auth_headers(self, config: APIConfiguration) -> Dict[str, str]:
        """Generar headers de autenticación"""
        headers = {}
        auth = config.auth_config
        
        if auth.auth_type == AuthType.API_KEY_HEADER:
            headers[auth.header_name] = auth.api_key
        elif auth.auth_type == AuthType.BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {auth.bearer_token}"
        elif auth.auth_type == AuthType.BASIC_AUTH:
            import base64
            credentials = base64.b64encode(f"{auth.username}:{auth.password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        elif auth.auth_type == AuthType.CUSTOM_HEADERS:
            headers.update(auth.custom_headers)
        
        return headers
    
    def _generate_cache_key(self, config: APIConfiguration) -> str:
        """Generar clave de cache"""
        key_data = f"{config.api_id}_{config.endpoint}_{json.dumps(config.default_params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Obtener datos del cache"""
        cache_doc = await self.cache_collection.find_one({
            "cache_key": cache_key,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if cache_doc:
            # Actualizar último acceso
            await self.cache_collection.update_one(
                {"_id": cache_doc["_id"]},
                {
                    "$set": {"last_accessed": datetime.utcnow()},
                    "$inc": {"access_count": 1}
                }
            )
            return cache_doc
        
        return None
    
    async def _save_to_cache(self, cache_key: str, data: Any, config: APIConfiguration):
        """Guardar datos en cache"""
        cache_entry = APICacheEntry(
            cache_id=f"{config.api_id}_{int(datetime.utcnow().timestamp())}",
            api_id=config.api_id,
            business_id=config.business_id,
            data=data,
            data_hash=hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest(),
            record_count=len(data) if isinstance(data, list) else 1,
            size_bytes=len(json.dumps(data).encode()),
            expires_at=datetime.utcnow() + timedelta(seconds=config.cache_config.ttl_seconds),
            cache_key=cache_key
        )
        
        await self.cache_collection.insert_one(cache_entry.dict())
    
    async def _process_response(self, response_text: str, config: APIConfiguration) -> Any:
        """Procesar respuesta de la API"""
        if config.response_format.value == "json":
            data = json.loads(response_text)
            
            # Si hay data_path configurado, navegar hasta los datos
            if config.data_path:
                for key in config.data_path.split('.'):
                    data = data.get(key, data)
            
            # Aplicar mapeo de campos si está configurado
            if config.data_mappings and isinstance(data, list):
                return [self._apply_field_mapping(item, config.data_mappings) for item in data]
            
            return data
        
        return response_text
    
    def _apply_field_mapping(self, item: Dict[str, Any], mappings: List) -> Dict[str, Any]:
        """Aplicar mapeo de campos a un item"""
        mapped_item = {}
        for mapping in mappings:
            source_value = item.get(mapping.source_field, mapping.default_value)
            mapped_item[mapping.target_field] = source_value
        return mapped_item
    
    async def _log_api_call(self, config: APIConfiguration, component_id: Optional[str], user_id: Optional[str], 
                          success: bool, status_code: Optional[int] = None, response_time_ms: Optional[float] = None,
                          records_count: Optional[int] = None, error_message: Optional[str] = None, 
                          error_type: Optional[str] = None):
        """Registrar llamada a API en logs"""
        log_entry = APICallLog(
            log_id=f"{config.api_id}_{int(datetime.utcnow().timestamp())}",
            api_id=config.api_id,
            business_id=config.business_id,
            component_id=component_id,
            request_method=config.method.value,
            request_url=f"{config.base_url}{config.endpoint}",
            response_status_code=status_code,
            response_time_ms=int(response_time_ms) if response_time_ms else None,
            success=success,
            error_message=error_message,
            error_type=error_type,
            records_returned=records_count,
            records_processed=records_count,
            triggered_by="user_request",
            user_id=user_id
        )
        
        await self.logs_collection.insert_one(log_entry.dict())