# ================================
# app/routers/business/advanced_dashboard.py
# ================================

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...auth.dependencies import get_current_business_user
from ...models.user import User
from ...models.responses import BaseResponse
from ...services.dashboard_service import AdvancedDashboardService
from ...services.advanced_analytics_service import AdvancedAnalyticsService
from ...services.cache_service import CacheService

router = APIRouter()

@router.get("/{business_id}/advanced")
async def get_advanced_dashboard(
    business_id: str,
    vista: str = Query("dashboard_principal", description="Nombre de la vista"),
    refresh_cache: bool = Query(False, description="Forzar actualización de cache"),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener dashboard avanzado con datos reales"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        dashboard_service = AdvancedDashboardService()
        dashboard_data = await dashboard_service.get_complete_dashboard_data(
            business_id=business_id,
            vista=vista,
            user=current_user,
            refresh_cache=refresh_cache
        )
        
        return BaseResponse(
            data=dashboard_data,
            message="Dashboard avanzado generado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{business_id}/component/{component_id}/realtime")
async def get_component_realtime_data(
    business_id: str,
    component_id: str,
    current_user: User = Depends(get_current_business_user)
):
    """Obtener datos en tiempo real de un componente específico"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        dashboard_service = AdvancedDashboardService()
        
        # Obtener configuración del componente
        view_config = await dashboard_service.view_service.get_view_config(business_id, "dashboard_principal")
        if not view_config:
            raise HTTPException(status_code=404, detail="Vista no encontrada")
        
        # Buscar el componente
        component_config = None
        for comp in view_config.configuracion.componentes:
            if comp.id == component_id:
                component_config = comp.dict()
                break
        
        if not component_config:
            raise HTTPException(status_code=404, detail="Componente no encontrado")
        
        # Generar datos del componente
        integration_data = await dashboard_service._get_integration_data(business_id)
        component_data = await dashboard_service._generate_advanced_component_data(
            business_id, component_config, current_user, integration_data
        )
        
        return BaseResponse(
            data=component_data,
            message="Datos de componente actualizados"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{business_id}/analytics/report")
async def generate_analytics_report(
    business_id: str,
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$", description="Período del reporte"),
    include_predictions: bool = Query(False, description="Incluir predicciones"),
    format: str = Query("json", regex="^(json|pdf)$", description="Formato del reporte"),
    current_user: User = Depends(get_current_business_user)
):
    """Generar reporte avanzado de analytics"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        analytics_service = AdvancedAnalyticsService()
        report = await analytics_service.generate_business_report(
            business_id=business_id,
            period=period,
            include_predictions=include_predictions,
            user=current_user
        )
        
        if not report["success"]:
            raise HTTPException(status_code=400, detail=report["error"])
        
        if format == "pdf":
            # TODO: Implementar generación de PDF
            return BaseResponse(
                data={"pdf_url": f"/reports/{business_id}/latest.pdf"},
                message="Reporte PDF generado (funcionalidad pendiente)"
            )
        
        return BaseResponse(
            data=report["report"],
            message=f"Reporte de {period} generado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{business_id}/cache/refresh")
async def refresh_dashboard_cache(
    business_id: str,
    background_tasks: BackgroundTasks,
    components: Optional[List[str]] = Query(None, description="Componentes específicos a refrescar"),
    current_user: User = Depends(get_current_business_user)
):
    """Refrescar cache del dashboard"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        cache_service = CacheService()
        
        if components:
            # Refrescar componentes específicos
            for component_id in components:
                pattern = f"component_{business_id}_{component_id}_*"
                await cache_service.clear_pattern(pattern)
        else:
            # Refrescar todo el dashboard
            pattern = f"dashboard_{business_id}_*"
            cleared_keys = await cache_service.clear_pattern(pattern)
        
        # Regenerar cache en background
        background_tasks.add_task(
            _regenerate_dashboard_cache,
            business_id,
            current_user
        )
        
        return BaseResponse(
            data={"refreshed": True, "components": components or "all"},
            message="Cache refrescado, regenerando en background"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{business_id}/integrations/status")
async def get_integrations_status(
    business_id: str,
    current_user: User = Depends(get_current_business_user)
):
    """Obtener estado de todas las integraciones"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        dashboard_service = AdvancedDashboardService()
        integration_data = await dashboard_service._get_integration_data(business_id)
        
        return BaseResponse(
            data=integration_data,
            message="Estado de integraciones obtenido"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{business_id}/performance/metrics")
async def get_performance_metrics(
    business_id: str,
    hours: int = Query(24, ge=1, le=168, description="Horas hacia atrás para métricas"),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener métricas de rendimiento del sistema"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        # Métricas simuladas por ahora
        # TODO: Implementar métricas reales desde logs y monitoring
        
        metrics = {
            "api_performance": {
                "avg_response_time_ms": 150,
                "requests_per_hour": 120,
                "error_rate_percent": 0.5,
                "cache_hit_rate_percent": 85
            },
            "database_performance": {
                "avg_query_time_ms": 25,
                "connections_active": 8,
                "slow_queries_count": 2
            },
            "integration_performance": {
                "whatsapp_response_time_ms": 200,
                "n8n_execution_success_rate": 95,
                "external_apis_uptime_percent": 99.5
            },
            "system_resources": {
                "cpu_usage_percent": 15,
                "memory_usage_percent": 45,
                "disk_usage_percent": 30
            }
        }
        
        return BaseResponse(
            data=metrics,
            message=f"Métricas de {hours}h obtenidas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Función auxiliar para background task
async def _regenerate_dashboard_cache(business_id: str, user: User):
    """Regenerar cache del dashboard en background"""
    try:
        dashboard_service = AdvancedDashboardService()
        await dashboard_service.get_complete_dashboard_data(
            business_id=business_id,
            vista="dashboard_principal",
            user=user,
            refresh_cache=True
        )
    except Exception as e:
        logger.error(f"Error regenerando cache para {business_id}: {e}")

# ================================
# app/routers/business/whatsapp_attention.py
# ================================

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List

from ...auth.dependencies import get_current_business_user
from ...models.user import User
from ...models.responses import BaseResponse
from ...services.whatsapp_human_attention_service import WhatsAppHumanAttentionService

router = APIRouter()

@router.get("/{business_id}/conversations")
async def get_active_conversations(
    business_id: str,
    status: Optional[str] = Query(None, regex="^(pendiente|atendiendo|finalizado)$"),
    area: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener conversaciones de WhatsApp"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        attention_service = WhatsAppHumanAttentionService()
        
        # Construir filtro
        filter_query = {"business_id": business_id}
        if status:
            filter_query["conversacion.estado"] = status
        if area:
            filter_query["conversacion.area_solicitada"] = area
        
        # Obtener conversaciones
        cursor = attention_service.db.atencion_humana.find(filter_query).sort("created_at", -1).limit(limit)
        conversations = await cursor.to_list(length=None)
        
        # Formatear para respuesta
        formatted_conversations = []
        for conv in conversations:
            formatted_conversations.append({
                "id": str(conv["_id"]),
                "whatsapp_numero": conv["whatsapp_numero"],
                "cliente": conv["cliente_externo"]["datos_cache"],
                "estado": conv["conversacion"]["estado"],
                "area": conv["conversacion"]["area_solicitada"],
                "usuario_atendiendo": conv["conversacion"].get("usuario_atendiendo"),
                "fecha_inicio": conv["conversacion"]["fecha_inicio"],
                "ultimo_mensaje": conv["conversacion"]["mensajes_contexto"][-1]["mensaje"] if conv["conversacion"]["mensajes_contexto"] else "",
                "created_at": conv["created_at"]
            })
        
        return BaseResponse(
            data={
                "conversations": formatted_conversations,
                "total": len(formatted_conversations),
                "filters": {"status": status, "area": area}
            },
            message=f"Se encontraron {len(formatted_conversations)} conversaciones"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{business_id}/conversations/{session_id}/take")
async def take_conversation(
    business_id: str,
    session_id: str,
    current_user: User = Depends(get_current_business_user)
):
    """Tomar una conversación para atender"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        attention_service = WhatsAppHumanAttentionService()
        result = await attention_service.take_conversation(session_id, current_user)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return BaseResponse(
            data=result,
            message="Conversación tomada exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{business_id}/conversations/{session_id}/send")
async def send_message(
    business_id: str,
    session_id: str,
    message_data: Dict[str, str],
    current_user: User = Depends(get_current_business_user)
):
    """Enviar mensaje a cliente"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if "mensaje" not in message_data:
        raise HTTPException(status_code=400, detail="Campo 'mensaje' requerido")
    
    try:
        attention_service = WhatsAppHumanAttentionService()
        result = await attention_service.send_message_to_client(
            session_id, message_data["mensaje"], current_user
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return BaseResponse(
            data=result,
            message="Mensaje enviado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{business_id}/conversations/{session_id}/close")
async def close_conversation(
    business_id: str,
    session_id: str,
    close_data: Dict[str, Any],
    current_user: User = Depends(get_current_business_user)
):
    """Finalizar conversación"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        attention_service = WhatsAppHumanAttentionService()
        result = await attention_service.close_conversation(
            session_id=session_id,
            user=current_user,
            notas=close_data.get("notas"),
            create_ticket=close_data.get("create_ticket", False)
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return BaseResponse(
            data=result,
            message="Conversación finalizada exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{business_id}/webhook/incoming")
async def handle_incoming_message(
    business_id: str,
    webhook_data: Dict[str, Any]
):
    """Manejar mensaje entrante de WhatsApp (webhook)"""
    
    try:
        attention_service = WhatsAppHumanAttentionService()
        result = await attention_service.process_incoming_message(
            business_id, webhook_data
        )
        
        return BaseResponse(
            data=result,
            message="Mensaje procesado"
        )
        
    except Exception as e:
        # No devolver error 400 para webhooks, solo loggear
        logger.error(f"Error procesando webhook WhatsApp: {e}")
        return BaseResponse(
            data={"success": False, "error": str(e)},
            message="Error procesando mensaje"
        )

@router.get("/{business_id}/stats")
async def get_whatsapp_stats(
    business_id: str,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener estadísticas de WhatsApp"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        attention_service = WhatsAppHumanAttentionService()
        
        # Obtener conversaciones del período
        cursor = attention_service.db.atencion_humana.find({
            "business_id": business_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        conversations = await cursor.to_list(length=None)
        
        # Calcular estadísticas
        total_conversations = len(conversations)
        by_status = {"pendiente": 0, "atendiendo": 0, "finalizado": 0}
        by_area = {}
        
        for conv in conversations:
            estado = conv["conversacion"]["estado"]
            area = conv["conversacion"]["area_solicitada"]
            
            by_status[estado] = by_status.get(estado, 0) + 1
            by_area[area] = by_area.get(area, 0) + 1
        
        stats = {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_conversations": total_conversations,
            "by_status": by_status,
            "by_area": by_area,
            "resolution_rate": round((by_status["finalizado"] / total_conversations * 100) if total_conversations > 0 else 0, 1),
            "daily_average": round(total_conversations / days, 1)
        }
        
        return BaseResponse(
            data=stats,
            message=f"Estadísticas de {days} días obtenidas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))