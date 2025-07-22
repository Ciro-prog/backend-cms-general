/* ===================================
   app/frontend/static/js/main.js
   =================================== */

// CMS Dinámico - JavaScript principal
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
    
    // Mejorar experiencia de formularios
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = 'Procesando...';
            }
        });
    });
});