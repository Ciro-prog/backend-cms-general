from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
import time

from .config import settings
from .database import connect_to_mongo, close_mongo_connection
from .routers import auth, admin, business, integrations
from .auth.middleware import ClerkAuthMiddleware

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    # Startup
    logger.info("Iniciando CMS Dinámico Backend...")
    await connect_to_mongo()
    yield
    # Shutdown
    logger.info("Cerrando CMS Dinámico Backend...")
    await close_mongo_connection()

app = FastAPI(
    title="CMS Dinámico API",
    description="Sistema de CMS dinámico y configurable",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.ngrok.io"]
)

# Middleware personalizado para logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    return response

# Agregar middleware de autenticación
app.add_middleware(ClerkAuthMiddleware)

# Rutas
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(business.router, prefix="/api/business", tags=["business"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])

@app.get("/")
async def root():
    return {
        "message": "CMS Dinámico API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}
