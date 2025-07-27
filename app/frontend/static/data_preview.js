// ================================
// app/frontend/static/data_preview.js
// JavaScript para preview y visualización de datos
// ================================

let currentView = 'table';
let currentPage = 1;
let itemsPerPage = 10;
let filteredData = [];
let allData = [];
let mappingConfig = {};

// ================================
// INICIALIZACIÓN
// ================================

document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadPreviewData();
});

function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 300));
    }
    
    // Items per page
    const itemsSelect = document.getElementById('itemsPerPage');
    if (itemsSelect) {
        itemsSelect.addEventListener('change', handleItemsPerPageChange);
    }
}

// ================================
// DATA LOADING
// ================================

async function loadPreviewData() {
    try {
        showLoading();
        
        // Obtener mapping_id desde URL o parámetros
        const urlParams = new URLSearchParams(window.location.search);
        const mappingId = urlParams.get('mapping_id') || 'default';
        
        const response = await fetch(`/admin/api-testing/preview-data/${mappingId}?limit=100`);
        const result = await response.json();
        
        if (result.success) {
            allData = result.data.preview_records || [];
            mappingConfig = result.data.field_config || [];
            
            applyFilters();
            renderCurrentView();
            
            showMessage('Datos cargados exitosamente', 'success');
        } else {
            throw new Error(result.message || 'Error cargando datos');
        }
        
    } catch (error) {
        console.error('Error loading preview data:', error);
        showError('Error cargando datos: ' + error.message);
    }
}

function showLoading() {
    const container = document.getElementById('dataContainer');
    container.innerHTML = `
        <div class="flex items-center justify-center py-12">
            <div class="text-center">
                <i class="fas fa-spinner fa-spin text-3xl text-blue-600 mb-4"></i>
                <p class="text-gray-600">Cargando datos...</p>
            </div>
        </div>
    `;
}

function showError(message) {
    const container = document.getElementById('dataContainer');
    container.innerHTML = `
        <div class="flex items-center justify-center py-12">
            <div class="text-center">
                <i class="fas fa-exclamation-triangle text-3xl text-red-500 mb-4"></i>
                <p class="text-red-600 mb-4">${message}</p>
                <button onclick="loadPreviewData()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                    <i class="fas fa-retry mr-2"></i>Reintentar
                </button>
            </div>
        </div>
    `;
}

// ================================
// VIEW MANAGEMENT
// ================================

function changeView(viewType) {
    currentView = viewType;
    
    // Update button states
    ['table', 'cards', 'chart'].forEach(type => {
        const btn = document.getElementById(`view${type.charAt(0).toUpperCase() + type.slice(1)}`);
        if (btn) {
            if (type === viewType) {
                btn.classList.add('bg-blue-600', 'text-white');
                btn.classList.remove('border-gray-300', 'text-gray-700');
            } else {
                btn.classList.remove('bg-blue-600', 'text-white');
                btn.classList.add('border-gray-300', 'text-gray-700', 'hover:bg-gray-50');
            }
        }
    });
    
    renderCurrentView();
}

function renderCurrentView() {
    switch (currentView) {
        case 'table':
            renderTableView();
            break;
        case 'cards':
            renderCardsView();
            break;
        case 'chart':
            renderChartView();
            break;
    }
    
    updatePagination();
}

// ================================
// TABLE VIEW
// ================================

function renderTableView() {
    const container = document.getElementById('dataContainer');
    
    if (!filteredData.length) {
        container.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-table text-3xl text-gray-400 mb-4"></i>
                <p class="text-gray-500">No hay datos para mostrar</p>
            </div>
        `;
        return;
    }
    
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageData = filteredData.slice(startIndex, endIndex);
    
    // Get visible columns
    const visibleFields = mappingConfig.filter(field => field.show_in_table !== false);
    const fieldNames = visibleFields.length ? visibleFields.map(f => f.display_name) : Object.keys(pageData[0] || {});
    
    let html = `
        <div class="overflow-x-auto">
            <table class="w-full">
                <thead class="bg-gray-50">
                    <tr>
    `;
    
    fieldNames.forEach(fieldName => {
        html += `
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ${fieldName}
            </th>
        `;
    });
    
    html += `
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
    `;
    
    pageData.forEach((row, index) => {
        const bgClass = index % 2 === 0 ? 'bg-white' : 'bg-gray-50';
        html += `<tr class="${bgClass} hover:bg-blue-50 transition-colors">`;
        
        fieldNames.forEach(fieldName => {
            const value = formatCellValue(row[fieldName], fieldName);
            html += `<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${value}</td>`;
        });
        
        html += `</tr>`;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// ================================
// CARDS VIEW
// ================================

function renderCardsView() {
    const container = document.getElementById('dataContainer');
    
    if (!filteredData.length) {
        container.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-th-large text-3xl text-gray-400 mb-4"></i>
                <p class="text-gray-500">No hay datos para mostrar</p>
            </div>
        `;
        return;
    }
    
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageData = filteredData.slice(startIndex, endIndex);
    
    // Get visible fields for cards
    const visibleFields = mappingConfig.filter(field => field.show_in_card !== false);
    const fieldNames = visibleFields.length ? visibleFields.map(f => f.display_name) : Object.keys(pageData[0] || {});
    
    let html = `
        <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
    `;
    
    pageData.forEach(row => {
        html += `
            <div class="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-shadow duration-200">
        `;
        
        fieldNames.forEach((fieldName, index) => {
            const value = formatCellValue(row[fieldName], fieldName);
            const isFirst = index === 0;
            
            html += `
                <div class="mb-3 ${isFirst ? 'border-b border-gray-100 pb-3' : ''}">
                    <div class="text-xs text-gray-500 uppercase tracking-wide font-semibold">${fieldName}</div>
                    <div class="text-sm font-medium text-gray-900 mt-1 ${isFirst ? 'text-lg' : ''}">${value}</div>
                </div>
            `;
        });
        
        html += `
                <div class="mt-4 pt-3 border-t border-gray-100">
                    <button class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                        <i class="fas fa-eye mr-1"></i>Ver detalles
                    </button>
                </div>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// ================================
// CHART VIEW
// ================================

function renderChartView() {
    const container = document.getElementById('dataContainer');
    
    if (!filteredData.length) {
        container.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-chart-bar text-3xl text-gray-400 mb-4"></i>
                <p class="text-gray-500">No hay datos para mostrar en gráfico</p>
            </div>
        `;
        return;
    }
    
    html = `
        <div class="p-6">
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Visualización de Datos</h3>
                
                <!-- Chart Type Selector -->
                <div class="flex items-center space-x-2 mb-4">
                    <label class="text-sm font-medium text-gray-700">Tipo de gráfico:</label>
                    <button onclick="renderChart('bar')" id="chartBar" 
                            class="px-3 py-1 text-sm border rounded bg-blue-600 text-white">
                        Barras
                    </button>
                    <button onclick="renderChart('line')" id="chartLine" 
                            class="px-3 py-1 text-sm border rounded border-gray-300 text-gray-700 hover:bg-gray-50">
                        Líneas
                    </button>
                    <button onclick="renderChart('pie')" id="chartPie" 
                            class="px-3 py-1 text-sm border rounded border-gray-300 text-gray-700 hover:bg-gray-50">
                        Pastel
                    </button>
                </div>
            </div>
            
            <!-- Chart Container -->
            <div class="bg-white border rounded-lg p-4">
                <canvas id="dataChart" width="400" height="200"></canvas>
            </div>
            
            <!-- Chart Statistics -->
            <div class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div class="text-blue-600 text-sm font-medium">Total Registros</div>
                    <div class="text-2xl font-bold text-blue-900">${filteredData.length}</div>
                </div>
                <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div class="text-green-600 text-sm font-medium">Campos Visualizados</div>
                    <div class="text-2xl font-bold text-green-900">${mappingConfig.length}</div>
                </div>
                <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div class="text-purple-600 text-sm font-medium">Última Actualización</div>
                    <div class="text-sm font-medium text-purple-900">${new Date().toLocaleString()}</div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Render default chart
    setTimeout(() => renderChart('bar'), 100);
}

function renderChart(type) {
    // Update chart type buttons
    ['bar', 'line', 'pie'].forEach(t => {
        const btn = document.getElementById(`chart${t.charAt(0).toUpperCase() + t.slice(1)}`);
        if (btn) {
            if (t === type) {
                btn.classList.add('bg-blue-600', 'text-white');
                btn.classList.remove('border-gray-300', 'text-gray-700');
            } else {
                btn.classList.remove('bg-blue-600', 'text-white');
                btn.classList.add('border-gray-300', 'text-gray-700', 'hover:bg-gray-50');
            }
        }
    });
    
    const canvas = document.getElementById('dataChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if any
    if (window.currentChart) {
        window.currentChart.destroy();
    }
    
    // Prepare data for chart
    const chartData = prepareChartData(type);
    
    // Chart configuration
    const config = {
        type: type,
        data: chartData,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Distribución de Datos'
                },
                legend: {
                    display: true,
                    position: 'bottom'
                }
            },
            scales: type !== 'pie' ? {
                y: {
                    beginAtZero: true
                }
            } : {}
        }
    };
    
    // Create new chart
    window.currentChart = new Chart(ctx, config);
}

function prepareChartData(type) {
    // Simple example: count records by first field value
    if (!filteredData.length || !mappingConfig.length) {
        return {
            labels: ['Sin datos'],
            datasets: [{
                label: 'Datos',
                data: [0],
                backgroundColor: ['#e5e7eb']
            }]
        };
    }
    
    const firstField = mappingConfig[0]?.display_name || Object.keys(filteredData[0])[0];
    const counts = {};
    
    filteredData.forEach(row => {
        const value = row[firstField] || 'Sin valor';
        counts[value] = (counts[value] || 0) + 1;
    });
    
    const labels = Object.keys(counts).slice(0, 10); // Limit to 10 categories
    const data = labels.map(label => counts[label]);
    
    const colors = [
        '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
        '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6b7280'
    ];
    
    return {
        labels: labels,
        datasets: [{
            label: firstField,
            data: data,
            backgroundColor: type === 'pie' ? colors.slice(0, labels.length) : colors[0],
            borderColor: type === 'pie' ? colors.slice(0, labels.length) : colors[0],
            borderWidth: 1
        }]
    };
}

// ================================
// FILTERING AND SEARCH
// ================================

function handleSearch(event) {
    const searchTerm = event.target.value.toLowerCase();
    applyFilters(searchTerm);
    currentPage = 1; // Reset to first page
    renderCurrentView();
}

function applyFilters(searchTerm = '') {
    if (!searchTerm) {
        filteredData = [...allData];
    } else {
        filteredData = allData.filter(row => {
            return Object.values(row).some(value => 
                String(value).toLowerCase().includes(searchTerm)
            );
        });
    }
}

function handleItemsPerPageChange(event) {
    itemsPerPage = parseInt(event.target.value);
    currentPage = 1; // Reset to first page
    renderCurrentView();
}

// ================================
// PAGINATION
// ================================

function updatePagination() {
    const totalItems = filteredData.length;
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    
    // Update items info
    const startIndex = (currentPage - 1) * itemsPerPage + 1;
    const endIndex = Math.min(currentPage * itemsPerPage, totalItems);
    
    document.getElementById('itemsFrom').textContent = totalItems > 0 ? startIndex : 0;
    document.getElementById('itemsTo').textContent = endIndex;
    document.getElementById('totalItems').textContent = totalItems;
    
    // Update pagination buttons
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    
    // Generate page numbers
    generatePageNumbers(totalPages);
}

function generatePageNumbers(totalPages) {
    const container = document.getElementById('pageNumbers');
    let html = '';
    
    if (totalPages <= 7) {
        // Show all pages
        for (let i = 1; i <= totalPages; i++) {
            html += createPageButton(i);
        }
    } else {
        // Show abbreviated pagination
        if (currentPage <= 4) {
            for (let i = 1; i <= 5; i++) {
                html += createPageButton(i);
            }
            html += '<span class="px-2 text-gray-500">...</span>';
            html += createPageButton(totalPages);
        } else if (currentPage >= totalPages - 3) {
            html += createPageButton(1);
            html += '<span class="px-2 text-gray-500">...</span>';
            for (let i = totalPages - 4; i <= totalPages; i++) {
                html += createPageButton(i);
            }
        } else {
            html += createPageButton(1);
            html += '<span class="px-2 text-gray-500">...</span>';
            for (let i = currentPage - 1; i <= currentPage + 1; i++) {
                html += createPageButton(i);
            }
            html += '<span class="px-2 text-gray-500">...</span>';
            html += createPageButton(totalPages);
        }
    }
    
    container.innerHTML = html;
}

function createPageButton(pageNum) {
    const isActive = pageNum === currentPage;
    const classes = isActive 
        ? 'px-3 py-2 bg-blue-600 text-white border border-blue-600 rounded-md text-sm'
        : 'px-3 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md text-sm cursor-pointer';
    
    return `<button onclick="goToPage(${pageNum})" class="${classes}">${pageNum}</button>`;
}

function changePage(direction) {
    if (direction === 'prev' && currentPage > 1) {
        currentPage--;
    } else if (direction === 'next') {
        const totalPages = Math.ceil(filteredData.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
        }
    }
    
    renderCurrentView();
}

function goToPage(pageNum) {
    currentPage = pageNum;
    renderCurrentView();
}

// ================================
// UTILITY FUNCTIONS
// ================================

function formatCellValue(value, fieldName) {
    if (value === null || value === undefined) {
        return '<span class="text-gray-400 italic">N/A</span>';
    }
    
    // Format based on field type
    const fieldConfig = mappingConfig.find(f => f.display_name === fieldName);
    const fieldType = fieldConfig?.type || 'text';
    
    switch (fieldType) {
        case 'email':
            return `<a href="mailto:${value}" class="text-blue-600 hover:underline">${value}</a>`;
        case 'phone':
            return `<a href="tel:${value}" class="text-blue-600 hover:underline">${value}</a>`;
        case 'url':
            return `<a href="${value}" target="_blank" class="text-blue-600 hover:underline">${value}</a>`;
        case 'date':
            return new Date(value).toLocaleDateString();
        case 'boolean':
            return value ? '<span class="text-green-600">✓ Sí</span>' : '<span class="text-red-600">✗ No</span>';
        case 'number':
            return typeof value === 'number' ? value.toLocaleString() : value;
        default:
            return String(value);
    }
}

function refreshData() {
    loadPreviewData();
}

function exportData() {
    const dataToExport = {
        metadata: {
            export_date: new Date().toISOString(),
            total_records: filteredData.length,
            mapping_config: mappingConfig
        },
        data: filteredData
    };
    
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `data-export-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showMessage('Datos exportados exitosamente', 'success');
}

function showMessage(message, type = 'info') {
    // Reuse the message function from wizard
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
    
    setTimeout(() => {
        if (messageEl.parentNode) {
            messageEl.parentNode.removeChild(messageEl);
        }
    }, 5000);
}

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
