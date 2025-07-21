# ================================
# scripts/monitoring.py
# ================================

#!/usr/bin/env python3
"""
Script de monitoreo para CMS Dinámico
"""

import asyncio
import aiohttp
import psutil
import logging
import json
from datetime import datetime
import sys
import os

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import connect_to_mongo, get_database
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Monitor del sistema y aplicación"""
    
    def __init__(self):
        self.metrics = {}
    
    async def check_api_health(self, url: str = "http://localhost:8000") -> dict:
        """Verificar salud de la API"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = datetime.now()
                async with session.get(f"{url}/health") as response:
                    end_time = datetime.now()
                    
                    response_time = (end_time - start_time).total_seconds() * 1000
                    
                    return {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "status_code": response.status,
                        "response_time_ms": response_time,
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_database_health(self) -> dict:
        """Verificar salud de MongoDB"""
        try:
            await connect_to_mongo()
            db = get_database()
            
            start_time = datetime.now()
            await db.command("ping")
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Obtener estadísticas de la base de datos
            stats = await db.command("dbStats")
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "collections": stats.get("collections", 0),
                "data_size_mb": round(stats.get("dataSize", 0) / 1024 / 1024, 2),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_redis_health(self) -> dict:
        """Verificar salud de Redis"""
        try:
            cache_service = CacheService()
            await cache_service.connect()
            
            start_time = datetime.now()
            await cache_service.redis_client.ping()
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Obtener información del servidor Redis
            info = await cache_service.redis_client.info()
            
            await cache_service.close()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "connected_clients": info.get("connected_clients", 0),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_system_metrics(self) -> dict:
        """Obtener métricas del sistema"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / 1024**3, 2),
                "available_gb": round(psutil.virtual_memory().available / 1024**3, 2),
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total_gb": round(psutil.disk_usage('/').total / 1024**3, 2),
                "free_gb": round(psutil.disk_usage('/').free / 1024**3, 2),
                "percent": psutil.disk_usage('/').percent
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def generate_report(self) -> dict:
        """Generar reporte completo de salud"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "api": await self.check_api_health(),
            "database": await self.check_database_health(),
            "redis": await self.check_redis_health(),
            "system": self.get_system_metrics()
        }
        
        # Calcular estado general
        all_healthy = all(
            service.get("status") == "healthy" 
            for service in [report["api"], report["database"], report["redis"]]
        )
        
        report["overall_status"] = "healthy" if all_healthy else "degraded"
        
        return report
    
    def save_report(self, report: dict, filename: str = None):
        """Guardar reporte en archivo"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitoring/health_report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Reporte guardado en: {filename}")

async def main():
    """Función principal"""
    monitor = SystemMonitor()
    
    print("🔍 Generando reporte de salud del sistema...")
    
    report = await monitor.generate_report()
    
    # Mostrar reporte en consola
    print("\n" + "="*60)
    print("📊 REPORTE DE SALUD - CMS DINÁMICO")
    print("="*60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Estado General: {report['overall_status'].upper()}")
    print()
    
    print("🌐 API:")
    api = report['api']
    print(f"  Estado: {api['status']}")
    if 'response_time_ms' in api:
        print(f"  Tiempo de respuesta: {api['response_time_ms']:.2f}ms")
    
    print("\n🗃️  Base de Datos:")
    db = report['database']
    print(f"  Estado: {db['status']}")
    if 'response_time_ms' in db:
        print(f"  Tiempo de respuesta: {db['response_time_ms']:.2f}ms")
        print(f"  Colecciones: {db['collections']}")
        print(f"  Tamaño de datos: {db['data_size_mb']} MB")
    
    print("\n🔄 Redis:")
    redis = report['redis']
    print(f"  Estado: {redis['status']}")
    if 'response_time_ms' in redis:
        print(f"  Tiempo de respuesta: {redis['response_time_ms']:.2f}ms")
        print(f"  Memoria usada: {redis['used_memory_mb']} MB")
        print(f"  Clientes conectados: {redis['connected_clients']}")
    
    print("\n💻 Sistema:")
    system = report['system']
    print(f"  CPU: {system['cpu_percent']}%")
    print(f"  Memoria: {system['memory']['percent']}% ({system['memory']['available_gb']:.1f}GB disponible)")
    print(f"  Disco: {system['disk']['percent']}% ({system['disk']['free_gb']:.1f}GB libre)")
    
    print("\n" + "="*60)
    
    # Guardar reporte
    monitor.save_report(report)
    
    # Exit code basado en el estado
    if report['overall_status'] != 'healthy':
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())