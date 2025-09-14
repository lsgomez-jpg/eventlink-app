# rutas/__init__.py
"""
Módulo de rutas de EventLink
Organización modular con blueprints
"""

from .usuario_rutas import usuario_bp
from .evento_rutas import evento_bp
from .servicio_rutas import servicio_bp
from .contratacion_rutas import contratacion_bp
from .pago_rutas import pago_bp
from .carrito_rutas import carrito_bp
from .resena_rutas import resena_bp
from .notificacion_rutas import notificacion_bp

__all__ = [
    'usuario_bp',
    'evento_bp',
    'servicio_bp', 
    'contratacion_bp',
    'pago_bp',
    'carrito_bp',
    'resena_bp',
    'notificacion_bp'
]



