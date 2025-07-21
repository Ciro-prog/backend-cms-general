# ================================
# run.py (ACTUALIZADO para cargar .env correctamente)
# ================================

#!/usr/bin/env python3
"""
Script para ejecutar el servidor de desarrollo
"""

import uvicorn
import os
from dotenv import load_dotenv

# Cargar variables de entorno ANTES de importar la app
load_dotenv()

if __name__ == "__main__":
    # Mostrar algunas variables para debug
    print("🔧 Variables de entorno cargadas:")
    print(f"WAHA URL: {os.getenv('DEFAULT_WAHA_URL', 'NO CONFIGURADO')}")
    print(f"N8N URL: {os.getenv('DEFAULT_N8N_URL', 'NO CONFIGURADO')}")
    print(f"WAHA API Key: {'✅ Configurado' if os.getenv('DEFAULT_WAHA_API_KEY') else '❌ Falta'}")
    print(f"N8N API Key: {'✅ Configurado' if os.getenv('DEFAULT_N8N_API_KEY') else '❌ Falta'}")
    print(f"Redis API Key: {'✅ Configurado' if os.getenv('REDIS_API_KEY') else '❌ Falta'}")
    print("")
    
    # Configuración para desarrollo
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    )
