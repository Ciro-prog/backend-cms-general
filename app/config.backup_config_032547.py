# ================================
# app/config.py (ACTUALIZADO COMPLETO)
# ================================

from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017/cms"
    mongodb_db_name: str = "cms"
    
    # Redis Cloud
    redis_url: str = "https://api.redislabs.com/v1"
    redis_api_key: Optional[str] = None
    
    # Clerk
    clerk_secret_key: str
    next_public_clerk_publishable_key: str
    
    # FastAPI
    api_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Encryption
    encryption_key: str
    
    # WAHA Integration (YA FUNCIONANDO)
    default_waha_url: str = "http://pampaservers.com:60513/"
    default_waha_api_key: Optional[str] = None
    
    # N8N Integration (YA FUNCIONANDO)
    default_n8n_url: str = "https://n8n.pampaservers.com/"
    default_n8n_api_key: Optional[str] = None
    
    # Cache
    cache_ttl_seconds: int = 300
    cache_enabled: bool = True
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "https://*.vercel.app"]
    
    model_config = ConfigDict(
        env_file = ".env",
        case_sensitive = False

    
    )
settings = Settings()