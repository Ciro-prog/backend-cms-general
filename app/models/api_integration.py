# ================================
# app/models/api_integration.py
# ================================

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class AuthType(str, Enum):
    NONE = "none"
    API_KEY_HEADER = "api_key_header"
    API_KEY_QUERY = "api_key_query"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    CUSTOM_HEADERS = "custom_headers"

class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class DataFormat(str, Enum):
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    PLAIN_TEXT = "plain_text"

class ComponentLayoutType(str, Enum):  # ← DEBE ESTAR DEFINIDO
    TAB = "tab"
    WIDGET = "widget" 
    PAGE = "page"
    TAB_AND_WIDGET = "tab_and_widget"
    PAGE_AND_WIDGET = "page_and_widget"


# ================================
# API CONFIGURATION
# ================================

class AuthConfig(BaseModel):
    """Configuración de autenticación"""
    auth_type: AuthType = AuthType.NONE
    
    # Para API Key
    api_key: Optional[str] = Field(None, description="API Key (será encriptada)")
    header_name: Optional[str] = Field("X-API-Key", description="Nombre del header para API key")
    query_param: Optional[str] = Field("api_key", description="Nombre del query param")
    
    # Para Bearer Token
    bearer_token: Optional[str] = Field(None, description="Bearer token (será encriptado)")
    
    # Para Basic Auth
    username: Optional[str] = Field(None, description="Username para basic auth")
    password: Optional[str] = Field(None, description="Password (será encriptado)")
    
    # Para OAuth2
    client_id: Optional[str] = Field(None, description="OAuth2 Client ID")
    client_secret: Optional[str] = Field(None, description="OAuth2 Client Secret (será encriptado)")
    token_url: Optional[str] = Field(None, description="OAuth2 Token URL")
    refresh_token: Optional[str] = Field(None, description="OAuth2 Refresh Token (será encriptado)")
    
    # Para Custom Headers
    custom_headers: Dict[str, str] = Field(default_factory=dict, description="Headers personalizados")

class CacheConfig(BaseModel):
    """Configuración de cache"""
    enabled: bool = Field(True, description="Si el cache está habilitado")
    ttl_seconds: int = Field(300, description="Tiempo de vida en segundos (5 min default)")
    max_size_mb: int = Field(5, description="Tamaño máximo en MB")
    cache_key_fields: List[str] = Field(default_factory=list, description="Campos para generar cache key")

class RateLimitConfig(BaseModel):
    """Configuración de rate limiting"""
    enabled: bool = Field(True, description="Si el rate limiting está habilitado")
    requests_per_minute: int = Field(60, description="Requests por minuto")
    burst_limit: int = Field(10, description="Límite de burst")

class DataMappingConfig(BaseModel):
    """Configuración de mapeo de datos"""
    source_field: str = Field(..., description="Campo en la respuesta de la API")
    target_field: str = Field(..., description="Campo en el componente")
    data_type: str = Field("string", description="Tipo de dato esperado")
    is_required: bool = Field(False, description="Si el campo es obligatorio")
    default_value: Optional[Any] = Field(None, description="Valor por defecto")
    transformation: Optional[str] = Field(None, description="Transformación a aplicar")

class APIConfiguration(BaseModel):
    """Configuración completa de una API externa"""
    api_id: str = Field(..., description="ID único de la API")
    business_id: str = Field(..., description="ID del business")
    
    # Información básica
    name: str = Field(..., description="Nombre de la API")
    description: Optional[str] = Field(None, description="Descripción de la API")
    base_url: HttpUrl = Field(..., description="URL base de la API")
    endpoint: str = Field(..., description="Endpoint específico")
    method: HTTPMethod = Field(HTTPMethod.GET, description="Método HTTP")
    
    # Configuraciones
    auth_config: AuthConfig = Field(default_factory=AuthConfig)
    cache_config: CacheConfig = Field(default_factory=CacheConfig)
    rate_limit_config: RateLimitConfig = Field(default_factory=RateLimitConfig)
    
    # Mapeo de datos
    data_mappings: List[DataMappingConfig] = Field(default_factory=list)
    
    # Configuración de respuesta
    response_format: DataFormat = Field(DataFormat.JSON)
    data_path: Optional[str] = Field(None, description="Path al array de datos (ej: 'data.users')")
    
    # Headers y parámetros adicionales
    default_headers: Dict[str, str] = Field(default_factory=dict)
    default_params: Dict[str, Any] = Field(default_factory=dict)
    
    # Configuración avanzada
    timeout_seconds: int = Field(30, description="Timeout en segundos")
    max_retries: int = Field(3, description="Máximo número de reintentos")
    retry_delay_seconds: int = Field(1, description="Delay entre reintentos")
    
    # Logging
    log_requests: bool = Field(True, description="Si loggear requests")
    log_responses: bool = Field(False, description="Si loggear responses (cuidado con datos sensibles)")
    
    # Metadata
    is_active: bool = Field(True, description="Si la API está activa")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None)

# ================================
# DYNAMIC COMPONENTS
# ================================

class ComponentLayoutType(str, Enum):
    TAB = "tab"
    WIDGET = "widget" 
    PAGE = "page"
    TAB_AND_WIDGET = "tab_and_widget"
    PAGE_AND_WIDGET = "page_and_widget"

class DynamicComponent(BaseModel):
    """Componente dinámico que consume una API"""
    component_id: str = Field(..., description="ID único del componente")
    business_id: str = Field(..., description="ID del business")
    api_id: str = Field(..., description="ID de la API que consume")
    
    # Información básica
    name: str = Field(..., description="Nombre del componente")
    description: Optional[str] = Field(None, description="Descripción")
    component_type: ComponentType = Field(..., description="Tipo de componente")
    
    # Configuración de layout
    layout_type: ComponentLayoutType = Field(ComponentLayoutType.TAB)
    
    # Configuración específica del componente
    component_config: Dict[str, Any] = Field(default_factory=dict, description="Configuración específica")
    
    # Para Tables
    table_config: Optional[Dict[str, Any]] = Field(None, description="Config específica de tabla")
    
    # Para Charts  
    chart_config: Optional[Dict[str, Any]] = Field(None, description="Config específica de gráfico")
    
    # Para Metrics
    metric_config: Optional[Dict[str, Any]] = Field(None, description="Config específica de métrica")
    
    # Configuración de actions
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Acciones disponibles")
    
    # Configuración de actualización
    auto_refresh: bool = Field(True, description="Si se actualiza automáticamente")
    refresh_interval_seconds: int = Field(300, description="Intervalo de actualización en segundos")
    
    # Permisos
    required_permissions: List[str] = Field(default_factory=list, description="Permisos requeridos")
    
    # Metadata
    is_active: bool = Field(True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ================================
# API CACHE & LOGS
# ================================

class APICallLog(BaseModel):
    """Log de llamada a API"""
    log_id: str = Field(..., description="ID único del log")
    api_id: str = Field(..., description="ID de la API")
    business_id: str = Field(..., description="ID del business")
    component_id: Optional[str] = Field(None, description="ID del componente que hizo la llamada")
    
    # Request info
    request_method: str
    request_url: str
    request_headers: Dict[str, str] = Field(default_factory=dict)
    request_params: Dict[str, Any] = Field(default_factory=dict)
    request_body: Optional[Dict[str, Any]] = None
    
    # Response info
    response_status_code: Optional[int] = None
    response_headers: Dict[str, str] = Field(default_factory=dict)
    response_size_bytes: Optional[int] = None
    response_time_ms: Optional[int] = None
    
    # Result info
    success: bool
    error_message: Optional[str] = None
    error_type: Optional[str] = None  # timeout, connection, auth, parse, server_error
    records_returned: Optional[int] = None
    records_processed: Optional[int] = None
    
    # Cache info
    cache_hit: bool = False
    cache_saved: bool = False
    
    # Context
    triggered_by: str = Field("user_request", description="auto_refresh, user_request, component_load")
    user_id: Optional[str] = None
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class APICacheEntry(BaseModel):
    """Entrada de cache para una API"""
    cache_id: str = Field(..., description="ID único del cache")
    api_id: str = Field(..., description="ID de la API")
    business_id: str = Field(..., description="ID del business")
    
    # Cache data
    data: Any = Field(..., description="Datos cacheados (procesados)")
    raw_data: Optional[Any] = Field(None, description="Datos originales (opcional)")
    data_hash: str = Field(..., description="Hash de los datos para detectar cambios")
    record_count: int = Field(0, description="Número de registros")
    size_bytes: int = Field(0, description="Tamaño en bytes")
    
    # Cache metadata
    cached_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Cuándo expira")
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(0, description="Número de accesos")
    
    # Request context
    request_params: Dict[str, Any] = Field(default_factory=dict)
    cache_key: str = Field(..., description="Clave de cache generada")
    
    # Status
    is_active: bool = Field(True)

# ================================
# REQUEST/RESPONSE MODELS
# ================================

class APIConfigurationCreate(BaseModel):
    """Crear configuración de API"""
    business_id: str
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    base_url: HttpUrl
    endpoint: str = Field(..., min_length=1)
    method: HTTPMethod = HTTPMethod.GET
    auth_config: AuthConfig = Field(default_factory=AuthConfig)
    cache_config: CacheConfig = Field(default_factory=CacheConfig)
    data_mappings: List[DataMappingConfig] = Field(default_factory=list)

class DynamicComponentCreate(BaseModel):
    """Crear componente dinámico"""
    business_id: str
    api_id: str
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    component_type: ComponentType
    layout_type: ComponentLayoutType = ComponentLayoutType.TAB
    component_config: Dict[str, Any] = Field(default_factory=dict)

# ================================
# EJEMPLOS PARA TESTING
# ================================

# API de ejemplo: JSONPlaceholder Users
EXAMPLE_JSONPLACEHOLDER_API = APIConfigurationCreate(
    business_id="isp_telconorte",
    name="JSONPlaceholder Users",
    description="API de prueba con usuarios",
    base_url="https://jsonplaceholder.typicode.com",
    endpoint="/users",
    method=HTTPMethod.GET,
    auth_config=AuthConfig(auth_type=AuthType.NONE),
    cache_config=CacheConfig(ttl_seconds=600, max_size_mb=2),
    data_mappings=[
        DataMappingConfig(source_field="id", target_field="cliente_id", data_type="integer"),
        DataMappingConfig(source_field="name", target_field="nombre", data_type="string"),
        DataMappingConfig(source_field="email", target_field="email", data_type="string"),
        DataMappingConfig(source_field="phone", target_field="telefono", data_type="string"),
        DataMappingConfig(source_field="website", target_field="sitio_web", data_type="string"),
    ]
)

# Componente de ejemplo: Tabla de usuarios
EXAMPLE_USERS_TABLE_COMPONENT = DynamicComponentCreate(
    business_id="isp_telconorte",
    api_id="jsonplaceholder_users",
    name="Tabla de Usuarios API",
    description="Tabla que muestra usuarios desde JSONPlaceholder",
    component_type=ComponentType.TABLE,
    layout_type=ComponentLayoutType.TAB_AND_WIDGET,
    component_config={
        "table_config": {
            "columns": ["cliente_id", "nombre", "email", "telefono"],
            "sortable_columns": ["nombre", "email"],
            "searchable_columns": ["nombre", "email"],
            "pagination": {"page_size": 20, "show_size_selector": True},
            "actions": [
                {"name": "Ver Detalle", "type": "modal", "icon": "eye"},
                {"name": "Editar", "type": "form", "icon": "edit"}
            ]
        },
        "widget_config": {
            "position": "top_right",
            "width": "half",
            "height": "medium",
            "show_actions": False
        }
    }
)