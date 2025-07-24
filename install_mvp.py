# ================================
# install_mvp.py - SCRIPT DE INSTALACIÓN COMPLETA
# ================================

#!/usr/bin/env python3
"""
Script de instalación completa del MVP del CMS Dinámico
"""

import os
import sys
import subprocess
import asyncio
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command, description=""):
    """Ejecutar comando del sistema"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        print(f"   Output: {e.stdout}")
        print(f"   Error: {e.stderr}")
        return None

def check_python_version():
    """Verificar versión de Python"""
    print("🐍 Verificando versión de Python...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requerido")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} OK")

def check_pip():
    """Verificar que pip esté disponible"""
    result = run_command("pip --version", "Verificando pip")
    if not result:
        print("❌ pip no está disponible")
        sys.exit(1)

def install_dependencies():
    """Instalar dependencias de Python"""
    requirements = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "motor==3.3.2",
        "aiohttp==3.9.1",
        "pydantic==2.5.0",
        "python-multipart==0.0.6",
        "jinja2==3.1.2",
        "python-dotenv==1.0.0"
    ]
    
    for req in requirements:
        result = run_command(f"pip install {req}", f"Instalando {req.split('==')[0]}")
        if not result:
            print(f"❌ Error instalando {req}")
            sys.exit(1)

def create_directory_structure():
    """Crear estructura de directorios"""
    directories = [
        "app/frontend/templates/business_types",
        "app/frontend/templates/api_configs", 
        "app/frontend/templates/components",
        "app/frontend/templates/logs",
        "app/frontend/static/css",
        "app/frontend/static/js",
        "app/frontend/static/images"
    ]
    
    print("📁 Creando estructura de directorios...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ {directory}")

def create_env_file():
    """Crear archivo .env si no existe"""
    env_content = """# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=cms_dinamico

# FastAPI Configuration
SECRET_KEY=cms-dinamico-mvp-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true

# Logging
LOG_LEVEL=INFO

# External Services (Simuladas para MVP)
WAHA_URL=http://localhost:3000
N8N_URL=http://localhost:5678
"""
    
    if not os.path.exists(".env"):
        print("📝 Creando archivo .env...")
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Archivo .env creado")
    else:
        print("ℹ️ Archivo .env ya existe")

def create_missing_templates():
    """Crear templates faltantes con contenido básico"""
    templates = {
        "app/frontend/templates/business_types/businesses.html": """{% extends "base.html" %}
{% block title %}Businesses - CMS Dinámico{% endblock %}
{% block content %}
<div class="space-y-6">
    <div class="md:flex md:items-center md:justify-between">
        <h2 class="text-2xl font-bold text-gray-900">Business Instances</h2>
        <button class="btn btn-primary">
            <i class="fas fa-plus mr-2"></i>Nueva Business Instance
        </button>
    </div>
    <div class="bg-white shadow rounded-lg p-6">
        <p class="text-gray-500">Gestión de instancias de negocio - En desarrollo</p>
    </div>
</div>
{% endblock %}""",
        
        "app/frontend/templates/components/list.html": """{% extends "base.html" %}
{% block title %}Componentes - CMS Dinámico{% endblock %}
{% block content %}
<div class="space-y-6">
    <div class="md:flex md:items-center md:justify-between">
        <h2 class="text-2xl font-bold text-gray-900">Dynamic Components</h2>
        <button class="btn btn-primary">
            <i class="fas fa-plus mr-2"></i>Nuevo Componente
        </button>
    </div>
    <div class="bg-white shadow rounded-lg p-6">
        <p class="text-gray-500">Gestión de componentes dinámicos - En desarrollo</p>
    </div>
</div>
{% endblock %}""",
        
        "app/frontend/templates/logs/list.html": """{% extends "base.html" %}
{% block title %}Logs - CMS Dinámico{% endblock %}
{% block content %}
<div class="space-y-6">
    <div class="md:flex md:items-center md:justify-between">
        <h2 class="text-2xl font-bold text-gray-900">System Logs</h2>
    </div>
    <div class="bg-white shadow rounded-lg p-6">
        <p class="text-gray-500">Logs del sistema - En desarrollo</p>
    </div>
</div>
{% endblock %}""",
        
        "app/frontend/templates/auth/login.html": """{% extends "base.html" %}
{% block title %}Login - CMS Dinámico{% endblock %}
{% block content %}
<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
        <div>
            <div class="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
                <i class="fas fa-cogs text-blue-600 text-2xl"></i>
            </div>
            <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
                CMS Dinámico MVP
            </h2>
            <p class="mt-2 text-center text-sm text-gray-600">
                Inicia sesión para continuar
            </p>
        </div>
        <form class="mt-8 space-y-6" method="post" action="/login">
            {% if error %}
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    {{ error }}
                </div>
            {% endif %}
            
            <div class="rounded-md shadow-sm -space-y-px">
                <div>
                    <input id="username" name="username" type="text" required 
                           class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" 
                           placeholder="Usuario">
                </div>
                <div>
                    <input id="password" name="password" type="password" required 
                           class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" 
                           placeholder="Contraseña">
                </div>
            </div>

            <div>
                <button type="submit" 
                        class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    Iniciar Sesión
                </button>
            </div>
            
            <div class="mt-6">
                <div class="text-center text-sm text-gray-600">
                    <strong>Usuarios de prueba:</strong><br>
                    superadmin / superadmin<br>
                    admin / admin<br>
                    tecnico / tecnico<br>
                    usuario / usuario
                </div>
            </div>
        </form>
    </div>
</div>
{% endblock %}"""
    }
    
    print("📄 Creando templates faltantes...")
    for template_path, content in templates.items():
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        if not os.path.exists(template_path):
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"   ✅ {template_path}")

def check_mongodb():
    """Verificar si MongoDB está disponible"""
    print("🗄️ Verificando MongoDB...")
    result = run_command("mongosh --eval 'db.runCommand({ connectionStatus: 1 })'", "Conectando a MongoDB")
    if result:
        print("✅ MongoDB está disponible")
        return True
    else:
        print("⚠️ MongoDB no está disponible. El MVP funcionará pero sin persistencia.")
        print("   Para instalar MongoDB: https://docs.mongodb.com/manual/installation/")
        return False

async def setup_database():
    """Configurar base de datos e inicializar datos"""
    print("🔧 Configurando base de datos...")
    try:
        # Importar módulos después de instalar dependencias
        from app.database import connect_to_mongo
        from app.services.business_service import BusinessService
        
        await connect_to_mongo()
        print("✅ Conexión a MongoDB establecida")
        
        # Obtener base de datos e inicializar datos
        from app.database import get_database
        db = get_database()
        service = BusinessService(db)
        await service.initialize_default_data()
        
        print("✅ Datos por defecto inicializados")
        
    except Exception as e:
        print(f"⚠️ Error configurando base de datos: {e}")
        print("   El MVP funcionará en modo demo sin persistencia")

def main():
    """Función principal de instalación"""
    print("🚀 Instalador del CMS Dinámico MVP\n")
    
    # Verificaciones previas
    check_python_version()
    check_pip()
    
    # Instalar dependencias
    install_dependencies()
    
    # Crear estructura
    create_directory_structure()
    create_env_file()
    create_missing_templates()
    
    # Verificar MongoDB
    mongodb_available = check_mongodb()
    
    # Configurar base de datos si está disponible
    if mongodb_available:
        try:
            asyncio.run(setup_database())
        except Exception as e:
            print(f"⚠️ Error en setup de BD: {e}")
    
    print("\n🎉 ¡Instalación completada!")
    print("\n📝 Próximos pasos:")
    print("1. Ejecutar: python run_mvp.py")
    print("2. Abrir: http://localhost:8000")
    print("3. Login: superadmin / superadmin")
    print("4. Explorar las funcionalidades del MVP")
    
    if not mongodb_available:
        print("\n⚠️ Nota: MongoDB no está disponible.")
        print("   El MVP funcionará con datos temporales.")
        print("   Para persistencia, instala MongoDB y reinicia.")

if __name__ == "__main__":
    main()