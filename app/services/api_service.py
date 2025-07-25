# ================================
# app/services/api_service.py - Motor APIs Externas
# ================================

import httpx
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..database import get_database
from ..models.api_config import ApiConfiguration, ApiTestResult, FieldMapping

logger = logging.getLogger(__name__)

class ApiService:
    """Servicio para manejar APIs externas"""
    
    def __init__(self):
        self.db = get_database()
    
    # ================================
    # GESTIÓN DE CONFIGURACIONES
    # ================================
    
    async def get_api_config(self, business_id: str, api_id: str) -> Optional[ApiConfiguration]:
        """Obtener configuración de API"""
        try:
            doc = await self.db.api_configurations.find_one({
                "business_id": business_id,
                "api_id": api_id
            })
            
            if doc:
                return ApiConfiguration(**doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración API {api_id}: {e}")
            return None
    
    async def save_api_config(self, config: ApiConfiguration) -> bool:
        """Guardar configuración de API"""
        try:
            config_dict = config.dict(by_alias=True, exclude_unset=True)
            config_dict["updated_at"] = datetime.utcnow()
            
            result = await self.db.api_configurations.update_one(
                {"business_id": config.business_id, "api_id": config.api_id},
                {"$set": config_dict},
                upsert=True
            )
            
            logger.info(f"Configuración API guardada: {config.api_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando configuración API: {e}")
            return False
    
    # ================================
    # TEST DE CONEXIÓN API
    # ================================
    
    async def test_api_connection(self, business_id: str, api_id: str, limit_records: int = 5) -> ApiTestResult:
        """Probar conexión con API externa"""
        start_time = time.time()
        
        try:
            # Obtener configuración
            config = await self.get_api_config(business_id, api_id)
            if not config:
                return ApiTestResult(
                    success=False,
                    error_message="Configuración de API no encontrada"
                )
            
            # Hacer request de prueba
            full_url = config.base_url.rstrip('/') + config.endpoint
            headers = await self._build_headers(config)
            params = await self._build_params(config, {"limit": str(limit_records)})
            
            async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
                response = await client.request(
                    method=config.method,
                    url=full_url,
                    headers=headers,
                    params=params
                )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Procesar respuesta
            if response.status_code == 200:
                try:
                    data = response.json()
                    sample_data, detected_fields = await self._process_response(data, config, limit_records)
                    
                    # Actualizar configuración con último test
                    await self._update_last_test(config, True, None)
                    
                    return ApiTestResult(
                        success=True,
                        status_code=response.status_code,
                        response_time_ms=response_time_ms,
                        sample_data=sample_data,
                        detected_fields=detected_fields,
                        total_records=len(sample_data) if sample_data else 0,
                        suggested_mappings=await self._suggest_field_mappings(detected_fields),
                        recommended_cache_ttl=await self._recommend_cache_ttl(response_time_ms)
                    )
                    
                except json.JSONDecodeError:
                    await self._update_last_test(config, False, "Respuesta no es JSON válido")
                    return ApiTestResult(
                        success=False,
                        status_code=response.status_code,
                        response_time_ms=response_time_ms,
                        error_message="Respuesta no es JSON válido"
                    )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                await self._update_last_test(config, False, error_msg)
                return ApiTestResult(
                    success=False,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    error_message=error_msg
                )
                
        except httpx.TimeoutException:
            await self._update_last_test(config, False, "Timeout en la conexión")
            return ApiTestResult(
                success=False,
                error_message="Timeout en la conexión"
            )
            
        except Exception as e:
            error_msg = f"Error en conexión: {str(e)}"
            if 'config' in locals():
                await self._update_last_test(config, False, error_msg)
            
            return ApiTestResult(
                success=False,
                error_message=error_msg
            )
    
    # ================================
    # LLAMADAS REALES A API
    # ================================
    
    async def fetch_api_data(self, business_id: str, api_id: str, page: int = 1, per_page: int = 10, filters: Dict[str, Any] = None) -> Tuple[List[Dict[str, Any]], int]:
        """Obtener datos reales de la API"""
        try:
            config = await self.get_api_config(business_id, api_id)
            if not config or not config.active:
                return [], 0
            
            # Construir parámetros con paginación
            params = await self._build_params(config, filters or {})
            params.update({
                "page": str(page),
                "per_page": str(per_page),
                "limit": str(per_page)
            })
            
            # Hacer request
            full_url = config.base_url.rstrip('/') + config.endpoint
            headers = await self._build_headers(config)
            
            async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
                response = await client.request(
                    method=config.method,
                    url=full_url,
                    headers=headers,
                    params=params
                )
            
            if response.status_code == 200:
                data = response.json()
                processed_data, _ = await self._process_response(data, config)
                
                # Aplicar field mapping
                mapped_data = await self._apply_field_mapping(processed_data, config.field_mappings)
                
                return mapped_data, len(mapped_data)
            else:
                logger.error(f"Error en API {api_id}: HTTP {response.status_code}")
                return [], 0
                
        except Exception as e:
            logger.error(f"Error obteniendo datos de API {api_id}: {e}")
            return [], 0
    
    # ================================
    # FUNCIONES AUXILIARES
    # ================================
    
    async def _build_headers(self, config: ApiConfiguration) -> Dict[str, str]:
        """Construir headers para el request"""
        headers = config.default_headers.copy()
        
        # Agregar autenticación
        if config.auth.type == "api_key_header":
            headers[config.auth.header_name] = config.auth.api_key
        elif config.auth.type == "bearer":
            headers["Authorization"] = f"Bearer {config.auth.access_token}"
        elif config.auth.type == "basic":
            import base64
            credentials = base64.b64encode(f"{config.auth.username}:{config.auth.password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        elif config.auth.type == "custom":
            headers.update(config.auth.custom_headers or {})
        
        return headers
    
    async def _build_params(self, config: ApiConfiguration, extra_params: Dict[str, Any] = None) -> Dict[str, str]:
        """Construir parámetros query"""
        params = config.default_query_params.copy()
        
        # Agregar autenticación por query param
        if config.auth.type == "api_key_query":
            params[config.auth.query_param] = config.auth.api_key
        
        # Agregar parámetros extra
        if extra_params:
            params.update({k: str(v) for k, v in extra_params.items()})
        
        return params
    
    async def _process_response(self, data: Any, config: ApiConfiguration, limit: Optional[int] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Procesar respuesta de la API"""
        try:
            # Extraer datos usando response_path si está configurado
            if config.response_path:
                # Simple JSONPath para casos básicos
                if config.response_path == "data":
                    data = data.get("data", data)
                elif "." in config.response_path:
                    for key in config.response_path.split("."):
                        data = data.get(key, data) if isinstance(data, dict) else data
            
            # Asegurar que tenemos una lista
            if not isinstance(data, list):
                if isinstance(data, dict) and "items" in data:
                    data = data["items"]
                elif isinstance(data, dict) and "results" in data:
                    data = data["results"]
                else:
                    data = [data] if data else []
            
            # Limitar registros si es necesario
            if limit:
                data = data[:limit]
            
            # Detectar campos únicos
            detected_fields = set()
            for item in data:
                if isinstance(item, dict):
                    detected_fields.update(item.keys())
            
            return data, list(detected_fields)
            
        except Exception as e:
            logger.error(f"Error procesando respuesta: {e}")
            return [], []
    
    async def _apply_field_mapping(self, data: List[Dict[str, Any]], mappings: List[FieldMapping]) -> List[Dict[str, Any]]:
        """Aplicar mapeo de campos"""
        if not mappings:
            return data
        
        mapping_dict = {m.api_field: m.entity_field for m in mappings}
        
        mapped_data = []
        for item in data:
            mapped_item = {}
            for api_field, value in item.items():
                entity_field = mapping_dict.get(api_field, api_field)
                mapped_item[entity_field] = value
            mapped_data.append(mapped_item)
        
        return mapped_data
    
    async def _suggest_field_mappings(self, detected_fields: List[str]) -> List[FieldMapping]:
        """Sugerir mapeos de campos automáticamente"""
        suggestions = []
        
        for field in detected_fields:
            # Sugerir tipo basado en nombre del campo
            field_type = "string"
            if any(keyword in field.lower() for keyword in ["id", "number", "count", "total"]):
                field_type = "number"
            elif any(keyword in field.lower() for keyword in ["email", "mail"]):
                field_type = "email"
            elif any(keyword in field.lower() for keyword in ["url", "link", "website"]):
                field_type = "url"
            elif any(keyword in field.lower() for keyword in ["date", "time", "created", "updated"]):
                field_type = "date"
            elif any(keyword in field.lower() for keyword in ["active", "enabled", "valid"]):
                field_type = "boolean"
            
            suggestions.append(FieldMapping(
                api_field=field,
                entity_field=field.lower().replace(" ", "_"),
                display_name=field.replace("_", " ").title(),
                field_type=field_type,
                visible=True,
                searchable=field_type in ["string", "email"],
                sortable=field_type in ["string", "number", "date"]
            ))
        
        return suggestions
    
    async def _recommend_cache_ttl(self, response_time_ms: float) -> int:
        """Recomendar TTL de cache basado en tiempo de respuesta"""
        if response_time_ms < 100:
            return 300   # 5 minutos para APIs rápidas
        elif response_time_ms < 1000:
            return 600   # 10 minutos para APIs normales
        else:
            return 1800  # 30 minutos para APIs lentas
    
    async def _update_last_test(self, config: ApiConfiguration, success: bool, error: Optional[str]):
        """Actualizar resultado del último test"""
        try:
            await self.db.api_configurations.update_one(
                {"business_id": config.business_id, "api_id": config.api_id},
                {
                    "$set": {
                        "last_test_at": datetime.utcnow(),
                        "last_test_success": success,
                        "last_error": error
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error actualizando último test: {e}")

# ================================
# FIN DEL SERVICIO DE APIs
# ================================