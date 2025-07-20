from typing import List, Dict, Any
from ..models.user import User

class PermissionManager:
    """Gestor de permisos del sistema"""
    
    @staticmethod
    def can_access_business(user: User, business_id: str) -> bool:
        """Verificar si el usuario puede acceder a un business"""
        if user.rol == "super_admin":
            return True
        return user.business_id == business_id
    
    @staticmethod
    def can_edit_entity(user: User, entity_name: str) -> bool:
        """Verificar si el usuario puede editar una entidad"""
        if user.rol in ["super_admin", "admin"]:
            return True
        
        entity_perms = user.permisos.get("entidades_acceso", [])
        return entity_name in entity_perms
    
    @staticmethod
    def can_access_view(user: User, view_name: str) -> bool:
        """Verificar si el usuario puede acceder a una vista"""
        if user.rol in ["super_admin", "admin"]:
            return True
        
        view_perms = user.permisos.get("vistas_acceso", [])
        return view_name in view_perms
    
    @staticmethod
    def filter_fields_by_role(user: User, fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtrar campos según rol del usuario"""
        visible_fields = []
        
        for field in fields:
            visible_roles = field.get("visible_roles", ["*"])
            if "*" in visible_roles or user.rol in visible_roles:
                visible_fields.append(field)
        
        return visible_fields