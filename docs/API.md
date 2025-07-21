# ================================
# docs/API.md
# ================================

# CMS Dinámico - Documentación de API

## Autenticación

Todas las peticiones a la API (excepto `/health` y `/`) requieren autenticación mediante Clerk.

### Headers requeridos:
```
Authorization: Bearer <clerk_session_token>
Content-Type: application/json
```

## Endpoints Principales

### Autenticación
- `GET /api/auth/me` - Obtener información del usuario actual
- `PUT /api/auth/me` - Actualizar información del usuario actual
- `POST /api/auth/webhook` - Webhook de Clerk (interno)

### Administración - Business Types
- `GET /api/admin/business-types` - Listar tipos de negocio
- `GET /api/admin/business-types/{tipo}` - Obtener tipo específico
- `POST /api/admin/business-types` - Crear nuevo tipo
- `PUT /api/admin/business-types/{tipo}` - Actualizar tipo
- `DELETE /api/admin/business-types/{tipo}` - Eliminar tipo

### Administración - Business Instances
- `GET /api/admin/businesses` - Listar instancias de negocio
- `GET /api/admin/businesses/{business_id}` - Obtener instancia específica
- `POST /api/admin/businesses` - Crear nueva instancia
- `PUT /api/admin/businesses/{business_id}` - Actualizar instancia
- `DELETE /api/admin/businesses/{business_id}` - Eliminar instancia

### Business Operations
- `GET /api/business/entities/{business_id}/{entidad}` - Obtener datos de entidad
- `POST /api/business/entities/{business_id}/{entidad}` - Crear item en entidad
- `GET /api/business/dashboard/{business_id}` - Obtener datos del dashboard

### Integraciones
- `GET /api/integrations/waha/{business_id}/sessions` - Sesiones de WhatsApp
- `POST /api/integrations/waha/{business_id}/send-message` - Enviar mensaje
- `GET /api/integrations/n8n/{business_id}/workflows` - Workflows de N8N

## Códigos de Respuesta

- `200` - Éxito
- `201` - Creado
- `400` - Error de validación
- `401` - No autenticado
- `403` - Sin permisos
- `404` - No encontrado
- `429` - Rate limit excedido
- `500` - Error interno

## Ejemplos de Uso

### Crear Business Type
```bash
curl -X POST "http://localhost:8000/api/admin/business-types" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "restaurante",
    "nombre": "Restaurante Template",
    "componentes_base": [
      {
        "id": "whatsapp",
        "nombre": "WhatsApp",
        "tipo": "integration",
        "obligatorio": true
      }
    ]
  }'
```

### Obtener Dashboard
```bash
curl -X GET "http://localhost:8000/api/business/dashboard/mi_restaurante" \
  -H "Authorization: Bearer $TOKEN"
```
