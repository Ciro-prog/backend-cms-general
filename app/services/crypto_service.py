from cryptography.fernet import Fernet
import base64
import logging
from typing import Union

from ..config import settings

logger = logging.getLogger(__name__)

class CryptoService:
    """Servicio para encriptación/desencriptación de datos sensibles"""
    
    def __init__(self):
        # Usar la key del settings o generar una nueva
        key = settings.encryption_key.encode() if settings.encryption_key else Fernet.generate_key()
        self.fernet = Fernet(base64.urlsafe_b64encode(key[:32]))
    
    async def encrypt(self, data: str) -> str:
        """Encriptar datos"""
        try:
            if not data:
                return data
            
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encriptando datos: {e}")
            raise
    
    async def decrypt(self, encrypted_data: str) -> str:
        """Desencriptar datos"""
        try:
            if not encrypted_data:
                return encrypted_data
            
            # Decodificar base64
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            # Desencriptar
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error desencriptando datos: {e}")
            raise
    
    async def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """Encriptar campos específicos de un diccionario"""
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = await self.encrypt(str(encrypted_data[field]))
        
        return encrypted_data
    
    async def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """Desencriptar campos específicos de un diccionario"""
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = await self.decrypt(decrypted_data[field])
        
        return decrypted_data