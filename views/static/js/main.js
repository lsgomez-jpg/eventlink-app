// EventLink - JavaScript principal optimizado

// ✅ Cargar componentes Bootstrap solo cuando estén disponibles
function initBootstrapComponents() {
    // Solo inicializar si Bootstrap está disponible
    if (typeof bootstrap === 'undefined') {
        console.warn('⚠️ Bootstrap no disponible, algunos componentes no se inicializarán');
        return;
    }

    // Inicializar tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));
    }

    // Inicializar popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    if (popoverTriggerList.length > 0) {
        [...popoverTriggerList].map(el => new bootstrap.Popover(el));
    }
}

// Auto-hide alerts después de 5 segundos
function initAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (typeof bootstrap !== 'undefined') {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.display = 'none';
            }
        }, 5000);
    });
}

// Validación de formularios
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    [...forms].forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// Confirmación de acciones destructivas
function initDeleteConfirmations() {
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

// Animación de entrada para cards (con Intersection Observer)
function initCardAnimations() {
    const cards = document.querySelectorAll('.card');
    
    if ('IntersectionObserver' in window && cards.length > 0) {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                    observer.unobserve(entry.target);
                }
            });
        }, { rootMargin: '50px' });

        cards.forEach(card => observer.observe(card));
    }
}

// ✅ Inicialización principal
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 EventLink JS inicializado');
    
    // Inicializar funcionalidades básicas
    initFormValidation();
    initDeleteConfirmations();
    initCardAnimations();
    initAlerts();
    
    // Esperar a que Bootstrap esté disponible (si se carga con defer)
    if (typeof bootstrap === 'undefined') {
        // Esperar hasta 3 segundos
        let attempts = 0;
        const checkBootstrap = setInterval(() => {
            attempts++;
            if (typeof bootstrap !== 'undefined') {
                console.log('✅ Bootstrap cargado, inicializando componentes');
                clearInterval(checkBootstrap);
                initBootstrapComponents();
            } else if (attempts >= 30) {
                clearInterval(checkBootstrap);
                console.warn('⚠️ Bootstrap no cargado después de 3s');
            }
        }, 100);
    } else {
        initBootstrapComponents();
    }
});

// ========== FUNCIONES UTILITARIAS ==========

function showLoading(element) {
    const spinner = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div>';
    element.innerHTML = spinner;
}

function hideLoading(element, originalContent) {
    element.innerHTML = originalContent;
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('es-CO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('es-CO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ========== BÚSQUEDA Y FILTROS ==========

function searchServices() {
    const form = document.getElementById('searchForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const params = new URLSearchParams();
    
    for (const [key, value] of formData.entries()) {
        if (value) params.append(key, value);
    }
    
    window.location.href = '/servicios/buscar?' + params.toString();
}

function clearFilters() {
    const form = document.getElementById('searchForm');
    if (!form) return;
    
    form.reset();
    window.location.href = '/servicios/buscar';
}

function updatePriceRange() {
    const minPrice = document.getElementById('precio_min')?.value;
    const maxPrice = document.getElementById('precio_max')?.value;
    const priceDisplay = document.getElementById('priceRange');
    
    if (!priceDisplay) return;
    
    if (minPrice || maxPrice) {
        let range = minPrice ? `$${minPrice}` : '$0';
        range += ' - ';
        range += maxPrice ? `$${maxPrice}` : 'Sin límite';
        priceDisplay.textContent = range;
    } else {
        priceDisplay.textContent = 'Cualquier precio';
    }
}

function updateRatingRange() {
    const minRating = document.getElementById('calificacion_min')?.value;
    const ratingDisplay = document.getElementById('ratingRange');
    
    if (!ratingDisplay) return;
    
    if (minRating) {
        const stars = '★'.repeat(minRating) + '☆'.repeat(5 - minRating);
        ratingDisplay.innerHTML = `Mínimo: ${stars}`;
    } else {
        ratingDisplay.textContent = 'Cualquier calificación';
    }
}

// ========== PAGOS ==========

async function processMercadoPagoPayment(contratacionId) {
    const form = document.getElementById('mercadopagoForm');
    if (!form) return;
    
    const formData = new FormData(form);
    
    try {
        const response = await fetch(`/pagos/mercadopago/${contratacionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                monto: formData.get('monto'),
                tipo_pago: formData.get('tipo_pago')
            })
        });
        
        const data = await response.json();
        
        if (data.exitoso) {
            window.location.href = data.url_pago;
        } else {
            showAlert('Error en el pago: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Error al procesar el pago', 'danger');
        console.error('Error:', error);
    }
}

// ========== NOTIFICACIONES ==========

async function markNotificationAsRead(notificationId) {
    try {
        const response = await fetch(`/notificaciones/${notificationId}/marcar-leida`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.exitoso) {
            const notification = document.getElementById(`notification-${notificationId}`);
            if (notification) {
                notification.classList.remove('no-leida');
                notification.classList.add('leida');
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// ========== CALIFICACIONES ==========

async function submitRating(contratacionId) {
    const form = document.getElementById('ratingForm');
    if (!form) return;
    
    const formData = new FormData(form);
    
    try {
        const response = await fetch(`/contrataciones/${contratacionId}/calificar`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showAlert('Calificación enviada exitosamente', 'success');
            setTimeout(() => window.location.reload(), 2000);
        } else {
            showAlert('Error al enviar la calificación', 'danger');
        }
    } catch (error) {
        showAlert('Error al enviar la calificación', 'danger');
        console.error('Error:', error);
    }
}

// ========== ALERTAS ==========

function showAlert(message, type = 'info') {
    const container = document.getElementById('alertContainer') || createAlertContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(alertDiv);
    
    // Auto-hide después de 5 segundos
    setTimeout(() => {
        if (typeof bootstrap !== 'undefined') {
            new bootstrap.Alert(alertDiv).close();
        } else {
            alertDiv.remove();
        }
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

function getAlertIcon(type) {
    const icons = {
        success: 'check-circle',
        danger: 'exclamation-triangle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// ========== PREVIEW DE IMÁGENES ==========

function previewImage(input) {
    if (!input.files || !input.files[0]) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = document.getElementById('imagePreview');
        if (preview) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        }
    };
    reader.readAsDataURL(input.files[0]);
}

// ========== VALIDACIONES ==========

function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePhone(phone) {
    return /^[\+]?[1-9][\d]{0,15}$/.test(phone.replace(/\s/g, ''));
}

function validatePassword(password) {
    return password.length >= 6;
}

// ========== VALIDACIÓN EN TIEMPO REAL ==========

function initRealtimeValidation() {
    // Email
    document.querySelectorAll('input[type="email"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !validateEmail(this.value)) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });

    // Teléfono
    document.querySelectorAll('input[type="tel"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !validatePhone(this.value)) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });

    // Password
    document.querySelectorAll('input[type="password"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !validatePassword(this.value)) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });
}

// Inicializar validaciones en tiempo real
document.addEventListener('DOMContentLoaded', initRealtimeValidation);

// Exportar funciones globales para uso desde HTML inline
window.EventLink = {
    searchServices,
    clearFilters,
    updatePriceRange,
    updateRatingRange,
    processMercadoPagoPayment,
    markNotificationAsRead,
    submitRating,
    showAlert,
    previewImage,
    formatCurrency,
    formatDate,
    formatDateTime
};