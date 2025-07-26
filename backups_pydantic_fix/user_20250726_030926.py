from pydantic import BaseModel, ConfigDict, Field, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

class PermisosUsuario(BaseModel):
    """Permisos específicos del usuario"""
    puede_editar_config: bool = False
    puede_responder_whatsapp: bool = False
    areas_whatsapp: List[str] = []
    entidades_acceso: List[str] = []
    vistas_acceso: List[str] = []

class PreferenciasUsuario(BaseModel):
    """Preferencias del usuario"""
    tema: str = "light"  # "light", "dark", "auto"
    idioma: str = "es"
    timezone: str = "America/Argentina/Buenos_Aires"

class PerfilUsuario(BaseModel):
    """Perfil del usuario"""
    nombre: str
    avatar_url: Optional[str] = None
    timezone: str = "America/Argentina/Buenos_Aires"
    preferencias: PreferenciasUsuario = Field(default_factory=PreferenciasUsuario)

class User(BaseModel):
    """Usuario del sistema"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    clerk_user_id: str = Field(..., description="ID del usuario en Clerk")
    business_id: Optional[str] = None  # null para super_admin
    email: EmailStr
    rol: str = "user"  # "super_admin", "admin", "user", "tecnico"
    permisos: PermisosUsuario = Field(default_factory=PermisosUsuario)
    perfil: PerfilUsuario
    ultimo_acceso: Optional[datetime] = None
    activo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name = True,
        arbitrary_types_allowed = True,
        json_encoders = {ObjectId: str}

    
    )
class UserCreate(BaseModel):
    """Modelo para crear usuario"""
    clerk_user_id: str
    business_id: Optional[str] = None
    email: EmailStr
    rol: str = "user"
    permisos: Optional[PermisosUsuario] = None
    perfil: PerfilUsuario

class UserUpdate(BaseModel):
    """Modelo para actualizar usuario"""
    business_id: Optional[str] = None
    rol: Optional[str] = None
    permisos: Optional[PermisosUsuario] = None
    perfil: Optional[PerfilUsuario] = None
    activo: Optional[bool] = None

# ================================
# app/models/api_config.py
# ================================

from pydantic import BaseModel, ConfigDict, Field
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
    
    model_config = ConfigDict(
        populate_by_name = True,
        arbitrary_types_allowed = True,
        json_encoders = {ObjectId: str}

    
    )
class ApiConfigurationCreate(BaseModel):
    """Modelo para crear configuración de API"""
    business_id: str
    api_name: str
    configuracion: ApiConfigData

class ApiConfigurationUpdate(BaseModel):
    """Modelo para actualizar configuración de API"""
    configuracion: Optional[ApiConfigData] = None
    activa: Optional[bool] = None   