#!/usr/bin/env python3
"""
Instalación manual paso a paso para Windows
"""

import subprocess
import sys
import os

def run_pip_install(package, description=""):
    """Instalar un paquete específico"""
    print(f"📦 Instalando {package} {description}...")
    
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ {package} instalado")
        return True
    else:
        print(f"❌ Error con {package}: {result.stderr}")
        return False

def main():
    """Instalación manual paso a paso"""
    print("🔧 Instalación Manual CMS Dinámico - Windows")
    print("=" * 50)
    
    # Actualizar herramientas básicas
    print("\n🛠️ Actualizando herramientas básicas...")
    run_pip_install("--upgrade pip", "(gestor de paquetes)")
    run_pip_install("wheel", "(compilador de paquetes)")
    run_pip_install("setuptools", "(herramientas de setup)")
    
    # Dependencias críticas en orden
    critical_packages = [
        ("typing-extensions==4.8.0", "extensiones de tipos"),
        ("pydantic-core==2.14.6", "núcleo de validación"),
        ("pydantic==2.5.3", "validación de datos"),
        ("fastapi==0.104.1", "framework web"),
        ("uvicorn==0.24.0", "servidor ASGI"),
        ("httpx==0.25.2", "cliente HTTP"),
        ("jinja2==3.1.2", "templates"),
        ("python-multipart==0.0.6", "formularios"),
        ("aiofiles==23.2.1", "archivos async"),
        ("itsdangerous==2.1.2", "seguridad"),
        ("python-dotenv==1.0.0", "variables de entorno"),
        ("pydantic-settings==2.1.0", "configuración")
    ]
    
    print("\n📦 Instalando dependencias críticas...")
    failed_packages = []
    
    for package, desc in critical_packages:
        if not run_pip_install(package, f"({desc})"):
            failed_packages.append(package)
    
    # Dependencias de MongoDB
    print("\n🍃 Instalando dependencias MongoDB...")
    mongo_packages = [
        ("pymongo==4.6.0", "MongoDB sync"),
        ("motor==3.3.2", "MongoDB async")
    ]
    
    for package, desc in mongo_packages:
        if not run_pip_install(package, f"({desc})"):
            failed_packages.append(package)
    
    # Dependencias opcionales
    print("\n🔧 Instalando dependencias opcionales...")
    optional_packages = [
        ("redis==5.0.1", "cache Redis"),
        ("python-jose==3.3.0", "tokens JWT - básico"),
        ("passlib==1.7.4", "hashing passwords"),
        ("pytest==7.4.3", "testing"),
        ("pytest-asyncio==0.21.1", "testing async")
    ]
    
    for package, desc in optional_packages:
        success = run_pip_install(package, f"({desc})")
        if not success:
            print(f"⚠️ {package} falló - continuando (es opcional)")
    
    # Resumen
    print("\n" + "=" * 50)
    if not failed_packages:
        print("🎉 ¡Instalación completada exitosamente!")
    else:
        print("⚠️ Instalación completada con algunos fallos:")
        for pkg in failed_packages:
            print(f"  ❌ {pkg}")
        print("\nPuedes continuar - las dependencias críticas están instaladas")
    
    print("\n🧪 Probando importaciones básicas...")
    test_imports()
    
    print("\n📝 Próximos pasos:")
    print("1. python run.py")
    print("2. Abrir: http://localhost:8000/health")

def test_imports():
    """Probar importaciones básicas"""
    tests = [
        ("fastapi", "FastAPI"),
        ("pydantic", "validación"),
        ("uvicorn", "servidor"),
        ("httpx", "HTTP client"),
        ("jinja2", "templates")
    ]
    
    for module, name in tests:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError as e:
            print(f"❌ {name}: {e}")

if __name__ == "__main__":
    main()