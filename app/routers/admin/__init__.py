
from fastapi import APIRouter
from . import business_types, business_instances, api_configs

router = APIRouter()

# Incluir todos los sub-routers
router.include_router(business_types.router, prefix="/business-types", tags=["admin-business-types"])
router.include_router(business_instances.router, prefix="/businesses", tags=["admin-businesses"])
router.include_router(api_configs.router, prefix="/api", tags=["admin-api"])

# Endpoint raíz del admin
@router.get("/")
async def admin_root():
    """Endpoint raíz del módulo admin"""
    return {
        "success": True,
        "message": "CMS Dinámico - Panel de Administración",
        "available_endpoints": [
            "/business-types - CRUD de Business Types",
            "/businesses - CRUD de Business Instances", 
            "/api/configurations - CRUD de API Configurations",
            "/api/components - CRUD de Dynamic Components",
            "/stats - Estadísticas del sistema",
            "/logs/recent - Logs recientes",
            "/initialize - Inicializar datos por defecto"
        ]
    }