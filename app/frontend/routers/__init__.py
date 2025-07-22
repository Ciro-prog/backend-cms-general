# ================================
# app/frontend/routers/__init__.py - CORREGIDO
# ================================

"""Routers del frontend - Importación lazy para evitar circulares"""

from fastapi import APIRouter

# Router principal del frontend
frontend_router = APIRouter()

# Importación lazy para evitar importaciones circulares
def setup_frontend_routes():
    """Configurar todas las rutas del frontend"""
    
    # Importar aquí para evitar circulares
    from .auth import router as auth_router
    from .dashboard import router as dashboard_router
    from .business_types import router as business_types_router  
    from .business import router as businesses_router
    
    # Incluir todos los sub-routers
    frontend_router.include_router(auth_router, tags=["frontend-auth"])
    frontend_router.include_router(dashboard_router, tags=["frontend-dashboard"])
    frontend_router.include_router(business_types_router, tags=["frontend-business-types"])
    frontend_router.include_router(businesses_router, tags=["frontend-businesses"])
    
    return frontend_router

# Configurar las rutas
setup_frontend_routes()