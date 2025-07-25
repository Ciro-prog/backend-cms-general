#!/usr/bin/env python3
"""
Script para limpiar cache de Python y reinstalar dependencias
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def remove_directory(path):
    """Remover directorio si existe"""
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            print(f"✅ Removido: {path}")
            return True
        except Exception as e:
            print(f"❌ Error removiendo {path}: {e}")
            return False
    return True

def remove_file(path):
    """Remover archivo si existe"""
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"✅ Removido: {path}")
            return True
        except Exception as e:
            print(f"❌ Error removiendo {path}: {e}")
            return False
    return True

def find_and_remove_pycache():
    """Encontrar y remover todos los __pycache__"""
    print("🔍 Buscando directorios __pycache__...")
    
    current_dir = Path(".")
    removed_count = 0
    
    for pycache_dir in current_dir.rglob("__pycache__"):
        if pycache_dir.is_dir():
            try:
                shutil.rmtree(pycache_dir)
                print(f"  ✅ {pycache_dir}")
                removed_count += 1
            except Exception as e:
                print(f"  ❌ {pycache_dir}: {e}")
    
    print(f"📊 Removidos {removed_count} directorios __pycache__")

def find_and_remove_pyc():
    """Encontrar y remover todos los .pyc"""
    print("🔍 Buscando archivos .pyc...")
    
    current_dir = Path(".")
    removed_count = 0
    
    for pyc_file in current_dir.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            print(f"  ✅ {pyc_file}")
            removed_count += 1
        except Exception as e:
            print(f"  ❌ {pyc_file}: {e}")
    
    print(f"📊 Removidos {removed_count} archivos .pyc")

def reinstall_pydantic():
    """Reinstalar Pydantic completamente"""
    print("\n🔄 Reinstalando Pydantic...")
    
    # Desinstalar primero
    cmd_uninstall = f"{sys.executable} -m pip uninstall -y pydantic pydantic-core pydantic-settings"
    result = subprocess.run(cmd_uninstall, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Pydantic desinstalado")
    else:
        print(f"⚠️ Error desinstalando: {result.stderr}")
    
    # Reinstalar
    cmd_install = f"{sys.executable} -m pip install pydantic>=2.11.7 pydantic-core>=2.23.0 pydantic-settings>=2.1.0"
    result = subprocess.run(cmd_install, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Pydantic reinstalado")
        return True
    else:
        print(f"❌ Error reinstalando: {result.stderr}")
        return False

def main():
    """Función principal"""
    print("🧹 Limpieza de Cache Python - CMS Dinámico")
    print("=" * 50)
    
    # Limpiar cache de Python
    find_and_remove_pycache()
    find_and_remove_pyc()
    
    # Remover directorios específicos problemáticos
    problematic_dirs = [
        ".pytest_cache",
        "build",
        "dist",
        "*.egg-info"
    ]
    
    print("\n🗑️ Removiendo directorios problemáticos...")
    for pattern in problematic_dirs:
        if "*" in pattern:
            # Usar glob para patrones
            from glob import glob
            for path in glob(pattern):
                remove_directory(path)
        else:
            remove_directory(pattern)
    
    # Reinstalar Pydantic
    reinstall_success = reinstall_pydantic()
    
    print("\n" + "=" * 50)
    if reinstall_success:
        print("🎉 ¡Limpieza completada!")
        print("\n📝 Próximos pasos:")
        print("1. python install_dependencies.py  # Para verificar todo")
        print("2. python run.py")
    else:
        print("⚠️ Limpieza parcial completada")
        print("   Intenta reinstalar manualmente:")
        print("   pip install --force-reinstall pydantic>=2.11.7")

if __name__ == "__main__":
    main()