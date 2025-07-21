# ================================
# app/services/visual_configurator_service.py
# ================================

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import get_database
from ..models.entity import EntityConfig, CampoConfig, ApiConfig, CrudConfig
from ..models.view import ViewConfig, ComponenteVista, ConfiguracionVista, LayoutConfig
from ..models.business import BusinessInstance, ConfiguracionBusiness
from ..models.user import User
from ..services.api_service import ApiService
from ..services.validation_service import ValidationService

logger = logging.getLogger(__name__)

class VisualConfiguratorService:
    """Servicio para configuración visual de entidades y vistas"""
    
    def __init__(self):
        self.db = get_database()
        self.api_service = ApiService()
        self.validation_service = ValidationService()
    
    # ================================
    # CONFIGURACIÓN DE ENTIDADES
    # ================================
    
    async def create_entity_from_api_discovery(
        self, 
        business_id: str, 
        api_name: str, 
        endpoint: str,
        entity_name: str,
        user: User
    ) -> Dict[str, Any]:
        """Crear entidad automáticamente descubriendo estructura de API"""
        
        try:
            # 1. Hacer petición de muestra para descubrir estructura
            sample_data = await self.api_service.make_request(
                business_id=business_id,
                api_name=api_name,
                endpoint=endpoint,
                method="GET",
                params={"limit": 5}  # Solo algunos registros para análisis
            )
            
            if not sample_data:
                return {"success": False, "error": "No se pudo obtener datos de muestra"}
            
            # 2. Analizar estructura de datos
            fields_analysis = await self._analyze_data_structure(sample_data)
            
            # 3. Generar configuración de campos automáticamente
            campos_config = []
            for field_name, field_info in fields_analysis.items():
                campo_config = {
                    "campo": field_name,
                    "tipo": field_info["suggested_type"],
                    "obligatorio": field_info["required"],
                    "visible_roles": ["*"],
                    "editable_roles": ["admin"],
                    "descripcion": field_info["description"]
                }
                
                # Agregar validaciones si aplica
                if field_info["validation"]:
                    campo_config["validacion"] = field_info["validation"]
                
                # Agregar opciones si es select
                if field_info["suggested_type"] == "select" and field_info["options"]:
                    campo_config["opciones"] = field_info["options"]
                
                campos_config.append(CampoConfig(**campo_config))
            
            # 4. Crear configuración de API
            api_config = ApiConfig(
                fuente=api_name,
                endpoint=endpoint,
                metodo="GET",
                mapeo=fields_analysis.get("field_mapping", {}),
                cache_config={"tipo": "tiempo", "refresh_seconds": 300}
            )
            
            # 5. Crear configuración CRUD básica
            crud_config = CrudConfig(
                crear={"habilitado": True, "roles": ["admin"]},
                editar={"habilitado": True, "roles": ["admin", "user"]},
                eliminar={"habilitado": True, "roles": ["admin"], "confirmacion": True}
            )
            
            # 6. Crear entidad
            entity_config = EntityConfig(
                business_id=business_id,
                entidad=entity_name,
                configuracion={
                    "campos": [campo.dict() for campo in campos_config],
                    "api_config": api_config.dict(),
                    "crud_config": crud_config.dict()
                }
            )
            
            # 7. Guardar en base de datos
            result = await self.db.entities_config.insert_one(entity_config.dict(by_alias=True))
            
            return {
                "success": True,
                "entity_id": str(result.inserted_id),
                "entity_name": entity_name,
                "fields_discovered": len(campos_config),
                "suggested_config": entity_config.dict(),
                "message": f"Entidad '{entity_name}' creada con {len(campos_config)} campos"
            }
            
        except Exception as e:
            logger.error(f"Error en auto-discovery de entidad: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_data_structure(self, data: Any) -> Dict[str, Dict[str, Any]]:
        """Analizar estructura de datos para generar configuración automática"""
        
        fields_info = {}
        
        # Obtener lista de registros
        if isinstance(data, dict):
            if "data" in data:
                records = data["data"]
            elif "items" in data:
                records = data["items"]
            else:
                records = [data]
        elif isinstance(data, list):
            records = data
        else:
            records = []
        
        if not records:
            return fields_info
        
        # Analizar cada campo en los registros
        all_fields = set()
        for record in records[:5]:  # Analizar máximo 5 registros
            if isinstance(record, dict):
                all_fields.update(record.keys())
        
        for field_name in all_fields:
            field_values = []
            field_types = set()
            non_null_count = 0
            
            # Recopilar valores del campo
            for record in records:
                if isinstance(record, dict) and field_name in record:
                    value = record[field_name]
                    if value is not None:
                        field_values.append(value)
                        field_types.add(type(value).__name__)
                        non_null_count += 1
            
            # Analizar el campo
            field_analysis = self._analyze_field(field_name, field_values, field_types, non_null_count, len(records))
            fields_info[field_name] = field_analysis
        
        return fields_info
    
    def _analyze_field(
        self, 
        field_name: str, 
        values: List[Any], 
        types: set, 
        non_null_count: int, 
        total_records: int
    ) -> Dict[str, Any]:
        """Analizar un campo específico"""
        
        analysis = {
            "suggested_type": "text",
            "required": non_null_count > (total_records * 0.8),  # 80% o más tienen valor
            "description": self._generate_field_description(field_name),
            "validation": None,
            "options": None
        }
        
        if not values:
            return analysis
        
        # Determinar tipo sugerido
        if len(types) == 1:
            type_name = list(types)[0]
            
            if type_name in ["int", "float"]:
                analysis["suggested_type"] = "number"
            elif type_name == "bool":
                analysis["suggested_type"] = "boolean"
            elif type_name == "str":
                # Analizar strings más a fondo
                str_analysis = self._analyze_string_field(field_name, values)
                analysis.update(str_analysis)
        
        # Detectar selects (pocas opciones únicas)
        unique_values = list(set(str(v) for v in values))
        if len(unique_values) <= 10 and len(values) > len(unique_values):
            analysis["suggested_type"] = "select"
            analysis["options"] = [{"value": v, "label": v} for v in unique_values]
        
        # Detectar campos de fecha
        if "date" in field_name.lower() or "created" in field_name.lower() or "updated" in field_name.lower():
            analysis["suggested_type"] = "date"
        
        return analysis
    
    def _analyze_string_field(self, field_name: str, values: List[str]) -> Dict[str, Any]:
        """Analizar campo de texto específicamente"""
        
        result = {"suggested_type": "text"}
        
        # Detectar emails
        if "email" in field_name.lower() or "mail" in field_name.lower():
            result["suggested_type"] = "email"
            result["validation"] = "email"
            return result
        
        # Detectar teléfonos
        if "phone" in field_name.lower() or "telefono" in field_name.lower() or "tel" in field_name.lower():
            result["suggested_type"] = "phone" 
            result["validation"] = "phone"
            return result
        
        # Detectar URLs
        if any(str(v).startswith(("http://", "https://")) for v in values[:5]):
            result["suggested_type"] = "url"
            result["validation"] = "url"
            return result
        
        # Analizar longitud promedio
        avg_length = sum(len(str(v)) for v in values) / len(values)
        
        if avg_length > 100:
            result["suggested_type"] = "textarea"
        elif avg_length < 10:
            result["suggested_type"] = "text"
            result["validation"] = f"max:{int(avg_length * 2)}"
        
        return result
    
    def _generate_field_description(self, field_name: str) -> str:
        """Generar descripción automática para un campo"""
        
        descriptions = {
            "id": "Identificador único",
            "name": "Nombre",
            "nombre": "Nombre",
            "email": "Dirección de correo electrónico",
            "phone": "Número de teléfono",
            "telefono": "Número de teléfono",
            "address": "Dirección",
            "direccion": "Dirección",
            "status": "Estado",
            "estado": "Estado",
            "active": "Activo/Inactivo",
            "activo": "Activo/Inactivo",
            "created_at": "Fecha de creación",
            "updated_at": "Fecha de actualización",
            "price": "Precio",
            "precio": "Precio",
            "amount": "Cantidad",
            "cantidad": "Cantidad"
        }
        
        field_lower = field_name.lower()
        
        for key, desc in descriptions.items():
            if key in field_lower:
                return desc
        
        # Descripción genérica basada en el nombre
        return f"Campo {field_name.replace('_', ' ').title()}"
    
    # ================================
    # CONFIGURACIÓN DE VISTAS
    # ================================
    
    async def create_dashboard_from_template(
        self, 
        business_id: str, 
        template_name: str, 
        dashboard_name: str,
        entities: List[str],
        user: User
    ) -> Dict[str, Any]:
        """Crear dashboard desde template predefinido"""
        
        try:
            templates = await self._get_dashboard_templates()
            
            if template_name not in templates:
                return {"success": False, "error": "Template no encontrado"}
            
            template = templates[template_name]
            
            # Generar componentes basados en las entidades disponibles
            componentes = []
            component_id = 0
            
            for entity_name in entities:
                # Obtener configuración de la entidad
                entity_config = await self.db.entities_config.find_one({
                    "business_id": business_id,
                    "entidad": entity_name
                })
                
                if not entity_config:
                    continue
                
                # Agregar componentes según el template
                if "stats_cards" in template["components"]:
                    stats_component = ComponenteVista(
                        id=f"stats_{entity_name}_{component_id}",
                        tipo="stats_card",
                        posicion={"x": (component_id % 4) * 3, "y": 0, "w": 3, "h": 2},
                        configuracion={
                            "titulo": f"Total {entity_name.title()}",
                            "entidad": entity_name,
                            "operacion": "count",
                            "icono": template["entity_icons"].get(entity_name, "database"),
                            "color": "primary"
                        },
                        permisos_rol=["*"]
                    )
                    componentes.append(stats_component)
                    component_id += 1
                
                if "data_tables" in template["components"]:
                    # Obtener campos visibles de la entidad
                    campos = entity_config.get("configuracion", {}).get("campos", [])
                    campos_visibles = [c["campo"] for c in campos[:5]]  # Primeros 5 campos
                    
                    table_component = ComponenteVista(
                        id=f"table_{entity_name}_{component_id}",
                        tipo="data_table",
                        posicion={"x": 0, "y": 4 + (component_id * 6), "w": 12, "h": 6},
                        configuracion={
                            "titulo": f"Lista de {entity_name.title()}",
                            "entidad": entity_name,
                            "columnas_visibles": campos_visibles,
                            "paginacion": {"items_per_page": 25},
                            "acciones": {
                                "crear": {"roles": ["admin"]},
                                "editar": {"roles": ["admin", "user"]},
                                "eliminar": {"roles": ["admin"]}
                            }
                        },
                        permisos_rol=["*"]
                    )
                    componentes.append(table_component)
                    component_id += 1
            
            # Agregar componentes de integración si están disponibles
            if template["include_integrations"]:
                # WhatsApp panel
                if await self._business_has_whatsapp(business_id):
                    whatsapp_component = ComponenteVista(
                        id=f"whatsapp_panel_{component_id}",
                        tipo="whatsapp_panel",
                        posicion={"x": 0, "y": 2, "w": 6, "h": 4},
                        configuracion={"titulo": "WhatsApp Business"},
                        permisos_rol=["admin", "user"]
                    )
                    componentes.append(whatsapp_component)
                
                # N8N panel
                if await self._business_has_n8n(business_id):
                    n8n_component = ComponenteVista(
                        id=f"n8n_panel_{component_id}",
                        tipo="n8n_panel", 
                        posicion={"x": 6, "y": 2, "w": 6, "h": 4},
                        configuracion={"titulo": "Workflows N8N"},
                        permisos_rol=["admin"]
                    )
                    componentes.append(n8n_component)
            
            # Crear navegación
            navegacion = []
            for entity in entities:
                navegacion.append({
                    "titulo": entity.title(),
                    "ruta": f"/{entity}",
                    "icono": template["entity_icons"].get(entity, "database"),
                    "permisos_rol": ["*"]
                })
            
            # Agregar navegación de integración
            if await self._business_has_whatsapp(business_id):
                navegacion.append({
                    "titulo": "WhatsApp",
                    "ruta": "/whatsapp",
                    "icono": "message-circle",
                    "permisos_rol": ["admin", "user"]
                })
            
            # Crear configuración de vista
            configuracion_vista = ConfiguracionVista(
                layout=LayoutConfig(
                    tipo="grid",
                    columnas=12,
                    gap=4,
                    responsive=True
                ),
                componentes=componentes,
                navegacion=navegacion
            )
            
            # Crear vista
            view_config = ViewConfig(
                business_id=business_id,
                vista=dashboard_name,
                configuracion=configuracion_vista,
                permisos_vista=["*"]
            )
            
            # Guardar en base de datos
            result = await self.db.views_config.insert_one(view_config.dict(by_alias=True))
            
            return {
                "success": True,
                "view_id": str(result.inserted_id),
                "dashboard_name": dashboard_name,
                "components_created": len(componentes),
                "entities_included": entities,
                "message": f"Dashboard '{dashboard_name}' creado con {len(componentes)} componentes"
            }
            
        except Exception as e:
            logger.error(f"Error creando dashboard desde template: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_dashboard_templates(self) -> Dict[str, Dict[str, Any]]:
        """Obtener templates predefinidos de dashboards"""
        
        return {
            "business_overview": {
                "name": "Vista General de Negocio",
                "description": "Dashboard completo con estadísticas, tablas e integraciones",
                "components": ["stats_cards", "data_tables", "charts"],
                "include_integrations": True,
                "entity_icons": {
                    "clientes": "users",
                    "productos": "package",
                    "ventas": "shopping-cart",
                    "tickets": "help-circle",
                    "facturas": "file-text",
                    "pagos": "credit-card",
                    "usuarios": "user"
                }
            },
            "analytics_focused": {
                "name": "Enfoque en Analytics",
                "description": "Dashboard con gráficos y métricas detalladas",
                "components": ["stats_cards", "charts"],
                "include_integrations": False,
                "entity_icons": {
                    "clientes": "users",
                    "ventas": "trending-up",
                    "productos": "package"
                }
            },
            "operational": {
                "name": "Vista Operacional",
                "description": "Dashboard para operaciones diarias",
                "components": ["data_tables", "integration_panels"],
                "include_integrations": True,
                "entity_icons": {
                    "tickets": "help-circle",
                    "tareas": "check-square",
                    "conversaciones": "message-square"
                }
            }
        }
    
    # ================================
    # CONFIGURACIÓN DE BRANDING
    # ================================
    
    async def update_business_branding(
        self, 
        business_id: str, 
        branding_config: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Actualizar configuración de branding del business"""
        
        try:
            # Validar colores
            colores = branding_config.get("colores", {})
            if not self._validate_color_scheme(colores):
                return {"success": False, "error": "Esquema de colores inválido"}
            
            # Preparar actualización
            update_data = {
                "configuracion.branding": branding_config,
                "updated_at": datetime.utcnow()
            }
            
            # Actualizar business
            result = await self.db.business_instances.update_one(
                {"business_id": business_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return {"success": False, "error": "Business no encontrado"}
            
            # Limpiar cache de dashboards que usan branding
            from ..services.cache_service import CacheService
            cache_service = CacheService()
            await cache_service.clear_pattern(f"dashboard_{business_id}_*")
            
            return {
                "success": True,
                "message": "Branding actualizado exitosamente",
                "branding": branding_config
            }
            
        except Exception as e:
            logger.error(f"Error actualizando branding: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_color_scheme(self, colores: Dict[str, Any]) -> bool:
        """Validar esquema de colores"""
        
        required_colors = ["primary", "secondary", "background", "text"]
        
        for color in required_colors:
            if color not in colores:
                return False
            
            color_value = colores[color]
            if not isinstance(color_value, str) or not color_value.startswith("#"):
                return False
            
            # Validar formato hex
            try:
                int(color_value[1:], 16)
            except ValueError:
                return False
        
        return True
    
    # ================================
    # UTILIDADES
    # ================================
    
    async def _business_has_whatsapp(self, business_id: str) -> bool:
        """Verificar si el business tiene WhatsApp configurado"""
        
        business_doc = await self.db.business_instances.find_one({"business_id": business_id})
        if not business_doc:
            return False
        
        componentes_activos = business_doc.get("configuracion", {}).get("componentes_activos", [])
        return "whatsapp" in componentes_activos
    
    async def _business_has_n8n(self, business_id: str) -> bool:
        """Verificar si el business tiene N8N configurado"""
        
        business_doc = await self.db.business_instances.find_one({"business_id": business_id})
        if not business_doc:
            return False
        
        componentes_activos = business_doc.get("configuracion", {}).get("componentes_activos", [])
        return "n8n" in componentes_activos
    
    async def export_business_configuration(
        self, 
        business_id: str,
        include_data: bool = False
    ) -> Dict[str, Any]:
        """Exportar configuración completa de un business"""
        
        try:
            # Obtener business instance
            business_doc = await self.db.business_instances.find_one({"business_id": business_id})
            if not business_doc:
                return {"success": False, "error": "Business no encontrado"}
            
            # Obtener configuraciones de entidades
            entities_cursor = self.db.entities_config.find({"business_id": business_id})
            entities = await entities_cursor.to_list(length=None)
            
            # Obtener configuraciones de vistas
            views_cursor = self.db.views_config.find({"business_id": business_id})
            views = await views_cursor.to_list(length=None)
            
            # Obtener configuraciones de APIs
            apis_cursor = self.db.api_configurations.find({"business_id": business_id})
            apis = await apis_cursor.to_list(length=None)
            
            export_data = {
                "business": self._clean_export_doc(business_doc),
                "entities": [self._clean_export_doc(doc) for doc in entities],
                "views": [self._clean_export_doc(doc) for doc in views],
                "api_configs": [self._clean_export_doc(doc) for doc in apis],
                "export_info": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "version": "1.0",
                    "include_data": include_data
                }
            }
            
            # Incluir datos si se solicita
            if include_data:
                export_data["sample_data"] = await self._export_sample_data(business_id)
            
            return {
                "success": True,
                "export_data": export_data,
                "entities_count": len(entities),
                "views_count": len(views),
                "apis_count": len(apis)
            }
            
        except Exception as e:
            logger.error(f"Error exportando configuración: {e}")
            return {"success": False, "error": str(e)}
    
    def _clean_export_doc(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Limpiar documento para exportación"""
        cleaned = doc.copy()
        
        # Remover campos internos
        for field in ["_id", "created_at", "updated_at"]:
            cleaned.pop(field, None)
        
        return cleaned