# ================================
# app/services/field_mapper_service.py
# Servicio para análisis y mapping de campos anidados
# ================================

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from ..models.field_mapping import NestedFieldStructure, MappedField, FieldType

class FieldMapperService:
    """Servicio para mapeo de campos anidados"""
    
    def __init__(self):
        self.type_mapping = {
            int: FieldType.NUMBER,
            float: FieldType.NUMBER, 
            str: FieldType.TEXT,
            bool: FieldType.BOOLEAN,
            list: FieldType.ARRAY,
            dict: FieldType.JSON,
        }
    
    def analyze_nested_structure(self, data: Any, max_depth: int = 5) -> List[NestedFieldStructure]:
        """Analizar estructura anidada de datos"""
        if not data:
            return []
        
        # Si es lista, tomar el primer elemento para análisis
        if isinstance(data, list) and data:
            data = data[0]
        
        if not isinstance(data, dict):
            return []
        
        return self._analyze_object(data, "", max_depth)
    
    def _analyze_object(self, obj: Dict[str, Any], base_path: str, max_depth: int) -> List[NestedFieldStructure]:
        """Analizar objeto recursivamente"""
        fields = []
        
        if max_depth <= 0:
            return fields
        
        for key, value in obj.items():
            current_path = f"{base_path}.{key}" if base_path else key
            
            # Detectar tipo del campo
            field_type = self._detect_field_type(value)
            is_array = isinstance(value, list)
            
            # Crear estructura básica
            field_structure = NestedFieldStructure(
                path=current_path,
                type=field_type.value,
                sample_value=self._get_sample_value(value),
                is_array=is_array
            )
            
            # Si es objeto anidado, analizar recursivamente
            if isinstance(value, dict):
                nested = self._analyze_object(value, current_path, max_depth - 1)
                if nested:
                    field_structure.nested_fields = nested
                    
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Si es array de objetos, analizar el primer objeto
                nested = self._analyze_object(value[0], current_path, max_depth - 1)
                if nested:
                    field_structure.nested_fields = nested
            
            fields.append(field_structure)
        
        return fields
    
    def _detect_field_type(self, value: Any) -> FieldType:
        """Detectar tipo de campo basado en el valor"""
        if value is None:
            return FieldType.TEXT
        
        value_type = type(value)
        
        # Mapeo básico de tipos
        if value_type in self.type_mapping:
            detected_type = self.type_mapping[value_type]
            
            # Detecciones especiales para strings
            if detected_type == FieldType.TEXT and isinstance(value, str):
                return self._detect_string_subtype(value)
            
            return detected_type
        
        return FieldType.TEXT
    
    def _detect_string_subtype(self, value: str) -> FieldType:
        """Detectar subtipo de string (email, phone, url, etc.)"""
        # Email pattern
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            return FieldType.EMAIL
        
        # Phone pattern (básico)
        if re.match(r'^[+]?[0-9\s\-\(\)]{10,}$', value):
            return FieldType.PHONE
        
        # URL pattern
        if re.match(r'^https?://[\w\.-]+', value):
            return FieldType.URL
        
        # Date pattern (ISO format)
        if re.match(r'^\d{4}-\d{2}-\d{2}', value):
            return FieldType.DATE
        
        return FieldType.TEXT
    
    def _get_sample_value(self, value: Any) -> Any:
        """Obtener valor de muestra limpio"""
        if isinstance(value, (dict, list)):
            # Para objetos complejos, devolver representación simplificada
            if isinstance(value, dict):
                return f"{{object with {len(value)} keys}}"
            elif isinstance(value, list):
                return f"[array with {len(value)} items]"
        
        # Para valores simples, devolver tal como están (con límite de caracteres)
        if isinstance(value, str) and len(value) > 50:
            return f"{value[:47]}..."
        
        return value
    
    def generate_field_paths(self, structure: List[NestedFieldStructure]) -> List[str]:
        """Generar lista de todas las rutas de campos disponibles"""
        paths = []
        
        for field in structure:
            # Agregar el campo actual
            paths.append(field.path)
            
            # Si tiene campos anidados, procesarlos recursivamente
            if field.nested_fields:
                nested_paths = self.generate_field_paths(field.nested_fields)
                paths.extend(nested_paths)
        
        return sorted(paths)
    
    def create_mapping_suggestions(self, structure: List[NestedFieldStructure]) -> List[MappedField]:
        """Crear sugerencias automáticas de mapping"""
        suggestions = []
        paths = self.generate_field_paths(structure)
        
        for i, path in enumerate(paths):
            # Encontrar la estructura del campo
            field_info = self._find_field_by_path(structure, path)
            if not field_info:
                continue
            
            # Generar nombre amigable
            display_name = self._generate_display_name(path)
            
            # Crear sugerencia de mapping
            mapped_field = MappedField(
                api_path=path,
                display_name=display_name,
                field_type=FieldType(field_info.type),
                order=i,
                show_in_table=i < 5,  # Solo mostrar primeros 5 en tabla por defecto
                show_in_card=i < 8,   # Mostrar más en cards
                show_in_form=True
            )
            
            suggestions.append(mapped_field)
        
        return suggestions
    
    def _find_field_by_path(self, structure: List[NestedFieldStructure], target_path: str) -> Optional[NestedFieldStructure]:
        """Encontrar campo por su path"""
        for field in structure:
            if field.path == target_path:
                return field
            
            if field.nested_fields:
                found = self._find_field_by_path(field.nested_fields, target_path)
                if found:
                    return found
        
        return None
    
    def _generate_display_name(self, path: str) -> str:
        """Generar nombre amigable desde path de API"""
        # Tomar la última parte del path
        parts = path.split('.')
        last_part = parts[-1]
        
        # Convertir snake_case y camelCase a formato legible
        name = re.sub(r'([a-z])([A-Z])', r'\1 \2', last_part)  # camelCase
        name = name.replace('_', ' ')  # snake_case
        
        # Capitalizar primera letra de cada palabra
        name = ' '.join(word.capitalize() for word in name.split())
        
        # Traducciones comunes
        translations = {
            'Id': 'ID',
            'Email': 'Correo',
            'Phone': 'Teléfono', 
            'Name': 'Nombre',
            'Last Name': 'Apellido',
            'First Name': 'Nombre',
            'Address': 'Dirección',
            'City': 'Ciudad',
            'Country': 'País',
            'Created At': 'Fecha Creación',
            'Updated At': 'Fecha Actualización'
        }
        
        return translations.get(name, name)
    
    def extract_value_by_path(self, data: Dict[str, Any], path: str) -> Any:
        """Extraer valor de datos usando path de campo"""
        current = data
        parts = path.split('.')
        
        try:
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list) and current:
                    # Si es lista, tomar primer elemento
                    current = current[0] if len(current) > 0 else None
                    if isinstance(current, dict):
                        current = current.get(part)
                else:
                    return None
                
                if current is None:
                    return None
            
            return current
            
        except (KeyError, IndexError, TypeError):
            return None
    
    def validate_mapping_configuration(self, mapping: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validar configuración de mapping"""
        errors = []
        
        # Validar campos requeridos
        if not mapping.get('mapped_fields'):
            errors.append("Al menos un campo debe estar mapeado")
        
        # Validar paths de campos
        for field in mapping.get('mapped_fields', []):
            if not field.get('api_path'):
                errors.append(f"Campo '{field.get('display_name', 'unknown')}' no tiene api_path")
            
            if not field.get('display_name'):
                errors.append(f"Campo con path '{field.get('api_path', 'unknown')}' no tiene display_name")
        
        # Validar nombres únicos
        display_names = [f.get('display_name') for f in mapping.get('mapped_fields', [])]
        duplicates = [name for name in display_names if display_names.count(name) > 1]
        if duplicates:
            errors.append(f"Nombres duplicados encontrados: {', '.join(set(duplicates))}")
        
        return len(errors) == 0, errors
