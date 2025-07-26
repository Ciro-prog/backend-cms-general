#!/usr/bin/env python3
# ================================
# fix_syntax_error.py - ARREGLAR ERROR DE SINTAXIS
# ================================

from pathlib import Path
from datetime import datetime

def fix_syntax_error_in_main():
    """Arreglar el error de sintaxis en main.py"""
    
    main_file = Path("app/main.py")
    
    if not main_file.exists():
        print("❌ main.py no existe")
        return
    
    print("🔧 Arreglando error de sintaxis en main.py...")
    
    # Backup
    timestamp = datetime.now().strftime("%H%M%S")
    backup_path = main_file.with_suffix(f'.backup_syntax_{timestamp}.py')
    
    try:
        content = main_file.read_text(encoding='utf-8')
        backup_path.write_text(content, encoding='utf-8')
        print(f"✅ Backup: {backup_path.name}")
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        return
    
    # El problema está en que el endpoint test-connection tiene un try sin except
    # Vamos a recrear ese endpoint completo y correcto
    
    # Buscar el endpoint problemático y reemplazarlo completamente
    lines = content.split('\n')
    new_lines = []
    skip_lines = False
    found_test_connection = False
    
    for i, line in enumerate(lines):
        # Detectar inicio del endpoint problemático
        if '@app.post("/api-management/test-connection")' in line:
            found_test_connection = True
            skip_lines = True
            # Agregar el endpoint corregido completo
            new_lines.extend([
                '@app.post("/api-management/test-connection")',
                'async def test_api_connection_ajax(request: Request):',
                '    """Test de conexión a API externa - CORREGIDO"""',
                '    try:',
                '        form = await request.form()',
                '        config_data = {',
                '            "business_id": form.get("business_id", "test"),',
                '            "name": form.get("name", "Test API"),',
                '            "base_url": form.get("base_url", ""),',
                '            "endpoint": form.get("endpoint", ""),',
                '            "method": form.get("method", "GET"),',
                '            "auth_type": form.get("auth_type", "none")',
                '        }',
                '        ',
                '        # Test directo con httpx',
                '        import httpx',
                '        import time',
                '        ',
                '        # Construir URL completa',
                '        base_url = config_data["base_url"].rstrip(\'/\')',
                '        endpoint = config_data["endpoint"].lstrip(\'/\')',
                '        if not endpoint.startswith(\'/\'):',
                '            endpoint = \'/\' + endpoint',
                '        full_url = base_url + endpoint',
                '        ',
                '        logger.info(f"🧪 Probando conexión a: {full_url}")',
                '        ',
                '        # Realizar petición',
                '        start_time = time.time()',
                '        ',
                '        try:',
                '            async with httpx.AsyncClient(timeout=10) as client:',
                '                if config_data["method"].upper() == "GET":',
                '                    response = await client.get(full_url)',
                '                elif config_data["method"].upper() == "POST":',
                '                    response = await client.post(full_url)',
                '                else:',
                '                    response = await client.request(config_data["method"].upper(), full_url)',
                '            ',
                '            response_time = (time.time() - start_time) * 1000',
                '            ',
                '            # Procesar respuesta',
                '            if response.status_code == 200:',
                '                try:',
                '                    json_data = response.json()',
                '                    ',
                '                    # Detectar estructura de datos',
                '                    if isinstance(json_data, dict):',
                '                        detected_fields = list(json_data.keys())',
                '                        sample_data = [json_data]  # Convertir a lista para consistencia',
                '                    elif isinstance(json_data, list) and len(json_data) > 0:',
                '                        detected_fields = list(json_data[0].keys()) if json_data[0] else []',
                '                        sample_data = json_data[:5]  # Primeros 5 elementos',
                '                    else:',
                '                        detected_fields = []',
                '                        sample_data = json_data',
                '                    ',
                '                    return {',
                '                        "success": True,',
                '                        "data": {',
                '                            "status_code": response.status_code,',
                '                            "response_time_ms": round(response_time, 2),',
                '                            "sample_data": sample_data,',
                '                            "detected_fields": detected_fields,',
                '                            "total_records": len(sample_data) if isinstance(sample_data, list) else 1,',
                '                            "data_type": type(json_data).__name__,',
                '                            "error_message": None',
                '                        }',
                '                    }',
                '                except Exception as json_error:',
                '                    return {',
                '                        "success": False,',
                '                        "data": {',
                '                            "status_code": response.status_code,',
                '                            "response_time_ms": round(response_time, 2),',
                '                            "error_message": f"Respuesta no es JSON válido: {str(json_error)}",',
                '                            "raw_content": response.text[:200] + "..." if len(response.text) > 200 else response.text',
                '                        }',
                '                    }',
                '            else:',
                '                return {',
                '                    "success": False,',
                '                    "data": {',
                '                        "status_code": response.status_code,',
                '                        "response_time_ms": round(response_time, 2),',
                '                        "error_message": f"HTTP {response.status_code}: {response.text[:100]}",',
                '                        "sample_data": None,',
                '                        "detected_fields": []',
                '                    }',
                '                }',
                '                ',
                '        except httpx.TimeoutException:',
                '            return {',
                '                "success": False,',
                '                "data": {',
                '                    "error_message": "Timeout - La API no respondió en 10 segundos",',
                '                    "status_code": None,',
                '                    "response_time_ms": None',
                '                }',
                '            }',
                '        except httpx.RequestError as e:',
                '            return {',
                '                "success": False,',
                '                "data": {',
                '                    "error_message": f"Error de conexión: {str(e)}",',
                '                    "status_code": None,',
                '                    "response_time_ms": None',
                '                }',
                '            }',
                '            ',
                '    except Exception as e:',
                '        logger.error(f"Error probando API: {e}")',
                '        return {',
                '            "success": False,',
                '            "error": str(e)',
                '        }',
                ''
            ])
            continue
        
        # Detectar fin del endpoint problemático
        if skip_lines and line.startswith('@app.') and 'test-connection' not in line:
            skip_lines = False
            new_lines.append(line)
            continue
        
        # Si no estamos saltando líneas, agregar línea normal
        if not skip_lines:
            new_lines.append(line)
    
    if found_test_connection:
        print("✅ Endpoint test-connection reemplazado completamente")
    else:
        print("⚠️ No se encontró el endpoint test-connection problemático")
    
    # Escribir archivo corregido
    try:
        corrected_content = '\n'.join(new_lines)
        main_file.write_text(corrected_content, encoding='utf-8')
        print(f"✅ Archivo main.py corregido")
    except Exception as e:
        print(f"❌ Error escribiendo archivo: {e}")

def verify_syntax():
    """Verificar que no hay errores de sintaxis"""
    
    print("\n🔍 Verificando sintaxis...")
    
    try:
        import ast
        main_file = Path("app/main.py")
        
        with open(main_file, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Intentar compilar el código
        ast.parse(source)
        print("✅ Sintaxis correcta - no hay errores")
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis encontrado:")
        print(f"   Línea {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error verificando sintaxis: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 ARREGLANDO ERROR DE SINTAXIS EN MAIN.PY")
    print("=" * 50)
    
    print("🎯 Error identificado:")
    print("   ❌ SyntaxError: expected 'except' or 'finally' block")
    print("   📍 Línea 513: @app.post('/api-management/test-connection')")
    print("   🔍 Problema: bloque try sin except correspondiente")
    print("")
    
    # Arreglar el error
    fix_syntax_error_in_main()
    
    # Verificar que se arregló
    syntax_ok = verify_syntax()
    
    print(f"\n🎉 CORRECCIÓN COMPLETADA")
    
    if syntax_ok:
        print("✅ Sintaxis corregida exitosamente")
        print("✅ Endpoint test-connection reconstruido")
        print("✅ Archivo listo para ejecutar")
        print("")
        print("🚀 AHORA EJECUTA:")
        print("   python run.py")
        print("")
        print("🎮 LUEGO PRUEBA POKEAPI:")
        print("   1. Ve a /api-management/wizard")
        print("   2. Cambia POST → GET")
        print("   3. Presiona 'Probar Conexión'")
    else:
        print("❌ Aún hay errores de sintaxis")
        print("💡 Puede que necesites revisar manualmente el archivo")

if __name__ == "__main__":
    main()