from typing import Dict, Any, List
import re
from datetime import datetime

def validate_business_id(business_id: str) -> bool:
    """Validar formato de business_id"""
    pattern = r'^[a-z0-9_]+$'
    return bool(re.match(pattern, business_id)) and len(business_id) >= 3

def validate_field_name(field_name: str) -> bool:
    """Validar nombre de campo"""
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, field_name))

def clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Limpiar diccionario removiendo valores None"""
    return {k: v for k, v in data.items() if v is not None}

def convert_objectid_to_str(data: Any) -> Any:
    """Convertir ObjectId a string recursivamente"""
    from bson import ObjectId
    
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, dict):
        return {k: convert_objectid_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    else:
        return data

def generate_api_key() -> str:
    """Generar API key aleatoria"""
    import secrets
    return f"cms_{secrets.token_urlsafe(32)}"

def format_datetime(dt: datetime) -> str:
    """Formatear datetime para respuestas API"""
    return dt.isoformat() + "Z"

def parse_filter_string(filter_str: str) -> Dict[str, Any]:
    """Parsear string de filtro como 'activo=true&plan=premium'"""
    filters = {}
    
    if not filter_str:
        return filters
    
    for part in filter_str.split('&'):
        if '=' in part:
            key, value = part.split('=', 1)
            # Convertir valores booleanos
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            
            filters[key] = value
    
    return filters
