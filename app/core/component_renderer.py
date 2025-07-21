# ================================
# app/core/component_renderer.py
# ================================

from typing import Dict, Any, List, Optional
import logging

from ..models.view import ComponenteVista
from ..models.user import User
from ..services.api_service import ApiService
from ..services.dynamic_crud_service import DynamicCrudService
from ..utils.helpers import parse_filter_string

logger = logging.getLogger(__name__)

class ComponentRenderer:
    """Renderizador de componentes dinámicos para vistas"""
    
    def __init__(self):
        self.api_service = ApiService()
        self.crud_service = DynamicCrudService()
    
    async def render_component(
        self,
        business_id: str,
        component: ComponenteVista,
        user: User,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Renderizar un componente específico"""
        
        component_type = component.tipo
        config = component.configuracion
        
        try:
            # Verificar permisos del componente
            if not self._check_component_permission(component, user):
                return {
                    "id": component.id,
                    "tipo": component_type,
                    "error": "Sin permisos para ver este componente"
                }
            
            # Renderizar según tipo
            if component_type == "stats_card":
                data = await self._render_stats_card(business_id, config, user)
            elif component_type == "chart":
                data = await self._render_chart(business_id, config, user)
            elif component_type == "data_table":
                data = await self._render_data_table(business_id, config, user, context)
            elif component_type == "form":
                data = await self._render_form(business_id, config, user)
            elif component_type == "metric_card":
                data = await self._render_metric_card(business_id, config, user)
            elif component_type == "activity_feed":
                data = await self._render_activity_feed(business_id, config, user)
            elif component_type == "progress_bar":
                data = await self._render_progress_bar(business_id, config, user)
            else:
                data = {"error": f"Tipo de componente no soportado: {component_type}"}
            
            # Agregar metadatos del componente
            return {
                "id": component.id,
                "tipo": component_type,
                "posicion": component.posicion.dict(),
                "configuracion": config.dict() if hasattr(config, 'dict') else config,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error renderizando componente {component.id}: {e}")
            return {
                "id": component.id,
                "tipo": component_type,
                "error": str(e)
            }
    
    async def _render_stats_card(
        self,
        business_id: str,
        config: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Renderizar tarjeta de estadísticas"""
        
        entidad = config.get("entidad")
        operacion = config.get("operacion", "count")
        filtro = config.get("filtro")
        
        if not entidad:
            return {"error": "Entidad no especificada"}
        
        try:
            # Obtener datos de la entidad
            crud_generator = DynamicCrudGenerator()
            
            # Para estadísticas, obtenemos todos los datos (sin paginación)
            result = await crud_generator.list_entities(
                business_id=business_id,
                entity_name=entidad,
                user=user,
                page=1,
                per_page=1000,  # Límite alto para estadísticas
                filters=filtro
            )
            
            items = result.get("items", [])
            
            # Calcular valor según operación
            if operacion == "count":
                valor = len(items)
            elif operacion == "sum":
                campo = config.get("campo_suma")
                if campo:
                    valor = sum(item.get(campo, 0) for item in items if isinstance(item.get(campo), (int, float)))
                else:
                    valor = 0
            elif operacion == "avg":
                campo = config.get("campo_promedio")
                if campo:
                    valores = [item.get(campo, 0) for item in items if isinstance(item.get(campo), (int, float))]
                    valor = sum(valores) / len(valores) if valores else 0
                else:
                    valor = 0
            else:
                valor = len(items)
            
            # Calcular tendencia (comparar con período anterior)
            tendencia = await self._calculate_trend(business_id, entidad, filtro, operacion, config)
            
            return {
                "titulo": config.get("titulo", "Estadística"),
                "valor": valor,
                "formato": config.get("formato", "number"),
                "icono": config.get("icono"),
                "color": config.get("color", "primary"),
                "tendencia": tendencia
            }
            
        except Exception as e:
            logger.error(f"Error en stats_card: {e}")
            return {"error": str(e)}
    
    async def _render_chart(
        self,
        business_id: str,
        config: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Renderizar gráfico"""
        
        entidades = config.get("entidades", [])
        tipo_grafico = config.get("tipo_grafico", "line")
        
        if not entidades:
            return {"error": "No se especificaron entidades para el gráfico"}
        
        try:
            chart_data = []
            crud_generator = DynamicCrudGenerator()
            
            for entidad_config in entidades:
                entidad_name = entidad_config.get("entidad")
                campo_fecha = entidad_config.get("campo_fecha", "created_at")
                operacion = entidad_config.get("operacion", "count_by_month")
                
                # Obtener datos de la entidad
                result = await crud_generator.list_entities(
                    business_id=business_id,
                    entity_name=entidad_name,
                    user=user,
                    page=1,
                    per_page=1000
                )
                
                items = result.get("items", [])
                
                # Procesar datos para el gráfico
                if operacion == "count_by_month":
                    processed_data = self._group_by_month(items, campo_fecha)
                elif operacion == "count_by_day":
                    processed_data = self._group_by_day(items, campo_fecha)
                else:
                    processed_data = items
                
                chart_data.append({
                    "name": entidad_config.get("label", entidad_name),
                    "data": processed_data
                })
            
            return {
                "titulo": config.get("titulo", "Gráfico"),
                "tipo_grafico": tipo_grafico,
                "datos": chart_data,
                "colores": config.get("colores", ["#3b82f6"]),
                "config_adicional": config.get("config_adicional", {})
            }
            
        except Exception as e:
            logger.error(f"Error en chart: {e}")
            return {"error": str(e)}
    
    async def _render_data_table(
        self,
        business_id: str,
        config: Dict[str, Any],
        user: User,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Renderizar tabla de datos"""
        
        entidad = config.get("entidad")
        if not entidad:
            return {"error": "Entidad no especificada"}
        
        try:
            # Obtener parámetros de contexto (paginación, filtros, etc.)
            page = context.get("page", 1) if context else 1
            per_page = config.get("paginacion", {}).get("items_per_page", 25)
            filters = context.get("filters") if context else None
            sort_by = context.get("sort_by") if context else None
            sort_order = context.get("sort_order", "asc") if context else "asc"
            
            # Obtener datos
            crud_generator = DynamicCrudGenerator()
            result = await crud_generator.list_entities(
                business_id=business_id,
                entity_name=entidad,
                user=user,
                page=page,
                per_page=per_page,
                filters=filters,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            return {
                "entidad": entidad,
                "columnas": config.get("columnas_visibles", []),
                "datos": result.get("items", []),
                "total": result.get("total", 0),
                "page": page,
                "per_page": per_page,
                "pages": (result.get("total", 0) + per_page - 1) // per_page,
                "acciones": config.get("acciones", {}),
                "filtros_config": config.get("filtros", []),
                "ordenamiento": config.get("ordenamiento", {})
            }
            
        except Exception as e:
            logger.error(f"Error en data_table: {e}")
            return {"error": str(e)}
    
    async def _render_form(
        self,
        business_id: str,
        config: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Renderizar formulario dinámico"""
        
        entidad = config.get("entidad")
        if not entidad:
            return {"error": "Entidad no especificada"}
        
        try:
            # Obtener configuración de la entidad para los campos
            crud_generator = DynamicCrudGenerator()
            entity_config = await crud_generator.get_entity_config(business_id, entidad)
            
            # Filtrar campos según permisos
            campos_visibles = []
            for campo_config in entity_config.configuracion.get("campos", []):
                editable_roles = campo_config.get("editable_roles", ["admin"])
                if "*" in editable_roles or user.rol in editable_roles:
                    campos_visibles.append(campo_config)
            
            return {
                "entidad": entidad,
                "campos": campos_visibles,
                "modo": config.get("modo", "create"),  # create, edit, view
                "titulo": config.get("titulo", f"Formulario {entidad}"),
                "acciones": config.get("acciones", ["guardar", "cancelar"])
            }
            
        except Exception as e:
            logger.error(f"Error en form: {e}")
            return {"error": str(e)}
    
    def _check_component_permission(self, component: ComponenteVista, user: User) -> bool:
        """Verificar permisos para ver un componente"""
        permisos_rol = component.permisos_rol
        return "*" in permisos_rol or user.rol in permisos_rol
    
    def _group_by_month(self, items: List[Dict[str, Any]], date_field: str) -> List[Dict[str, Any]]:
        """Agrupar items por mes"""
        from collections import defaultdict
        from datetime import datetime
        
        monthly_counts = defaultdict(int)
        
        for item in items:
            date_value = item.get(date_field)
            if date_value:
                try:
                    # Convertir a datetime si es string
                    if isinstance(date_value, str):
                        date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    else:
                        date_obj = date_value
                    
                    month_key = date_obj.strftime("%Y-%m")
                    monthly_counts[month_key] += 1
                except:
                    continue
        
        # Convertir a formato para gráficos
        return [
            {"fecha": month, "valor": count}
            for month, count in sorted(monthly_counts.items())
        ]
    
    def _group_by_day(self, items: List[Dict[str, Any]], date_field: str) -> List[Dict[str, Any]]:
        """Agrupar items por día"""
        from collections import defaultdict
        from datetime import datetime
        
        daily_counts = defaultdict(int)
        
        for item in items:
            date_value = item.get(date_field)
            if date_value:
                try:
                    if isinstance(date_value, str):
                        date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    else:
                        date_obj = date_value
                    
                    day_key = date_obj.strftime("%Y-%m-%d")
                    daily_counts[day_key] += 1
                except:
                    continue
        
        return [
            {"fecha": day, "valor": count}
            for day, count in sorted(daily_counts.items())
        ]
    
    async def _calculate_trend(
        self,
        business_id: str,
        entidad: str,
        filtro: Optional[str],
        operacion: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calcular tendencia comparativa"""
        # TODO: Implementar cálculo de tendencia real
        # Por ahora retornamos datos mock
        import random
        
        return {
            "porcentaje": round(random.uniform(-20, 30), 1),
            "direccion": random.choice(["up", "down", "neutral"]),
            "periodo": "vs mes anterior"
        }