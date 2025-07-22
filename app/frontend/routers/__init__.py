# ================================
# app/frontend/routers/__init__.py - CON DASHBOARD
# ================================

"""Routers del frontend"""

from fastapi import APIRouter

# Router principal del frontend
frontend_router = APIRouter()

# Importar routers disponibles
try:
    from .auth import router as auth_router
    frontend_router.include_router(auth_router, tags=["frontend-auth"])
    print("✅ Auth router incluido")
except Exception as e:
    print(f"⚠️ Error incluyendo auth router: {e}")

try:
    from .dashboard import router as dashboard_router
    frontend_router.include_router(dashboard_router, tags=["frontend-dashboard"])
    print("✅ Dashboard router incluido")
except Exception as e:
    print(f"⚠️ Error incluyendo dashboard router: {e}")
