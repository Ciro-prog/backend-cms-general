from typing import List, Optional
from datetime import datetime
import logging

from ..database import get_database
from ..models.api_config import ApiConfiguration, ApiConfigurationCreate, ApiConfigurationUpdate
from .crypto_service import CryptoService

logger = logging.getLogger(__name__)

class ApiConfigService:
    """Servicio para gestión de configuraciones de API"""
    
    def __init__(self):
        self.db = get_database()
        self.crypto_service = CryptoService()
    
    async def get_api_configs_by_business(self, business_id: str) -> List[ApiConfiguration]:
        """Obtener todas las configuraciones de API de un business"""
        cursor = self.db.api_configurations.find({"business_id": business_id}).sort("api_name", 1)
        configs = []
        
        async for doc in cursor:
            # Desencriptar credenciales para respuesta
            config = ApiConfiguration(**doc)
            config = await self._decrypt_credentials(config)
            configs.append(config)
        
        return configs
    
    async def get_api_config(self, business_id: str, api_name: str) -> Optional[ApiConfiguration]:
        """Obtener configuración específica de API"""
        doc = await self.db.api_configurations.find_one({
            "business_id": business_id,
            "api_name": api_name
        })
        
        if doc:
            config = ApiConfiguration(**doc)
            return await self._decrypt_credentials(config)
        
        return None
    
    async def create_api_config(self, config_data: ApiConfigurationCreate) -> ApiConfiguration:
        """Crear nueva configuración de API"""
        config = ApiConfiguration(**config_data.dict())
        
        # Encriptar credenciales
        config = await self._encrypt_credentials(config)
        
        result = await self.db.api_configurations.insert_one(config.dict(by_alias=True))
        config.id = result.inserted_id
        
        logger.info(f"Configuración de API creada: {config.business_id}.{config.api_name}")
        return config
    
    async def update_api_config(
        self, 
        business_id: str, 
        api_name: str, 
        config_update: ApiConfigurationUpdate
    ) -> Optional[ApiConfiguration]:
        """Actualizar configuración de API"""
        update_data = config_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Si hay datos de configuración, encriptar credenciales
        if "configuracion" in update_data:
            temp_config = ApiConfiguration(
                business_id=business_id,
                api_name=api_name,
                configuracion=update_data["configuracion"]
            )
            encrypted_config = await self._encrypt_credentials(temp_config)
            update_data["configuracion"] = encrypted_config.configuracion
        
        result = await self.db.api_configurations.find_one_and_update(
            {"business_id": business_id, "api_name": api_name},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            logger.info(f"Configuración de API actualizada: {business_id}.{api_name}")
            config = ApiConfiguration(**result)
            return await self._decrypt_credentials(config)
        
        return None
    
    async def _encrypt_credentials(self, config: ApiConfiguration) -> ApiConfiguration:
        """Encriptar credenciales sensibles"""
        auth = config.configuracion.auth
        
        if auth.token:
            auth.token = await self.crypto_service.encrypt(auth.token)
        if auth.password:
            auth.password = await self.crypto_service.encrypt(auth.password)
        if auth.api_key:
            auth.api_key = await self.crypto_service.encrypt(auth.api_key)
        
        return config
    
    async def _decrypt_credentials(self, config: ApiConfiguration) -> ApiConfiguration:
        """Desencriptar credenciales para uso"""
        auth = config.configuracion.auth
        
        try:
            if auth.token:
                auth.token = await self.crypto_service.decrypt(auth.token)
            if auth.password:
                auth.password = await self.crypto_service.decrypt(auth.password)
            if auth.api_key:
                auth.api_key = await self.crypto_service.decrypt(auth.api_key)
        except Exception as e:
            logger.error(f"Error desencriptando credenciales: {e}")
        
        return config