
from fastapi import APIRouter
from . import entities, dashboard, analytics

router = APIRouter()

router.include_router(entities.router, prefix="/entities", tags=["business-entities"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])