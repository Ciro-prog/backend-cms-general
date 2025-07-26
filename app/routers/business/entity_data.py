# ================================
# app/routers/business/entity_data.py - BÁSICO
# ================================

from fastapi import APIRouter, Query
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/business", tags=["Entity Data"])

@router.get("/{business_id}/entity-data/{entity_name}")
async def get_entity_data(
    business_id: str,
    entity_name: str,
    limit: int = Query(25, ge=1, le=100),
    refresh_cache: bool = Query(False),
    format: str = Query("json", regex="^(json|table|cards|stats)$")
):
    """Obtener datos de una entidad - versión básica"""
    
    try:
        sample_data = {
            "entity_name": entity_name,
            "business_id": business_id,
            "items": [
                {
                    "id": f"{entity_name}_{i}",
                    "name": f"Registro {i} de {entity_name}",
                    "status": "active" if i % 2 == 0 else "inactive",
                    "created_at": datetime.utcnow().isoformat()
                }
                for i in range(1, min(limit + 1, 6))
            ],
            "total_records": min(limit, 5),
            "from_cache": False,
            "last_updated": datetime.utcnow().isoformat(),
            "data_source": "demo"
        }
        
        logger.info(f"📊 Datos obtenidos (simulado): {entity_name} - {len(sample_data['items'])} registros")
        
        return {
            "success": True,
            "data": sample_data,
            "message": f"Datos obtenidos: {len(sample_data['items'])} registros (simulado)"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de entidad {entity_name}: {e}")
        return {
            "success": False,
            "data": {"error": str(e)},
            "message": f"Error obteniendo datos: {str(e)}"
        }

logger.info("📊 Router Entity Data básico configurado")
