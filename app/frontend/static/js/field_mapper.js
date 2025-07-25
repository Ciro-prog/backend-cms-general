// field_mapper.js

// Simulación de campos detectados de la API y de la entidad
const apiFields = [
    { name: 'id', type: 'number' },
    { name: 'nombre', type: 'string' },
    { name: 'email', type: 'string' },
    { name: 'telefono', type: 'string' }
];
const entityFields = [
    { name: 'cliente_id', type: 'number' },
    { name: 'nombre_completo', type: 'string' },
    { name: 'correo', type: 'string' },
    { name: 'telefono', type: 'string' }
];
let mapping = {};

function renderFields() {
    const apiList = document.getElementById('apiFields');
    const entityList = document.getElementById('entityFields');
    apiList.innerHTML = '';
    entityList.innerHTML = '';
    apiFields.forEach(field => {
        const li = document.createElement('li');
        li.textContent = field.name;
        li.className = 'p-2 bg-blue-50 rounded cursor-move border border-blue-200';
        li.draggable = true;
        li.ondragstart = e => {
            e.dataTransfer.setData('text/plain', field.name);
        };
        apiList.appendChild(li);
    });
    entityFields.forEach(field => {
        const li = document.createElement('li');
        li.textContent = field.name;
        li.className = 'p-2 bg-green-50 rounded border border-green-200 flex justify-between items-center';
        li.ondragover = e => e.preventDefault();
        li.ondrop = e => {
            e.preventDefault();
            const apiField = e.dataTransfer.getData('text/plain');
            mapping[field.name] = apiField;
            renderMapping();
        };
        // Mostrar mapeo actual
        if (mapping[field.name]) {
            const span = document.createElement('span');
            span.textContent = '← ' + mapping[field.name];
            span.className = 'ml-2 text-xs text-blue-600';
            li.appendChild(span);
        }
        entityList.appendChild(li);
    });
}

function renderMapping() {
    document.getElementById('mappingPreview').textContent = JSON.stringify(mapping, null, 2);
    renderFields();
}

function saveMapping() {
    alert('Funcionalidad de guardado pendiente');
}

function autoMap() {
    alert('Funcionalidad de autocompletar pendiente');
}

document.addEventListener('DOMContentLoaded', () => {
    renderFields();
    renderMapping();
}); 