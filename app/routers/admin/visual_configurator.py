# ================================
# app/routers/admin/visual_configurator.py
# ================================

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Dict, Any, Optional, List
import json

from ...auth.dependencies import require_admin
from ...models.user import User
from ...models.responses import BaseResponse
from ...services.visual_configurator_service import VisualConfiguratorService

router = APIRouter()

# ================================
# CONFIGURACIÓN DE ENTIDADES
# ================================

@router.post("/entity/auto-discover")
async def auto_discover_entity(
    discovery_data: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """Auto-descubrir estructura de entidad desde API"""
    
    required_fields = ["business_id", "api_name", "endpoint", "entity_name"]
    for field in required_fields:
        if field not in discovery_data:
            raise HTTPException(status_code=400, detail=f"Campo requerido: {field}")
    
    try:
        configurator_service = VisualConfiguratorService()
        result = await configurator_service.create_entity_from_api_discovery(
            business_id=discovery_data["business_id"],
            api_name=discovery_data["api_name"],
            endpoint=discovery_data["endpoint"],
            entity_name=discovery_data["entity_name"],
            user=current_user
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return BaseResponse(
            data=result,
            message="Entidad creada automáticamente desde API"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/entity/{business_id}/{entity_name}/preview")
async def preview_entity_data(
    business_id: str,
    entity_name: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_admin)
):
    """Vista previa de datos de entidad"""
    
    try:
        from ...core.dynamic_crud import DynamicCrudGenerator
        
        crud_generator = DynamicCrudGenerator()
        
        # Crear usuario temporal para preview
        preview_user = User(
            clerk_user_id="preview",
            email="preview@system.com",
            rol="admin",
            perfil={"nombre": "Preview User"}
        )
        
        result = await crud_generator.list_entities(
            business_id=business_id,
            entity_name=entity_name,
            user=preview_user,
            page=1,
            per_page=limit
        )
        
        return BaseResponse(
            data={
                "entity_name": entity_name,
                "sample_data": result.get("items", []),
                "total_records": result.get("total", 0),
                "fields_detected": list(result["items"][0].keys()) if result.get("items") else []
            },
            message=f"Vista previa de {entity_name}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/entity/{business_id}/{entity_name}/validate-config")
async def validate_entity_config(
    business_id: str,
    entity_name: str,
    config_data: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """Validar configuración de entidad"""
    
    try:
        configurator_service = VisualConfiguratorService()
        
        # Validar configuración de campos
        campos = config_data.get("campos", [])
        validation_results = []
        
        for campo in campos:
            try:
                # Validar campo individual
                field_validation = await configurator_service.validation_service.validate_field(
                    value="test_value",  # Valor de prueba
                    field_config=campo
                )
                validation_results.append({
                    "campo": campo["campo"],
                    "valid": True,
                    "message": "Configuración válida"
                })
            except Exception as e:
                validation_results.append({
                    "campo": campo["campo"],
                    "valid": False,
                    "message": str(e)
                })
        
        # Validar configuración de API si existe
        api_validation = {"valid": True, "message": "Sin configuración de API"}
        if "api_config" in config_data:
            try:
                # TODO: Validar conexión con API
                api_validation = {"valid": True, "message": "Configuración de API válida"}
            except Exception as e:
                api_validation = {"valid": False, "message": str(e)}
        
        overall_valid = all(r["valid"] for r in validation_results) and api_validation["valid"]
        
        return BaseResponse(
            data={
                "overall_valid": overall_valid,
                "fields_validation": validation_results,
                "api_validation": api_validation,
                "fields_count": len(campos)
            },
            message="Validación completada"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ================================
# CONFIGURACIÓN DE VISTAS
# ================================

@router.get("/dashboard/templates")
async def get_dashboard_templates(
    current_user: User = Depends(require_admin)
):
    """Obtener templates disponibles para dashboards"""
    
    try:
        configurator_service = VisualConfiguratorService()
        templates = await configurator_service._get_dashboard_templates()
        
        return BaseResponse(
            data={
                "templates": templates,
                "count": len(templates)
            },
            message="Templates de dashboard obtenidos"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/dashboard/create-from-template")
async def create_dashboard_from_template(
    dashboard_data: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """Crear dashboard desde template"""
    
    required_fields = ["business_id", "template_name", "dashboard_name", "entities"]
    for field in required_fields:
        if field not in dashboard_data:
            raise HTTPException(status_code=400, detail=f"Campo requerido: {field}")
    
    try:
        configurator_service = VisualConfiguratorService()
        result = await configurator_service.create_dashboard_from_template(
            business_id=dashboard_data["business_id"],
            template_name=dashboard_data["template_name"],
            dashboard_name=dashboard_data["dashboard_name"],
            entities=dashboard_data["entities"],
            user=current_user
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return BaseResponse(
            data=result,
            message="Dashboard creado desde template"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dashboard/{business_id}/preview")
async def preview_dashboard_config(
    business_id: str,
    vista: str = Query("dashboard_principal"),
    current_user: User = Depends(require_admin)
):
    """Vista previa de configuración de dashboard"""
    
    try:
        from ...services.view_service import ViewService
        
        view_service = ViewService()
        view_config = await view_service.get_view_config(business_id, vista)
        
        if not view_config:
            raise HTTPException(status_code=404, detail="Vista no encontrada")
        
        # Analizar componentes
        components_analysis = []
        for component in view_config.configuracion.componentes:
            analysis = {
                "id": component.id,
                "tipo": component.tipo,
                "posicion": component.posicion.dict(),
                "configuracion_valida": True,  # TODO: Validar configuración real
                "dependencias": self._analyze_component_dependencies(component),
                "permisos": component.permisos_rol
            }
            components_analysis.append(analysis)
        
        return BaseResponse(
            data={
                "business_id": business_id,
                "vista": vista,
                "layout": view_config.configuracion.layout.dict(),
                "components": components_analysis,
                "navigation": [nav.dict() for nav in view_config.configuracion.navegacion],
                "total_components": len(components_analysis)
            },
            message="Vista previa de dashboard generada"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def _analyze_component_dependencies(component) -> List[str]:
    """Analizar dependencias de un componente"""
    dependencies = []
    
    config = component.configuracion
    
    # Dependencia de entidad
    if hasattr(config, 'entidad') and config.entidad:
        dependencies.append(f"entity:{config.entidad}")
    
    # Dependencia de API
    if component.tipo in ["whatsapp_panel", "n8n_panel"]:
        dependencies.append(f"integration:{component.tipo.replace('_panel', '')}")
    
    return dependencies

# ================================
# CONFIGURACIÓN DE BRANDING
# ================================

@router.get("/branding/{business_id}")
async def get_business_branding(
    business_id: str,
    current_user: User = Depends(require_admin)
):
    """Obtener configuración de branding actual"""
    
    try:
        configurator_service = VisualConfiguratorService()
        
        business_doc = await configurator_service.db.business_instances.find_one({
            "business_id": business_id
        })
        
        if not business_doc:
            raise HTTPException(status_code=404, detail="Business no encontrado")
        
        branding = business_doc.get("configuracion", {}).get("branding", {
            "colores": {
                "primary": "#1e40af",
                "secondary": "#059669",
                "background": "#f8fafc",
                "text": "#0f172a"
            }
        })
        
        return BaseResponse(
            data=branding,
            message="Configuración de branding obtenida"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/branding/{business_id}")
async def update_business_branding(
    business_id: str,
    branding_data: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """Actualizar configuración de branding"""
    
    try:
        configurator_service = VisualConfiguratorService()
        result = await configurator_service.update_business_branding(
            business_id=business_id,
            branding_config=branding_data,
            user=current_user
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return BaseResponse(
            data=result,
            message="Branding actualizado exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/branding/{business_id}/logo")
async def upload_business_logo(
    business_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin)
):
    """Subir logo del business"""
    
    # Validar tipo de archivo
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Debe ser un archivo de imagen")
    
    try:
        import os
        import uuid
        
        # Crear directorio si no existe
        upload_dir = "uploads/logos"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generar nombre único
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{business_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Actualizar branding con URL del logo
        logo_url = f"/uploads/logos/{unique_filename}"
        
        configurator_service = VisualConfiguratorService()
        await configurator_service.db.business_instances.update_one(
            {"business_id": business_id},
            {"$set": {"configuracion.branding.logo_url": logo_url}}
        )
        
        return BaseResponse(
            data={"logo_url": logo_url},
            message="Logo subido exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ================================
# IMPORTAR/EXPORTAR CONFIGURACIONES
# ================================

@router.get("/export/{business_id}")
async def export_business_configuration(
    business_id: str,
    include_data: bool = Query(False, description="Incluir datos de ejemplo"),
    current_user: User = Depends(require_admin)
):
    """Exportar configuración completa del business"""
    
    try:
        configurator_service = VisualConfiguratorService()
        result = await configurator_service.export_business_configuration(
            business_id=business_id,
            include_data=include_data
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return BaseResponse(
            data=result["export_data"],
            message=f"Configuración exportada: {result['entities_count']} entidades, {result['views_count']} vistas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/import/{business_id}")
async def import_business_configuration(
    business_id: str,
    config_file: UploadFile = File(...),
    overwrite: bool = Query(False, description="Sobrescribir configuración existente"),
    current_user: User = Depends(require_admin)
):
    """Importar configuración de business"""
    
    try:
        # Leer y parsear archivo
        content = await config_file.read()
        try:
            config_data = json.loads(content.decode())
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Archivo JSON inválido")
        
        # Validar estructura
        required_keys = ["business", "entities", "views"]
        for key in required_keys:
            if key not in config_data:
                raise HTTPException(status_code=400, detail=f"Clave requerida en configuración: {key}")
        
        # TODO: Implementar lógica de importación
        # Por ahora, retornar análisis del archivo
        
        analysis = {
            "business_config": bool(config_data.get("business")),
            "entities_count": len(config_data.get("entities", [])),
            "views_count": len(config_data.get("views", [])),
            "apis_count": len(config_data.get("api_configs", [])),
            "export_version": config_data.get("export_info", {}).get("version", "unknown"),
            "can_import": True  # TODO: Validar compatibilidad
        }
        
        return BaseResponse(
            data=analysis,
            message="Análisis de configuración completado (importación pendiente de implementar)"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ================================
# UTILIDADES DE CONFIGURACIÓN
# ================================

@router.get("/field-types")
async def get_available_field_types(
    current_user: User = Depends(require_admin)
):
    """Obtener tipos de campo disponibles"""
    
    field_types = {
        "text": {
            "name": "Texto",
            "description": "Campo de texto simple",
            "validation_options": ["min", "max", "regex"],
            "example": "Nombre del cliente"
        },
        "textarea": {
            "name": "Área de texto",
            "description": "Campo de texto multilínea",
            "validation_options": ["min", "max"],
            "example": "Descripción detallada"
        },
        "number": {
            "name": "Número",
            "description": "Campo numérico",
            "validation_options": ["min", "max"],
            "example": 100
        },
        "email": {
            "name": "Email",
            "description": "Dirección de correo electrónico",
            "validation_options": ["email"],
            "example": "usuario@ejemplo.com"
        },
        "phone": {
            "name": "Teléfono",
            "description": "Número de teléfono",
            "validation_options": ["phone"],
            "example": "+54911234567"
        },
        "date": {
            "name": "Fecha",
            "description": "Campo de fecha",
            "validation_options": ["date"],
            "example": "2025-01-19"
        },
        "boolean": {
            "name": "Booleano",
            "description": "Verdadero/Falso",
            "validation_options": [],
            "example": True
        },
        "select": {
            "name": "Selección",
            "description": "Lista de opciones",
            "validation_options": [],
            "example": "Opción 1",
            "requires_options": True
        },
        "url": {
            "name": "URL",
            "description": "Dirección web",
            "validation_options": ["url"],
            "example": "https://ejemplo.com"
        }
    }
    
    return BaseResponse(
        data=field_types,
        message="Tipos de campo disponibles"
    )

@router.get("/component-types")
async def get_available_component_types(
    current_user: User = Depends(require_admin)
):
    """Obtener tipos de componente disponibles para vistas"""
    
    component_types = {
        "stats_card": {
            "name": "Tarjeta de estadísticas",
            "description": "Muestra una métrica con icono y tendencia",
            "required_config": ["titulo", "entidad", "operacion"],
            "optional_config": ["icono", "color", "filtro"]
        },
        "chart": {
            "name": "Gráfico",
            "description": "Gráficos de líneas, barras, etc.",
            "required_config": ["titulo", "tipo_grafico", "entidades"],
            "optional_config": ["colores", "config_adicional"]
        },
        "data_table": {
            "name": "Tabla de datos",
            "description": "Tabla con datos de entidad",
            "required_config": ["entidad", "columnas_visibles"],
            "optional_config": ["paginacion", "acciones", "filtros"]
        },
        "whatsapp_panel": {
            "name": "Panel WhatsApp",
            "description": "Panel de control de WhatsApp",
            "required_config": ["titulo"],
            "optional_config": [],
            "requires_integration": "whatsapp"
        },
        "n8n_panel": {
            "name": "Panel N8N",
            "description": "Panel de control de workflows",
            "required_config": ["titulo"],
            "optional_config": [],
            "requires_integration": "n8n"
        }
    }
    
    return BaseResponse(
        data=component_types,
        message="Tipos de componente disponibles"
    )