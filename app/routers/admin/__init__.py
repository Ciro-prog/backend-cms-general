from fastapi import APIRouter
from . import business_types, business_instances, entities, views, api_configs

router = APIRouter()

# Incluir todos los sub-routers
router.include_router(business_types.router, prefix="/business-types", tags=["business-types"])
router.include_router(business_instances.router, prefix="/businesses", tags=["businesses"])
router.include_router(entities.router, prefix="/entities", tags=["entities"])
router.include_router(views.router, prefix="/views", tags=["views"])
router.include_router(api_configs.router, prefix="/api-configs", tags=["api-configs"])
