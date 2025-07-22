// ===================================================================
// JAVASCRIPT COMPLETO PARA EL CONFIGURADOR DE ENTIDADES
// ===================================================================

// Estado global
let currentBusiness = null;
let currentEntity = null;
let businessList = [];
let entityConfigs = {};

// URLs de la API - usar la misma base que el servidor actual
const API_BASE = window.location.origin + '/api';

// Inicialización
document.addEventListener('DOMContentLoaded', async () => {
    await loadBusinessList();
});

// ================================
// GESTIÓN DE BUSINESSES
// ================================

// Cargar lista de businesses
async function loadBusinessList() {
    try {
        const response = await fetch(`${API_BASE}/admin/businesses`);
        if (!response.ok) throw new Error('Error cargando businesses');
        
        businessList = await response.json();
        const select = document.getElementById('businessSelect');
        
        select.innerHTML = '<option value="">Selecciona un business...</option>';
        businessList.forEach(business => {
            const option = document.createElement('option');
            option.value = business.business_id;
            option.textContent = `${business.nombre} (${business.business_id})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error cargando businesses', 'error');
    }
}

// Cargar business seleccionado
async function loadBusiness() {
    const businessId = document.getElementById('businessSelect').value;
    if (!businessId) {
        document.getElementById('entitiesList').innerHTML = '<div class="text-gray-500 text-center py-4">Selecciona un business primero</div>';
        return;
    }

    currentBusiness = businessList.find(b => b.business_id === businessId);
    document.getElementById('businessName').textContent = currentBusiness?.nombre || businessId;

    await loadEntities(businessId);
}

// ================================
// GESTIÓN DE ENTIDADES
// ================================

// Cargar entidades del business
async function loadEntities(businessId) {
    try {
        const response = await fetch(`${API_BASE}/admin/entities/${businessId}`);
        const entities = response.ok ? await response.json() : [];
        
        const container = document.getElementById('entitiesList');
        
        if (entities.length === 0) {
            container.innerHTML = `
                <div class="text-gray-500 text-center py-4">
                    <div class="text-2xl mb-2">📊</div>
                    <div>No hay entidades configuradas</div>
                    <button onclick="createNewEntity()" class="text-blue-600 hover:text-blue-800 mt-2">
                        Crear la primera entidad
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = entities.map(entity => `
            <div class="entity-item p-3 border rounded-lg cursor-pointer hover:bg-gray-50 ${currentEntity?.entidad === entity.entidad ? 'bg-blue-50 border-blue-300' : ''}"
                 onclick="selectEntity('${entity.entidad}')">
                <div class="font-medium">${entity.entidad}</div>
                <div class="text-sm text-gray-600">${entity.configuracion?.descripcion || 'Sin descripción'}</div>
                <div class="text-xs text-gray-500 mt-1">
                    ${entity.configuracion?.campos?.length || 0} campos configurados
                </div>
            </div>
        `).join('');

        // Cargar configuraciones en memoria
        entities.forEach(entity => {
            entityConfigs[entity.entidad] = entity;
        });

    } catch (error) {
        console.error('Error:', error);
        showNotification('Error cargando entidades', 'error');
    }
}

// Seleccionar entidad para configurar
async function selectEntity(entityName) {
    currentEntity = entityConfigs[entityName];
    
    // Actualizar UI de selección
    document.querySelectorAll('.entity-item').forEach(item => {
        item.classList.remove('bg-blue-50', 'border-blue-300');
    });
    event.target.closest('.entity-item').classList.add('bg-blue-50', 'border-blue-300');
    
    await renderEntityConfig();
}

// ================================
// RENDERIZADO DE CONFIGURACIÓN
// ================================

// Renderizar configuración de entidad
async function renderEntityConfig() {
    if (!currentEntity) return;

    const panel = document.getElementById('entityConfigPanel');
    const config = currentEntity.configuracion || {};
    const campos = config.campos || [];

    panel.innerHTML = `
        <div class="space-y-6">
            <!-- Header de la Entidad -->
            <div class="border-b pb-4">
                <div class="flex justify-between items-center">
                    <div>
                        <h2 class="text-xl font-semibold text-gray-900">📊 ${currentEntity.entidad}</h2>
                        <p class="text-gray-600">${config.descripcion || 'Sin descripción'}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="testEntityAPI()" class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                            🧪 Test API
                        </button>
                        <button onclick="deleteEntity()" class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700">
                            🗑️ Eliminar
                        </button>
                    </div>
                </div>
            </div>

            <!-- Tabs -->
            <div class="border-b">
                <nav class="flex space-x-8">
                    <button onclick="showTab('campos')" class="tab-btn py-2 px-1 border-b-2 border-blue-500 text-blue-600 font-medium">
                        📝 Campos
                    </button>
                    <button onclick="showTab('api')" class="tab-btn py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700">
                        🔌 API Externa
                    </button>
                    <button onclick="showTab('permisos')" class="tab-btn py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700">
                        🔒 Permisos
                    </button>
                    <button onclick="showTab('crud')" class="tab-btn py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700">
                        ⚡ CRUD
                    </button>
                </nav>
            </div>

            <!-- Tab Content -->
            <div id="tabContent">
                ${renderCamposTab(campos)}
            </div>
        </div>
    `;
}

// ================================
// RENDERIZADO DE TABS
// ================================

// Renderizar tab de campos
function renderCamposTab(campos) {
    return `
        <div class="space-y-4">
            <div class="flex justify-between items-center">
                <h3 class="text-lg font-medium">Configuración de Campos</h3>
                <button onclick="addNewField()" class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                    ➕ Nuevo Campo
                </button>
            </div>
            
            <div id="fieldsContainer" class="space-y-3">
                ${campos.map((campo, index) => renderFieldConfig(campo, index)).join('')}
                ${campos.length === 0 ? '<div class="text-center text-gray-500 py-8">No hay campos configurados</div>' : ''}
            </div>
        </div>
    `;
}

// Renderizar configuración de campo individual
function renderFieldConfig(campo, index) {
    const tipos = ['text', 'number', 'select', 'date', 'boolean', 'phone', 'email', 'textarea'];
    const roles = ['admin', 'tecnico', 'user', 'viewer'];

    return `
        <div class="field-config border rounded-lg p-4 bg-gray-50">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <!-- Información básica -->
                <div class="space-y-3">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Nombre del Campo</label>
                        <input type="text" value="${campo.campo}" onchange="updateField(${index}, 'campo', this.value)" 
                               class="w-full p-2 border rounded">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                        <select onchange="updateField(${index}, 'tipo', this.value)" class="w-full p-2 border rounded">
                            ${tipos.map(tipo => `<option value="${tipo}" ${campo.tipo === tipo ? 'selected' : ''}>${tipo}</option>`).join('')}
                        </select>
                    </div>
                    <div class="flex items-center space-x-2">
                        <input type="checkbox" ${campo.obligatorio ? 'checked' : ''} 
                               onchange="updateField(${index}, 'obligatorio', this.checked)" id="req_${index}">
                        <label for="req_${index}" class="text-sm text-gray-700">Obligatorio</label>
                    </div>
                </div>

                <!-- Permisos -->
                <div class="space-y-3">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Visible para roles</label>
                        <div class="space-y-1">
                            ${roles.map(rol => `
                                <label class="flex items-center space-x-2">
                                    <input type="checkbox" ${(campo.visible_roles || ['*']).includes(rol) || (campo.visible_roles || ['*']).includes('*') ? 'checked' : ''}
                                           onchange="updateFieldRoles(${index}, 'visible_roles', '${rol}', this.checked)">
                                    <span class="text-sm">${rol}</span>
                                </label>
                            `).join('')}
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Editable por roles</label>
                        <div class="space-y-1">
                            ${roles.map(rol => `
                                <label class="flex items-center space-x-2">
                                    <input type="checkbox" ${(campo.editable_roles || ['admin']).includes(rol) ? 'checked' : ''}
                                           onchange="updateFieldRoles(${index}, 'editable_roles', '${rol}', this.checked)">
                                    <span class="text-sm">${rol}</span>
                                </label>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- Validación y opciones -->
                <div class="space-y-3">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Validación</label>
                        <input type="text" value="${campo.validacion || ''}" 
                               onchange="updateField(${index}, 'validacion', this.value)"
                               placeholder="ej: min:10, max:100, email"
                               class="w-full p-2 border rounded">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Placeholder</label>
                        <input type="text" value="${campo.placeholder || ''}" 
                               onchange="updateField(${index}, 'placeholder', this.value)"
                               class="w-full p-2 border rounded">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
                        <textarea onchange="updateField(${index}, 'descripcion', this.value)"
                                  class="w-full p-2 border rounded" rows="2">${campo.descripcion || ''}</textarea>
                    </div>
                    <button onclick="removeField(${index})" class="text-red-600 hover:text-red-800 text-sm">
                        🗑️ Eliminar Campo
                    </button>
                </div>
            </div>
        </div>
    `;
}

function renderAPITab() {
    const apiConfig = currentEntity.configuracion?.api_config || {};
    
    return `
        <div class="space-y-6">
            <h3 class="text-lg font-medium">Configuración de API Externa</h3>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Configuración básica -->
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Fuente de API</label>
                        <select onchange="updateAPIConfig('fuente', this.value)" class="w-full p-3 border rounded-lg">
                            <option value="">Seleccionar API...</option>
                            <option value="ispcube" ${apiConfig.fuente === 'ispcube' ? 'selected' : ''}>ISPCube</option>
                            <option value="waha" ${apiConfig.fuente === 'waha' ? 'selected' : ''}>WAHA WhatsApp</option>
                            <option value="n8n" ${apiConfig.fuente === 'n8n' ? 'selected' : ''}>N8N</option>
                            <option value="custom" ${apiConfig.fuente === 'custom' ? 'selected' : ''}>API Personalizada</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Endpoint</label>
                        <input type="text" value="${apiConfig.endpoint || ''}" 
                               onchange="updateAPIConfig('endpoint', this.value)"
                               placeholder="/api/clientes"
                               class="w-full p-3 border rounded-lg">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Método HTTP</label>
                        <select onchange="updateAPIConfig('metodo', this.value)" class="w-full p-3 border rounded-lg">
                            <option value="GET" ${apiConfig.metodo === 'GET' ? 'selected' : ''}>GET</option>
                            <option value="POST" ${apiConfig.metodo === 'POST' ? 'selected' : ''}>POST</option>
                            <option value="PUT" ${apiConfig.metodo === 'PUT' ? 'selected' : ''}>PUT</option>
                            <option value="DELETE" ${apiConfig.metodo === 'DELETE' ? 'selected' : ''}>DELETE</option>
                        </select>
                    </div>
                </div>
                
                <!-- Mapeo de campos -->
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Mapeo de Campos</label>
                        <div class="text-sm text-gray-600 mb-3">
                            Define cómo mapear los campos de la API a los campos de la entidad
                        </div>
                        <div id="mappingContainer" class="space-y-2">
                            ${renderAPIMapping(apiConfig.mapeo || {})}
                        </div>
                        <button onclick="addMapping()" class="text-blue-600 hover:text-blue-800 text-sm">
                            ➕ Agregar Mapeo
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Cache Configuration -->
            <div class="border-t pt-6">
                <h4 class="text-md font-medium mb-4">Configuración de Cache</h4>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Tipo de Cache</label>
                        <select onchange="updateCacheConfig('tipo', this.value)" class="w-full p-2 border rounded">
                            <option value="tiempo" ${(apiConfig.cache_config?.tipo || 'tiempo') === 'tiempo' ? 'selected' : ''}>Por Tiempo</option>
                            <option value="webhook" ${apiConfig.cache_config?.tipo === 'webhook' ? 'selected' : ''}>Por Webhook</option>
                            <option value="manual" ${apiConfig.cache_config?.tipo === 'manual' ? 'selected' : ''}>Manual</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Tiempo de Refresh (segundos)</label>
                        <input type="number" value="${apiConfig.cache_config?.refresh_seconds || 300}" 
                               onchange="updateCacheConfig('refresh_seconds', parseInt(this.value))"
                               class="w-full p-2 border rounded">
                    </div>
                    
                    <div>
                        <button onclick="testAPIConnection()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 w-full">
                            🧪 Probar Conexión
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderAPIMapping(mapeo) {
    const mappings = Object.entries(mapeo);
    if (mappings.length === 0) {
        return '<div class="text-gray-500 text-sm">No hay mapeos configurados</div>';
    }
    
    return mappings.map(([apiField, entityField], index) => `
        <div class="flex items-center space-x-2">
            <input type="text" value="${apiField}" 
                   onchange="updateMapping(${index}, 'api', this.value)"
                   placeholder="Campo API"
                   class="flex-1 p-2 border rounded text-sm">
            <span class="text-gray-500">→</span>
            <input type="text" value="${entityField}" 
                   onchange="updateMapping(${index}, 'entity', this.value)"
                   placeholder="Campo Entidad"
                   class="flex-1 p-2 border rounded text-sm">
            <button onclick="removeMapping(${index})" class="text-red-600 hover:text-red-800">
                🗑️
            </button>
        </div>
    `).join('');
}

function renderPermisosTab() {
    return `
        <div class="space-y-6">
            <h3 class="text-lg font-medium">Configuración de Permisos por Rol</h3>
            
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex items-center space-x-2 mb-2">
                    <span class="text-blue-600">ℹ️</span>
                    <span class="font-medium text-blue-900">Configuración Actual</span>
                </div>
                <p class="text-blue-800 text-sm">
                    Los permisos se configuran a nivel de campo en la pestaña "Campos".
                    Aquí puedes ver un resumen y configurar permisos globales de la entidad.
                </p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-4">
                    <h4 class="font-medium">Permisos de Visualización</h4>
                    ${renderRolePermissions('view')}
                </div>
                
                <div class="space-y-4">
                    <h4 class="font-medium">Permisos de Edición</h4>
                    ${renderRolePermissions('edit')}
                </div>
            </div>
        </div>
    `;
}

function renderRolePermissions(type) {
    const roles = ['admin', 'tecnico', 'user', 'viewer'];
    const campos = currentEntity.configuracion?.campos || [];
    
    return roles.map(rol => {
        const visibleFields = campos.filter(campo => 
            (campo.visible_roles || ['*']).includes(rol) || 
            (campo.visible_roles || ['*']).includes('*')
        ).length;
        
        const editableFields = campos.filter(campo => 
            (campo.editable_roles || ['admin']).includes(rol)
        ).length;
        
        return `
            <div class="p-3 border rounded-lg">
                <div class="flex justify-between items-center">
                    <span class="font-medium capitalize">${rol}</span>
                    <span class="text-sm text-gray-600">
                        ${type === 'view' ? `${visibleFields} campos visibles` : `${editableFields} campos editables`}
                    </span>
                </div>
            </div>
        `;
    }).join('');
}

function renderCRUDTab() {
    const crudConfig = currentEntity.configuracion?.crud_config || {};
    
    return `
        <div class="space-y-6">
            <h3 class="text-lg font-medium">Configuración de Operaciones CRUD</h3>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                ${renderCRUDOperation('crear', crudConfig.crear)}
                ${renderCRUDOperation('editar', crudConfig.editar)}
                ${renderCRUDOperation('eliminar', crudConfig.eliminar)}
            </div>
            
            <div class="border-t pt-6">
                <h4 class="text-md font-medium mb-4">Configuración Avanzada</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Campos requeridos para crear</label>
                        <input type="text" value="${(crudConfig.crear?.campos_requeridos || []).join(', ')}" 
                               onchange="updateCRUDRequiredFields('crear', this.value)"
                               placeholder="nombre, email, telefono"
                               class="w-full p-2 border rounded">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Confirmación para eliminar</label>
                        <label class="flex items-center space-x-2">
                            <input type="checkbox" ${crudConfig.eliminar?.confirmacion ? 'checked' : ''}
                                   onchange="updateCRUDConfig('eliminar', 'confirmacion', this.checked)">
                            <span class="text-sm">Requiere confirmación</span>
                        </label>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderCRUDOperation(operation, config = {}) {
    const roles = ['admin', 'tecnico', 'user', 'viewer'];
    const operationNames = {
        crear: 'Crear',
        editar: 'Editar', 
        eliminar: 'Eliminar'
    };
    
    return `
        <div class="border rounded-lg p-4">
            <div class="flex items-center justify-between mb-4">
                <h4 class="font-medium">${operationNames[operation]}</h4>
                <label class="flex items-center space-x-2">
                    <input type="checkbox" ${config.habilitado ? 'checked' : ''}
                           onchange="updateCRUDConfig('${operation}', 'habilitado', this.checked)">
                    <span class="text-sm">Habilitado</span>
                </label>
            </div>
            
            <div class="space-y-2">
                <label class="block text-sm font-medium text-gray-700">Roles permitidos</label>
                ${roles.map(rol => `
                    <label class="flex items-center space-x-2">
                        <input type="checkbox" ${(config.roles || ['admin']).includes(rol) ? 'checked' : ''}
                               onchange="updateCRUDRoles('${operation}', '${rol}', this.checked)">
                        <span class="text-sm capitalize">${rol}</span>
                    </label>
                `).join('')}
            </div>
        </div>
    `;
}

// ================================
// FUNCIONES DE GESTIÓN DE CAMPOS
// ================================

function addNewField() {
    if (!currentEntity.configuracion) currentEntity.configuracion = {};
    if (!currentEntity.configuracion.campos) currentEntity.configuracion.campos = [];
    
    const newField = {
        campo: `nuevo_campo_${Date.now()}`,
        tipo: 'text',
        obligatorio: false,
        visible_roles: ['*'],
        editable_roles: ['admin']
    };
    
    currentEntity.configuracion.campos.push(newField);
    renderEntityConfig();
}

function updateField(index, property, value) {
    if (!currentEntity.configuracion.campos[index]) return;
    currentEntity.configuracion.campos[index][property] = value;
}

function updateFieldRoles(index, roleType, role, checked) {
    if (!currentEntity.configuracion.campos[index]) return;
    
    let roles = currentEntity.configuracion.campos[index][roleType] || [];
    if (checked) {
        if (!roles.includes(role)) roles.push(role);
    } else {
        roles = roles.filter(r => r !== role);
    }
    currentEntity.configuracion.campos[index][roleType] = roles;
}

function removeField(index) {
    if (confirm('¿Estás seguro de eliminar este campo?')) {
        currentEntity.configuracion.campos.splice(index, 1);
        renderEntityConfig();
    }
}

// ================================
// FUNCIONES DE GESTIÓN DE API
// ================================

function updateAPIConfig(property, value) {
    if (!currentEntity.configuracion) currentEntity.configuracion = {};
    if (!currentEntity.configuracion.api_config) currentEntity.configuracion.api_config = {};
    
    currentEntity.configuracion.api_config[property] = value;
}

function updateCacheConfig(property, value) {
    if (!currentEntity.configuracion) currentEntity.configuracion = {};
    if (!currentEntity.configuracion.api_config) currentEntity.configuracion.api_config = {};
    if (!currentEntity.configuracion.api_config.cache_config) currentEntity.configuracion.api_config.cache_config = {};
    
    currentEntity.configuracion.api_config.cache_config[property] = value;
}

function addMapping() {
    if (!currentEntity.configuracion.api_config) currentEntity.configuracion.api_config = {};
    if (!currentEntity.configuracion.api_config.mapeo) currentEntity.configuracion.api_config.mapeo = {};
    
    const container = document.getElementById('mappingContainer');
    const newIndex = Object.keys(currentEntity.configuracion.api_config.mapeo).length;
    
    // Agregar mapping temporal
    currentEntity.configuracion.api_config.mapeo[`nuevo_campo_api_${newIndex}`] = `nuevo_campo_entidad_${newIndex}`;
    
    // Re-renderizar
    container.innerHTML = renderAPIMapping(currentEntity.configuracion.api_config.mapeo);
}

function updateMapping(index, type, value) {
    const mapeo = currentEntity.configuracion.api_config?.mapeo || {};
    const mappings = Object.entries(mapeo);
    
    if (mappings[index]) {
        const [oldApiField, oldEntityField] = mappings[index];
        
        if (type === 'api') {
            delete mapeo[oldApiField];
            mapeo[value] = oldEntityField;
        } else if (type === 'entity') {
            mapeo[oldApiField] = value;
        }
    }
}

function removeMapping(index) {
    const mapeo = currentEntity.configuracion.api_config?.mapeo || {};
    const mappings = Object.entries(mapeo);
    
    if (mappings[index]) {
        const [apiField] = mappings[index];
        delete mapeo[apiField];
        
        const container = document.getElementById('mappingContainer');
        container.innerHTML = renderAPIMapping(mapeo);
    }
}

async function testAPIConnection() {
    if (!currentEntity.configuracion?.api_config?.endpoint) {
        showNotification('Configura un endpoint primero', 'warning');
        return;
    }
    
    showNotification('Probando conexión API...', 'info');
    
    try {
        // Simular test de API
        await new Promise(resolve => setTimeout(resolve, 1000));
        showNotification('✅ Conexión API exitosa', 'success');
    } catch (error) {
        showNotification('❌ Error en conexión API', 'error');
    }
}

// ================================
// FUNCIONES DE GESTIÓN DE CRUD
// ================================

function updateCRUDConfig(operation, property, value) {
    if (!currentEntity.configuracion) currentEntity.configuracion = {};
    if (!currentEntity.configuracion.crud_config) currentEntity.configuracion.crud_config = {};
    if (!currentEntity.configuracion.crud_config[operation]) currentEntity.configuracion.crud_config[operation] = {};
    
    currentEntity.configuracion.crud_config[operation][property] = value;
}

function updateCRUDRoles(operation, role, checked) {
    if (!currentEntity.configuracion.crud_config) currentEntity.configuracion.crud_config = {};
    if (!currentEntity.configuracion.crud_config[operation]) currentEntity.configuracion.crud_config[operation] = {};
    
    let roles = currentEntity.configuracion.crud_config[operation].roles || [];
    
    if (checked) {
        if (!roles.includes(role)) roles.push(role);
    } else {
        roles = roles.filter(r => r !== role);
    }
    
    currentEntity.configuracion.crud_config[operation].roles = roles;
}

function updateCRUDRequiredFields(operation, value) {
    if (!currentEntity.configuracion.crud_config) currentEntity.configuracion.crud_config = {};
    if (!currentEntity.configuracion.crud_config[operation]) currentEntity.configuracion.crud_config[operation] = {};
    
    const fields = value.split(',').map(f => f.trim()).filter(f => f);
    currentEntity.configuracion.crud_config[operation].campos_requeridos = fields;
}

// ================================
// GESTIÓN DE TABS
// ================================

function showTab(tabName) {
    // Actualizar botones de tab
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('border-blue-500', 'text-blue-600', 'font-medium');
        btn.classList.add('border-transparent', 'text-gray-500');
    });
    
    event.target.classList.remove('border-transparent', 'text-gray-500');
    event.target.classList.add('border-blue-500', 'text-blue-600', 'font-medium');

    // Renderizar contenido del tab
    const content = document.getElementById('tabContent');
    switch(tabName) {
        case 'campos':
            content.innerHTML = renderCamposTab(currentEntity.configuracion?.campos || []);
            break;
        case 'api':
            content.innerHTML = renderAPITab();
            break;
        case 'permisos':
            content.innerHTML = renderPermisosTab();
            break;
        case 'crud':
            content.innerHTML = renderCRUDTab();
            break;
    }
}

// ================================
// MODAL PARA NUEVA ENTIDAD
// ================================

function createNewEntity() {
    if (!currentBusiness) {
        showNotification('Selecciona un business primero', 'warning');
        return;
    }
    document.getElementById('newEntityModal').classList.remove('hidden');
    document.getElementById('newEntityModal').classList.add('flex');
}

function closeNewEntityModal() {
    document.getElementById('newEntityModal').classList.add('hidden');
    document.getElementById('newEntityModal').classList.remove('flex');
    document.getElementById('newEntityName').value = '';
    document.getElementById('newEntityDescription').value = '';
}

async function saveNewEntity(event) {
    event.preventDefault();
    
    const name = document.getElementById('newEntityName').value.trim();
    const description = document.getElementById('newEntityDescription').value.trim();
    
    if (!name || !currentBusiness) return;

    try {
        const newEntity = {
            business_id: currentBusiness.business_id,
            entidad: name,
            configuracion: {
                descripcion: description,
                campos: [],
                api_config: null,
                crud_config: {
                    crear: { habilitado: true, roles: ['admin'] },
                    editar: { habilitado: true, roles: ['admin'] },
                    eliminar: { habilitado: false, roles: ['admin'] }
                }
            }
        };

        const response = await fetch(`${API_BASE}/admin/entities/${currentBusiness.business_id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newEntity)
        });

        if (!response.ok) throw new Error('Error creando entidad');

        closeNewEntityModal();
        await loadEntities(currentBusiness.business_id);
        showNotification('Entidad creada exitosamente', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error creando entidad', 'error');
    }
}

// ================================
// FUNCIONES AUXILIARES
// ================================

async function saveAllConfigs() {
    if (!currentEntity || !currentBusiness) {
        showNotification('No hay configuración para guardar', 'warning');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/admin/entities/${currentBusiness.business_id}/${currentEntity.entidad}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentEntity)
        });

        if (!response.ok) throw new Error('Error guardando configuración');

        showNotification('Configuración guardada exitosamente', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error guardando configuración', 'error');
    }
}

async function deleteEntity() {
    if (!currentEntity || !currentBusiness) return;
    
    if (!confirm(`¿Estás seguro de eliminar la entidad "${currentEntity.entidad}"?`)) return;
    
    try {
        const response = await fetch(`${API_BASE}/admin/entities/${currentBusiness.business_id}/${currentEntity.entidad}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Error eliminando entidad');

        currentEntity = null;
        await loadEntities(currentBusiness.business_id);
        document.getElementById('entityConfigPanel').innerHTML = `
            <div class="text-center text-gray-500 py-12">
                <div class="text-6xl mb-4">⚙️</div>
                <h3 class="text-lg font-medium mb-2">Configurador de Entidades</h3>
                <p>Selecciona una entidad de la lista para configurar sus campos, API y permisos</p>
            </div>
        `;
        
        showNotification('Entidad eliminada exitosamente', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error eliminando entidad', 'error');
    }
}

async function testEntityAPI() {
    if (!currentEntity?.configuracion?.api_config) {
        showNotification('No hay configuración de API para probar', 'warning');
        return;
    }
    
    showNotification('Probando API de la entidad...', 'info');
    
    try {
        // Simular test de API
        await new Promise(resolve => setTimeout(resolve, 1500));
        showNotification('✅ Test de API exitoso', 'success');
    } catch (error) {
        showNotification('❌ Error en test de API', 'error');
    }
}

function showNotification(message, type = 'info') {
    const colors = {
        success: 'bg-green-100 border-green-300 text-green-800',
        error: 'bg-red-100 border-red-300 text-red-800',
        warning: 'bg-yellow-100 border-yellow-300 text-yellow-800',
        info: 'bg-blue-100 border-blue-300 text-blue-800'
    };

    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg border ${colors[type]} z-50`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}