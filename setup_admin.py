#!/usr/bin/env python3
"""
🚨 SCRIPT DE LIMPIEZA DE EMERGENCIA
Ejecutar para encontrar y comentar rutas problemáticas automáticamente
"""

import os
import shutil
from pathlib import Path

def backup_main_py():
    """Crear backup del main.py antes de modificar"""
    if os.path.exists("app/main.py"):
        shutil.copy2("app/main.py", "app/main.py.backup")
        print("✅ Backup creado: app/main.py.backup")

def clean_main_py():
    """Limpiar rutas problemáticas de main.py"""
    
    if not os.path.exists("app/main.py"):
        print("❌ No se encuentra app/main.py")
        return False
    
    # Leer el archivo
    with open("app/main.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Líneas problemáticas a comentar
    problematic_patterns = [
        "@app.get(\"/admin",
        "async def admin_",
        "async def redirect_to_admin",
        "from .frontend.routers.admin",
        "admin_frontend_router",
        "RedirectResponse(url=\"/admin\"",
        "templates = Jinja2Templates(directory=\"app/frontend/templates\")",  # Si está duplicado
    ]
    
    cleaned_lines = []
    changes_made = 0
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        should_comment = False
        
        # Verificar si la línea contiene patrones problemáticos
        for pattern in problematic_patterns:
            if pattern in line and not line_stripped.startswith("#"):
                should_comment = True
                break
        
        if should_comment:
            # Comentar la línea
            if line.startswith("    "):  # Conservar indentación
                cleaned_lines.append("    # " + line[4:])
            elif line.startswith("\t"):
                cleaned_lines.append("\t# " + line[1:])
            else:
                cleaned_lines.append("# " + line)
            changes_made += 1
            print(f"🔧 Comentada línea {i+1}: {line_stripped[:50]}...")
        else:
            cleaned_lines.append(line)
    
    # Escribir archivo limpio
    with open("app/main.py", "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)
    
    print(f"✅ {changes_made} líneas comentadas en main.py")
    return changes_made > 0

def remove_problematic_files():
    """Eliminar archivos problemáticos"""
    files_to_remove = [
        "app/frontend/routers/admin.py",
        "app/frontend/templates/admin",
    ]
    
    for file_path in files_to_remove:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"✅ Eliminado archivo: {file_path}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"✅ Eliminado directorio: {file_path}")
        except Exception as e:
            print(f"⚠️ No se pudo eliminar {file_path}: {e}")

def verify_main_py():
    """Verificar que main.py no tiene líneas problemáticas"""
    
    if not os.path.exists("app/main.py"):
        return False
    
    with open("app/main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Buscar patrones problemáticos no comentados
    problematic_active = []
    
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if (line_stripped.startswith('@app.get("/admin') and 
            not line_stripped.startswith('#')):
            problematic_active.append(f"Línea {i}: {line_stripped}")
        
        if (line_stripped.startswith('async def admin_') and 
            not line_stripped.startswith('#')):
            problematic_active.append(f"Línea {i}: {line_stripped}")
        
        if ('admin_frontend_router' in line_stripped and 
            not line_stripped.startswith('#')):
            problematic_active.append(f"Línea {i}: {line_stripped}")
    
    if problematic_active:
        print("❌ Aún hay líneas problemáticas:")
        for line in problematic_active:
            print(f"   {line}")
        return False
    else:
        print("✅ No se encontraron líneas problemáticas activas")
        return True

def main():
    """Función principal de limpieza"""
    print("🚨 LIMPIEZA DE EMERGENCIA DEL BACKEND")
    print("=" * 50)
    
    # 1. Crear backup
    backup_main_py()
    
    # 2. Eliminar archivos problemáticos
    print("\n📁 Eliminando archivos problemáticos...")
    remove_problematic_files()
    
    # 3. Limpiar main.py
    print("\n🧹 Limpiando main.py...")
    if clean_main_py():
        print("✅ main.py limpiado exitosamente")
    else:
        print("⚠️ No se realizaron cambios en main.py")
    
    # 4. Verificar resultado
    print("\n🔍 Verificando resultado...")
    if verify_main_py():
        print("✅ Limpieza completada exitosamente")
        print("\n🚀 PRÓXIMOS PASOS:")
        print("1. Ejecutar: python run.py")
        print("2. Verificar: curl http://localhost:8000/health")
        print("3. Si funciona, proceder con los templates")
    else:
        print("❌ Aún hay problemas. Revisar manualmente main.py")
        print("\n🔧 SOLUCIÓN MANUAL:")
        print("Abrir app/main.py y comentar TODAS las líneas que contengan:")
        print("- @app.get(\"/admin")
        print("- async def admin_")
        print("- admin_frontend_router")
        print("- RedirectResponse(url=\"/admin\"")
    
    print(f"\n💾 Backup guardado en: app/main.py.backup")

if __name__ == "__main__":
    main()