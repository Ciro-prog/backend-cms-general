// ================================
// app/frontend/static/enhanced_wizard.js
// JavaScript mejorado para wizard con mapping manual
// ================================

// Estado global de la aplicación
let currentStep = 1;
let apiTestResult = null;
let detectedFields = [];
let mappingConfiguration = {
    api_id: null,
    mapping_type: "automatic",
    mapped_fields: [],
    auto_detected_structure: null
};
let currentFieldConfig = null;

// ================================
// INICIALIZACIÓN
// ================================

document.addEventListener('DOMContentLoaded', function() {
    // Event listeners para navegación
    setupEventListeners();
    
    // Update URL preview when inputs change
    ['baseUrl', 'endpoint'].forEach(id => {
        document.getElementById(id).addEventListener('input', updateUrlPreview);
    });
    
    // Setup mapping type change
    document.querySelectorAll('input[name="mappingType"]').forEach(radio => {
        radio.addEventListener('change', onMappingTypeChange);
    });
    
    // Initialize first step
    updateUrlPreview();
});

function setupEventListeners() {
    // Form validation on input
    const form = document.getElementById('apiConfigForm');
    if (form) {
        form.addEventListener('input', validateStep1);
    }
}

// ================================
// STEP NAVIGATION
// ================================

function goToStep(stepNumber) {
    // Validate current step before proceeding
    if (stepNumber > currentStep && !validateCurrentStep()) {
        return;
    }
    
    // Hide all step contents
    for (let i = 1; i <= 3; i++) {
        const content = document.getElementById(`step${i}-content`);
        const circle = document.getElementById(`step${i}-circle`);
        
        if (content) content.classList.add('hidden');
        
        if (circle) {
            circle.classList.remove('bg-blue-600', 'text-white');
            circle.classList.add('bg-gray-300', 'text-gray-500');
        }
    }
    
    // Show target step
    const targetContent = document.getElementById(`step${stepNumber}-content`);
    const targetCircle = document.getElementById(`step${stepNumber}-circle`);
    
    if (targetContent) {
        targetContent.classList.remove('hidden');
        targetContent.classList.add('fade-in');
    }
    
    if (targetCircle) {
        targetCircle.classList.remove('bg-gray-300', 'text-gray-500');
        targetCircle.classList.add('bg-blue-600', 'text-white');
    }
    
    currentStep = stepNumber;
    
    // Step-specific actions
    if (stepNumber === 2) {
        initializeMappingStep();
    } else if (stepNumber === 3) {
        initializePreviewStep();
    }
}

function validateCurrentStep() {
    switch (currentStep) {
        case 1:
            return apiTestResult && apiTestResult.success;
        case 2:
            return mappingConfiguration.mapped_fields.length > 0;
        case 3:
            return true;
        default:
            return false;
    }
}

// ================================
// STEP 1: API CONFIGURATION
// ================================

function updateUrlPreview() {
    const baseUrl = document.getElementById('baseUrl').value || 'https://api.ejemplo.com';
    const endpoint = document.getElementById('endpoint').value || '/api/v1/endpoint';
    
    const fullUrl = `${baseUrl.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`;
    document.getElementById('urlPreview').textContent = fullUrl;
}

function validateStep1() {
    const requiredFields = ['apiName', 'businessId', 'baseUrl', 'endpoint'];
    const allFilled = requiredFields.every(id => {
        const element = document.getElementById(id);
        return element && element.value.trim() !== '';
    });
    
    // Enable/disable test button
    const testButton = document.querySelector('button[onclick="testConnection()"]');
    if (testButton) {
        testButton.disabled = !allFilled;
        testButton.classList.toggle('bg-blue-600', allFilled);
        testButton.classList.toggle('hover:bg-blue-700', allFilled);
        testButton.classList.toggle('bg-gray-300', !allFilled);
        testButton.classList.toggle('cursor-not-allowed', !allFilled);
    }
}

async function testConnection() {
    const button = event.target;
    const originalText = button.innerHTML;
    
    try {
        // Update button state
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Probando...';
        button.disabled = true;
        
        // Gather form data
        const formData = new FormData(document.getElementById('apiConfigForm'));
        
        // Make test request
        const response = await fetch('/admin/api-testing/test-connection', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        // Store result
        apiTestResult = result;
        
        // Update UI
        displayTestResults(result);
        
        if (result.success) {
            // Enable next step
            const nextButton = document.getElementById('nextStep1');
            nextButton.disabled = false;
            nextButton.classList.remove('bg-gray-300', 'text-gray-500', 'cursor-not-allowed');
            nextButton.classList.add('bg-blue-600', 'text-white', 'hover:bg-blue-700');
            
            // Store detected fields for mapping
            if (result.field_analysis) {
                detectedFields = result.field_analysis.available_paths || [];
                mappingConfiguration.auto_detected_structure = result.field_analysis.detected_structure;
                mappingConfiguration.api_id = `api_${Date.now()}`;
            }
            
            showMessage('✅ Conexión exitosa - Puedes continuar al mapping', 'success');
        } else {
            showMessage('❌ Error en la conexión - Verifica la configuración', 'error');
        }
        
    } catch (error) {
        console.error('Error testing connection:', error);
        showMessage('❌ Error de red - Intenta nuevamente', 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

function displayTestResults(result) {
    const container = document.getElementById('testResults');
    container.classList.remove('hidden');
    
    let html = `
        <div class="flex items-center justify-between mb-4">
            <h4 class="font-medium text-gray-900">Resultados del Test</h4>
            <span class="px-3 py-1 rounded-full text-sm ${result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                ${result.success ? 'Exitoso' : 'Error'}
            </span>
        </div>
    `;
    
    if (result.success) {
        html += `
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div>
                    <h5 class="font-medium text-gray-700 mb-2">Respuesta de la API</h5>
                    <pre class="bg-gray-100 p-3 rounded text-xs overflow-auto max-h-40">${JSON.stringify(result.response_data, null, 2)}</pre>
                </div>
        `;
        
        if (result.field_analysis) {
            html += `
                <div>
                    <h5 class="font-medium text-gray-700 mb-2">Campos Detectados (${result.field_analysis.available_paths.length})</h5>
                    <div class="bg-blue-50 p-3 rounded max-h-40 overflow-auto">
                        ${result.field_analysis.available_paths.map(path => 
                            `<div class="text-sm text-blue-700 mb-1">• ${path}</div>`
                        ).join('')}
                    </div>
                </div>
            `;
        }
        
        html += `</div>`;
    } else {
        html += `
            <div class="bg-red-50 border border-red-200 rounded p-4">
                <p class="text-red-700">
                    <strong>Error:</strong> ${result.message || 'Error desconocido'}
                </p>
                ${result.status_code ? `<p class="text-sm text-red-600 mt-1">Código: ${result.status_code}</p>` : ''}
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// ================================
// STEP 2: FIELD MAPPING
// ================================

function initializeMappingStep() {
    displayDetectedFields();
    
    // Set default mapping type
    const autoRadio = document.querySelector('input[name="mappingType"][value="automatic"]');
    if (autoRadio) autoRadio.checked = true;
    
    // Apply auto-mapping if we have suggestions
    if (apiTestResult && apiTestResult.field_analysis && apiTestResult.field_analysis.mapping_suggestions) {
        autoMapFields();
    }
}

function displayDetectedFields() {
    const container = document.getElementById('detectedFields');
    
    if (!detectedFields || detectedFields.length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <i class="fas fa-exclamation-triangle text-3xl mb-2"></i>
                <p>No se detectaron campos</p>
                <button onclick="goToStep(1)" class="mt-2 text-blue-600 hover:underline">
                    Volver al test de conexión
                </button>
            </div>
        `;
        return;
    }
    
    let html = '';
    detectedFields.forEach((path, index) => {
        const isNested = path.includes('.');
        const displayPath = path;
        const pathParts = path.split('.');
        const fieldName = pathParts[pathParts.length - 1];
        
        html += `
            <div class="field-item bg-white border rounded-lg p-3 cursor-pointer hover:border-blue-300" 
                 onclick="selectFieldForMapping('${path}')"
                 data-field-path="${path}">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        ${isNested ? '<i class="fas fa-sitemap text-blue-500 text-sm"></i>' : '<i class="fas fa-square text-gray-400 text-sm"></i>'}
                        <span class="font-mono text-sm text-gray-700">${displayPath}</span>
                    </div>
                    <button class="text-blue-600 hover:text-blue-800 text-sm" 
                            onclick="event.stopPropagation(); addFieldToMapping('${path}')">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
                ${isNested ? `<div class="mt-1 text-xs text-gray-500">${pathParts.slice(0, -1).join(' → ')} → <strong>${fieldName}</strong></div>` : ''}
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function displayMappedFields() {
    const container = document.getElementById('mappedFields');
    
    if (!mappingConfiguration.mapped_fields || mappingConfiguration.mapped_fields.length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <i class="fas fa-plus text-3xl mb-2"></i>
                <p>Selecciona campos para mapear</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    mappingConfiguration.mapped_fields.forEach((field, index) => {
        html += `
            <div class="bg-white border rounded-lg p-3 border-green-200 bg-green-50">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <div class="font-medium text-gray-900">${field.display_name}</div>
                        <div class="text-xs text-gray-500 font-mono">${field.api_path}</div>
                        <div class="flex items-center space-x-2 mt-1">
                            <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">${field.field_type}</span>
                            ${field.show_in_table ? '<span class="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Tabla</span>' : ''}
                            ${field.show_in_card ? '<span class="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">Card</span>' : ''}
                        </div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button onclick="editFieldMapping(${index})" 
                                class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="removeFieldMapping(${index})" 
                                class="text-red-600 hover:text-red-800">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Update counter
    document.getElementById('mappedCount').textContent = mappingConfiguration.mapped_fields.length;
    
    // Enable/disable next step
    const nextButton = document.getElementById('nextStep2');
    const hasFields = mappingConfiguration.mapped_fields.length > 0;
    
    nextButton.disabled = !hasFields;
    nextButton.classList.toggle('bg-blue-600', hasFields);
    nextButton.classList.toggle('text-white', hasFields);
    nextButton.classList.toggle('hover:bg-blue-700', hasFields);
    nextButton.classList.toggle('bg-gray-300', !hasFields);
    nextButton.classList.toggle('text-gray-500', !hasFields);
    nextButton.classList.toggle('cursor-not-allowed', !hasFields);
}

function autoMapFields() {
    if (!apiTestResult || !apiTestResult.field_analysis || !apiTestResult.field_analysis.mapping_suggestions) {
        showMessage('No hay sugerencias automáticas disponibles', 'warning');
        return;
    }
    
    // Use API suggestions
    mappingConfiguration.mapped_fields = apiTestResult.field_analysis.mapping_suggestions.map((suggestion, index) => ({
        api_path: suggestion.api_path,
        display_name: suggestion.display_name,
        field_type: suggestion.field_type || 'text',
        show_in_table: index < 5,
        show_in_card: index < 8,
        show_in_form: true,
        order: index
    }));
    
    mappingConfiguration.mapping_type = 'automatic';
    
    displayMappedFields();
    showMessage(`✅ Auto-mapping aplicado: ${mappingConfiguration.mapped_fields.length} campos`, 'success');
}

function clearMapping() {
    mappingConfiguration.mapped_fields = [];
    displayMappedFields();
    showMessage('Mapping limpiado', 'info');
}

function addFieldToMapping(fieldPath) {
    // Check if field is already mapped
    const existing = mappingConfiguration.mapped_fields.find(f => f.api_path === fieldPath);
    if (existing) {
        showMessage('Campo ya está mapeado', 'warning');
        return;
    }
    
    // Generate display name
    const displayName = generateDisplayName(fieldPath);
    const fieldType = detectFieldType(fieldPath);
    
    // Add to mapping
    const newField = {
        api_path: fieldPath,
        display_name: displayName,
        field_type: fieldType,
        show_in_table: true,
        show_in_card: true,
        show_in_form: true,
        order: mappingConfiguration.mapped_fields.length
    };
    
    mappingConfiguration.mapped_fields.push(newField);
    mappingConfiguration.mapping_type = 'manual';
    
    displayMappedFields();
    showMessage(`Campo "${displayName}" agregado al mapping`, 'success');
}

function removeFieldMapping(index) {
    const removed = mappingConfiguration.mapped_fields.splice(index, 1);
    displayMappedFields();
    showMessage(`Campo "${removed[0].display_name}" eliminado del mapping`, 'info');
}

function editFieldMapping(index) {
    const field = mappingConfiguration.mapped_fields[index];
    currentFieldConfig = { index, ...field };
    
    // Populate configuration panel
    document.getElementById('configFieldName').textContent = field.api_path;
    document.getElementById('configDisplayName').value = field.display_name;
    document.getElementById('configFieldType').value = field.field_type;
    document.getElementById('configShowTable').checked = field.show_in_table;
    document.getElementById('configShowCard').checked = field.show_in_card;
    
    // Show panel
    document.getElementById('fieldConfigPanel').classList.remove('hidden');
}

function saveFieldConfig() {
    if (!currentFieldConfig) return;
    
    const index = currentFieldConfig.index;
    const field = mappingConfiguration.mapped_fields[index];
    
    // Update field with new config
    field.display_name = document.getElementById('configDisplayName').value;
    field.field_type = document.getElementById('configFieldType').value;
    field.show_in_table = document.getElementById('configShowTable').checked;
    field.show_in_card = document.getElementById('configShowCard').checked;
    
    displayMappedFields();
    closeFieldConfig();
    showMessage('Configuración de campo guardada', 'success');
}

function closeFieldConfig() {
    document.getElementById('fieldConfigPanel').classList.add('hidden');
    currentFieldConfig = null;
}

function onMappingTypeChange(event) {
    mappingConfiguration.mapping_type = event.target.value;
    
    if (event.target.value === 'automatic') {
        autoMapFields();
    }
}

// ================================
// STEP 3: PREVIEW
// ================================

function initializePreviewStep() {
    generateConfigSummary();
    refreshPreview();
}

function generateConfigSummary() {
    const container = document.getElementById('configSummary');
    
    const summary = {
        'API': document.getElementById('apiName').value,
        'Business': document.getElementById('businessId').selectedOptions[0]?.text || 'N/A',
        'Endpoint': `${document.getElementById('baseUrl').value}${document.getElementById('endpoint').value}`,
        'Campos Mapeados': mappingConfiguration.mapped_fields.length,
        'Tipo de Mapping': mappingConfiguration.mapping_type === 'automatic' ? 'Automático' : 'Manual',
        'Visualización': 'Tabla, Cards disponibles'
    };
    
    let html = '';
    Object.entries(summary).forEach(([key, value]) => {
        html += `
            <div class="bg-white p-3 rounded border">
                <div class="text-xs text-gray-500 uppercase tracking-wide">${key}</div>
                <div class="text-sm font-medium text-gray-900 mt-1">${value}</div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function changePreviewType(type) {
    // Update buttons
    ['table', 'cards', 'chart'].forEach(t => {
        const btn = document.getElementById(`view${t.charAt(0).toUpperCase() + t.slice(1)}`);
        if (btn) {
            if (t === type) {
                btn.classList.add('bg-blue-600', 'text-white');
                btn.classList.remove('border-gray-300', 'text-gray-700');
            } else {
                btn.classList.remove('bg-blue-600', 'text-white');
                btn.classList.add('border-gray-300', 'text-gray-700');
            }
        }
    });
    
    // Generate preview
    generatePreview(type);
}

function generatePreview(type = 'table') {
    const container = document.getElementById('previewContainer');
    
    // Sample data based on mapping
    const sampleData = [
        {
            'ID': 1,
            'Nombre': 'Juan Pérez',
            'Correo': 'juan@ejemplo.com',
            'Teléfono': '+1234567890'
        },
        {
            'ID': 2,
            'Nombre': 'María García',
            'Correo': 'maria@ejemplo.com',
            'Teléfono': '+0987654321'
        },
        {
            'ID': 3,
            'Nombre': 'Carlos López',
            'Correo': 'carlos@ejemplo.com',
            'Teléfono': '+1122334455'
        }
    ];
    
    let html = '';
    
    if (type === 'table') {
        html = generateTablePreview(sampleData);
    } else if (type === 'cards') {
        html = generateCardsPreview(sampleData);
    } else if (type === 'chart') {
        html = generateChartPreview(sampleData);
    }
    
    container.innerHTML = html;
}

function generateTablePreview(data) {
    if (!mappingConfiguration.mapped_fields.length) {
        return `<div class="text-center text-gray-500 py-8">No hay campos mapeados para mostrar</div>`;
    }
    
    const tableFields = mappingConfiguration.mapped_fields.filter(f => f.show_in_table);
    
    let html = `
        <div class="bg-white rounded-lg border overflow-hidden">
            <div class="px-4 py-3 border-b bg-gray-50">
                <h4 class="font-medium text-gray-900">Vista de Tabla</h4>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead class="bg-gray-50">
                        <tr>
    `;
    
    tableFields.forEach(field => {
        html += `<th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${field.display_name}</th>`;
    });
    
    html += `
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
    `;
    
    data.forEach((row, index) => {
        html += `<tr class="${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}">`;
        tableFields.forEach(field => {
            const value = row[field.display_name] || 'N/A';
            html += `<td class="px-4 py-3 text-sm text-gray-900">${value}</td>`;
        });
        html += `</tr>`;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    return html;
}

function generateCardsPreview(data) {
    if (!mappingConfiguration.mapped_fields.length) {
        return `<div class="text-center text-gray-500 py-8">No hay campos mapeados para mostrar</div>`;
    }
    
    const cardFields = mappingConfiguration.mapped_fields.filter(f => f.show_in_card);
    
    let html = `
        <div class="bg-white rounded-lg border p-4">
            <div class="mb-4">
                <h4 class="font-medium text-gray-900">Vista de Cards</h4>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    `;
    
    data.forEach(row => {
        html += `
            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 hover:shadow-md transition-shadow">
        `;
        
        cardFields.forEach(field => {
            const value = row[field.display_name] || 'N/A';
            html += `
                <div class="mb-2">
                    <div class="text-xs text-gray-500 uppercase tracking-wide">${field.display_name}</div>
                    <div class="text-sm font-medium text-gray-900">${value}</div>
                </div>
            `;
        });
        
        html += `</div>`;
    });
    
    html += `
            </div>
        </div>
    `;
    
    return html;
}

function generateChartPreview(data) {
    return `
        <div class="bg-white rounded-lg border p-4">
            <div class="text-center py-12">
                <i class="fas fa-chart-bar text-4xl text-gray-400 mb-4"></i>
                <h4 class="font-medium text-gray-900 mb-2">Vista de Gráfico</h4>
                <p class="text-gray-500">Los gráficos se implementarán con Chart.js</p>
                <p class="text-sm text-gray-400 mt-2">Próximamente: gráficos de barras, líneas y pasteles</p>
            </div>
        </div>
    `;
}

function refreshPreview() {
    generatePreview('table');
}

// ================================
// CONFIGURATION ACTIONS
// ================================

async function saveConfiguration() {
    try {
        showMessage('Guardando configuración...', 'info');
        
        const configData = {
            api_id: mappingConfiguration.api_id,
            name: document.getElementById('apiName').value,
            business_id: document.getElementById('businessId').value,
            base_url: document.getElementById('baseUrl').value,
            endpoint: document.getElementById('endpoint').value,
            method: document.getElementById('method').value,
            headers: document.getElementById('headers').value,
            params: document.getElementById('params').value,
            mapped_fields: mappingConfiguration.mapped_fields,
            mapping_type: mappingConfiguration.mapping_type,
            auto_detected_structure: mappingConfiguration.auto_detected_structure
        };
        
        const response = await fetch('/admin/api-testing/save-mapping', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessModal('¡API configurada exitosamente!', 'Tu configuración ha sido guardada y está lista para usar.');
        } else {
            showMessage('Error guardando configuración: ' + result.message, 'error');
        }
        
    } catch (error) {
        console.error('Error saving configuration:', error);
        showMessage('Error de red guardando configuración', 'error');
    }
}

function exportConfig() {
    const config = {
        api_config: {
            name: document.getElementById('apiName').value,
            business_id: document.getElementById('businessId').value,
            base_url: document.getElementById('baseUrl').value,
            endpoint: document.getElementById('endpoint').value,
            method: document.getElementById('method').value,
            headers: document.getElementById('headers').value,
            params: document.getElementById('params').value
        },
        mapping_config: mappingConfiguration,
        export_date: new Date().toISOString(),
        version: '1.0'
    };
    
    const blob = new Blob([JSON.stringify(config, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `api-config-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showMessage('Configuración exportada', 'success');
}

// ================================
// UTILITY FUNCTIONS
// ================================

function generateDisplayName(fieldPath) {
    const parts = fieldPath.split('.');
    const lastPart = parts[parts.length - 1];
    
    // Convert camelCase and snake_case to readable format
    let name = lastPart.replace(/([a-z])([A-Z])/g, '$1 $2');
    name = name.replace(/_/g, ' ');
    
    // Capitalize each word
    name = name.split(' ').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ');
    
    // Common translations
    const translations = {
        'Id': 'ID',
        'Email': 'Correo',
        'Phone': 'Teléfono',
        'Name': 'Nombre',
        'Last Name': 'Apellido',
        'First Name': 'Nombre',
        'Address': 'Dirección',
        'City': 'Ciudad',
        'Country': 'País',
        'Created At': 'Fecha Creación',
        'Updated At': 'Fecha Actualización'
    };
    
    return translations[name] || name;
}

function detectFieldType(fieldPath) {
    const path = fieldPath.toLowerCase();
    
    if (path.includes('email')) return 'email';
    if (path.includes('phone') || path.includes('telefono')) return 'phone';
    if (path.includes('url') || path.includes('website')) return 'url';
    if (path.includes('date') || path.includes('created') || path.includes('updated')) return 'date';
    if (path.includes('id') || path.includes('count') || path.includes('number')) return 'number';
    if (path.includes('active') || path.includes('enabled') || path.includes('visible')) return 'boolean';
    
    return 'text';
}

function showMessage(message, type = 'info') {
    // Create or update message container
    let container = document.getElementById('messageContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'messageContainer';
        container.className = 'fixed top-4 right-4 z-50';
        document.body.appendChild(container);
    }
    
    const colors = {
        success: 'bg-green-100 border-green-400 text-green-700',
        error: 'bg-red-100 border-red-400 text-red-700',
        warning: 'bg-yellow-100 border-yellow-400 text-yellow-700',
        info: 'bg-blue-100 border-blue-400 text-blue-700'
    };
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const messageEl = document.createElement('div');
    messageEl.className = `${colors[type]} border px-4 py-3 rounded mb-2 shadow-lg max-w-sm`;
    messageEl.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${icons[type]} mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(messageEl);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageEl.parentNode) {
            messageEl.parentNode.removeChild(messageEl);
        }
    }, 5000);
}

function showSuccessModal(title, message) {
    document.getElementById('successMessage').textContent = message;
    document.getElementById('successModal').classList.remove('hidden');
}

function goToApiManagement() {
    window.location.href = '/api-management';
}

function createAnother() {
    window.location.reload();
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('successModal');
    if (event.target === modal) {
        modal.classList.add('hidden');
    }
});
