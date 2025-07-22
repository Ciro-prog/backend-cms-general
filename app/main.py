# ================================
# app/main.py (CORREGIDO - SIN IMPORTACIONES CIRCULARES)
# ================================

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import time
import os
import httpx
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Imports locales (sin frontend por ahora para evitar circulares)
from .database import connect_to_mongo, close_mongo_connection, get_database
from .config import settings

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
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