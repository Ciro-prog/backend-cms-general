# ================================
# app/models/api_config.py - MODELOS DE CONFIGURACIÓN DE API
# ================================

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from bson import ObjectId
from ._common import PyObjectId

# Configuración estándar para Pydantic v2
API_CONFIG = ConfigDict(
    populate_by_name=True,
    arbitrary_types_allowed=True,
    json_encoders={ObjectId: str},
    str_strip_whitespace=True,
    validate_assignment=True
)

# ================================
# CONFIGURACIONES DE AUTENTICACIÓN
# ================================

class AuthConfig(BaseModel):
    """Configuración de autenticación para API externa"""
    tipo: Literal["none", "api_key_header", "api_key_query", "bearer", "basic", "oauth2", "custom"] = "none"
    
    # Para API Key
    api_key: Optional[str] = None
    header_name: str = "X-API-Key"
    query_param: str = "api_key"
    
    # Para Bearer Token
    token: Optional[str] = None
    
    # Para Basic Auth
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Para OAuth2
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    token_url: Optional[str] = None
    scope: Optional[str] = None

class RateLimitConfig(BaseModel):
    """Configuración de rate limiting"""
    requests_per_minute: int = 60
    burst: int = 10
    enabled: bool = True

class RetryConfig(BaseModel):
    """Configuración de reintentos"""
    max_retries: int = 3
    backoff_factor: float = 1.0
    retry_on_status: List[int] = [500, 502, 503, 504]

class CacheConfig(BaseModel):
    """Configuración de caché"""
    enabled: bool = True
    ttl_seconds: int = 300  # 5 minutos
    max_size: int = 1000

class FieldMapping(BaseModel):
    """Mapeo de campos entre API externa y sistema interno"""
    external_field: str
    internal_field: str
    transformation: Optional[str] = None  # "date", "number", "boolean", etc.
    default_value: Optional[Any] = None

# ================================
# CONFIGURACIÓN PRINCIPAL DE API
# ================================

class ApiConfiguration(BaseModel):
    """Configuración completa de API externa"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    business_id: str
    name: str = Field(..., description="Nombre identificativo de la API")
    description: Optional[str] = None
    
    # Configuración de conexión
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET"
    base_url: str = Field(..., description="URL base de la API")
    endpoint: str = Field(..., description="Endpoint específico")
    
    # Autenticación y seguridad
    auth: AuthConfig = Field(default_factory=AuthConfig)
    
    # Headers y parámetros por defecto
    default_headers: Optional[Dict[str, str]] = None
    default_query_params: Optional[Dict[str, str]] = None
    
    # Mapeo de campos
    field_mappings: Optional[List[FieldMapping]] = None
    
    # Configuraciones adicionales
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    cache_config: CacheConfig = Field(default_factory=CacheConfig)
    
    # Estado y metadata
    active: bool = True
    last_test_status: Optional[str] = None
    last_test_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = API_CONFIG
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url debe comenzar con http:// o https://')
        return v
    
    @field_validator('endpoint')
    @classmethod
    def validate_endpoint(cls, v):
        if not v.startswith('/'):
            return '/' + v
        return v

class ApiConfigurationCreate(BaseModel):
    """Modelo para crear configuración de API"""
    business_id: str
    name: str
    description: Optional[str] = None
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET"
    base_url: str
    endpoint: str
    auth: Optional[AuthConfig] = None
    default_headers: Optional[Dict[str, str]] = None
    default_query_params: Optional[Dict[str, str]] = None
    field_mappings: Optional[List[FieldMapping]] = None
    cache_config: Optional[CacheConfig] = None

class ApiConfigurationUpdate(BaseModel):
    """Modelo para actualizar configuración de API"""
    name: Optional[str] = None
    description: Optional[str] = None
    method: Optional[Literal["GET", "POST", "PUT", "DELETE", "PATCH"]] = None
    base_url: Optional[str] = None
    endpoint: Optional[str] = None
    auth: Optional[AuthConfig] = None
    default_headers: Optional[Dict[str, str]] = None
    default_query_params: Optional[Dict[str, str]] = None
    field_mappings: Optional[List[FieldMapping]] = None
    cache_config: Optional[CacheConfig] = None
    active: Optional[bool] = None

# ================================
# MODELOS PARA TESTING DE API
# ================================

class ApiTestRequest(BaseModel):
    """Request para probar API"""
    limit_records: int = Field(5, ge=1, le=50, description="Límite de registros para test")
    custom_params: Optional[Dict[str, str]] = None

class ApiTestResult(BaseModel):
    """Resultado del test de API"""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    sample_data: Optional[List[Dict[str, Any]]] = None
    detected_fields: Optional[List[str]] = None
    total_records: Optional[int] = None
    
    # Sugerencias automáticas
    suggested_mappings: Optional[List[FieldMapping]] = None
    recommended_cache_ttl: Optional[int] = None
