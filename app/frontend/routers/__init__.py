# ================================
# app/routers/__init__.py - CORREGIDO
# ================================

"""Routers del CMS Dinámico"""

from fastapi import APIRouter

# Importar sub-routers disponibles
try:
    from . import admin
except ImportError:
    admin = None

try:
    from . import business  
except ImportError:
    business = None

try:
    from . import auth
except ImportError:
    auth = None

# Router principal de la API
api_router = APIRouter()

# Incluir routers que estén disponibles
if admin:
    api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

if business:
    api_router.include_router(business.router, prefix="/business", tags=["business"])

if auth:
    api_router.include_router(auth.router, prefix="/auth", tags=["auth"])