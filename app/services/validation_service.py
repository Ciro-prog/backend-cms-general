# ================================
# app/services/validation_service.py
# ================================

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from ..utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

class ValidationService:
    """Servicio para validaciones dinámicas de campos"""
    
    def __init__(self):
        self.validators = {
            "email": self._validate_email,
            "phone": self._validate_phone,
            "url": self._validate_url,
            "min": self._validate_min,
            "max": self._validate_max,
            "regex": self._validate_regex,
            "required": self._validate_required,
            "numeric": self._validate_numeric,
            "date": self._validate_date,
            "boolean": self._validate_boolean
        }
    
    async def validate_field(self, value: Any, field_config: Dict[str, Any]) -> Any:
        """Validar un campo según su configuración"""
        
        field_name = field_config.get("campo", "unknown")
        field_type = field_config.get("tipo", "text")
        validacion = field_config.get("validacion")
        obligatorio = field_config.get("obligatorio", False)
        
        # Verificar si es obligatorio
        if obligatorio and (value is None or value == ""):
            raise ValidationError(field_name, "Campo obligatorio")
        
        # Si el valor está vacío y no es obligatorio, permitir
        if value is None or value == "":
            return value
        
        # Validar por tipo de campo
        validated_value = await self._validate_by_type(value, field_type, field_name)
        
        # Aplicar validaciones personalizadas
        if validacion:
            validated_value = await self._apply_custom_validations(
                validated_value, validacion, field_name
            )
        
        return validated_value
    
    async def _validate_by_type(self, value: Any, field_type: str, field_name: str) -> Any:
        """Validar por tipo de campo"""
        
        if field_type == "text":
            return str(value)
        
        elif field_type == "number":
            try:
                return float(value) if '.' in str(value) else int(value)
            except (ValueError, TypeError):
                raise ValidationError(field_name, "Debe ser un número válido")
        
        elif field_type == "email":
            return await self._validate_email(value, field_name)
        
        elif field_type == "phone":
            return await self._validate_phone(value, field_name)
        
        elif field_type == "date":
            return await self._validate_date(value, field_name)
        
        elif field_type == "boolean":
            return await self._validate_boolean(value, field_name)
        
        elif field_type == "select":
            return str(value)  # Las opciones se validan en el frontend
        
        elif field_type == "url":
            return await self._validate_url(value, field_name)
        
        else:
            return value
    
    async def _apply_custom_validations(
        self, 
        value: Any, 
        validacion: str, 
        field_name: str
    ) -> Any:
        """Aplicar validaciones personalizadas"""
        
        # Parsear string de validación (ej: "min:5,max:100,regex:^[a-z]+$")
        validations = self._parse_validation_string(validacion)
        
        for validation_name, validation_param in validations.items():
            if validation_name in self.validators:
                value = await self.validators[validation_name](
                    value, validation_param, field_name
                )
        
        return value
    
    def _parse_validation_string(self, validacion: str) -> Dict[str, str]:
        """Parsear string de validación"""
        validations = {}
        
        for rule in validacion.split(','):
            rule = rule.strip()
            if ':' in rule:
                name, param = rule.split(':', 1)
                validations[name] = param
            else:
                validations[rule] = None
        
        return validations
    
    # === VALIDATORS ESPECÍFICOS ===
    
    async def _validate_email(self, value: Any, param: Any = None, field_name: str = "email") -> str:
        """Validar email"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        email_str = str(value)
        
        if not re.match(email_pattern, email_str):
            raise ValidationError(field_name, "Formato de email inválido")
        
        return email_str
    
    async def _validate_phone(self, value: Any, param: Any = None, field_name: str = "phone") -> str:
        """Validar teléfono"""
        phone_str = str(value).strip()
        
        # Remover caracteres no numéricos excepto + al inicio
        clean_phone = re.sub(r'[^\d+]', '', phone_str)
        
        # Verificar formato básico
        if not clean_phone:
            raise ValidationError(field_name, "Número de teléfono requerido")
        
        # Verificar longitud mínima
        digits_only = re.sub(r'[^\d]', '', clean_phone)
        if len(digits_only) < 10:
            raise ValidationError(field_name, "Número de teléfono muy corto")
        
        return clean_phone
    
    async def _validate_url(self, value: Any, param: Any = None, field_name: str = "url") -> str:
        """Validar URL"""
        url_pattern = r'^https?:\/\/[^\s/$.?#].[^\s]*$'
        url_str = str(value)
        
        if not re.match(url_pattern, url_str):
            raise ValidationError(field_name, "URL inválida")
        
        return url_str
    
    async def _validate_min(self, value: Any, param: str, field_name: str) -> Any:
        """Validar valor mínimo"""
        min_val = float(param)
        
        if isinstance(value, (int, float)):
            if value < min_val:
                raise ValidationError(field_name, f"Valor mínimo: {min_val}")
        elif isinstance(value, str):
            if len(value) < min_val:
                raise ValidationError(field_name, f"Longitud mínima: {min_val} caracteres")
        
        return value
    
    async def _validate_max(self, value: Any, param: str, field_name: str) -> Any:
        """Validar valor máximo"""
        max_val = float(param)
        
        if isinstance(value, (int, float)):
            if value > max_val:
                raise ValidationError(field_name, f"Valor máximo: {max_val}")
        elif isinstance(value, str):
            if len(value) > max_val:
                raise ValidationError(field_name, f"Longitud máxima: {max_val} caracteres")
        
        return value
    
    async def _validate_regex(self, value: Any, param: str, field_name: str) -> Any:
        """Validar con expresión regular"""
        if not re.match(param, str(value)):
            raise ValidationError(field_name, "Formato inválido")
        
        return value
    
    async def _validate_required(self, value: Any, param: Any = None, field_name: str = "field") -> Any:
        """Validar campo requerido"""
        if value is None or value == "":
            raise ValidationError(field_name, "Campo requerido")
        
        return value
    
    async def _validate_numeric(self, value: Any, param: Any = None, field_name: str = "field") -> Any:
        """Validar que sea numérico"""
        try:
            return float(value) if '.' in str(value) else int(value)
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Debe ser un número")
    
    async def _validate_date(self, value: Any, param: Any = None, field_name: str = "date") -> datetime:
        """Validar fecha"""
        if isinstance(value, datetime):
            return value
        
        date_str = str(value)
        
        # Intentar varios formatos de fecha
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d/%m/%Y",
            "%d-%m-%Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValidationError(field_name, "Formato de fecha inválido")
    
    async def _validate_boolean(self, value: Any, param: Any = None, field_name: str = "boolean") -> bool:
        """Validar booleano"""
        if isinstance(value, bool):
            return value
        
        value_str = str(value).lower()
        
        if value_str in ['true', '1', 'yes', 'on', 'active']:
            return True
        elif value_str in ['false', '0', 'no', 'off', 'inactive']:
            return False
        else:
            raise ValidationError(field_name, "Debe ser verdadero o falso")