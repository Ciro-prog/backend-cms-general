# ================================
# app/services/cache_service.py (ACTUALIZADO para Redis Cloud)
# ================================

import httpx
import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta

from ..config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """Servicio para manejo de cache con Redis Cloud API"""
    
    def __init__(self):
        self.redis_url = settings.redis_url
        self.api_key = settings.redis_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json"
        }
        self._client = None
        self._connected = False
    
    async def _get_client(self):
        """Obtener cliente HTTP para Redis Cloud"""
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.redis_url,
                headers=self.headers,
                timeout=30.0
            )
        return self._client
    
    async def connect(self):
        """Conectar a Redis Cloud"""
        if not self._connected and settings.cache_enabled:
            try:
                client = await self._get_client()
                # Test connection with a simple ping
                response = await client.get("/ping")
                if response.status_code == 200:
                    self._connected = True
                    logger.info("Conectado a Redis Cloud exitosamente")
            except Exception as e:
                logger.error(f"Error conectando a Redis Cloud: {e}")
                self._client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        if not settings.cache_enabled or not self._connected:
            return None
        
        try:
            await self.connect()
            client = await self._get_client()
            
            response = await client.get(f"/get/{key}")
            if response.status_code == 200:
                data = response.json()
                if data.get("value"):
                    return json.loads(data["value"])
            return None
        except Exception as e:
            logger.error(f"Error obteniendo cache key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Guardar valor en cache"""
        if not settings.cache_enabled:
            return False
        
        try:
            await self.connect()
            client = await self._get_client()
            
            ttl = ttl or settings.cache_ttl_seconds
            
            payload = {
                "key": key,
                "value": json.dumps(value, default=str),
                "ttl": ttl
            }
            
            response = await client.post("/set", json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error guardando cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Eliminar valor del cache"""
        if not self._connected:
            return False
        
        try:
            await self.connect()
            client = await self._get_client()
            
            response = await client.delete(f"/delete/{key}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error eliminando cache key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Eliminar todas las keys que coincidan con un patrón"""
        if not self._connected:
            return 0
        
        try:
            await self.connect()
            client = await self._get_client()
            
            # Para Redis Cloud, necesitamos hacer esto de manera diferente
            # ya que no tenemos acceso directo a KEYS
            payload = {"pattern": pattern}
            response = await client.post("/keys", json=payload)
            
            if response.status_code == 200:
                keys = response.json().get("keys", [])
                deleted_count = 0
                
                for key in keys:
                    if await self.delete(key):
                        deleted_count += 1
                
                return deleted_count
            
            return 0
        except Exception as e:
            logger.error(f"Error limpiando cache pattern {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Verificar si existe una key"""
        if not self._connected:
            return False
        
        try:
            await self.connect()
            client = await self._get_client()
            
            response = await client.get(f"/exists/{key}")
            if response.status_code == 200:
                return response.json().get("exists", False)
            return False
        except Exception as e:
            logger.error(f"Error verificando cache key {key}: {e}")
            return False
    
    async def close(self):
        """Cerrar conexión"""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._connected = False

