from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017/cms_dinamico"
    mongodb_db_name: str = "cms_dinamico"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Clerk
    clerk_secret_key: str
    clerk_publishable_key: str
    
    # FastAPI
    api_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Encryption
    encryption_key: str
    
    # Integrations
    default_waha_url: str = "http://localhost:3000"
    default_n8n_url: str = "http://localhost:5678"
    
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
    allowed_origins: list = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()