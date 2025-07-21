from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

from ..database import get_database
from ..models.user import User
from ..services.view_service import ViewService
from ..services.api_service import ApiService
from ..utils.helpers import parse_filter_string

logger = logging.getLogger(__name__)

class DashboardService:
    """Servicio para generar datos del dashboard dinámicamente"""
    
    def __init__(self):
        self.db = get_database()
        self.view_service = ViewService()
        self.api_service = ApiService()
    
    async def get_dashboard_data(
        self, 
        business_id: str, 
        vista: str, 
        user: User
    ) -> Dict[str, Any]:
        """Obtener datos completos del dashboard"""
        
        # Obtener configuración de la vista
        view_config = await self.view_service.get_view_config_for_user(
            business_id, vista, user
        )
        
        if not view_config:
            return {"error": "Vista no encontrada o sin permisos"}
        
        dashboard_data = {
            "business_id": business_id,
            "vista": vista,
            "layout": view_config["configuracion"]["layout"],
            "navegacion": view_config["configuracion"]["navegacion"],
            "componentes": []
        }
        
        # Generar datos para cada componente
        for component_config in view_config["configuracion"]["componentes"]:
            component_data = await self._generate_component_data(
                business_id, component_config, user
            )
            dashboard_data["componentes"].append(component_data)
        
        return dashboard_data
    
    async def _generate_component_data(
        self, 
        business_id: str, 
        component_config: Dict[str, Any], 
        user: User
    ) -> Dict[str, Any]:
        """Generar datos para un componente específico"""
        
        component_type = component_config["tipo"]
        config = component_config["configuracion"]
        
        try:
            if component_type == "stats_card":
                return await self._generate_stats_card(business_id, config)
            elif component_type == "chart":
                return await self._generate_chart_data(business_id, config)
            elif component_type == "data_table":
                return await self._generate_table_data(business_id, config, user)
            else:
                return {
                    "id": component_config["id"],
                    "tipo": component_type,
                    "error": f"Tipo de componente no soportado: {component_type}"
                }
        except Exception as e:
            logger.error(f"Error generando datos para componente {component_config['id']}: {e}")
            return {
                "id": component_config["id"],
                "tipo": component_type,
                "error": str(e)
            }
    
    async def _generate_stats_card(
        self, 
        business_id: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generar datos para tarjeta de estadísticas"""
        
        entidad = config.get("entidad")
        operacion = config.get("operacion", "count")
        filtro = config.get("filtro")
        
        if not entidad:
            return {"error": "Entidad no especificada"}
        
        # Por ahora devolvemos datos mock
        # TODO: Implementar consulta real a API externa
        mock_value = 150 if operacion == "count" else 1250.50
        
        return {
            "titulo": config.get("titulo", "Sin título"),
            "valor": mock_value,
            "icono": config.get("icono"),
            "color": config.get("color", "primary"),
            "tendencia": {
                "porcentaje": 12.5,
                "direccion": "up"
            }
        }
    
    async def _generate_chart_data(
        self, 
        business_id: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generar datos para gráficos"""
        
        # Datos mock para gráficos
        mock_data = [
            {"fecha": "2025-01", "valor": 45},
            {"fecha": "2025-02", "valor": 52},
            {"fecha": "2025-03", "valor": 48},
            {"fecha": "2025-04", "valor": 61},
            {"fecha": "2025-05", "valor": 55}
        ]
        
        return {
            "titulo": config.get("titulo", "Gráfico"),
            "tipo_grafico": config.get("tipo_grafico", "line"),
            "datos": mock_data,
            "colores": config.get("colores", ["#3b82f6"])
        }
    
    async def _generate_table_data(
        self, 
        business_id: str, 
        config: Dict[str, Any], 
        user: User
    ) -> Dict[str, Any]:
        """Generar datos para tablas"""
        
        entidad = config.get("entidad")
        columnas_visibles = config.get("columnas_visibles", [])
        
        # Datos mock para tabla
        mock_data = [
            {
                "id": 1,
                "nombre": "Cliente 1",
                "telefono": "+54911123456",
                "plan_velocidad": "100MB",
                "activo": True
            },
            {
                "id": 2,
                "nombre": "Cliente 2", 
                "telefono": "+54911654321",
                "plan_velocidad": "50MB",
                "activo": True
            }
        ]
        
        return {
            "entidad": entidad,
            "columnas": columnas_visibles,
            "datos": mock_data,
            "total": len(mock_data),
            "paginacion": config.get("paginacion", {"items_per_page": 25}),
            "acciones": config.get("acciones", {})
        }