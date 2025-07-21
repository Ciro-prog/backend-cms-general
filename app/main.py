# ================================
# app/main.py (VERSIÓN SIMPLIFICADA)
# ================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
import json
import os
from datetime import datetime

# Crear la app
app = FastAPI(
    title="CMS Dinámico API",
    description="Sistema de CMS dinámico y configurable",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# MODELOS BÁSICOS
# ================================

class HealthResponse(BaseModel):
    status: str
    timestamp: float
    version: str

class BusinessType(BaseModel):
    id: str
    tipo: str
    nombre: str
    descripcion: Optional[str] = None
    created_at: str

class BusinessInstance(BaseModel):
    business_id: str
    nombre: str
    tipo_base: str
    activo: bool = True
    created_at: str

# ================================
# ALMACENAMIENTO TEMPORAL (EN MEMORIA)
# ================================

# Datos temporales para probar (se reemplazará con MongoDB)
BUSINESS_TYPES = {
    "isp": {
        "id": "isp",
        "tipo": "isp", 
        "nombre": "ISP Template",
        "descripcion": "Template para proveedores de internet",
        "created_at": datetime.now().isoformat()
    },
    "clinica": {
        "id": "clinica",
        "tipo": "clinica",
        "nombre": "Clínica Template", 
        "descripcion": "Template para clínicas médicas",
        "created_at": datetime.now().isoformat()
    }
}

BUSINESS_INSTANCES = {
    "isp_telconorte": {
        "business_id": "isp_telconorte",
        "nombre": "TelcoNorte ISP",
        "tipo_base": "isp",
        "activo": True,
        "created_at": datetime.now().isoformat()
    },
    "clinica_demo": {
        "business_id": "clinica_demo", 
        "nombre": "Clínica Demo",
        "tipo_base": "clinica",
        "activo": True,
        "created_at": datetime.now().isoformat()
    }
}

# ================================
# ENDPOINTS BÁSICOS
# ================================

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "🎉 CMS Dinámico API - FUNCIONANDO!",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "✅ FastAPI funcionando",
            "✅ CORS configurado", 
            "✅ Documentación automática",
            "🔄 MongoDB pendiente",
            "🔄 Redis pendiente"
        ]
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check para monitoreo"""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="1.0.0"
    )

@app.get("/info")
async def app_info():
    """Información de la aplicación"""
    return {
        "name": "CMS Dinámico",
        "version": "1.0.0",
        "description": "Sistema de CMS dinámico y configurable",
        "environment": "development",
        "python_version": "3.13",
        "dependencies_status": {
            "fastapi": "✅ 0.108.0",
            "uvicorn": "✅ 0.25.0", 
            "pydantic": "✅ 2.11.7",
            "httpx": "✅ 0.26.0",
            "cryptography": "✅ 42.0.0",
            "motor": "❌ Pendiente arreglo",
            "redis": "❌ Pendiente instalación"
        }
    }

# ================================
# ENDPOINTS DE BUSINESS TYPES (TEMPORALES)
# ================================

@app.get("/api/admin/business-types")
async def get_business_types():
    """Obtener todos los tipos de negocio"""
    return {
        "success": True,
        "data": list(BUSINESS_TYPES.values()),
        "total": len(BUSINESS_TYPES)
    }

@app.get("/api/admin/business-types/{tipo}")
async def get_business_type(tipo: str):
    """Obtener tipo de negocio específico"""
    if tipo not in BUSINESS_TYPES:
        raise HTTPException(status_code=404, detail="Tipo de negocio no encontrado")
    
    return {
        "success": True,
        "data": BUSINESS_TYPES[tipo]
    }

@app.post("/api/admin/business-types")
async def create_business_type(business_type: BusinessType):
    """Crear nuevo tipo de negocio"""
    if business_type.tipo in BUSINESS_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de negocio ya existe")
    
    new_type = business_type.dict()
    new_type["created_at"] = datetime.now().isoformat()
    BUSINESS_TYPES[business_type.tipo] = new_type
    
    return {
        "success": True,
        "data": new_type,
        "message": "Tipo de negocio creado exitosamente"
    }

# ================================
# ENDPOINTS DE BUSINESS INSTANCES (TEMPORALES)
# ================================

@app.get("/api/admin/businesses")
async def get_business_instances():
    """Obtener todas las instancias de negocio"""
    return {
        "success": True,
        "data": list(BUSINESS_INSTANCES.values()),
        "total": len(BUSINESS_INSTANCES)
    }

@app.get("/api/admin/businesses/{business_id}")
async def get_business_instance(business_id: str):
    """Obtener instancia de negocio específica"""
    if business_id not in BUSINESS_INSTANCES:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    
    return {
        "success": True,
        "data": BUSINESS_INSTANCES[business_id]
    }

@app.post("/api/admin/businesses")
async def create_business_instance(business: BusinessInstance):
    """Crear nueva instancia de negocio"""
    if business.business_id in BUSINESS_INSTANCES:
        raise HTTPException(status_code=400, detail="Negocio ya existe")
    
    # Verificar que el tipo base existe
    if business.tipo_base not in BUSINESS_TYPES:
        raise HTTPException(status_code=400, detail="Tipo base no existe")
    
    new_business = business.dict()
    new_business["created_at"] = datetime.now().isoformat()
    BUSINESS_INSTANCES[business.business_id] = new_business
    
    return {
        "success": True,
        "data": new_business,
        "message": "Negocio creado exitosamente"
    }

# ================================
# ENDPOINTS DE TESTING
# ================================

@app.get("/api/test/waha")
async def test_waha():
    """Probar configuración de WAHA con headers correctos"""
    import httpx
    
    try:
        waha_url = os.getenv("DEFAULT_WAHA_URL", "http://pampaservers.com:60513/")
        api_key = os.getenv("DEFAULT_WAHA_API_KEY", "")
        
        # WAHA usa X-Api-Key, no Authorization Bearer
        headers = {
            "accept": "application/json"
        }
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
                "headers_used": headers,
                "response": response.json() if response.status_code == 200 else response.text[:200]
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "waha_url": waha_url if 'waha_url' in locals() else "No configurado"
        }

@app.get("/api/test/n8n")
async def test_n8n():
    """Probar configuración de N8N con headers correctos"""
    import httpx
    
    try:
        n8n_url = os.getenv("DEFAULT_N8N_URL", "https://n8n.pampaservers.com/")
        api_key = os.getenv("DEFAULT_N8N_API_KEY", "")
        
        # N8N usa X-N8N-API-KEY, no Authorization Bearer
        headers = {
            "accept": "application/json"
        }
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
                "headers_used": headers,
                "workflows_count": workflows_count,
                "response_preview": response.text[:200] if response.status_code != 200 else "OK"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "n8n_url": n8n_url if 'n8n_url' in locals() else "No configurado"
        }

@app.get("/api/test/redis")
async def test_redis():
    """Probar configuración de Redis Cloud"""
    import httpx
    
    try:
        redis_url = os.getenv("REDIS_URL", "https://api.redislabs.com/v1")
        api_key = os.getenv("REDIS_API_KEY", "")
        
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        async with httpx.AsyncClient() as client:
            # Probar con endpoint de ping
            response = await client.get(
                f"{redis_url}/ping",
                headers=headers,
                timeout=10.0
            )
            
            return {
                "success": response.status_code == 200,
                "redis_url": redis_url,
                "status_code": response.status_code,
                "api_key_configured": bool(api_key),
                "headers_used": headers,
                "response": response.text[:200]
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "redis_url": redis_url if 'redis_url' in locals() else "No configurado"
        }

# ================================
# NUEVO ENDPOINT: Test completo de integraciones
# ================================

@app.get("/api/test/all")
async def test_all_integrations():
    """Probar todas las integraciones de una vez"""
    
    results = {}
    
    # Test WAHA
    try:
        waha_result = await test_waha()
        results["waha"] = {
            "status": "✅ OK" if waha_result["success"] else "❌ ERROR",
            "details": waha_result
        }
    except Exception as e:
        results["waha"] = {
            "status": "❌ ERROR",
            "error": str(e)
        }
    
    # Test N8N
    try:
        n8n_result = await test_n8n()
        results["n8n"] = {
            "status": "✅ OK" if n8n_result["success"] else "❌ ERROR", 
            "details": n8n_result
        }
    except Exception as e:
        results["n8n"] = {
            "status": "❌ ERROR",
            "error": str(e)
        }
    
    # Test Redis
    try:
        redis_result = await test_redis()
        results["redis"] = {
            "status": "✅ OK" if redis_result["success"] else "❌ ERROR",
            "details": redis_result
        }
    except Exception as e:
        results["redis"] = {
            "status": "❌ ERROR", 
            "error": str(e)
        }
    
    # Calcular estado general
    all_success = all(
        result.get("details", {}).get("success", False) 
        for result in results.values()
    )
    
    return {
        "overall_status": "✅ TODAS LAS INTEGRACIONES OK" if all_success else "⚠️ ALGUNAS INTEGRACIONES CON PROBLEMAS",
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "next_steps": [
            "✅ WAHA: Listo para WhatsApp Business" if results.get("waha", {}).get("details", {}).get("success") else "🔧 WAHA: Verificar API key",
            "✅ N8N: Listo para workflows" if results.get("n8n", {}).get("details", {}).get("success") else "🔧 N8N: Verificar API key",
            "✅ Redis: Listo para cache" if results.get("redis", {}).get("details", {}).get("success") else "🔧 Redis: Verificar configuración"
        ]
    }

# ================================
# ENDPOINT PARA VERIFICAR ENV
# ================================

@app.get("/api/debug/env")
async def debug_env():
    """Debug de variables de entorno (solo para desarrollo)"""
    
    return {
        "env_status": {
            "waha_url": os.getenv("DEFAULT_WAHA_URL", "❌ NO CONFIGURADO"),
            "waha_api_key": "✅ Configurado" if os.getenv("DEFAULT_WAHA_API_KEY") else "❌ Falta",
            "n8n_url": os.getenv("DEFAULT_N8N_URL", "❌ NO CONFIGURADO"),
            "n8n_api_key": "✅ Configurado" if os.getenv("DEFAULT_N8N_API_KEY") else "❌ Falta",
            "redis_url": os.getenv("REDIS_URL", "❌ NO CONFIGURADO"),
            "redis_api_key": "✅ Configurado" if os.getenv("REDIS_API_KEY") else "❌ Falta",
            "clerk_secret": "✅ Configurado" if os.getenv("CLERK_SECRET_KEY") else "❌ Falta"
        },
        "file_check": {
            "dotenv_file_exists": os.path.exists(".env"),
            "current_directory": os.getcwd()
        }
    }