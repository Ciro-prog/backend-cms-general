# ================================
# app/core/api_client.py
# ================================

import httpx
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import logging
import json

from ..models.api_config import ApiConfiguration
from ..services.crypto_service import CryptoService
from ..utils.exceptions import CMSException

logger = logging.getLogger(__name__)

class GenericApiClient:
    """Cliente genérico para APIs externas con funcionalidades avanzadas"""
    
    def __init__(self, config: ApiConfiguration):
        self.config = config
        self.crypto_service = CryptoService()
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limiter = {}
    
    async def __aenter__(self):
        """Async context manager entrada"""
        await self._initialize_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager salida"""
        await self.close()
    
    async def _initialize_client(self):
        """Inicializar cliente HTTP"""
        if self._client:
            return
        
        # Desencriptar credenciales
        auth_config = self.config.configuracion.auth
        if auth_config.token:
            auth_config.token = await self.crypto_service.decrypt(auth_config.token)
        if auth_config.password:
            auth_config.password = await self.crypto_service.decrypt(auth_config.password)
        if auth_config.api_key:
            auth_config.api_key = await self.crypto_service.decrypt(auth_config.api_key)
        
        # Configurar headers
        headers = self.config.configuracion.headers.copy()
        
        # Configurar autenticación
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
        self._client = httpx.AsyncClient(
            base_url=self.config.configuracion.base_url,
            headers=headers,
            timeout=self.config.configuracion.timeout,
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10
            )
        )
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Realizar petición HTTP con manejo completo de errores y reintentos"""
        
        if not self._client:
            await self._initialize_client()
        
        # Verificar rate limiting
        await self._check_rate_limit()
        
        # Preparar URL
        url = endpoint
        if not endpoint.startswith('http'):
            # Buscar endpoint en configuración
            endpoints = self.config.configuracion.endpoints
            if endpoint in endpoints:
                url = endpoints[endpoint]
            else:
                url = endpoint
        
        # Realizar petición con reintentos
        return await self._request_with_retry(
            method, url, params, data, headers, timeout
        )
    
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]],
        data: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]],
        timeout: Optional[float]
    ) -> Dict[str, Any]:
        """Realizar petición con reintentos automáticos"""
        
        retry_config = self.config.configuracion.retry_config
        last_exception = None
        
        for attempt in range(retry_config.max_retries + 1):
            try:
                # Preparar argumentos de petición
                request_kwargs = {
                    "method": method,
                    "url": url,
                    "timeout": timeout or self.config.configuracion.timeout
                }
                
                if params:
                    request_kwargs["params"] = params
                
                if data and method.upper() != "GET":
                    request_kwargs["json"] = data
                
                if headers:
                    request_kwargs["headers"] = headers
                
                # Realizar petición
                response = await self._client.request(**request_kwargs)
                
                # Verificar si debemos reintentar por status code
                if response.status_code in retry_config.retry_on_status:
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code}: {response.text}",
                        request=response.request,
                        response=response
                    )
                
                # Verificar éxito
                response.raise_for_status()
                
                # Parsear respuesta
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"raw_response": response.text}
                
            except Exception as e:
                last_exception = e
                
                if attempt < retry_config.max_retries:
                    wait_time = retry_config.backoff_factor ** attempt
                    logger.warning(
                        f"Intento {attempt + 1} falló para {method} {url}, "
                        f"reintentando en {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Todos los reintentos fallaron para {method} {url}: {e}")
                    break
        
        # Si llegamos aquí, todos los reintentos fallaron
        raise CMSException(f"Error en petición API: {str(last_exception)}")
    
    async def _check_rate_limit(self):
        """Verificar y aplicar rate limiting"""
        rate_limit = self.config.configuracion.rate_limit
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Limpiar peticiones antiguas
        self._rate_limiter = {
            timestamp: count for timestamp, count in self._rate_limiter.items()
            if timestamp > minute_ago
        }
        
        # Contar peticiones en el último minuto
        total_requests = sum(self._rate_limiter.values())
        
        if total_requests >= rate_limit.requests_per_minute:
            # Calcular tiempo de espera hasta que se libere una petición
            oldest_request = min(self._rate_limiter.keys())
            wait_time = (oldest_request + timedelta(minutes=1) - now).total_seconds()
            
            if wait_time > 0:
                logger.info(f"Rate limit alcanzado, esperando {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        # Registrar petición actual
        current_minute = now.replace(second=0, microsecond=0)
        self._rate_limiter[current_minute] = self._rate_limiter.get(current_minute, 0) + 1
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Petición GET"""
        return await self.request("GET", endpoint, params=params, **kwargs)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Petición POST"""
        return await self.request("POST", endpoint, data=data, **kwargs)
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Petición PUT"""
        return await self.request("PUT", endpoint, data=data, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Petición DELETE"""
        return await self.request("DELETE", endpoint, **kwargs)
    
    async def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Petición PATCH"""
        return await self.request("PATCH", endpoint, data=data, **kwargs)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Probar conexión con la API"""
        try:
            start_time = datetime.now()
            
            # Intentar endpoint de health o root
            test_endpoints = ["/health", "/status", "/ping", "/"]
            
            for endpoint in test_endpoints:
                try:
                    response = await self.get(endpoint)
                    end_time = datetime.now()
                    
                    return {
                        "success": True,
                        "endpoint": endpoint,
                        "response_time_ms": (end_time - start_time).total_seconds() * 1000,
                        "response": response
                    }
                except:
                    continue
            
            # Si ningún endpoint funciona, intentar con la base URL
            response = await self.get("/")
            end_time = datetime.now()
            
            return {
                "success": True,
                "endpoint": "/",
                "response_time_ms": (end_time - start_time).total_seconds() * 1000,
                "response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close(self):
        """Cerrar cliente HTTP"""
        if self._client:
            await self._client.aclose()
            self._client = None