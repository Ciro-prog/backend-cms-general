# ================================
# startup_mvp.py - SCRIPT ÚNICO PARA INICIAR TODO
# ================================

#!/usr/bin/env python3
"""
Script único para iniciar el MVP del CMS Dinámico
Incluye instalación, configuración y ejecución
"""

import os
import sys
import subprocess
import asyncio
import logging
import time
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MVPSetup:
    """Clase para gestionar la configuración del MVP"""
    
    def __init__(self):
        self.base_dir = Path.cwd()
        self.required_packages = [
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0", 
            "motor==3.3.2",
            "aiohttp==3.9.1",
            "pydantic==2.5.0",
            "python-multipart==0.0.6",
            "jinja2==3.1.2",
            "python-dotenv==1.0.0"
        ]
    
    def check_python(self):
        """Verificar versión de Python"""
        print("🐍 Verificando Python...")
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ requerido")
            sys.exit(1)
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} OK")
    
    def install_dependencies(self):
        """Instalar dependencias automáticamente"""
        print("📦 Instalando dependencias...")
        
        for package in self.required_packages:
            try:
                # Verificar si ya está instalado
                package_name = package.split("==")[0].replace("[standard]", "")
                __import__(package_name)
                print(f"✅ {package_name} ya instalado")
            except ImportError:
                print(f"🔄 Instalando {package}...")
                result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {package} instalado")
                else:
                    print(f"❌ Error instalando {package}: {result.stderr}")
    
    def create_directory_structure(self):
        """Crear estructura completa de directorios"""
        directories = [
            "app",
            "app/frontend",
            "app/frontend/routers", 
            "app/frontend/templates",
            "app/frontend/templates/auth",
            "app/frontend/templates/business_types",
            "app/frontend/templates/api_configs",
            "app/frontend/templates/components",
            "app/frontend/templates/logs",
            "app/frontend/static",
            "app/frontend/static/css",
            "app/frontend/static/js",
            "app/frontend/static/images",
            "app/models",
            "app/services", 
            "app/routers",
            "app/routers/admin",
            "app/routers/business"
        ]
        
        print("📁 Creando estructura de directorios...")
        for directory in directories:
            dir_path = self.base_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Crear __init__.py en directorios de Python
            if "app" in directory and not directory.endswith(("static", "templates", "css", "js", "images", "auth")):
                init_file = dir_path / "__init__.py"
                if not init_file.exists():
                    init_file.write_text('"""CMS Dinámico module"""\n')
        
        print("✅ Estructura de directorios creada")
    
    def create_essential_files(self):
        """Crear archivos esenciales si no existen"""
        
        # .env file
        env_content = """# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=cms_dinamico

# FastAPI Configuration  
SECRET_KEY=cms-dinamico-mvp-secret-key-change-in-production
ALGORITHM=HS256

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true

# Logging
LOG_LEVEL=INFO
"""
        
        env_file = self.base_dir / ".env"
        if not env_file.exists():
            env_file.write_text(env_content)
            print("✅ Archivo .env creado")
        
        # requirements.txt
        requirements_content = "\n".join(self.required_packages)
        req_file = self.base_dir / "requirements.txt"
        if not req_file.exists():
            req_file.write_text(requirements_content)
            print("✅ requirements.txt creado")
        
        # Simple CSS for MVP
        css_content = """/* CMS Dinámico MVP - Estilos básicos */
.btn {
    display: inline-flex;
    align-items: center;
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    font-weight: 500;
    text-decoration: none;
    transition: all 0.2s;
}

.btn-primary {
    background-color: #2563eb;
    color: white;
    border: 1px solid #2563eb;
}

.btn-primary:hover {
    background-color: #1d4ed8;
}

.btn-secondary {
    background-color: #6b7280;
    color: white;
    border: 1px solid #6b7280;
}

.loading-spinner {
    border: 2px solid #f3f3f3;
    border-top: 2px solid #3498db;
    border-radius: 50%;
    width: 16px;
    height: 16px;
    animation: spin 1s linear infinite;
    display: inline-block;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.flash-message {
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}
"""
        
        css_file = self.base_dir / "app/frontend/static/css/style.css"
        if not css_file.exists():
            css_file.write_text(css_content)
            print("✅ CSS básico creado")
    
    def check_mongodb(self):
        """Verificar MongoDB (opcional)"""
        try:
            import pymongo
            client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
            client.server_info()
            print("✅ MongoDB disponible")
            return True
        except Exception:
            print("⚠️ MongoDB no disponible - usando modo demo")
            return False
    
    def create_run_script(self):
        """Crear script de ejecución simple"""
        run_content = '''#!/usr/bin/env python3
"""Script simple para ejecutar el CMS Dinámico MVP"""

import uvicorn
import sys
import os

def main():
    """Ejecutar servidor"""
    print("🚀 Iniciando CMS Dinámico MVP...")
    print("📍 URL: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("🔑 Login: superadmin / superadmin")
    print("\\n⏹️  Presiona Ctrl+C para detener\\n")
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0", 
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\\n👋 Servidor detenido")
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        run_file = self.base_dir / "start_mvp.py"
        run_file.write_text(run_content)
        print("✅ Script de ejecución creado")
    
    async def initialize_database(self):
        """Inicializar base de datos si está disponible"""
        try:
            # Solo si MongoDB está disponible
            if self.check_mongodb():
                from app.database import connect_to_mongo, get_database
                from app.services.business_service import BusinessService
                
                await connect_to_mongo()
                db = get_database()
                service = BusinessService(db)
                await service.initialize_default_data()
                print("✅ Base de datos inicializada")
            else:
                print("ℹ️ Ejecutando en modo demo sin persistencia")
        except Exception as e:
            print(f"⚠️ Error BD: {e} - Continuando en modo demo")

def main():
    """Función principal"""
    print("🚀 CMS Dinámico MVP - Setup Automático\\n")
    
    setup = MVPSetup()
    
    # 1. Verificaciones básicas
    setup.check_python()
    
    # 2. Instalar dependencias automáticamente
    setup.install_dependencies()
    
    # 3. Crear estructura
    setup.create_directory_structure()
    setup.create_essential_files()
    setup.create_run_script()
    
    # 4. Inicializar BD si está disponible
    try:
        asyncio.run(setup.initialize_database())
    except Exception as e:
        print(f"⚠️ Error en BD: {e}")
    
    print("\\n🎉 ¡Setup completado!")
    print("\\n📝 Para ejecutar:")
    print("   python start_mvp.py")
    print("\\n📝 O manualmente:")
    print("   python -m uvicorn app.main:app --reload")
    print("\\n🌐 URLs importantes:")
    print("   • Frontend: http://localhost:8000")
    print("   • API Docs: http://localhost:8000/docs")
    print("   • Health: http://localhost:8000/health")
    print("\\n🔑 Usuarios demo:")
    print("   • superadmin / superadmin (Super Admin)")
    print("   • admin / admin (Admin)")
    print("   • tecnico / tecnico (Técnico)")
    print("   • usuario / usuario (Usuario)")

if __name__ == "__main__":
    main()
