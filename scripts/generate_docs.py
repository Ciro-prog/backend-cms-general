# ================================
# scripts/generate_docs.py
# ================================

#!/usr/bin/env python3
"""
Script para generar documentación automática de la API
"""

import json
import sys
import os
from pathlib import Path

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_openapi_docs():
    """Generar documentación OpenAPI"""
    from app.main import app
    
    openapi_schema = app.openapi()
    
    # Guardar schema
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    with open(docs_dir / "openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print("✅ Documentación OpenAPI generada en docs/openapi.json")

def generate_postman_collection():
    """Generar colección de Postman"""
    from app.main import app
    
    # TODO: Implementar generación de colección Postman
    print("🚧 Generación de colección Postman pendiente")

if __name__ == "__main__":
    print("📚 Generando documentación...")
    generate_openapi_docs()
    generate_postman_collection()
    print("✅ Documentación generada")