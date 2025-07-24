from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional

from ...auth.dependencies import get_current_business_user
from ...models.user import User
from ...models.responses import BaseResponse, PaginatedResponse
from ...services.dynamic_crud_service import DynamicCrudService
from ...core.dynamic_crud import DynamicCrudGenerator
from enum import Enum  # ← AGREGADO: Import faltante



router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{business_id}/{entity_name}")
async def get_entity_data(
    business_id: str,
    entity_name: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: Optional[str] = Query("asc")
):
    """Obtener datos de una entidad específica"""
    try:
        # Para MVP, simular datos de clientes
        if entity_name == "clientes":
            return await _get_clientes_data(business_id, page, per_page, search, sort_by, sort_order)
        else:
            return {
                "success": True,
                "data": [],
                "message": f"Entidad {entity_name} no implementada en MVP"
            }
            
    except Exception as e:
        logger.error(f"Error obteniendo datos de entidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _get_clientes_data(business_id: str, page: int, per_page: int, 
                           search: Optional[str], sort_by: Optional[str], 
                           sort_order: str) -> Dict[str, Any]:
    """Generar datos de ejemplo para clientes"""
    # Datos de ejemplo para MVP
    clientes_ejemplo = [
        {
            "id": 1,
            "nombre": "Juan Pérez",
            "email": "juan@email.com",
            "telefono": "+54 11 1234-5678",
            "plan": "Fibra 100MB",
            "estado": "Activo",
            "fecha_alta": "2024-01-15",
            "direccion": "Av. Corrientes 1234"
        },
        {
            "id": 2,
            "nombre": "María González",
            "email": "maria@email.com",
            "telefono": "+54 11 8765-4321",
            "plan": "Fibra 50MB",
            "estado": "Activo",
            "fecha_alta": "2024-02-20",
            "direccion": "San Martín 567"
        },
        {
            "id": 3,
            "nombre": "Carlos López",
            "email": "carlos@email.com",
            "telefono": "+54 11 5555-5555",
            "plan": "Fibra 200MB",
            "estado": "Suspendido",
            "fecha_alta": "2023-12-10",
            "direccion": "Belgrano 890"
        },
        {
            "id": 4,
            "nombre": "Ana Martínez",
            "email": "ana@email.com",
            "telefono": "+54 11 9999-9999",
            "plan": "Fibra 100MB",
            "estado": "Activo",
            "fecha_alta": "2024-03-05",
            "direccion": "Rivadavia 345"
        },
        {
            "id": 5,
            "nombre": "Roberto Silva",
            "email": "roberto@email.com",
            "telefono": "+54 11 7777-7777",
            "plan": "Fibra 300MB",
            "estado": "Activo",
            "fecha_alta": "2024-01-28",
            "direccion": "Mitre 123"
        }
    ]
    
    # Aplicar filtro de búsqueda si existe
    filtered_clientes = clientes_ejemplo
    if search:
        search_lower = search.lower()
        filtered_clientes = [
            cliente for cliente in clientes_ejemplo
            if search_lower in cliente["nombre"].lower() or 
               search_lower in cliente["email"].lower() or
               search_lower in cliente["plan"].lower()
        ]
    
    # Aplicar ordenamiento
    if sort_by and sort_by in ["nombre", "email", "plan", "estado", "fecha_alta"]:
        reverse = sort_order == "desc"
        filtered_clientes.sort(key=lambda x: x[sort_by], reverse=reverse)
    
    # Aplicar paginación
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_clientes = filtered_clientes[start_idx:end_idx]
    
    return {
        "success": True,
        "data": paginated_clientes,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": len(filtered_clientes),
            "total_pages": (len(filtered_clientes) + per_page - 1) // per_page
        },
        "message": f"Se encontraron {len(paginated_clientes)} clientes"
    }

router = APIRouter()

@router.get("/{business_id}/{entidad}")
async def get_entity_data(
    business_id: str,
    entidad: str,
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(10, ge=1, le=100, description="Items por página"),
    filters: Optional[str] = Query(None, description="Filtros en formato key=value&key2=value2"),
    sort_by: Optional[str] = Query(None, description="Campo para ordenar"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Dirección del ordenamiento"),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener datos de una entidad con paginación y filtros"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        result = await crud_generator.list_entities(
            business_id=business_id,
            entity_name=entidad,
            user=current_user,
            page=page,
            per_page=per_page,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return BaseResponse(data=result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{business_id}/{entidad}/{item_id}")
async def get_entity_item(
    business_id: str,
    entidad: str,
    item_id: str,
    current_user: User = Depends(get_current_business_user)
):
    """Obtener un item específico de una entidad"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        item = await crud_generator.get_entity(
            business_id=business_id,
            entity_name=entidad,
            entity_id=item_id,
            user=current_user
        )
        
        return BaseResponse(data=item)
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{business_id}/{entidad}")
async def create_entity_item(
    business_id: str,
    entidad: str,
    item_data: Dict[str, Any],
    current_user: User = Depends(get_current_business_user)
):
    """Crear nuevo item en entidad"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        item = await crud_generator.create_entity(
            business_id=business_id,
            entity_name=entidad,
            data=item_data,
            user=current_user
        )
        
        return BaseResponse(data=item, message="Item creado exitosamente")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{business_id}/{entidad}/{item_id}")
async def update_entity_item(
    business_id: str,
    entidad: str,
    item_id: str,
    item_data: Dict[str, Any],
    current_user: User = Depends(get_current_business_user)
):
    """Actualizar item existente en entidad"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        item = await crud_generator.update_entity(
            business_id=business_id,
            entity_name=entidad,
            entity_id=item_id,
            data=item_data,
            user=current_user
        )
        
        return BaseResponse(data=item, message="Item actualizado exitosamente")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{business_id}/{entidad}/{item_id}")
async def delete_entity_item(
    business_id: str,
    entidad: str,
    item_id: str,
    current_user: User = Depends(get_current_business_user)
):
    """Eliminar item de entidad"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        success = await crud_generator.delete_entity(
            business_id=business_id,
            entity_name=entidad,
            entity_id=item_id,
            user=current_user
        )
        
        if success:
            return BaseResponse(data={"deleted": True}, message="Item eliminado exitosamente")
        else:
            raise HTTPException(status_code=404, detail="Item no encontrado")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))