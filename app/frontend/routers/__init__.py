# ================================
# app/frontend/routers/__init__.py (ACTUALIZADO)
# ================================

"""Routers del frontend con Business Types y Businesses"""

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

# NUEVOS ROUTERS - Business Types y Businesses
try:
    from .business_types import router as business_types_router
    frontend_router.include_router(business_types_router, tags=["frontend-business-types"])
    print("✅ Business Types router incluido")
except Exception as e:
    print(f"⚠️ Error incluyendo business types router: {e}")

try:
    from .business import router as businesses_router
    frontend_router.include_router(businesses_router, tags=["frontend-businesses"])
    print("✅ Businesses router incluido")
except Exception as e:
    print(f"⚠️ Error incluyendo businesses router: {e}")

print("🎯 Frontend routers configurados exitosamente")