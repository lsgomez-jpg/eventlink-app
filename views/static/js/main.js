// EventLink - JavaScript principal

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar popovers de Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts después de 5 segundos
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Validación de formularios
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Confirmación de acciones destructivas
    var deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            var message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Animación de entrada para cards
    var cards = document.querySelectorAll('.card');
    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    });

    cards.forEach(function(card) {
        observer.observe(card);
    });
});

// Funciones utilitarias
function showLoading(element) {
    element.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div>';
}

function hideLoading(element, originalContent) {
    element.innerHTML = originalContent;
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Funciones para búsqueda
function searchServices() {
    var form = document.getElementById('searchForm');
    var formData = new FormData(form);
    var params = new URLSearchParams();
    
    for (var pair of formData.entries()) {
        if (pair[1]) {
            params.append(pair[0], pair[1]);
        }
    }
    
    window.location.href = '/servicios/buscar?' + params.toString();
}

function clearFilters() {
    var form = document.getElementById('searchForm');
    form.reset();
    window.location.href = '/servicios/buscar';
}

// Funciones para pagos
// Función de Stripe removida - solo MercadoPago

function processMercadoPagoPayment(contratacionId) {
    var form = document.getElementById('mercadopagoForm');
    var formData = new FormData(form);
    
    fetch('/pagos/mercadopago/' + contratacionId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            monto: formData.get('monto'),
            tipo_pago: formData.get('tipo_pago')
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.exitoso) {
            // Redirigir a MercadoPago
            window.location.href = data.url_pago;
        } else {
            showAlert('Error en el pago: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error al procesar el pago', 'danger');
        console.error('Error:', error);
    });
}

// Funciones para notificaciones
function markNotificationAsRead(notificationId) {
    fetch('/notificaciones/' + notificationId + '/marcar-leida', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.exitoso) {
            var notification = document.getElementById('notification-' + notificationId);
            if (notification) {
                notification.classList.remove('no-leida');
                notification.classList.add('leida');
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Funciones para calificaciones
function submitRating(contratacionId) {
    var form = document.getElementById('ratingForm');
    var formData = new FormData(form);
    
    fetch('/contrataciones/' + contratacionId + '/calificar', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            showAlert('Calificación enviada exitosamente', 'success');
            setTimeout(function() {
                window.location.reload();
            }, 2000);
        } else {
            showAlert('Error al enviar la calificación', 'danger');
        }
    })
    .catch(error => {
        showAlert('Error al enviar la calificación', 'danger');
        console.error('Error:', error);
    });
}

// Función para mostrar alertas
function showAlert(message, type) {
    var alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alertDiv.innerHTML = 
        '<i class="fas fa-' + getAlertIcon(type) + ' me-2"></i>' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-hide después de 5 segundos
    setTimeout(function() {
        var bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

function createAlertContainer() {
    var container = document.createElement('div');
    container.id = 'alertContainer';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

function getAlertIcon(type) {
    var icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Funciones para filtros dinámicos
function updatePriceRange() {
    var minPrice = document.getElementById('precio_min').value;
    var maxPrice = document.getElementById('precio_max').value;
    var priceDisplay = document.getElementById('priceRange');
    
    if (minPrice || maxPrice) {
        var range = '';
        if (minPrice) range += '$' + minPrice;
        range += ' - ';
        if (maxPrice) range += '$' + maxPrice;
        else range += 'Sin límite';
        priceDisplay.textContent = range;
    } else {
        priceDisplay.textContent = 'Cualquier precio';
    }
}

function updateRatingRange() {
    var minRating = document.getElementById('calificacion_min').value;
    var ratingDisplay = document.getElementById('ratingRange');
    
    if (minRating) {
        ratingDisplay.innerHTML = 'Mínimo: ' + '★'.repeat(minRating) + '☆'.repeat(5 - minRating);
    } else {
        ratingDisplay.textContent = 'Cualquier calificación';
    }
}

// Funciones para mapas (si se implementan)
function initMap() {
    // Implementación futura para mapas
    console.log('Mapa inicializado');
}

// Funciones para carga de archivos
function previewImage(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
            var preview = document.getElementById('imagePreview');
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Funciones para validación en tiempo real
function validateEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    var re = /^[\+]?[1-9][\d]{0,15}$/;
    return re.test(phone.replace(/\s/g, ''));
}

function validatePassword(password) {
    return password.length >= 6;
}

// Event listeners para validación en tiempo real
document.addEventListener('DOMContentLoaded', function() {
    var emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value && !validateEmail(this.value)) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });

    var phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value && !validatePhone(this.value)) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });

    var passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value && !validatePassword(this.value)) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });
});







