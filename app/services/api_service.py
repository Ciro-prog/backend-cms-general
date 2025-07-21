import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import json

from ..database import get_database
from ..models.api_config import ApiConfiguration
from ..services.cache_service import CacheService
from ..services.crypto_service import CryptoService
from ..utils.exceptions import CMSException

logger = logging.getLogger(__name__)

class ApiService:
    """Servicio para manejo de APIs externas"""
    
    def __init__(self):
        self.db = get_database()
        self.cache_service = CacheService()
        self.crypto_service = CryptoService()
        self._clients = {}  # Cache de clientes HTTP
    
    async def get_api_config(self, business_id: str, api_name: str) -> Optional[ApiConfiguration]:
        """Obtener configuración de API"""
        doc = await self.db.api_configurations.find_one({
            "business_id": business_id,
            "api_name": api_name,
            "activa": True
        })
        return ApiConfiguration(**doc) if doc else None
    
    async def get_http_client(self, config: ApiConfiguration) -> httpx.AsyncClient:
        """Obtener cliente HTTP configurado"""
        cache_key = f"{config.business_id}_{config.api_name}"
        
        if cache_key not in self._clients:
            # Desencriptar credenciales
            auth_config = config.configuracion.auth
            if auth_config.token:
                auth_config.token = await self.crypto_service.decrypt(auth_config.token)
            if auth_config.password:
                auth_config.password = await self.crypto_service.decrypt(auth_config.password)
            
            # Configurar headers de autenticación
            headers = config.configuracion.headers.copy()
            
            if auth_config.tipo == "bearer" and auth_config.token:
                headers[auth_config.header] = f"Bearer {auth_config.token}"
            elif auth_config.tipo == "api_key" and auth_config.api_key:
                headers[auth_config.header] = auth_config.api_key
            elif auth_config.tipo == "basic" and auth_config.username and auth_config.password:
                import base64
                credentials = base64.b64encode(
                    f"{auth_config.username}:{auth_config.password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"
            
            # Crear cliente
            self._clients[cache_key] = httpx.AsyncClient(
                base_url=config.configuracion.base_url,
                headers=headers,
                timeout=config.configuracion.timeout,
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5
                )
            )
        
        return self._clients[cache_key]
    
    async def make_request(
        self,
        business_id: str,
        api_name: str,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Realizar petición a API externa"""
        
        # Obtener configuración
        config = await self.get_api_config(business_id, api_name)
        if not config:
            raise CMSException(f"Configuración de API no encontrada: {api_name}")
        
        # Verificar cache
        cache_key = f"api_{business_id}_{api_name}_{endpoint}_{json.dumps(params or {})}"
        if use_cache and method == "GET":
            cached_data = await self.cache_service.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit para {cache_key}")
                return cached_data
        
        # Realizar petición
        client = await self.get_http_client(config)
        
        try:
            # Rate limiting básico
            await self._check_rate_limit(business_id, api_name, config)
            
            # Construir URL completa
            url = endpoint
            if not endpoint.startswith('http'):
                # Usar endpoint desde configuración o construir
                if endpoint in config.configuracion.endpoints:
                    url = config.configuracion.endpoints[endpoint]
                else:
                    url = endpoint
            
            # Realizar petición con reintentos
            response_data = await self._make_request_with_retry(
                client, method, url, params, data, config
            )
            
            # Guardar en cache si es GET
            if use_cache and method == "GET":
                await self.cache_service.set(
                    cache_key, 
                    response_data, 
                    ttl=config.configuracion.cache_config.refresh_seconds if hasattr(config.configuracion, 'cache_config') else 300
                )
            
            logger.info(f"API request exitosa: {api_name} {method} {url}")
            return response_data
            
        except Exception as e:
            logger.error(f"Error en API request: {api_name} {method} {endpoint} - {e}")
            raise CMSException(f"Error en API externa: {str(e)}")
    
    async def _make_request_with_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]],
        data: Optional[Dict[str, Any]],
        config: ApiConfiguration
    ) -> Dict[str, Any]:
        """Realizar petición con reintentos"""
        
        retry_config = config.configuracion.retry_config
        last_exception = None
        
        for attempt in range(retry_config.max_retries + 1):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data if method != "GET" else None
                )
                
                # Verificar status code
                if response.status_code in retry_config.retry_on_status:
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response
                    )
                
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                last_exception = e
                
                if attempt < retry_config.max_retries:
                    wait_time = retry_config.backoff_factor ** attempt
                    logger.warning(f"Intento {attempt + 1} falló, reintentando en {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Todos los reintentos fallaron: {e}")
                    break
        
        raise last_exception
    
    async def _check_rate_limit(self, business_id: str, api_name: str, config: ApiConfiguration):
        """Verificar rate limiting"""
        if not hasattr(config.configuracion, 'rate_limit'):
            return
        
        rate_limit = config.configuracion.rate_limit
        key = f"rate_limit_{business_id}_{api_name}"
        
        # Obtener contador actual
        current_count = await self.cache_service.get(key) or 0
        
        if current_count >= rate_limit.requests_per_minute:
            raise CMSException("Rate limit excedido")
        
        # Incrementar contador
        await self.cache_service.set(key, current_count + 1, ttl=60)
    
    async def test_connection(self, business_id: str, api_name: str) -> Dict[str, Any]:
        """Probar conexión con API externa"""
        try:
            config = await self.get_api_config(business_id, api_name)
            if not config:
                return {"success": False, "error": "Configuración no encontrada"}
            
            client = await self.get_http_client(config)
            
            # Intentar un endpoint básico o health check
            test_endpoint = "/health" if "/health" in config.configuracion.endpoints else "/"
            
            start_time = datetime.utcnow()
            response = await client.get(test_endpoint)
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "base_url": config.configuracion.base_url
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close_clients(self):
        """Cerrar todos los clientes HTTP"""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()