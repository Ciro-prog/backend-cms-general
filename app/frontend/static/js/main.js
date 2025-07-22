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
});
