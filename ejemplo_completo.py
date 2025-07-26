# ================================
# EJEMPLO COMPLETO DE INTEGRACIÓN - CMS DINÁMICO
# ================================

"""
Este ejemplo demuestra el flujo completo de:
1. Configurar una API externa 
2. Auto-discovery de campos
3. Mapeo de campos
4. Crear entidad
5. Visualizar datos
6. Exportar resultados

CASO DE USO: ISP TelcoNorte - Gestión de Clientes desde CRM
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

# Simulación de datos que vendrian de un CRM real
MOCK_CRM_DATA = [
    {
        "customer_id": "CLT001",
        "full_name": "María García López", 
        "email_address": "maria.garcia@email.com",
        "phone_number": "+54911234567",
        "service_plan": "Fibra 100MB",
        "monthly_fee": 2500.00,
        "installation_date": "2024-01-15",
        "account_status": "active",
        "address_street": "Av. Libertador 1234",
        "address_city": "Buenos Aires",
        "support_tickets": 2,
        "last_payment": "2024-11-01"
    },
    {
        "customer_id": "CLT002", 
        "full_name": "Carlos Rodríguez",
        "email_address": "carlos.rodriguez@email.com",
        "phone_number": "+54911234568",
        "service_plan": "Fibra 300MB",
        "monthly_fee": 4500.00,
        "installation_date": "2023-08-20",
        "account_status": "active", 
        "address_street": "San Martín 567",
        "address_city": "La Plata",
        "support_tickets": 0,
        "last_payment": "2024-11-01"
    },
    {
        "customer_id": "CLT003",
        "full_name": "Ana Fernández",
        "email_address": "ana.fernandez@email.com", 
        "phone_number": "+54911234569",
        "service_plan": "Fibra 500MB",
        "monthly_fee": 6500.00,
        "installation_date": "2024-03-10",
        "account_status": "suspended",
        "address_street": "Corrientes 890", 
        "address_city": "Buenos Aires",
        "support_tickets": 5,
        "last_payment": "2024-10-15"
    }
]

# ================================
# PASO 1: CONFIGURACIÓN DE API
# ================================

async def step1_configure_api():
    """Configurar API del CRM"""
    
    print("🔧 PASO 1: Configurando API del CRM...")
    
    api_config = {
        "business_id": "isp_telconorte",
        "api_id": "crm_clientes",
        "name": "CRM Clientes TelcoNorte", 
        "base_url": "https://api-mock.telconorte.com",
        "endpoint": "/customers",
        "method": "GET",
        "auth_type": "api_key",
        "auth_config": {
            "api_key": "TNC_API_2024_SECURE_KEY",
            "header_name": "X-TNC-API-Key"
        },
        "cache_ttl": 300,  # 5 minutos
        "active": True
    }
    
    print(f"✅ API configurada: {api_config['name']}")
    print(f"   URL: {api_config['base_url']}{api_config['endpoint']}")
    print(f"   Autenticación: {api_config['auth_type']}")
    print(f"   Cache TTL: {api_config['cache_ttl']}s")
    
    return api_config

# ================================
# PASO 2: AUTO-DISCOVERY
# ================================

async def step2_auto_discovery(api_config: Dict[str, Any]):
    """Simular auto-discovery de campos"""
    
    print("\n🔍 PASO 2: Auto-discovery de campos...")
    
    # Simular detección de campos del CRM
    detected_fields = list(MOCK_CRM_DATA[0].keys())
    
    print(f"✅ Campos detectados: {len(detected_fields)}")
    for field in detected_fields:
        print(f"   - {field}")
    
    # Generar mapeos automáticos inteligentes
    field_mappings = {
        "customer_id": "cliente_id",
        "full_name": "nombre_completo", 
        "email_address": "correo_electronico",
        "phone_number": "telefono",
        "service_plan": "plan_servicio",
        "monthly_fee": "tarifa_mensual",
        "installation_date": "fecha_instalacion",
        "account_status": "estado_cuenta",
        "address_street": "direccion",
        "address_city": "ciudad",
        "support_tickets": "tickets_soporte",
        "last_payment": "ultimo_pago"
    }
    
    print(f"\n🔗 Auto-mapeo generado:")
    for api_field, entity_field in field_mappings.items():
        confidence = calculate_mapping_confidence(api_field, entity_field)
        print(f"   {api_field} → {entity_field} (confianza: {confidence}%)")
    
    return {
        "detected_fields": detected_fields,
        "suggested_mappings": field_mappings,
        "sample_data": MOCK_CRM_DATA[:2]  # Primeras 2 muestras
    }

def calculate_mapping_confidence(api_field: str, entity_field: str) -> int:
    """Calcular confianza del mapeo"""
    # Lógica simplificada de confianza
    if api_field.lower() in entity_field.lower():
        return 95
    elif any(word in entity_field.lower() for word in api_field.lower().split('_')):
        return 85
    else:
        return 70

# ================================
# PASO 3: CREAR ENTIDAD
# ================================

async def step3_create_entity(discovery_result: Dict[str, Any]):
    """Crear configuración de entidad"""
    
    print("\n📋 PASO 3: Creando entidad 'clientes'...")
    
    # Configuración de campos con validaciones
    campos_config = []
    
    field_configs = {
        "cliente_id": {"tipo": "string", "obligatorio": True, "unico": True},
        "nombre_completo": {"tipo": "string", "obligatorio": True},
        "correo_electronico": {"tipo": "email", "obligatorio": True},
        "telefono": {"tipo": "phone", "obligatorio": True},
        "plan_servicio": {"tipo": "string", "opciones": ["Fibra 100MB", "Fibra 300MB", "Fibra 500MB"]},
        "tarifa_mensual": {"tipo": "number", "obligatorio": True, "min": 0},
        "fecha_instalacion": {"tipo": "date", "obligatorio": True},
        "estado_cuenta": {"tipo": "string", "opciones": ["active", "suspended", "cancelled"]},
        "direccion": {"tipo": "string"},
        "ciudad": {"tipo": "string"},
        "tickets_soporte": {"tipo": "number", "min": 0},
        "ultimo_pago": {"tipo": "date"}
    }
    
    for api_field, entity_field in discovery_result["suggested_mappings"].items():
        campo_config = {
            "campo": entity_field,
            "campo_api": api_field,
            "obligatorio": field_configs.get(entity_field, {}).get("obligatorio", False),
            "tipo": field_configs.get(entity_field, {}).get("tipo", "string"),
            "visible_roles": ["admin", "operador"],
            "editable_roles": ["admin"]
        }
        
        if "opciones" in field_configs.get(entity_field, {}):
            campo_config["opciones"] = field_configs[entity_field]["opciones"]
            
        if "min" in field_configs.get(entity_field, {}):
            campo_config["validacion"] = {"min": field_configs[entity_field]["min"]}
        
        campos_config.append(campo_config)
    
    entity_config = {
        "business_id": "isp_telconorte",
        "entidad": "clientes",
        "configuracion": {
            "descripcion": "Gestión de clientes desde CRM TelcoNorte",
            "campos": campos_config,
            "api_config": {
                "api_id": "crm_clientes",
                "mapeo": discovery_result["suggested_mappings"],
                "cache_ttl": 300,
                "auto_refresh": True
            },
            "crud_config": {
                "crear": {"habilitado": True, "roles": ["admin"]},
                "editar": {"habilitado": True, "roles": ["admin", "operador"]},
                "eliminar": {"habilitado": False},  # No permitir eliminar clientes
                "exportar": {"habilitado": True, "formatos": ["csv", "json"]}
            },
            "dashboard_config": {
                "vista_defecto": "tabla",
                "campos_resumen": ["nombre_completo", "plan_servicio", "estado_cuenta", "tarifa_mensual"],
                "metricas": ["total_clientes", "clientes_activos", "ingresos_mensuales", "tickets_promedio"]
            }
        }
    }
    
    print(f"✅ Entidad creada: {entity_config['entidad']}")
    print(f"   Campos configurados: {len(campos_config)}")
    print(f"   CRUD habilitado: Crear ✅, Editar ✅, Eliminar ❌")
    print(f"   Exportación: CSV ✅, JSON ✅")
    
    return entity_config

# ================================
# PASO 4: PROBAR Y VISUALIZAR
# ================================

async def step4_test_and_visualize(entity_config: Dict[str, Any]):
    """Probar API y visualizar datos"""
    
    print("\n📊 PASO 4: Probando API y visualizando datos...")
    
    # Simular test de API exitoso
    test_result = {
        "success": True,
        "status_code": 200,
        "response_time_ms": 250,
        "total_records": len(MOCK_CRM_DATA),
        "sample_data": MOCK_CRM_DATA,
        "detected_fields": list(MOCK_CRM_DATA[0].keys())
    }
    
    # Aplicar mapeo de campos
    mapped_data = []
    mapeo = entity_config["configuracion"]["api_config"]["mapeo"]
    
    for item in MOCK_CRM_DATA:
        mapped_item = {}
        for api_field, entity_field in mapeo.items():
            if api_field in item:
                mapped_item[entity_field] = item[api_field]
        mapped_data.append(mapped_item)
    
    print(f"✅ Test API exitoso:")
    print(f"   Status: {test_result['status_code']}")
    print(f"   Tiempo respuesta: {test_result['response_time_ms']}ms")
    print(f"   Registros obtenidos: {test_result['total_records']}")
    
    print(f"\n🔗 Datos mapeados (muestra):")
    for i, item in enumerate(mapped_data[:2]):
        print(f"   Cliente {i+1}:")
        for field, value in item.items():
            print(f"     {field}: {value}")
        print()
    
    # Generar diferentes visualizaciones
    visualizations = generate_visualizations(mapped_data)
    
    return {
        "test_result": test_result,
        "mapped_data": mapped_data,
        "visualizations": visualizations
    }

def generate_visualizations(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generar diferentes tipos de visualización"""
    
    # Vista de tabla
    table_view = {
        "type": "table",
        "columns": list(data[0].keys()) if data else [],
        "rows": data,
        "pagination": {"page": 1, "per_page": 10, "total": len(data)}
    }
    
    # Vista de cards
    cards_view = {
        "type": "cards",
        "items": data,
        "primary_field": "nombre_completo",
        "secondary_fields": ["plan_servicio", "estado_cuenta", "tarifa_mensual"]
    }
    
    # Estadísticas
    stats = calculate_business_stats(data)
    
    # Gráficos
    charts = generate_charts_data(data)
    
    return {
        "table": table_view,
        "cards": cards_view, 
        "stats": stats,
        "charts": charts
    }

def calculate_business_stats(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcular estadísticas del negocio"""
    
    if not data:
        return {}
    
    total_clientes = len(data)
    clientes_activos = len([c for c in data if c.get("estado_cuenta") == "active"])
    
    # Ingresos mensuales
    ingresos = sum(float(c.get("tarifa_mensual", 0)) for c in data if c.get("estado_cuenta") == "active")
    
    # Tickets promedio
    total_tickets = sum(int(c.get("tickets_soporte", 0)) for c in data)
    tickets_promedio = total_tickets / total_clientes if total_clientes > 0 else 0
    
    # Distribución por plan
    planes = {}
    for cliente in data:
        plan = cliente.get("plan_servicio", "Sin plan")
        planes[plan] = planes.get(plan, 0) + 1
    
    return {
        "total_clientes": total_clientes,
        "clientes_activos": clientes_activos,
        "tasa_actividad": round((clientes_activos / total_clientes) * 100, 1) if total_clientes > 0 else 0,
        "ingresos_mensuales": ingresos,
        "tickets_promedio": round(tickets_promedio, 1),
        "distribucion_planes": planes,
        "arpu": round(ingresos / clientes_activos, 2) if clientes_activos > 0 else 0  # Average Revenue Per User
    }

def generate_charts_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generar datos para gráficos"""
    
    if not data:
        return {}
    
    # Gráfico de barras: Clientes por plan
    planes = {}
    for cliente in data:
        plan = cliente.get("plan_servicio", "Sin plan")
        planes[plan] = planes.get(plan, 0) + 1
    
    chart_planes = {
        "type": "bar",
        "title": "Clientes por Plan de Servicio",
        "labels": list(planes.keys()),
        "data": list(planes.values()),
        "backgroundColor": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"]
    }
    
    # Gráfico de pie: Estados de cuenta
    estados = {}
    for cliente in data:
        estado = cliente.get("estado_cuenta", "unknown")
        estados[estado] = estados.get(estado, 0) + 1
    
    chart_estados = {
        "type": "pie",
        "title": "Distribución por Estado de Cuenta",
        "labels": list(estados.keys()),
        "data": list(estados.values()),
        "backgroundColor": ["#10B981", "#F59E0B", "#EF4444"]
    }
    
    # Gráfico de línea: Ingresos por plan
    ingresos_plan = {}
    for cliente in data:
        if cliente.get("estado_cuenta") == "active":
            plan = cliente.get("plan_servicio", "Sin plan")
            tarifa = float(cliente.get("tarifa_mensual", 0))
            ingresos_plan[plan] = ingresos_plan.get(plan, 0) + tarifa
    
    chart_ingresos = {
        "type": "bar",
        "title": "Ingresos Mensuales por Plan",
        "labels": list(ingresos_plan.keys()),
        "data": list(ingresos_plan.values()),
        "backgroundColor": "#059669"
    }
    
    return {
        "planes_distribucion": chart_planes,
        "estados_cuenta": chart_estados,
        "ingresos_por_plan": chart_ingresos
    }

# ================================
# PASO 5: EXPORTACIÓN
# ================================

async def step5_export_data(visualization_result: Dict[str, Any]):
    """Exportar datos en diferentes formatos"""
    
    print("\n📄 PASO 5: Exportando datos...")
    
    mapped_data = visualization_result["mapped_data"]
    
    # Exportar a CSV
    csv_content = generate_csv_export(mapped_data)
    print(f"✅ CSV generado: {len(csv_content)} caracteres")
    
    # Exportar a JSON
    json_export = {
        "entity_name": "clientes",
        "business_id": "isp_telconorte",
        "export_date": datetime.now().isoformat(),
        "total_records": len(mapped_data),
        "data": mapped_data,
        "metadata": {
            "source": "CRM TelcoNorte",
            "api_endpoint": "/customers",
            "mapping_applied": True
        }
    }
    
    json_content = json.dumps(json_export, indent=2, ensure_ascii=False)
    print(f"✅ JSON generado: {len(json_content)} caracteres")
    
    # Resumen de exportación
    stats = visualization_result["visualizations"]["stats"]
    
    print(f"\n📊 Resumen de exportación:")
    print(f"   Total clientes: {stats['total_clientes']}")
    print(f"   Clientes activos: {stats['clientes_activos']} ({stats['tasa_actividad']}%)")
    print(f"   Ingresos mensuales: ${stats['ingresos_mensuales']:,.2f}")
    print(f"   ARPU: ${stats['arpu']:,.2f}")
    print(f"   Tickets promedio: {stats['tickets_promedio']}")
    
    return {
        "csv_export": csv_content,
        "json_export": json_content,
        "export_stats": stats
    }

def generate_csv_export(data: List[Dict[str, Any]]) -> str:
    """Generar contenido CSV"""
    
    if not data:
        return ""
    
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()

# ================================
# FUNCIÓN PRINCIPAL
# ================================

async def run_complete_example():
    """Ejecutar ejemplo completo de integración"""
    
    print("🚀 INICIANDO EJEMPLO COMPLETO DE INTEGRACIÓN")
    print("=" * 60)
    print("CASO DE USO: ISP TelcoNorte - Gestión de Clientes desde CRM")
    print("=" * 60)
    
    try:
        # Paso 1: Configurar API
        api_config = await step1_configure_api()
        
        # Paso 2: Auto-discovery 
        discovery_result = await step2_auto_discovery(api_config)
        
        # Paso 3: Crear entidad
        entity_config = await step3_create_entity(discovery_result)
        
        # Paso 4: Probar y visualizar
        visualization_result = await step4_test_and_visualize(entity_config)
        
        # Paso 5: Exportar datos
        export_result = await step5_export_data(visualization_result)
        
        print("\n🎉 EJEMPLO COMPLETADO EXITOSAMENTE!")
        print("=" * 60)
        
        # Mostrar comandos para probar en el servidor real
        print("\n🔧 COMANDOS PARA PROBAR EN EL SERVIDOR:")
        print_test_commands()
        
        return {
            "api_config": api_config,
            "entity_config": entity_config,
            "test_result": visualization_result["test_result"],
            "export_stats": export_result["export_stats"]
        }
        
    except Exception as e:
        print(f"\n❌ ERROR EN EL EJEMPLO: {e}")
        raise

def print_test_commands():
    """Imprimir comandos para probar en servidor real"""
    
    commands = [
        "# 1. Iniciar servidor",
        "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
        "",
        "# 2. Cargar ejemplos de APIs",
        "curl -X GET http://localhost:8000/api/admin/load-examples",
        "",
        "# 3. Acceder a interfaz de testing",
        "# http://localhost:8000/api-testing",
        "",
        "# 4. Probar API JSONPlaceholder",
        """curl -X POST http://localhost:8000/api/admin/api-test \\
  -H "Content-Type: application/json" \\
  -d '{
    "business_id": "demo_testing",
    "api_id": "jsonplaceholder_users",
    "base_url": "https://jsonplaceholder.typicode.com",
    "endpoint": "/users",
    "method": "GET",
    "limit_records": 5
  }'""",
        "",
        "# 5. Auto-discovery de campos",
        """curl -X POST http://localhost:8000/api/admin/api-discover \\
  -H "Content-Type: application/json" \\
  -d '{
    "business_id": "demo_testing",
    "api_id": "jsonplaceholder_users"
  }'""",
        "",
        "# 6. Ver datos de entidad",
        "curl -X GET http://localhost:8000/api/business/demo_testing/entity-data/usuarios",
        "",
        "# 7. Acceder a dashboard de visualización", 
        "# http://localhost:8000/data-visualization",
        "",
        "# 8. Ver logs de API",
        "tail -f logs/api-testing.log"
    ]
    
    for cmd in commands:
        print(cmd)

# ================================
# EJECUTAR EJEMPLO
# ================================

if __name__ == "__main__":
    # Ejecutar ejemplo completo
    result = asyncio.run(run_complete_example())
    
    print(f"\n📋 RESULTADO FINAL:")
    print(f"API configurada: ✅")
    print(f"Entidad creada: ✅") 
    print(f"Test exitoso: ✅")
    print(f"Datos exportados: ✅")
    
    # Guardar configuraciones en archivos
    with open("api_config_example.json", "w") as f:
        json.dump(result["api_config"], f, indent=2, ensure_ascii=False)
    
    with open("entity_config_example.json", "w") as f:
        json.dump(result["entity_config"], f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Configuraciones guardadas:")
    print(f"   api_config_example.json")
    print(f"   entity_config_example.json")