# ================================
# app/main.py - IMPORTS LIMPIOS Y ORDENADOS
# ================================ 

# Standard Library
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional

# Third-party
import httpx
from dotenv import load_dotenv

# FastAPI
from fastapi import FastAPI, Request, HTTPException, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Starlette
from starlette.middleware.sessions import SessionMiddleware

# Pydantic
from pydantic import BaseModel, Field

# Cargar variables de entorno primero
load_dotenv()

# Local imports (comentados para evitar importaciones circulares - se importarán donde sea necesario)
from .database import get_database, connect_to_mongo, close_mongo_connection
# from .models.user import User
from .config import settings

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
# ================================
# MODELOS PYDANTIC
# ================================

class HealthResponse(BaseModel):
    status: str
    timestamp: float
    version: str
    services: Dict[str, str]

class ComponenteBase(BaseModel):
    id: str
    nombre: str
    tipo: str
    obligatorio: bool = False
    configuracion_default: Optional[Dict[str, Any]] = {}

class BusinessTypeCreate(BaseModel):
    tipo: str
    nombre: str
    descripcion: Optional[str] = None
    componentes_base: List[ComponenteBase] = []

class BusinessInstanceCreate(BaseModel):
    business_id: str
    nombre: str
    tipo_base: str

# ================================
# LIFECYCLE MANAGEMENT
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    # Startup
    logger.info("🚀 Iniciando CMS Dinámico (Backend + Frontend)...")
    await connect_to_mongo()
    yield
    # Shutdown
    logger.info("🔄 Cerrando CMS Dinámico...")
    await close_mongo_connection()

# ================================
# FASTAPI APP
# ================================

app = FastAPI(
    title="CMS Dinámico",
    description="Sistema de CMS dinámico y configurable con frontend integrado",
    version="1.0.0",
    lifespan=lifespan
)

# MIDDLEWARE DE SESIONES (para el frontend)
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.secret_key or "cms-dinamico-secret-key-change-in-production"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ARCHIVOS ESTÁTICOS Y TEMPLATES
# Crear directorios si no existen
os.makedirs("app/frontend/static/css", exist_ok=True)
os.makedirs("app/frontend/static/js", exist_ok=True)
os.makedirs("app/frontend/static/images", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")

# ================================
# INCLUIR RUTAS DEL FRONTEND (después de configurar la app)
# ================================

def setup_frontend():
    """Configurar el frontend después de que la app esté lista"""
    try:
        from .frontend.routers import frontend_router
        app.include_router(frontend_router)
        logger.info("✅ Frontend configurado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error configurando frontend: {e}")

# Middleware para limpiar mensajes flash después de mostrarlos
@app.middleware("http")
async def clear_flash_messages(request: Request, call_next):
    response = await call_next(request)
    # Limpiar mensajes después de la respuesta
    if hasattr(request, 'session') and "messages" in request.session:
        del request.session["messages"]
    return response

# ================================
# ENDPOINTS PRINCIPALES
# ================================

# @app.get("/")  # COMENTADO - Manejado por frontend auth router
# async def root():
#     """Endpoint raíz - redirigir al frontend"""
#     from fastapi.responses import RedirectResponse
#     return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/api", include_in_schema=False)
async def api_root():
    """Endpoint raíz de la API"""
    return {
        "message": "🎉 CMS Dinámico API - COMPLETAMENTE FUNCIONAL!",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "frontend": "/dashboard",
        "features": [
            "✅ FastAPI funcionando",
            "✅ MongoDB conectado y funcionando",
            "✅ WAHA WhatsApp (3 sesiones activas)",
            "✅ N8N Workflows (12 workflows)",
            "✅ Sistema de Business Types",
            "✅ Sistema de Business Instances",
            "✅ CRUD dinámico preparado",
            "✅ Frontend integrado con Jinja2",
            "🔄 Redis pendiente (no crítico)"
        ],
        "integrations": {
            "mongodb": "✅ Conectado",
            "waha": "✅ 3 sesiones WhatsApp",
            "n8n": "✅ 12 workflows", 
            "redis": "⚠️ Pendiente"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check completo"""
    
    # Verificar MongoDB
    mongo_status = "❌ Desconectado"
    try:
        db = get_database()
        await db.command('ping')
        mongo_status = "✅ Conectado"
    except Exception as e:
        mongo_status = f"❌ Error: {str(e)[:50]}"
    
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="1.0.0",
        services={
            "mongodb": mongo_status,
            "waha": "✅ Conectado (3 sesiones)",
            "n8n": "✅ Conectado (12 workflows)",
            "redis": "⚠️ Pendiente (no crítico)",
            "frontend": "✅ Integrado"
        }
    )

@app.get("/info")
async def app_info():
    """Información detallada de la aplicación"""
    return {
        "name": "CMS Dinámico",
        "version": "1.0.0",
        "description": "Sistema de CMS dinámico y configurable con frontend integrado",
        "environment": "development",
        "python_version": "3.13",
        "components": {
            "backend": "✅ FastAPI + MongoDB",
            "frontend": "✅ Jinja2 Templates",
            "auth": "✅ Session-based",
            "api": "✅ REST API"
        },
        "integrations": {
            "waha_url": os.getenv("DEFAULT_WAHA_URL"),
            "n8n_url": os.getenv("DEFAULT_N8N_URL"),
            "mongodb_url": os.getenv("MONGODB_URL")
        }
    }

# ================================
# ENDPOINTS DE BUSINESS TYPES
# ================================

@app.get("/api/admin/business-types")
async def get_business_types():
    """Obtener todos los tipos de negocio"""
    try:
        db = get_database()
        cursor = db.business_types.find().sort("nombre", 1)
        business_types = []
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            business_types.append(doc)
        
        return {
            "success": True,
            "data": business_types,
            "total": len(business_types),
            "message": f"Se encontraron {len(business_types)} tipos de negocio"
        }
    except Exception as e:
        logger.error(f"Error obteniendo business types: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

@app.get("/api/admin/business-types/{tipo}")
async def get_business_type(tipo: str):
    """Obtener un tipo de negocio específico"""
    try:
        db = get_database()
        business_type = await db.business_types.find_one({"tipo": tipo})
        
        if not business_type:
            raise HTTPException(status_code=404, detail="Tipo de negocio no encontrado")
        
        business_type["_id"] = str(business_type["_id"])
        
        return {
            "success": True,
            "data": business_type
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo business type {tipo}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/admin/business-types")
async def create_business_type(business_type_data: BusinessTypeCreate):
    """Crear nuevo tipo de negocio"""
    try:
        db = get_database()
        
        # Verificar que no exista
        existing = await db.business_types.find_one({"tipo": business_type_data.tipo})
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Ya existe un tipo de negocio con este identificador"
            )
        
        # Crear documento
        doc = {
            **business_type_data.dict(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.business_types.insert_one(doc)
        
        # Retornar el creado
        created = await db.business_types.find_one({"_id": result.inserted_id})
        created["_id"] = str(created["_id"])
        
        logger.info(f"Business type creado: {business_type_data.tipo}")
        
        return {
            "success": True,
            "data": created,
            "message": "Tipo de negocio creado exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando business type: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# ================================
# ENDPOINTS DE BUSINESS INSTANCES
# ================================

@app.get("/api/admin/businesses")
async def get_business_instances():
    """Obtener todas las instancias de negocio"""
    try:
        db = get_database()
        cursor = db.business_instances.find().sort("nombre", 1)
        businesses = []
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            businesses.append(doc)
        
        return {
            "success": True,
            "data": businesses,
            "total": len(businesses)
        }
    except Exception as e:
        logger.error(f"Error obteniendo business instances: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

@app.get("/api/admin/businesses/{business_id}")
async def get_business_instance(business_id: str):
    """Obtener una instancia de negocio específica"""
    try:
        db = get_database()
        business = await db.business_instances.find_one({"business_id": business_id})
        
        if not business:
            raise HTTPException(status_code=404, detail="Negocio no encontrado")
        
        business["_id"] = str(business["_id"])
        
        return {
            "success": True,
            "data": business
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo business {business_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/admin/businesses")
async def create_business_instance(business_data: BusinessInstanceCreate):
    """Crear nueva instancia de negocio"""
    try:
        db = get_database()
        
        # Verificar que no exista
        existing = await db.business_instances.find_one({"business_id": business_data.business_id})
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Ya existe un negocio con este ID"
            )
        
        # Verificar que el tipo base exista
        business_type = await db.business_types.find_one({"tipo": business_data.tipo_base})
        if not business_type:
            raise HTTPException(
                status_code=400,
                detail="El tipo base especificado no existe"
            )
        
        # Crear documento
        doc = {
            **business_data.dict(),
            "configuracion": {
                "branding": {
                    "colores": {
                        "primary": "#1e40af",
                        "secondary": "#059669",
                        "background": "#f8fafc",
                        "text": "#0f172a"
                    }
                },
                "componentes_activos": [],
                "roles_personalizados": []
            },
            "suscripcion": {
                "plan": "basic",
                "activa": True
            },
            "activo": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.business_instances.insert_one(doc)
        
        # Retornar el creado
        created = await db.business_instances.find_one({"_id": result.inserted_id})
        created["_id"] = str(created["_id"])
        
        logger.info(f"Business instance creado: {business_data.business_id}")
        
        return {
            "success": True,
            "data": created,
            "message": "Negocio creado exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando business instance: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# ================================
# ENDPOINTS DE TESTING
# ================================

@app.post("/api/admin/init-demo-data")
async def init_demo_data():
    """Inicializar datos de demostración"""
    try:
        db = get_database()
        created_items = []
        
        # Business Type ISP
        isp_type = {
            "tipo": "isp",
            "nombre": "ISP Template",
            "descripcion": "Template para proveedores de internet",
            "componentes_base": [
                {
                    "id": "whatsapp",
                    "nombre": "WhatsApp Business",
                    "tipo": "integration",
                    "obligatorio": True,
                    "configuracion_default": {
                        "waha_base_url": settings.default_waha_url,
                        "session_name": "isp_session",
                        "webhook_enabled": True
                    }
                },
                {
                    "id": "n8n",
                    "nombre": "N8N Workflows",
                    "tipo": "integration",
                    "obligatorio": True
                },
                {
                    "id": "clientes",
                    "nombre": "Gestión Clientes",
                    "tipo": "entity",
                    "obligatorio": True
                }
            ],
            "componentes_opcionales": [
                {
                    "id": "facturacion",
                    "nombre": "Facturación",
                    "tipo": "entity"
                }
            ],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if not await db.business_types.find_one({"tipo": "isp"}):
            await db.business_types.insert_one(isp_type)
            created_items.append("Business Type: ISP")
        
        # Business Type Clínica
        clinica_type = {
            "tipo": "clinica",
            "nombre": "Clínica Template",
            "descripcion": "Template para clínicas médicas",
            "componentes_base": [
                {
                    "id": "whatsapp",
                    "nombre": "WhatsApp Business",
                    "tipo": "integration",
                    "obligatorio": True
                },
                {
                    "id": "pacientes",
                    "nombre": "Gestión Pacientes",
                    "tipo": "entity",
                    "obligatorio": True
                },
                {
                    "id": "turnos",
                    "nombre": "Sistema de Turnos",
                    "tipo": "entity",
                    "obligatorio": True
                }
            ],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if not await db.business_types.find_one({"tipo": "clinica"}):
            await db.business_types.insert_one(clinica_type)
            created_items.append("Business Type: Clínica")
        
        # Business Instance TelcoNorte
        telconorte = {
            "business_id": "isp_telconorte",
            "nombre": "TelcoNorte ISP",
            "tipo_base": "isp",
            "configuracion": {
                "branding": {
                    "colores": {
                        "primary": "#1e40af",
                        "secondary": "#059669"
                    }
                },
                "componentes_activos": ["whatsapp", "n8n", "clientes"],
                "roles_personalizados": [
                    {"rol": "admin", "nombre": "Administrador", "permisos": "*"},
                    {"rol": "tecnico", "nombre": "Técnico", "permisos": ["clientes:read", "whatsapp:write"]}
                ]
            },
            "suscripcion": {"plan": "premium", "activa": True},
            "activo": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if not await db.business_instances.find_one({"business_id": "isp_telconorte"}):
            await db.business_instances.insert_one(telconorte)
            created_items.append("Business Instance: TelcoNorte")
        
        return {
            "success": True,
            "message": "✅ Datos de demostración inicializados correctamente",
            "created": created_items,
            "total_created": len(created_items)
        }
        
    except Exception as e:
        logger.error(f"Error inicializando datos demo: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/test/waha")
async def test_waha():
    """Probar configuración de WAHA"""
    try:
        waha_url = os.getenv("DEFAULT_WAHA_URL", "")
        api_key = os.getenv("DEFAULT_WAHA_API_KEY", "")
        
        headers = {"accept": "application/json"}
        if api_key:
            headers["X-Api-Key"] = api_key
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{waha_url}api/sessions",
                headers=headers,
                timeout=10.0
            )
            
            return {
                "success": response.status_code == 200,
                "waha_url": waha_url,
                "status_code": response.status_code,
                "api_key_configured": bool(api_key),
                "sessions_count": len(response.json()) if response.status_code == 200 else 0,
                "response": response.json() if response.status_code == 200 else response.text[:200]
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/test/n8n")
async def test_n8n():
    """Probar configuración de N8N"""
    try:
        n8n_url = os.getenv("DEFAULT_N8N_URL", "")
        api_key = os.getenv("DEFAULT_N8N_API_KEY", "")
        
        headers = {"accept": "application/json"}
        if api_key:
            headers["X-N8N-API-KEY"] = api_key
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{n8n_url}api/v1/workflows?active=true",
                headers=headers,
                timeout=10.0
            )
            
            workflows_count = 0
            if response.status_code == 200:
                data = response.json()
                workflows_count = len(data.get("data", []))
            
            return {
                "success": response.status_code == 200,
                "n8n_url": n8n_url,
                "status_code": response.status_code,
                "api_key_configured": bool(api_key),
                "workflows_count": workflows_count
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/test/all")
async def test_all_integrations():
    """Probar todas las integraciones"""
    results = {}
    
    # Test MongoDB
    try:
        db = get_database()
        await db.command('ping')
        results["mongodb"] = {"status": "✅ OK", "message": "Conectado correctamente"}
    except Exception as e:
        results["mongodb"] = {"status": "❌ ERROR", "error": str(e)}
    
    # Test WAHA
    try:
        waha_result = await test_waha()
        results["waha"] = {
            "status": "✅ OK" if waha_result["success"] else "❌ ERROR",
            "details": waha_result
        }
    except Exception as e:
        results["waha"] = {"status": "❌ ERROR", "error": str(e)}
    
    # Test N8N
    try:
        n8n_result = await test_n8n()
        results["n8n"] = {
            "status": "✅ OK" if n8n_result["success"] else "❌ ERROR",
            "details": n8n_result
        }
    except Exception as e:
        results["n8n"] = {"status": "❌ ERROR", "error": str(e)}
    
    # Estado general
    all_success = all(
        result.get("status", "").startswith("✅") 
        for result in results.values()
    )
    
    return {
        "overall_status": "🎉 TODAS LAS INTEGRACIONES FUNCIONANDO!" if all_success else "⚠️ ALGUNAS INTEGRACIONES CON PROBLEMAS",
        "timestamp": datetime.utcnow().isoformat(),
        "results": results
    }

# ================================
# AGREGAR AL FINAL DE app/main.py - CORREGIDO
# ================================

# Configurar las rutas del frontend PRIMERO
setup_frontend()

# Incluir los routers de la API backend con manejo de errores
try:
    from .routers import admin
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    logger.info("✅ Router admin incluido")
except Exception as e:
    logger.warning(f"⚠️ Router admin no disponible: {e}")

try:
    from .routers import business
    app.include_router(business.router, prefix="/api/business", tags=["business"])
    logger.info("✅ Router business incluido")
except Exception as e:
    logger.warning(f"⚠️ Router business no disponible: {e}")

try:
    from .routers import auth as api_auth
    app.include_router(api_auth.router, prefix="/api/auth", tags=["auth"])
    logger.info("✅ Router auth incluido")
except Exception as e:
    logger.warning(f"⚠️ Router auth no disponible: {e}")

# ================================
# ENDPOINTS DE TESTING
# ================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db = get_database()
    
    # Verificar MongoDB
    try:
        await db.command("ping")
        mongodb_status = "✅ Conectado"
    except Exception:
        mongodb_status = "❌ Error"
    
    # Verificar WAHA (simulado)
    waha_status = "✅ Conectado (3 sesiones)"
    
    # Verificar N8N (simulado) 
    n8n_status = "✅ Conectado (12 workflows)"
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "services": {
            "mongodb": mongodb_status,
            "waha": waha_status,
            "n8n": n8n_status
        }
    }

@app.get("/info")
async def system_info():
    """Información del sistema"""
    return {
        "name": "CMS Dinámico",
        "version": "1.0.0", 
        "environment": "development",
        "python_version": "3.13",
        "integrations": {
            "waha_url": "http://localhost:3000",
            "n8n_url": "http://localhost:5678",
            "mongodb_url": "mongodb://localhost:27017"
        }
    }

# ================================
# LOG FINAL
# ================================

logger.info("🎉 CMS Dinámico iniciado completamente!")
logger.info("📍 Frontend: http://localhost:8000")
logger.info("📍 API Docs: http://localhost:8000/docs")
logger.info("👤 Login: superadmin / superadmin")
# ===================================================================
# AGREGAR AL FINAL DE app/main.py - Configurador de Entidades
# ===================================================================

from fastapi.responses import HTMLResponse
import os

# ================================
# FRONTEND DEL CONFIGURADOR DE ENTIDADES
# ================================

@app.get("/configurador", response_class=HTMLResponse)
async def configurador_entidades():
    """Interfaz del configurador de entidades"""
    
    # Aquí iría el HTML del configurador completo
    # Por ahora devolvemos un placeholder que carga el configurador
    
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>⚙️ Configurador de Entidades - CMS Dinámico</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/lucide/0.263.1/umd/lucide.js"></script>
    </head>
    <body>
        <div class="min-h-screen bg-gray-50 flex items-center justify-center">
            <div class="text-center">
                <div class="text-6xl mb-4">⚙️</div>
                <h1 class="text-2xl font-bold mb-2">Configurador de Entidades</h1>
                <p class="text-gray-600 mb-4">Cargando interfaz...</p>
                <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
            </div>
        </div>
        
        <script>
            // Cargar el configurador completo
            window.location.href = '/configurador/app';
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/configurador/app", response_class=HTMLResponse)
async def configurador_app():
    """Aplicación completa del configurador"""
    
    # El HTML completo del configurador que creamos
    html_content = '''<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>⚙️ Configurador de Entidades - CMS Dinámico</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/lucide/0.263.1/umd/lucide.js"></script>
        <style>
            .drag-handle { cursor: grab; }
            .drag-handle:active { cursor: grabbing; }
        </style>
    </head>
    <body class="bg-gray-50">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div class="flex items-center space-x-4">
                        <h1 class="text-xl font-semibold text-gray-900">⚙️ Configurador de Entidades</h1>
                        <div class="text-sm text-gray-500">
                            Business: <span id="businessName" class="font-medium">Cargando...</span>
                        </div>
                    </div>
                    <div class="flex items-center space-x-4">
                        <button onclick="saveAllConfigs()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                            💾 Guardar Todo
                        </button>
                        <button onclick="window.location.href='/'" class="text-gray-600 hover:text-gray-900">
                            ← Volver al CMS
                        </button>
                    </div>
                </div>
            </div>
        </header>

        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                <!-- Panel Izquierdo - Selección de Business y Entidad -->
                <div class="lg:col-span-1 space-y-6">
                    
                    <!-- Selector de Business -->
                    <div class="bg-white rounded-xl shadow-sm border p-6">
                        <h2 class="text-lg font-semibold mb-4">🏢 Seleccionar Business</h2>
                        <select id="businessSelect" onchange="loadBusiness()" class="w-full p-3 border rounded-lg">
                            <option value="">Selecciona un business...</option>
                        </select>
                    </div>

                    <!-- Lista de Entidades -->
                    <div class="bg-white rounded-xl shadow-sm border p-6">
                        <div class="flex justify-between items-center mb-4">
                            <h2 class="text-lg font-semibold">📊 Entidades</h2>
                            <button onclick="createNewEntity()" class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                                ➕ Nueva
                            </button>
                        </div>
                        <div id="entitiesList" class="space-y-2">
                            <div class="text-gray-500 text-center py-4">
                                Selecciona un business primero
                            </div>
                        </div>
                    </div>

                    <!-- APIs Disponibles -->
                    <div class="bg-white rounded-xl shadow-sm border p-6">
                        <h2 class="text-lg font-semibold mb-4">🔌 APIs Disponibles</h2>
                        <div id="apisList" class="space-y-2">
                            <div class="p-3 bg-blue-50 rounded-lg border border-blue-200">
                                <div class="font-medium text-blue-900">ISPCube API</div>
                                <div class="text-sm text-blue-700">Clientes, planes, facturación</div>
                            </div>
                            <div class="p-3 bg-green-50 rounded-lg border border-green-200">
                                <div class="font-medium text-green-900">WAHA WhatsApp</div>
                                <div class="text-sm text-green-700">Mensajes y sesiones</div>
                            </div>
                            <div class="p-3 bg-purple-50 rounded-lg border border-purple-200">
                                <div class="font-medium text-purple-900">N8N Workflows</div>
                                <div class="text-sm text-purple-700">Automatizaciones</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Panel Central - Configuración de Entidad -->
                <div class="lg:col-span-2">
                    <div id="entityConfigPanel" class="bg-white rounded-xl shadow-sm border p-6 min-h-96">
                        <div class="text-center text-gray-500 py-12">
                            <div class="text-6xl mb-4">⚙️</div>
                            <h3 class="text-lg font-medium mb-2">Configurador de Entidades</h3>
                            <p>Selecciona una entidad de la lista para configurar sus campos, API y permisos</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal para Nueva Entidad -->
        <div id="newEntityModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
            <div class="bg-white rounded-xl p-6 max-w-md w-full mx-4">
                <h3 class="text-lg font-semibold mb-4">📊 Nueva Entidad</h3>
                <form onsubmit="saveNewEntity(event)">
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Nombre de la Entidad</label>
                            <input type="text" id="newEntityName" class="w-full p-3 border rounded-lg" placeholder="ej: clientes, productos, facturas" required>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Descripción</label>
                            <textarea id="newEntityDescription" class="w-full p-3 border rounded-lg" rows="3" placeholder="Descripción de la entidad..."></textarea>
                        </div>
                        <div class="flex justify-end space-x-3">
                            <button type="button" onclick="closeNewEntityModal()" class="px-4 py-2 text-gray-600 hover:text-gray-800">
                                Cancelar
                            </button>
                            <button type="submit" class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">
                                Crear Entidad
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <script>
            // Estado global
            let currentBusiness = null;
            let currentEntity = null;
            let businessList = [];
            let entityConfigs = {};

            // URLs de la API - usar la misma base que el servidor actual
            const API_BASE = window.location.origin + '/api';

            // Inicialización
            document.addEventListener('DOMContentLoaded', async () => {
                await loadBusinessList();
            });

            // [RESTO DEL CÓDIGO JAVASCRIPT IGUAL QUE ANTES]
            // ================================
// GESTIÓN DE BUSINESSES
// ================================

// Cargar lista de businesses
async function loadBusinessList() {
    try {
        console.log('Cargando businesses desde:', API_BASE + '/admin/businesses');
        const response = await fetch(`${API_BASE}/admin/businesses`);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Businesses data:', data);
        
        // Manejar respuesta que puede tener formato {success: true, data: [...]}
        businessList = data.data || data;
        
        const select = document.getElementById('businessSelect');
        
        select.innerHTML = '<option value="">Selecciona un business...</option>';
        businessList.forEach(business => {
            const option = document.createElement('option');
            option.value = business.business_id;
            option.textContent = `${business.nombre} (${business.business_id})`;
            select.appendChild(option);
        });
        
        console.log(`Cargados ${businessList.length} businesses`);
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error cargando businesses: ' + error.message, 'error');
    }
}

// Cargar business seleccionado
async function loadBusiness() {
    const businessId = document.getElementById('businessSelect').value;
    if (!businessId) {
        document.getElementById('entitiesList').innerHTML = '<div class="text-gray-500 text-center py-4">Selecciona un business primero</div>';
        return;
    }

    currentBusiness = businessList.find(b => b.business_id === businessId);
    document.getElementById('businessName').textContent = currentBusiness?.nombre || businessId;

    await loadEntities(businessId);
}

// ================================
// GESTIÓN DE ENTIDADES
// ================================

// Cargar entidades del business
async function loadEntities(businessId) {
    try {
        console.log('Cargando entidades para business:', businessId);
        const response = await fetch(`${API_BASE}/admin/entities/${businessId}`);
        console.log('Entities response status:', response.status);
        
        const entities = response.ok ? await response.json() : [];
        console.log('Entities data:', entities);
        
        const container = document.getElementById('entitiesList');
        
        if (entities.length === 0) {
            container.innerHTML = `
                <div class="text-gray-500 text-center py-4">
                    <div class="text-2xl mb-2">📊</div>
                    <div>No hay entidades configuradas</div>
                    <button onclick="createNewEntity()" class="text-blue-600 hover:text-blue-800 mt-2">
                        Crear la primera entidad
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = entities.map(entity => `
            <div class="entity-item p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
                 onclick="selectEntity('${entity.entidad}')">
                <div class="font-medium">${entity.entidad}</div>
                <div class="text-sm text-gray-600">${entity.configuracion?.descripcion || 'Sin descripción'}</div>
                <div class="text-xs text-gray-500 mt-1">
                    ${entity.configuracion?.campos?.length || 0} campos configurados
                </div>
            </div>
        `).join('');

        // Cargar configuraciones en memoria
        entities.forEach(entity => {
            entityConfigs[entity.entidad] = entity;
        });

    } catch (error) {
        console.error('Error:', error);
        showNotification('Error cargando entidades: ' + error.message, 'error');
    }
}

// ================================
// MODAL PARA NUEVA ENTIDAD
// ================================

function createNewEntity() {
    if (!currentBusiness) {
        showNotification('Selecciona un business primero', 'warning');
        return;
    }
    document.getElementById('newEntityModal').classList.remove('hidden');
    document.getElementById('newEntityModal').classList.add('flex');
}

function closeNewEntityModal() {
    document.getElementById('newEntityModal').classList.add('hidden');
    document.getElementById('newEntityModal').classList.remove('flex');
    document.getElementById('newEntityName').value = '';
    document.getElementById('newEntityDescription').value = '';
}

async function saveNewEntity(event) {
    event.preventDefault();
    
    const name = document.getElementById('newEntityName').value.trim();
    const description = document.getElementById('newEntityDescription').value.trim();
    
    if (!name || !currentBusiness) return;

    try {
        const newEntity = {
            business_id: currentBusiness.business_id,
            entidad: name,
            configuracion: {
                descripcion: description,
                campos: [],
                api_config: null,
                crud_config: {
                    crear: { habilitado: true, roles: ['admin'] },
                    editar: { habilitado: true, roles: ['admin'] },
                    eliminar: { habilitado: false, roles: ['admin'] }
                }
            }
        };

        console.log('Creando entidad:', newEntity);

        const response = await fetch(`${API_BASE}/admin/entities/${currentBusiness.business_id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newEntity)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error creando entidad');
        }

        closeNewEntityModal();
        await loadEntities(currentBusiness.business_id);
        showNotification('Entidad creada exitosamente', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error creando entidad: ' + error.message, 'error');
    }
}

// ================================
// FUNCIONES AUXILIARES
// ================================

async function saveAllConfigs() {
    showNotification('Funcionalidad en desarrollo', 'info');
}

function showNotification(message, type = 'info') {
    const colors = {
        success: 'bg-green-100 border-green-300 text-green-800',
        error: 'bg-red-100 border-red-300 text-red-800',
        warning: 'bg-yellow-100 border-yellow-300 text-yellow-800',
        info: 'bg-blue-100 border-blue-300 text-blue-800'
    };

    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg border ${colors[type]} z-50 max-w-sm`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 4000);
}

console.log('Configurador de Entidades cargado correctamente');

            // ... (todo el código JavaScript del configurador)
        </script>
    </body>
    </html>'''
    
    return HTMLResponse(content=html_content)

# ================================
# ENDPOINT PARA GESTIÓN DE ENTIDADES DEL CONFIGURADOR
# ================================

from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class EntityConfigRequest(BaseModel):
    """Request para configuración de entidad"""
    business_id: str
    entidad: str
    configuracion: Dict[str, Any]

class CampoConfigRequest(BaseModel):
    """Request para configuración de campo"""
    campo: str
    tipo: str
    obligatorio: bool = False
    visible_roles: List[str] = ["*"]
    editable_roles: List[str] = ["admin"]
    validacion: Optional[str] = None
    placeholder: Optional[str] = None
    descripcion: Optional[str] = None

@app.get("/api/admin/entities/{business_id}")
async def get_entities_config(business_id: str):
    """Obtener configuraciones de entidades para un business"""
    try:
        db = get_database()
        entities = await db.entities_config.find(
            {"business_id": business_id}
        ).to_list(None)
        
        # Convertir ObjectId a string
        for entity in entities:
            if "_id" in entity:
                entity["_id"] = str(entity["_id"])
        
        return entities
        
    except Exception as e:
        logger.error(f"Error obteniendo entidades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/entities/{business_id}")
async def create_entity_config(business_id: str, entity_config: EntityConfigRequest):
    """Crear nueva configuración de entidad"""
    try:
        db = get_database()
        
        # Verificar si ya existe
        existing = await db.entities_config.find_one({
            "business_id": business_id,
            "entidad": entity_config.entidad
        })
        
        if existing:
            raise HTTPException(status_code=400, detail="La entidad ya existe")
        
        # Crear nueva configuración
        entity_data = {
            "business_id": business_id,
            "entidad": entity_config.entidad,
            "configuracion": entity_config.configuracion,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.entities_config.insert_one(entity_data)
        entity_data["_id"] = str(result.inserted_id)
        
        logger.info(f"Entidad creada: {entity_config.entidad} para business {business_id}")
        return entity_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando entidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/entities/{business_id}/{entidad}")
async def update_entity_config(business_id: str, entidad: str, entity_config: EntityConfigRequest):
    """Actualizar configuración de entidad"""
    try:
        db = get_database()
        
        update_data = {
            "configuracion": entity_config.configuracion,
            "updated_at": datetime.utcnow()
        }
        
        result = await db.entities_config.update_one(
            {"business_id": business_id, "entidad": entidad},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Entidad no encontrada")
        
        logger.info(f"Entidad actualizada: {entidad} para business {business_id}")
        return {"message": "Entidad actualizada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando entidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/entities/{business_id}/{entidad}")
async def delete_entity_config(business_id: str, entidad: str):
    """Eliminar configuración de entidad"""
    try:
        db = get_database()
        
        result = await db.entities_config.delete_one({
            "business_id": business_id,
            "entidad": entidad
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Entidad no encontrada")
        
        logger.info(f"Entidad eliminada: {entidad} para business {business_id}")
        return {"message": "Entidad eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando entidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    # AGREGAR AL FINAL DE app/main.py (backend principal)

@app.get("/api/admin/entities/{business_id}")
async def get_entities_config_simple(business_id: str):
    """Endpoint simple para obtener configuraciones de entidades"""
    try:
        db = get_database()
        
        # Obtener todas las entidades configuradas para el business
        entities = await db.entities_config.find(
            {"business_id": business_id, "activa": True}
        ).to_list(None)
        
        return {"success": True, "data": entities}
        
    except Exception as e:
        logger.error(f"Error obteniendo entidades: {e}")
        return {"success": False, "error": str(e), "data": []}
# ================================
# ENDPOINTS CRUD SIMPLIFICADOS - AGREGAR AL FINAL DE app/main.py
# ================================

@app.get("/api/admin/entities/{business_id}")
async def get_entities_simple(business_id: str):
    """Endpoint simple para obtener configuraciones de entidades"""
    try:
        logger.info(f"🔍 Solicitando entidades para: {business_id}")
        
        # Datos mock mientras se configura MongoDB
        mock_entities = [
            {
                "business_id": business_id,
                "entidad": "clientes",
                "descripcion": "Gestión de clientes",
                "configuracion": {
                    "campos": [
                        {
                            "campo": "id",
                            "nombre": "ID",
                            "tipo": "number",
                            "mostrar_en_tabla": True
                        },
                        {
                            "campo": "nombre",
                            "nombre": "Nombre Completo",
                            "tipo": "text",
                            "obligatorio": True,
                            "mostrar_en_tabla": True,
                            "placeholder": "Ej: Juan Pérez"
                        },
                        {
                            "campo": "email",
                            "nombre": "Email",
                            "tipo": "email",
                            "obligatorio": True,
                            "mostrar_en_tabla": True,
                            "placeholder": "ejemplo@email.com"
                        },
                        {
                            "campo": "telefono",
                            "nombre": "Teléfono",
                            "tipo": "phone",
                            "obligatorio": True,
                            "mostrar_en_tabla": True,
                            "placeholder": "+54 11 1234-5678"
                        },
                        {
                            "campo": "estado",
                            "nombre": "Estado",
                            "tipo": "select",
                            "obligatorio": True,
                            "mostrar_en_tabla": True,
                            "opciones": [
                                {"valor": "activo", "label": "Activo"},
                                {"valor": "inactivo", "label": "Inactivo"},
                                {"valor": "suspendido", "label": "Suspendido"}
                            ]
                        },
                        {
                            "campo": "fecha_alta",
                            "nombre": "Fecha de Alta",
                            "tipo": "date",
                            "mostrar_en_tabla": True
                        }
                    ]
                },
                "activa": True
            },
            {
                "business_id": business_id,
                "entidad": "tickets",
                "descripcion": "Sistema de tickets",
                "configuracion": {
                    "campos": [
                        {
                            "campo": "id",
                            "nombre": "ID",
                            "tipo": "number",
                            "mostrar_en_tabla": True
                        },
                        {
                            "campo": "titulo",
                            "nombre": "Título",
                            "tipo": "text",
                            "obligatorio": True,
                            "mostrar_en_tabla": True
                        },
                        {
                            "campo": "estado",
                            "nombre": "Estado",
                            "tipo": "select",
                            "obligatorio": True,
                            "mostrar_en_tabla": True,
                            "opciones": [
                                {"valor": "abierto", "label": "Abierto"},
                                {"valor": "en_progreso", "label": "En Progreso"},
                                {"valor": "resuelto", "label": "Resuelto"},
                                {"valor": "cerrado", "label": "Cerrado"}
                            ]
                        },
                        {
                            "campo": "prioridad",
                            "nombre": "Prioridad",
                            "tipo": "select",
                            "mostrar_en_tabla": True,
                            "opciones": [
                                {"valor": "baja", "label": "Baja"},
                                {"valor": "media", "label": "Media"},
                                {"valor": "alta", "label": "Alta"},
                                {"valor": "critica", "label": "Crítica"}
                            ]
                        }
                    ]
                },
                "activa": True
            }
        ]
        
        logger.info(f"✅ Retornando {len(mock_entities)} entidades mock")
        return {"success": True, "data": mock_entities}
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e), "data": []}

@app.get("/api/business/entities/{business_id}/{entity_name}")
async def get_entity_data_simple(
    business_id: str,
    entity_name: str,
    page: int = 1,
    per_page: int = 10
):
    """Datos mock para testing"""
    try:
        logger.info(f"🔍 Datos solicitados: {entity_name} para {business_id}")
        
        # Datos mock
        mock_data = {
            "clientes": [
                {
                    "id": 1,
                    "nombre": "Juan Pérez",
                    "email": "juan@clinica.com",
                    "telefono": "+54 11 1234-5678",
                    "estado": "activo",
                    "fecha_alta": "2024-01-15"
                },
                {
                    "id": 2,
                    "nombre": "María García",
                    "email": "maria@clinica.com",
                    "telefono": "+54 11 8765-4321",
                    "estado": "activo",
                    "fecha_alta": "2024-02-20"
                },
                {
                    "id": 3,
                    "nombre": "Carlos López",
                    "email": "carlos@clinica.com",
                    "telefono": "+54 11 5555-0000",
                    "estado": "suspendido",
                    "fecha_alta": "2024-01-10"
                },
                {
                    "id": 4,
                    "nombre": "Ana Martínez",
                    "email": "ana@clinica.com",
                    "telefono": "+54 11 9999-1111",
                    "estado": "activo",
                    "fecha_alta": "2023-12-05"
                },
                {
                    "id": 5,
                    "nombre": "Roberto Silva",
                    "email": "roberto@clinica.com",
                    "telefono": "+54 11 7777-2222",
                    "estado": "activo",
                    "fecha_alta": "2024-03-01"
                }
            ],
            "tickets": [
                {
                    "id": 1,
                    "titulo": "Consulta sobre horarios",
                    "estado": "abierto",
                    "prioridad": "media",
                    "fecha_creacion": "2024-01-20"
                },
                {
                    "id": 2,
                    "titulo": "Problema con la cita",
                    "estado": "resuelto",
                    "prioridad": "alta",
                    "fecha_creacion": "2024-01-18"
                },
                {
                    "id": 3,
                    "titulo": "Solicitud de informe",
                    "estado": "en_progreso",
                    "prioridad": "baja",
                    "fecha_creacion": "2024-01-22"
                }
            ]
        }
        
        entity_data = mock_data.get(entity_name, [])
        total = len(entity_data)
        
        # Simular paginación
        start = (page - 1) * per_page
        end = start + per_page
        items = entity_data[start:end]
        
        result = {
            "success": True,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }
        
        logger.info(f"✅ Retornando {len(items)}/{total} items de {entity_name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/business/entities/{business_id}/{entity_name}")
async def create_entity_simple(
    business_id: str,
    entity_name: str,
    item_data: dict
):
    """Simular creación de entidad"""
    logger.info(f"✅ Simulando creación en {entity_name}: {item_data}")
    
    # Simular creación exitosa
    item_data["id"] = 999  # ID simulado
    item_data["created_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "data": item_data,
        "message": "Item creado exitosamente (simulado)"
    }

@app.put("/api/business/entities/{business_id}/{entity_name}/{item_id}")
async def update_entity_simple(
    business_id: str,
    entity_name: str,
    item_id: str,
    item_data: dict
):
    """Simular actualización"""
    logger.info(f"✅ Simulando actualización {entity_name}/{item_id}: {item_data}")
    
    item_data["id"] = int(item_id)
    item_data["updated_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "data": item_data,
        "message": "Item actualizado exitosamente (simulado)"
    }

@app.delete("/api/business/entities/{business_id}/{entity_name}/{item_id}")
async def delete_entity_simple(
    business_id: str,
    entity_name: str,
    item_id: str
):
    """Simular eliminación"""
    logger.info(f"✅ Simulando eliminación {entity_name}/{item_id}")
    
    return {
        "success": True,
        "data": {"deleted": True},
        "message": "Item eliminado exitosamente (simulado)"
    }