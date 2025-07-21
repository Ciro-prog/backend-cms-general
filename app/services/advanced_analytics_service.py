# ================================
# app/services/advanced_analytics_service.py
# ================================

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from ..database import get_database
from ..models.user import User
from ..services.api_service import ApiService
from ..services.cache_service import CacheService
from ..services.waha_service import WAHAService
from ..services.n8n_service import N8NService
from ..core.dynamic_crud import DynamicCrudGenerator

logger = logging.getLogger(__name__)

class AdvancedAnalyticsService:
    """Servicio de analytics y reportes avanzados"""
    
    def __init__(self):
        self.db = get_database()
        self.api_service = ApiService()
        self.cache_service = CacheService()
        self.waha_service = WAHAService()
        self.n8n_service = N8NService()
        self.crud_generator = DynamicCrudGenerator()
    
    # ================================
    # REPORTES PRINCIPALES
    # ================================
    
    async def generate_business_report(
        self, 
        business_id: str, 
        period: str = "30d",
        include_predictions: bool = False,
        user: User = None
    ) -> Dict[str, Any]:
        """Generar reporte completo del business"""
        
        try:
            # Calcular fechas del período
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, period)
            
            # Obtener datos en paralelo
            tasks = [
                self._get_business_overview(business_id, start_date, end_date),
                self._get_entities_analytics(business_id, start_date, end_date, user),
                self._get_integrations_analytics(business_id, start_date, end_date),
                self._get_user_activity_analytics(business_id, start_date, end_date),
                self._get_performance_metrics(business_id, start_date, end_date)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            overview, entities, integrations, user_activity, performance = results
            
            report = {
                "business_id": business_id,
                "period": {
                    "range": period,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "generated_at": datetime.utcnow().isoformat(),
                "overview": overview if not isinstance(overview, Exception) else {"error": str(overview)},
                "entities": entities if not isinstance(entities, Exception) else {"error": str(entities)},
                "integrations": integrations if not isinstance(integrations, Exception) else {"error": str(integrations)},
                "user_activity": user_activity if not isinstance(user_activity, Exception) else {"error": str(user_activity)},
                "performance": performance if not isinstance(performance, Exception) else {"error": str(performance)}
            }
            
            # Agregar predicciones si se solicita
            if include_predictions:
                predictions = await self._generate_predictions(business_id, report)
                report["predictions"] = predictions
            
            # Generar insights automáticos
            report["insights"] = await self._generate_insights(report)
            
            # Calcular score general
            report["health_score"] = self._calculate_health_score(report)
            
            return {
                "success": True,
                "report": report,
                "summary": self._generate_report_summary(report)
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte de business: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_business_overview(
        self, 
        business_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Obtener vista general del business"""
        
        # Obtener información del business
        business_doc = await self.db.business_instances.find_one({"business_id": business_id})
        if not business_doc:
            return {"error": "Business no encontrado"}
        
        # Obtener configuraciones
        entities_count = await self.db.entities_config.count_documents({"business_id": business_id})
        views_count = await self.db.views_config.count_documents({"business_id": business_id})
        apis_count = await self.db.api_configurations.count_documents({"business_id": business_id, "activa": True})
        
        # Obtener actividad de usuarios
        users_count = await self.db.users.count_documents({"business_id": business_id, "activo": True})
        active_users = await self.db.users.count_documents({
            "business_id": business_id,
            "activo": True,
            "ultimo_acceso": {"$gte": start_date}
        })
        
        return {
            "business_info": {
                "name": business_doc.get("nombre"),
                "type": business_doc.get("tipo_base"),
                "active": business_doc.get("activo", True),
                "subscription": business_doc.get("suscripcion", {})
            },
            "configuration": {
                "entities_configured": entities_count,
                "views_configured": views_count,
                "apis_connected": apis_count,
                "components_active": len(business_doc.get("configuracion", {}).get("componentes_activos", []))
            },
            "users": {
                "total_users": users_count,
                "active_users_period": active_users,
                "activity_rate": round((active_users / users_count * 100) if users_count > 0 else 0, 1)
            }
        }
    
    async def _get_entities_analytics(
        self, 
        business_id: str, 
        start_date: datetime, 
        end_date: datetime,
        user: User
    ) -> Dict[str, Any]:
        """Analytics de entidades del business"""
        
        if not user:
            return {"error": "Usuario requerido para analytics de entidades"}
        
        # Obtener entidades configuradas
        entities_cursor = self.db.entities_config.find({"business_id": business_id})
        entities_configs = await entities_cursor.to_list(length=None)
        
        entities_analytics = {}
        
        for entity_config in entities_configs:
            entity_name = entity_config["entidad"]
            
            try:
                # Obtener datos de la entidad
                result = await self.crud_generator.list_entities(
                    business_id=business_id,
                    entity_name=entity_name,
                    user=user,
                    page=1,
                    per_page=1000
                )
                
                items = result.get("items", [])
                
                # Analizar datos
                entity_analytics = self._analyze_entity_data(items, start_date, end_date)
                entities_analytics[entity_name] = entity_analytics
                
            except Exception as e:
                logger.error(f"Error analizando entidad {entity_name}: {e}")
                entities_analytics[entity_name] = {"error": str(e)}
        
        return {
            "entities_analyzed": len(entities_configs),
            "entities": entities_analytics,
            "summary": self._summarize_entities_analytics(entities_analytics)
        }
    
    def _analyze_entity_data(
        self, 
        items: List[Dict[str, Any]], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analizar datos de una entidad específica"""
        
        total_items = len(items)
        
        # Analizar por fechas si hay campo de fecha
        date_fields = ["created_at", "fecha_creacion", "date", "timestamp"]
        date_field = None
        
        for field in date_fields:
            if items and field in items[0]:
                date_field = field
                break
        
        period_items = []
        growth_data = []
        
        if date_field:
            # Filtrar items del período
            for item in items:
                item_date_str = item.get(date_field)
                if item_date_str:
                    try:
                        if isinstance(item_date_str, str):
                            item_date = datetime.fromisoformat(item_date_str.replace('Z', '+00:00'))
                        else:
                            item_date = item_date_str
                        
                        if start_date <= item_date <= end_date:
                            period_items.append(item)
                    except:
                        continue
            
            # Calcular crecimiento por día
            growth_data = self._calculate_daily_growth(items, date_field, start_date, end_date)
        
        # Analizar campos numéricos
        numeric_analytics = self._analyze_numeric_fields(items)
        
        # Analizar campos categóricos
        categorical_analytics = self._analyze_categorical_fields(items)
        
        return {
            "total_records": total_items,
            "period_records": len(period_items),
            "growth_rate": self._calculate_growth_rate(growth_data),
            "daily_growth": growth_data,
            "numeric_fields": numeric_analytics,
            "categorical_fields": categorical_analytics,
            "data_quality": self._assess_data_quality(items)
        }
    
    def _analyze_numeric_fields(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizar campos numéricos"""
        
        if not items:
            return {}
        
        numeric_fields = {}
        
        # Identificar campos numéricos
        for item in items[:10]:  # Analizar primeros 10 items
            for field, value in item.items():
                if isinstance(value, (int, float)) and field not in numeric_fields:
                    numeric_fields[field] = []
        
        # Recopilar valores
        for item in items:
            for field in numeric_fields.keys():
                value = item.get(field)
                if isinstance(value, (int, float)):
                    numeric_fields[field].append(value)
        
        # Calcular estadísticas
        analytics = {}
        for field, values in numeric_fields.items():
            if values:
                analytics[field] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": round(statistics.mean(values), 2),
                    "median": round(statistics.median(values), 2),
                    "std_dev": round(statistics.stdev(values), 2) if len(values) > 1 else 0,
                    "sum": sum(values)
                }
        
        return analytics
    
    def _analyze_categorical_fields(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizar campos categóricos"""
        
        if not items:
            return {}
        
        categorical_analytics = {}
        
        # Identificar campos categóricos
        for item in items[:50]:  # Analizar primeros 50 items
            for field, value in item.items():
                if isinstance(value, str) and field not in categorical_analytics:
                    categorical_analytics[field] = defaultdict(int)
        
        # Contar valores
        for item in items:
            for field in categorical_analytics.keys():
                value = item.get(field)
                if isinstance(value, str):
                    categorical_analytics[field][value] += 1
        
        # Convertir a formato de análisis
        analytics = {}
        for field, counts in categorical_analytics.items():
            if counts:
                total = sum(counts.values())
                sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                
                analytics[field] = {
                    "unique_values": len(counts),
                    "most_common": sorted_counts[:5],  # Top 5
                    "distribution": [
                        {"value": value, "count": count, "percentage": round(count/total*100, 1)}
                        for value, count in sorted_counts[:10]
                    ]
                }
        
        return analytics
    
    def _calculate_daily_growth(
        self, 
        items: List[Dict[str, Any]], 
        date_field: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Calcular crecimiento diario"""
        
        daily_counts = defaultdict(int)
        
        for item in items:
            date_str = item.get(date_field)
            if date_str:
                try:
                    if isinstance(date_str, str):
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        date_obj = date_str
                    
                    if start_date <= date_obj <= end_date:
                        day_key = date_obj.strftime("%Y-%m-%d")
                        daily_counts[day_key] += 1
                except:
                    continue
        
        # Convertir a lista ordenada
        growth_data = []
        current_date = start_date
        
        while current_date <= end_date:
            day_key = current_date.strftime("%Y-%m-%d")
            count = daily_counts.get(day_key, 0)
            
            growth_data.append({
                "date": day_key,
                "count": count,
                "cumulative": sum(d["count"] for d in growth_data) + count
            })
            
            current_date += timedelta(days=1)
        
        return growth_data
    
    async def _get_integrations_analytics(
        self, 
        business_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analytics de integraciones"""
        
        try:
            # Analytics de WhatsApp
            whatsapp_analytics = await self._get_whatsapp_analytics(business_id, start_date, end_date)
            
            # Analytics de N8N
            n8n_analytics = await self._get_n8n_analytics(business_id, start_date, end_date)
            
            # Analytics de APIs externas
            apis_analytics = await self._get_apis_analytics(business_id, start_date, end_date)
            
            return {
                "whatsapp": whatsapp_analytics,
                "n8n": n8n_analytics,
                "external_apis": apis_analytics,
                "overall_health": self._calculate_integrations_health([
                    whatsapp_analytics, n8n_analytics, apis_analytics
                ])
            }
            
        except Exception as e:
            logger.error(f"Error en analytics de integraciones: {e}")
            return {"error": str(e)}
    
    async def _get_whatsapp_analytics(
        self, 
        business_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analytics específicos de WhatsApp"""
        
        try:
            # Obtener sesiones de WhatsApp
            sessions = await self.waha_service.get_sessions_for_business(business_id)
            
            # Obtener conversaciones del período
            conversations_cursor = self.db.atencion_humana.find({
                "business_id": business_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
            
            conversations = await conversations_cursor.to_list(length=None)
            
            # Analizar conversaciones
            total_conversations = len(conversations)
            pending_conversations = len([c for c in conversations if c["conversacion"]["estado"] == "pendiente"])
            resolved_conversations = len([c for c in conversations if c["conversacion"]["estado"] == "finalizado"])
            
            # Calcular tiempo promedio de respuesta
            response_times = []
            for conv in conversations:
                if conv["conversacion"]["estado"] == "finalizado":
                    start_time = conv["conversacion"]["fecha_inicio"]
                    end_time = conv["conversacion"].get("fecha_finalizacion")
                    if end_time:
                        duration = (end_time - start_time).total_seconds() / 60  # minutos
                        response_times.append(duration)
            
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            # Analizar por área
            areas_analysis = defaultdict(int)
            for conv in conversations:
                area = conv["conversacion"]["area_solicitada"]
                areas_analysis[area] += 1
            
            return {
                "status": "connected" if sessions else "disconnected",
                "sessions_count": len(sessions) if sessions else 0,
                "conversations": {
                    "total": total_conversations,
                    "pending": pending_conversations,
                    "resolved": resolved_conversations,
                    "resolution_rate": round((resolved_conversations / total_conversations * 100) if total_conversations > 0 else 0, 1)
                },
                "performance": {
                    "avg_response_time_minutes": round(avg_response_time, 1),
                    "daily_conversations": len([c for c in conversations if (datetime.utcnow() - c["created_at"]).days == 0])
                },
                "areas_distribution": dict(areas_analysis),
                "health_score": self._calculate_whatsapp_health_score(sessions, conversations)
            }
            
        except Exception as e:
            logger.error(f"Error en analytics de WhatsApp: {e}")
            return {"error": str(e), "status": "error"}
    
    async def _get_n8n_analytics(
        self, 
        business_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analytics específicos de N8N"""
        
        try:
            # Obtener workflows
            workflows = await self.n8n_service.get_workflows(business_id)
            
            if not workflows:
                return {"status": "disconnected", "error": "No se pudieron obtener workflows"}
            
            active_workflows = [w for w in workflows if w.get("active")]
            
            # Obtener ejecuciones recientes (simulado por ahora)
            total_executions = 0
            successful_executions = 0
            failed_executions = 0
            
            for workflow in workflows:
                # TODO: Obtener ejecuciones reales de N8N
                # Por ahora, simulamos datos
                total_executions += 15
                successful_executions += 12
                failed_executions += 3
            
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            return {
                "status": "connected",
                "workflows": {
                    "total": len(workflows),
                    "active": len(active_workflows),
                    "inactive": len(workflows) - len(active_workflows)
                },
                "executions": {
                    "total": total_executions,
                    "successful": successful_executions,
                    "failed": failed_executions,
                    "success_rate": round(success_rate, 1)
                },
                "health_score": self._calculate_n8n_health_score(workflows, success_rate)
            }
            
        except Exception as e:
            logger.error(f"Error en analytics de N8N: {e}")
            return {"error": str(e), "status": "error"}
    
    # ================================
    # PREDICCIONES Y INSIGHTS
    # ================================
    
    async def _generate_predictions(
        self, 
        business_id: str, 
        report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generar predicciones basadas en datos históricos"""
        
        try:
            predictions = {}
            
            # Predicción de crecimiento de entidades
            entities_data = report.get("entities", {}).get("entities", {})
            
            for entity_name, entity_data in entities_data.items():
                if isinstance(entity_data, dict) and "daily_growth" in entity_data:
                    growth_data = entity_data["daily_growth"]
                    if len(growth_data) >= 7:  # Mínimo 7 días de datos
                        prediction = self._predict_entity_growth(growth_data)
                        predictions[f"{entity_name}_growth"] = prediction
            
            # Predicción de carga de WhatsApp
            whatsapp_data = report.get("integrations", {}).get("whatsapp", {})
            if whatsapp_data.get("status") == "connected":
                whatsapp_prediction = self._predict_whatsapp_load(whatsapp_data)
                predictions["whatsapp_load"] = whatsapp_prediction
            
            # Predicción de salud general del sistema
            health_prediction = self._predict_system_health(report)
            predictions["system_health"] = health_prediction
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generando predicciones: {e}")
            return {"error": str(e)}
    
    def _predict_entity_growth(self, growth_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predicción simple de crecimiento de entidad"""
        
        # Usar regresión lineal simple
        recent_days = growth_data[-7:]  # Últimos 7 días
        daily_counts = [day["count"] for day in recent_days]
        
        if not daily_counts:
            return {"error": "Sin datos suficientes"}
        
        # Calcular tendencia
        avg_daily = statistics.mean(daily_counts)
        trend = "stable"
        
        if len(daily_counts) > 1:
            recent_avg = statistics.mean(daily_counts[-3:])  # Últimos 3 días
            older_avg = statistics.mean(daily_counts[:3])    # Primeros 3 días
            
            if recent_avg > older_avg * 1.1:
                trend = "growing"
            elif recent_avg < older_avg * 0.9:
                trend = "declining"
        
        # Predicción para próximos 7 días
        next_week_prediction = avg_daily * 7
        
        return {
            "trend": trend,
            "avg_daily": round(avg_daily, 1),
            "next_week_predicted": round(next_week_prediction),
            "confidence": "medium"
        }
    
    async def _generate_insights(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generar insights automáticos del reporte"""
        
        insights = []
        
        try:
            # Insight sobre actividad de usuarios
            overview = report.get("overview", {})
            users_data = overview.get("users", {})
            
            if users_data.get("activity_rate", 0) < 50:
                insights.append({
                    "type": "warning",
                    "category": "users",
                    "title": "Baja actividad de usuarios",
                    "description": f"Solo {users_data.get('activity_rate', 0)}% de los usuarios han estado activos en el período",
                    "recommendation": "Considerar estrategias de engagement o training de usuarios",
                    "priority": "medium"
                })
            
            # Insight sobre integraciones
            integrations = report.get("integrations", {})
            whatsapp_data = integrations.get("whatsapp", {})
            
            if whatsapp_data.get("conversations", {}).get("resolution_rate", 0) < 80:
                insights.append({
                    "type": "warning", 
                    "category": "whatsapp",
                    "title": "Baja tasa de resolución en WhatsApp",
                    "description": f"Solo {whatsapp_data.get('conversations', {}).get('resolution_rate', 0)}% de conversaciones se resuelven",
                    "recommendation": "Revisar procesos de atención al cliente y training del personal",
                    "priority": "high"
                })
            
            # Insight sobre crecimiento de entidades
            entities = report.get("entities", {}).get("entities", {})
            growing_entities = []
            declining_entities = []
            
            for entity_name, entity_data in entities.items():
                if isinstance(entity_data, dict):
                    growth_rate = entity_data.get("growth_rate", 0)
                    if growth_rate > 10:
                        growing_entities.append(entity_name)
                    elif growth_rate < -10:
                        declining_entities.append(entity_name)
            
            if growing_entities:
                insights.append({
                    "type": "success",
                    "category": "growth",
                    "title": "Crecimiento positivo detectado",
                    "description": f"Las entidades {', '.join(growing_entities)} muestran crecimiento significativo",
                    "recommendation": "Mantener las estrategias actuales para estas áreas",
                    "priority": "low"
                })
            
            if declining_entities:
                insights.append({
                    "type": "warning",
                    "category": "decline", 
                    "title": "Declive en algunas áreas",
                    "description": f"Las entidades {', '.join(declining_entities)} muestran declive",
                    "recommendation": "Investigar causas y implementar acciones correctivas",
                    "priority": "high"
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generando insights: {e}")
            return [{"type": "error", "description": f"Error generando insights: {str(e)}"}]
    
    # ================================
    # UTILIDADES DE CÁLCULO
    # ================================
    
    def _calculate_start_date(self, end_date: datetime, period: str) -> datetime:
        """Calcular fecha de inicio según el período"""
        
        if period == "7d":
            return end_date - timedelta(days=7)
        elif period == "30d":
            return end_date - timedelta(days=30)
        elif period == "90d":
            return end_date - timedelta(days=90)
        elif period == "1y":
            return end_date - timedelta(days=365)
        else:
            return end_date - timedelta(days=30)  # Default 30 días
    
    def _calculate_growth_rate(self, growth_data: List[Dict[str, Any]]) -> float:
        """Calcular tasa de crecimiento"""
        
        if len(growth_data) < 2:
            return 0
        
        first_week = sum(d["count"] for d in growth_data[:7])
        last_week = sum(d["count"] for d in growth_data[-7:])
        
        if first_week == 0:
            return 100 if last_week > 0 else 0
        
        return round(((last_week - first_week) / first_week) * 100, 1)
    
    def _calculate_health_score(self, report: Dict[str, Any]) -> int:
        """Calcular score de salud general (0-100)"""
        
        score = 100
        
        try:
            # Penalizar por errores
            sections = ["overview", "entities", "integrations", "user_activity", "performance"]
            for section in sections:
                if isinstance(report.get(section), dict) and "error" in report[section]:
                    score -= 20
            
            # Evaluar actividad de usuarios
            users_data = report.get("overview", {}).get("users", {})
            activity_rate = users_data.get("activity_rate", 0)
            if activity_rate < 50:
                score -= 15
            elif activity_rate < 75:
                score -= 5
            
            # Evaluar integraciones
            integrations = report.get("integrations", {})
            if integrations.get("whatsapp", {}).get("status") != "connected":
                score -= 10
            if integrations.get("n8n", {}).get("status") != "connected":
                score -= 10
            
            return max(0, min(100, score))
            
        except Exception:
            return 50  # Score neutral si hay errores
    
    def _calculate_whatsapp_health_score(
        self, 
        sessions: List[Dict[str, Any]], 
        conversations: List[Dict[str, Any]]
    ) -> int:
        """Calcular score de salud de WhatsApp"""
        
        score = 100
        
        # Sin sesiones activas
        if not sessions:
            return 0
        
        # Muchas conversaciones pendientes
        pending = len([c for c in conversations if c["conversacion"]["estado"] == "pendiente"])
        total = len(conversations)
        
        if total > 0:
            pending_rate = pending / total
            if pending_rate > 0.5:
                score -= 30
            elif pending_rate > 0.3:
                score -= 15
        
        return max(0, score)