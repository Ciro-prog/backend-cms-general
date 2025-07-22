#!/usr/bin/env python3
"""Verificación rápida del backend"""

import os
import sys

def check_file(path, required=True):
    """Verificar si existe un archivo"""
    exists = os.path.exists(path)
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {path}")
    return exists

def check_directory(path):
    """Verificar si existe un directorio"""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} {path}/")
    return exists

def main():
    print("🔍 Verificando estructura del backend...\n")
    
    # Archivos críticos
    print("📄 Archivos críticos:")
    files_ok = True
    files_ok &= check_file("app/main.py")
    files_ok &= check_file("app/routers/__init__.py")
    files_ok &= check_file("app/routers/auth.py")
    files_ok &= check_file("app/frontend/auth.py")
    files_ok &= check_file("app/frontend/routers/__init__.py")
    
    print("\n📄 Archivos frontend:")
    files_ok &= check_file("app/frontend/routers/auth.py", False)
    files_ok &= check_file("app/frontend/templates/auth/login.html", False)
    
    print("\n📁 Directorios:")
    dirs_ok = True
    dirs_ok &= check_directory("app/frontend/templates/auth")
    dirs_ok &= check_directory("app/frontend/static/css")
    dirs_ok &= check_directory("app/frontend/static/js")
    
    print("\n📦 Test de importación:")
    try:
        import app.main
        print("✅ app.main importa correctamente")
        import_ok = True
    except Exception as e:
        print(f"❌ Error importando app.main: {e}")
        import_ok = False
    
    print(f"\n📊 Resultado:")
    print(f"  Archivos: {'✅' if files_ok else '❌'}")
    print(f"  Directorios: {'✅' if dirs_ok else '❌'}")
    print(f"  Importación: {'✅' if import_ok else '❌'}")
    
    if files_ok and dirs_ok and import_ok:
        print("\n🎉 ¡Todo OK! Puedes ejecutar 'python run.py'")
        return 0
    else:
        print("\n🔧 Ejecuta 'python fix_backend.py' para corregir")
        return 1

if __name__ == "__main__":
    sys.exit(main())