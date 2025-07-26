#!/usr/bin/env python3
# ================================
# fix_pydantic_v2_robust.py - ARREGLADOR SÚPER ROBUSTO
# ================================
# Guarda como fix_pydantic_v2_robust.py y ejecuta: python fix_pydantic_v2_robust.py

import os
import re
import shutil
import ast
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

class PydanticV2Fixer:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backups_pydantic_fix"
        self.backup_dir.mkdir(exist_ok=True)
        self.fixed_files = []
        self.errors = []
        
    def log(self, message: str, level: str = "INFO"):
        """Logging mejorado"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "FIX": "🔧"}
        print(f"{icons.get(level, '📝')} [{timestamp}] {message}")
    
    def create_backup(self, file_path: Path) -> Path:
        """Crear backup de archivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def find_python_files(self) -> List[Path]:
        """Encontrar todos los archivos Python relevantes"""
        patterns = [
            "app/**/*.py",
            "*.py"
        ]
        
        files = []
        for pattern in patterns:
            files.extend(self.project_root.glob(pattern))
        
        # Filtrar archivos relevantes
        relevant_files = []
        for file in files:
            if any(exclude in str(file) for exclude in ['__pycache__', '.git', 'venv', 'env']):
                continue
            relevant_files.append(file)
        
        return relevant_files
    
    def detect_pydantic_issues(self, content: str) -> Dict[str, List[str]]:
        """Detectar todos los problemas de Pydantic v2"""
        issues = {
            "pyobjectid_old": [],
            "config_class": [],
            "modify_schema": [],
            "json_encoders": [],
            "missing_imports": [],
            "field_validators": []
        }
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # PyObjectId con __modify_schema__
            if '__modify_schema__' in line:
                issues["modify_schema"].append(f"Línea {i}: {line.strip()}")
            
            # class Config en lugar de model_config
            if re.match(r'\s*class Config\s*:', line):
                issues["config_class"].append(f"Línea {i}: {line.strip()}")
            
            # json_encoders sin ConfigDict
            if 'json_encoders' in line and 'ConfigDict' not in content:
                issues["json_encoders"].append(f"Línea {i}: {line.strip()}")
            
            # PyObjectId con __get_pydantic_core_schema__ faltante
            if 'class PyObjectId' in line and '__get_pydantic_core_schema__' not in content:
                issues["pyobjectid_old"].append(f"Línea {i}: PyObjectId no compatible con v2")
            
            # @validator en lugar de @field_validator
            if '@validator' in line and 'from pydantic import' in content:
                issues["field_validators"].append(f"Línea {i}: {line.strip()}")
        
        # Imports faltantes
        if 'ConfigDict' in content and 'from pydantic import' in content:
            if 'ConfigDict' not in content.split('model_config')[0]:
                issues["missing_imports"].append("ConfigDict no importado")
        
        return issues
    
    def fix_pyobjectid(self, content: str) -> str:
        """Arreglar PyObjectId para ser compatible con Pydantic v2"""
        
        self.log("Arreglando PyObjectId...", "FIX")
        
        # PyObjectId compatible con Pydantic v2
        new_pyobjectid = '''
class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2 - FIXED"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        try:
            from pydantic_core import core_schema
            return core_schema.with_info_plain_validator_function(
                cls._validate,
                serialization=core_schema.to_string_ser_schema()
            )
        except ImportError:
            from pydantic_core import core_schema
            return core_schema.str_schema()

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, model_type=None):
        field_schema.update(
            type="string",
            format="objectid", 
            examples=["507f1f77bcf86cd799439011"],
            pattern="^[0-9a-fA-F]{24}$"
        )
        return field_schema
    
    @classmethod
    def _validate(cls, v, info=None):
        if v is None:
            return None
        if isinstance(v, ObjectId):
            return cls(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return cls(v)
            raise ValueError(f"Invalid ObjectId: {v}")
        raise ValueError(f"ObjectId expected, got {type(v)}")
    
    def __str__(self):
        return str(super())
    
    def __repr__(self):
        return f"PyObjectId('{self}')"
'''
        
        # Remover PyObjectId existente
        pattern = r'class PyObjectId.*?(?=\n\nclass|\n\n# |\nclass [A-Z]|$)'
        content = re.sub(pattern, new_pyobjectid, content, flags=re.DOTALL)
        
        # Si no se encontró, agregar al final de los imports
        if 'class PyObjectId' not in content and 'ObjectId' in content:
            # Encontrar donde terminar los imports
            lines = content.split('\n')
            insert_line = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('from ') or line.strip().startswith('import '):
                    insert_line = i + 1
                elif line.strip() and not line.startswith('#'):
                    break
            
            lines.insert(insert_line, new_pyobjectid)
            content = '\n'.join(lines)
        
        return content
    
    def fix_config_class(self, content: str) -> str:
        """Convertir class Config a model_config"""
        
        self.log("Convirtiendo class Config a model_config...", "FIX")
        
        def replace_config_class(match):
            full_match = match.group(0)
            indent = match.group(1)
            config_body = match.group(2)
            
            # Extraer configuraciones
            config_items = []
            for line in config_body.split('\n'):
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    config_items.append(f"        {line}")
            
            # Crear model_config
            if config_items:
                new_config = f"{indent}model_config = ConfigDict(\n"
                new_config += ',\n'.join(config_items)
                new_config += f"\n{indent})"
            else:
                new_config = f"{indent}model_config = ConfigDict()"
            
            return new_config
        
        # Patrón para capturar class Config completa
        pattern = r'(\s+)class Config:\s*\n((?:\s{2,}.*\n?)*)'
        content = re.sub(pattern, replace_config_class, content)
        
        return content
    
    def fix_imports(self, content: str) -> str:
        """Arreglar imports para Pydantic v2"""
        
        self.log("Arreglando imports...", "FIX")
        
        # Si usa model_config pero no importa ConfigDict
        if 'model_config = ConfigDict' in content:
            if 'from pydantic import' in content and 'ConfigDict' not in content.split('model_config')[0]:
                content = re.sub(
                    r'from pydantic import (.*?)BaseModel',
                    r'from pydantic import \1BaseModel, ConfigDict',
                    content
                )
        
        # Agregar pydantic_core si se necesita
        if '__get_pydantic_core_schema__' in content and 'from pydantic_core import' not in content:
            # Buscar línea de imports de pydantic
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'from pydantic import' in line:
                    lines.insert(i + 1, 'from pydantic_core import core_schema')
                    break
            content = '\n'.join(lines)
        
        # Arreglar @validator -> @field_validator
        content = re.sub(r'@validator\(', '@field_validator(', content)
        if '@field_validator' in content and 'field_validator' not in content.split('@field_validator')[0]:
            content = re.sub(
                r'from pydantic import (.*?)BaseModel',
                r'from pydantic import \1BaseModel, field_validator',
                content
            )
        
        return content
    
    def add_standard_config(self, content: str) -> str:
        """Agregar configuración estándar si falta"""
        
        # Si tiene modelos pero no model_config
        if 'class ' in content and 'BaseModel' in content and 'model_config' not in content:
            
            standard_config = '''
# Configuración estándar para Pydantic v2
STANDARD_MODEL_CONFIG = ConfigDict(
    populate_by_name=True,
    arbitrary_types_allowed=True,
    json_encoders={ObjectId: str},
    str_strip_whitespace=True,
    validate_assignment=True
)
'''
            
            # Agregar después de los imports
            lines = content.split('\n')
            insert_line = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('from ') or line.strip().startswith('import '):
                    insert_line = i + 1
                elif line.strip() and not line.startswith('#'):
                    break
            
            lines.insert(insert_line, standard_config)
            content = '\n'.join(lines)
            
            # Agregar model_config a modelos que no lo tengan
            pattern = r'(class \w+\(BaseModel\):.*?(?=\n\nclass|\n\n# |$))'
            
            def add_config_to_model(match):
                model_content = match.group(1)
                if 'model_config' not in model_content:
                    # Encontrar la última línea del modelo
                    lines = model_content.split('\n')
                    # Agregar model_config antes del final
                    lines.append('    model_config = STANDARD_MODEL_CONFIG')
                    return '\n'.join(lines)
                return model_content
            
            content = re.sub(pattern, add_config_to_model, content, flags=re.DOTALL)
        
        return content
    
    def fix_file(self, file_path: Path) -> bool:
        """Arreglar un archivo específico"""
        
        try:
            # Leer archivo
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Detectar problemas
            issues = self.detect_pydantic_issues(original_content)
            
            # Si no hay problemas, skip
            if not any(issues.values()):
                return False
            
            self.log(f"Arreglando: {file_path}", "FIX")
            
            # Crear backup
            backup_path = self.create_backup(file_path)
            self.log(f"Backup creado: {backup_path}", "INFO")
            
            # Aplicar arreglos
            content = original_content
            
            # 1. Arreglar PyObjectId
            if issues["pyobjectid_old"] or issues["modify_schema"]:
                content = self.fix_pyobjectid(content)
            
            # 2. Arreglar class Config
            if issues["config_class"]:
                content = self.fix_config_class(content)
            
            # 3. Arreglar imports
            content = self.fix_imports(content)
            
            # 4. Agregar configuración estándar si es necesario
            content = self.add_standard_config(content)
            
            # Guardar archivo arreglado
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.fixed_files.append(str(file_path))
            self.log(f"✅ Arreglado: {file_path}", "SUCCESS")
            
            return True
            
        except Exception as e:
            error_msg = f"Error arreglando {file_path}: {e}"
            self.errors.append(error_msg)
            self.log(error_msg, "ERROR")
            return False
    
    def test_imports(self) -> List[str]:
        """Probar imports después del arreglo"""
        
        self.log("Probando imports...", "INFO")
        
        test_modules = [
            "app.models.business",
            "app.models.api_config",
            "app.models.entity", 
            "app.models.user",
            "app.main"
        ]
        
        working_modules = []
        broken_modules = []
        
        for module in test_modules:
            try:
                # Cambiar al directorio del proyecto
                old_path = sys.path[:]
                sys.path.insert(0, str(self.project_root))
                
                exec(f"import {module}")
                working_modules.append(module)
                self.log(f"✅ {module}", "SUCCESS")
                
            except Exception as e:
                broken_modules.append(f"{module}: {e}")
                self.log(f"❌ {module}: {e}", "ERROR")
            finally:
                sys.path = old_path
        
        return working_modules, broken_modules
    
    def run(self):
        """Ejecutar el arreglador completo"""
        
        self.log("🚀 Iniciando arreglador robusto de Pydantic v2...", "INFO")
        
        # Encontrar archivos
        python_files = self.find_python_files()
        self.log(f"Encontrados {len(python_files)} archivos Python", "INFO")
        
        # Arreglar archivos
        for file_path in python_files:
            if file_path.suffix == '.py':
                self.fix_file(file_path)
        
        # Resumen
        self.log(f"\n📊 RESUMEN:", "INFO")
        self.log(f"Archivos arreglados: {len(self.fixed_files)}", "SUCCESS")
        
        for file in self.fixed_files:
            self.log(f"  ✅ {file}", "SUCCESS")
        
        if self.errors:
            self.log(f"Errores: {len(self.errors)}", "ERROR")
            for error in self.errors:
                self.log(f"  ❌ {error}", "ERROR")
        
        # Probar imports
        working, broken = self.test_imports()
        
        if broken:
            self.log(f"\n🔧 ARREGLOS ADICIONALES NECESARIOS:", "WARNING")
            for issue in broken:
                self.log(f"  ⚠️ {issue}", "WARNING")
        else:
            self.log(f"\n🎉 ¡TODOS LOS IMPORTS FUNCIONAN!", "SUCCESS")
        
        # Comandos finales
        self.log(f"\n💡 PRÓXIMOS PASOS:", "INFO")
        self.log(f"1. uvicorn app.main:app --reload", "INFO")
        self.log(f"2. Ve a: http://localhost:8000", "INFO")
        self.log(f"3. ¡Deberías ver tu aplicación funcionando!", "INFO")
        
        if self.fixed_files:
            self.log(f"\n📁 Backups guardados en: {self.backup_dir}", "INFO")

# ================================
# FUNCIÓN PRINCIPAL
# ================================

def main():
    """Función principal"""
    
    print("🔧 ARREGLADOR ROBUSTO DE PYDANTIC V2")
    print("=" * 50)
    
    # Verificar si estamos en el directorio correcto
    if not Path("app").exists():
        print("❌ No se encuentra el directorio 'app'")
        print("   Ejecuta este script desde la raíz del proyecto")
        return
    
    # Ejecutar arreglador
    fixer = PydanticV2Fixer()
    fixer.run()

if __name__ == "__main__":
    main()