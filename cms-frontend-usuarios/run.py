#!/usr/bin/env python3
"""
CMS Dinámico - Frontend Usuario Final
Ejecutor principal
"""

import uvicorn
import logging
import sys
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Función principal para ejecutar el frontend"""
    
    print("🚀 CMS Dinámico - Dashboard Usuario Final")
    print("=" * 50)
    print("📍 Frontend URL: http://localhost:3001")
    print("🔗 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    
    # Verificar si existe el directorio templates
    if not os.path.exists('templates'):
        logger.error("❌ Directorio 'templates' no encontrado")
        logger.info("💡 Asegúrate de crear la carpeta 'templates' con los archivos HTML")
        sys.exit(1)
    
    # Verificar archivos de template esenciales
    required_templates = [
        'templates/base.html',
        'templates/login.html', 
        'templates/business_dashboard.html'
    ]
    
    missing_templates = []
    for template in required_templates:
        if not os.path.exists(template):
            missing_templates.append(template)
    
    if missing_templates:
        logger.error("❌ Templates faltantes:")
        for template in missing_templates:
            logger.error(f"   - {template}")
        logger.info("💡 Crea los archivos de template necesarios")
        sys.exit(1)
    
    # Crear directorio static si no existe
    os.makedirs('static', exist_ok=True)
    logger.info("✅ Directorio static verificado")
    
    print("\n👥 Usuarios Demo Disponibles:")
    print("   - admin / admin (Administrador)")
    print("   - tecnico / tecnico (Técnico)")
    print("   - usuario / usuario (Usuario Final)")
    print("   - superadmin / superadmin (Super Admin)")
    print("\n🎯 Business Demo: TelcoNorte ISP")
    print("\n⚠️  IMPORTANTE: Asegúrate de que el backend esté corriendo en localhost:8000")
    
    # Ejecutar servidor
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=3001,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("\n👋 Apagando servidor frontend...")
    except Exception as e:
        logger.error(f"❌ Error ejecutando servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()