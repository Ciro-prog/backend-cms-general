# ================================
# app/services/waha_service.py (ACTUALIZADO con API Key)
# ================================

import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import get_database
from ..models.atencion_humana import AtencionHumana, AtencionHumanaCreate
from ..config import settings

logger = logging.getLogger(__name__)

class WAHAService:
    """Servicio WAHA con headers correctos"""
    
    def __init__(self):
        self.base_url = os.getenv("DEFAULT_WAHA_URL", "").rstrip('/')
        self.api_key = os.getenv("DEFAULT_WAHA_API_KEY", "")
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        if self.api_key:
            self.headers["X-Api-Key"] = self.api_key
    
    async def get_sessions(self):
        """Obtener sesiones de WhatsApp"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/sessions",
                headers=self.headers,
                timeout=30.0
            )
            return response.json() if response.status_code == 200 else None

class N8NService:
    """Servicio N8N con headers correctos"""
    
    def __init__(self):
        self.base_url = os.getenv("DEFAULT_N8N_URL", "").rstrip('/')
        self.api_key = os.getenv("DEFAULT_N8N_API_KEY", "")
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        if self.api_key:
            self.headers["X-N8N-API-KEY"] = self.api_key
    
    async def get_workflows(self):
        """Obtener workflows activos"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/workflows?active=true",
                headers=self.headers,
                timeout=30.0
            )
            return response.json() if response.status_code == 200 else None
