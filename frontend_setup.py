#!/usr/bin/env python3
"""
Script para crear la estructura completa del frontend
"""

import os

# Directorios a crear
directories = [
    "app/frontend",
    "app/frontend/routers", 
    "app/frontend/templates",
    "app/frontend/templates/business_types",
    "app/frontend/templates/businesses",
    "app/frontend/static",
    "app/frontend/static/css",
    "app/frontend/static/js", 
    "app/frontend/static/images"
]

# Archivos __init__.py a crear
init_files = [
    "app/frontend/__init__.py",
    "app/frontend/routers/__init__.py"
]

# Archivos básicos de contenido
basic_files = {
    "app/frontend/static/css/style.css": """/* CMS Dinámico - Estilos personalizados */
.cms-logo {
    max-width: 200px;
}

.sidebar-active {
    background-color: #eff6ff;
    border-right: 2px solid #3b82f6;
}

.flash-message {
    animation: fadeIn 0.5s;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
""",
    
    "app/frontend/static/js/main.js": """// CMS Dinámico - JavaScript principal
document.addEventListener('DOMContentLoaded', function() {
    console.log('CMS Dinámico frontend cargado');
    
    // Auto-hide flash messages after 5 seconds
    setTimeout(function() {
        const messages = document.querySelectorAll('.flash-message');
        messages.forEach(function(msg) {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        });
    }, 5000);
});
"""
}

def create_directories():
    """Crear directorios necesarios"""
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directorio creado: {directory}")

def create_init_files():
    """Crear archivos __init__.py"""
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('"""Frontend módulo"""\n')
            print(f"✅ Archivo creado: {init_file}")

def create_basic_files():
    """Crear archivos básicos"""
    for file_path, content in basic_files.items():
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Archivo creado: {file_path}")

def main():
    """Función principal"""
    print("🚀 Configurando estructura del frontend...")
    
    create_directories()
    create_init_files() 
    create_basic_files()
    
    print("\n✅ Estructura del frontend creada exitosamente!")
    print("\n📝 Próximos pasos:")
    print("1. Ejecutar: python run.py")
    print("2. Abrir: http://localhost:8000")
    print("3. Login: superadmin / superadmin")

if __name__ == "__main__":
    main()