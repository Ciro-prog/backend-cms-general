from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

class AuthConfig(BaseModel):
    """Configuración de autenticación para API externa"""
    tipo: str  # "bearer", "basic", "api_key", "oauth"
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    header: str = "Authorization"

class RateLimitConfig(BaseModel):
    """Configuración de rate limiting"""
    requests_per_minute: int = 60
    burst: int = 10

class RetryConfig(BaseModel):
    """Configuración de reintentos"""
    max_retries: int = 3
    backoff_factor: float = 2.0
    retry_on_status: List[int] = [429, 500, 502, 503, 504]

class ApiConfigData(BaseModel):
    """Datos de configuración de API"""
    nombre: str
    descripcion: Optional[str] = None
    base_url: str
    auth: AuthConfig
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    endpoints: Dict[str, str] = {}
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    timeout: int = 30
    retry_config: RetryConfig = Field(default_factory=RetryConfig)

class ApiConfiguration(BaseModel):
    """Configuración de API externa"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    business_id: str
    api_name: str
    configuracion: ApiConfigData
    activa: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ApiConfigurationCreate(BaseModel):
    """Modelo para crear configuración de API"""
    business_id: str
    api_name: str
    configuracion: ApiConfigData

class ApiConfigurationUpdate(BaseModel):
    """Modelo para actualizar configuración de API"""
    configuracion: Optional[ApiConfigData] = None
    activa: Optional[bool] = None

# ================================
# app/models/atencion_humana.py
# ================================

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

class ClienteExterno(BaseModel):
    """Información del cliente desde API externa"""
    api_origen: str
    cliente_id: str
    datos_cache: Dict[str, Any] = {}
    ultimo_refresh: datetime = Field(default_factory=datetime.utcnow)

class MensajeWhatsApp(BaseModel):
    """Mensaje de WhatsApp"""
    timestamp: datetime
    de: str  # número de teléfono
    para: str  # número de teléfono
    mensaje: str
    tipo: str = "texto"  # "texto", "imagen", "audio", "documento"
    metadata: Dict[str, Any] = {}

class ConversacionData(BaseModel):
    """Datos de la conversación"""
    requiere_atencion: bool = True
    area_solicitada: str  # "ventas", "soporte", "admin", "tecnica"
    estado: str = "pendiente"  # "pendiente", "atendiendo", "finalizado"
    mensajes_contexto: List[MensajeWhatsApp] = []
    usuario_atendiendo: Optional[str] = None
    fecha_inicio: datetime = Field(default_factory=datetime.utcnow)
    fecha_finalizacion: Optional[datetime] = None
    notas_atencion: Optional[str] = None
    tags: List[str] = []

class TicketExterno(BaseModel):
    """Información del ticket en sistema externo"""
    ticket_id: str
    estado: str
    prioridad: str = "media"
    url: Optional[str] = None

class AtencionHumana(BaseModel):
    """Sesión de atención humana WhatsApp"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    business_id: str
    whatsapp_numero: str
    cliente_externo: ClienteExterno
    conversacion: ConversacionData
    ticket_externo: Optional[TicketExterno] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AtencionHumanaCreate(BaseModel):
    """Modelo para crear sesión de atención"""
    business_id: str
    whatsapp_numero: str
    cliente_externo: ClienteExterno
    conversacion: ConversacionData
    ticket_externo: Optional[TicketExterno] = None

class AtencionHumanaUpdate(BaseModel):
    """Modelo para actualizar sesión de atención"""
    conversacion: Optional[ConversacionData] = None
    ticket_externo: Optional[TicketExterno] = None
