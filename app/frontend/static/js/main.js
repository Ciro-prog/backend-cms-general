/* ================================ */
/* ARCHIVO: app/frontend/static/js/main.js */
/* RUTA: app/frontend/static/js/main.js */
/* ================================ */

// CMS Dinámico MVP - JavaScript principal

// Configuración global
window.CMS = {
    baseURL: window.location.origin,
    
    // Utilidades
    utils: {
        /**
         * Mostrar spinner de carga en un elemento
         */
        showLoading: function(element, text = 'Cargando...') {
            if (typeof element === 'string') {
                element = document.querySelector(element);
            }
            if (element) {
                element.innerHTML = `
                    <div class="flex items-center justify-center py-4">
                        <div class="loading-spinner mr-2"></div>
                        <span class="text-gray-600">${text}</span>
                    </div>
                `;
            }
        },

        /**
         * Realizar llamada a la API
         */
        apiCall: async function(url, options = {}) {
            try {
                const response = await fetch(url, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.message || `HTTP ${response.status}`);
                }

                return data;
            } catch (error) {
                console.error('API Error:', error);
                throw error;
            }
        },

        /**
         * Formatear fecha
         */
        formatDate: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        /**
         * Formatear número
         */
        formatNumber: function(number) {
            return new Intl.NumberFormat('es-ES').format(number);
        },

        /**
         * Debounce para búsquedas
         */
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Generar ID único
         */
        generateId: function() {
            return Math.random().toString(36).substr(2, 9);
        },

        /**
         * Copiar texto al clipboard
         */
        copyToClipboard: async function(text) {
            try {
                await navigator.clipboard.writeText(text);
                this.showToast('Copiado al clipboard', 'success');
            } catch (err) {
                console.error('Error copiando al clipboard:', err);
                this.showToast('Error copiando texto', 'error');
            }
        },

        /**
         * Mostrar toast notification
         */
        showToast: function(message, type = 'info', duration = 3000) {
            const toast = document.createElement('div');
            toast.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-md shadow-lg max-w-sm transform transition-all duration-300 translate-x-full opacity-0`;
            
            const typeClasses = {
                success: 'bg-green-100 border border-green-400 text-green-700',
                error: 'bg-red-100 border border-red-400 text-red-700',
                warning: 'bg-yellow-100 border border-yellow-400 text-yellow-700',
                info: 'bg-blue-100 border border-blue-400 text-blue-700'
            };
            
            toast.className += ` ${typeClasses[type] || typeClasses.info}`;
            toast.innerHTML = `
                <div class="flex items-center">
                    <i class="fas fa-${this.getToastIcon(type)} mr-2"></i>
                    <span>${message}</span>
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-lg leading-none">×</button>
                </div>
            `;
            
            document.body.appendChild(toast);
            
            // Animate in
            setTimeout(() => {
                toast.classList.remove('translate-x-full', 'opacity-0');
            }, 100);
            
            // Auto remove
            setTimeout(() => {
                toast.classList.add('translate-x-full', 'opacity-0');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        },

        getToastIcon: function(type) {
            const icons = {
                success: 'check-circle',
                error: 'exclamation-circle',
                warning: 'exclamation-triangle',
                info: 'info-circle'
            };
            return icons[type] || icons.info;
        }
    },

    // Componentes UI
    components: {
        /**
         * Inicializar modal
         */
        initModal: function(modalId) {
            const modal = document.getElementById(modalId);
            if (!modal) return;

            // Cerrar con ESC
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                    modal.classList.add('hidden');
                }
            });

            // Cerrar clickeando fuera
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.classList.add('hidden');
                }
            });
        },

        /**
         * Inicializar tooltips
         */
        initTooltips: function() {
            const tooltips = document.querySelectorAll('[data-tooltip]');
            tooltips.forEach(element => {
                element.classList.add('tooltip');
            });
        },

        /**
         * Inicializar dropdowns
         */
        initDropdowns: function() {
            document.addEventListener('click', function(e) {
                // Cerrar todos los dropdowns cuando se hace click fuera
                const dropdowns = document.querySelectorAll('.dropdown-menu');
                dropdowns.forEach(dropdown => {
                    if (!dropdown.contains(e.target) && !dropdown.previousElementSibling.contains(e.target)) {
                        dropdown.classList.add('hidden');
                    }
                });
            });
        },

        /**
         * Inicializar confirmaciones
         */
        initConfirmations: function() {
            const confirmButtons = document.querySelectorAll('[data-confirm]');
            confirmButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    const message = this.getAttribute('data-confirm');
                    if (!confirm(message)) {
                        e.preventDefault();
                        return false;
                    }
                });
            });
        }
    },

    // Datos y estado
    data: {
        cache: new Map(),
        
        /**
         * Obtener datos del cache
         */
        getCache: function(key) {
            return this.cache.get(key);
        },

        /**
         * Guardar en cache
         */
        setCache: function(key, data, ttl = 300000) { // 5 minutos por defecto
            this.cache.set(key, {
                data: data,
                expires: Date.now() + ttl
            });
        },

        /**
         * Verificar si el cache es válido
         */
        isCacheValid: function(key) {
            const cached = this.cache.get(key);
            return cached && cached.expires > Date.now();
        },

        /**
         * Limpiar cache expirado
         */
        cleanExpiredCache: function() {
            const now = Date.now();
            for (let [key, value] of this.cache.entries()) {
                if (value.expires <= now) {
                    this.cache.delete(key);
                }
            }
        }
    },

    // Funciones específicas del CMS
    business: {
        /**
         * Refrescar estadísticas del dashboard
         */
        refreshStats: async function() {
            try {
                const stats = await CMS.utils.apiCall('/api/admin/stats');
                if (stats.success) {
                    // Actualizar elementos en el DOM
                    const elements = {
                        'stat-business-types': stats.data.total_business_types,
                        'stat-businesses': stats.data.total_business_instances,
                        'stat-apis': stats.data.total_api_configurations,
                        'stat-components': stats.data.total_dynamic_components
                    };

                    Object.entries(elements).forEach(([id, value]) => {
                        const element = document.getElementById(id);
                        if (element) {
                            element.textContent = value || 0;
                        }
                    });
                }
            } catch (error) {
                console.error('Error refreshing stats:', error);
            }
        },

        /**
         * Probar conexión de API
         */
        testApiConnection: async function(apiId) {
            try {
                CMS.utils.showToast('Probando conexión API...', 'info');
                
                const result = await CMS.utils.apiCall(`/api/admin/api/configurations/${apiId}/test`, {
                    method: 'POST'
                });

                if (result.success) {
                    CMS.utils.showToast('API conectada exitosamente', 'success');
                    return result;
                } else {
                    throw new Error(result.error || 'Error desconocido');
                }
            } catch (error) {
                CMS.utils.showToast(`Error probando API: ${error.message}`, 'error');
                throw error;
            }
        },

        /**
         * Refrescar componente específico
         */
        refreshComponent: async function(componentId) {
            try {
                const element = document.getElementById(`component-${componentId}`);
                if (element) {
                    CMS.utils.showLoading(element, 'Actualizando componente...');
                }

                // Aquí iría la lógica específica para refrescar el componente
                // Por ahora es simulado para el MVP
                
                setTimeout(() => {
                    if (element) {
                        element.innerHTML = '<p class="text-green-600">Componente actualizado</p>';
                    }
                    CMS.utils.showToast('Componente actualizado', 'success');
                }, 1000);

            } catch (error) {
                CMS.utils.showToast(`Error actualizando componente: ${error.message}`, 'error');
            }
        }
    },

    // Inicialización
    init: function() {
        console.log('🚀 CMS Dinámico MVP - JavaScript inicializado');
        
        // Inicializar componentes
        this.components.initTooltips();
        this.components.initDropdowns();
        this.components.initConfirmations();
        
        // Limpiar cache cada 5 minutos
        setInterval(() => {
            this.data.cleanExpiredCache();
        }, 300000);

        // Auto-hide flash messages
        this.initFlashMessages();

        // Inicializar modales comunes
        ['businessTypeModal', 'businessModal', 'apiConfigModal', 'componentModal'].forEach(modalId => {
            this.components.initModal(modalId);
        });
    },

    initFlashMessages: function() {
        setTimeout(() => {
            const messages = document.querySelectorAll('.flash-message');
            messages.forEach(msg => {
                msg.style.opacity = '0';
                setTimeout(() => {
                    if (msg.parentNode) {
                        msg.remove();
                    }
                }, 500);
            });
        }, 5000);
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.CMS.init();
});

// Funciones globales para compatibilidad
window.showMessage = function(type, text) {
    window.CMS.utils.showToast(text, type);
};

window.refreshStats = function() {
    window.CMS.business.refreshStats();
};

