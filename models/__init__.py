# models/__init__.py
"""
Módulo de modelos de EventLink
Implementa el patrón MVC y principios SOLID
"""

from .usuario import Usuario, RolUsuario
from .evento import Evento, EstadoEvento, TipoEvento
from .servicio import Servicio, CategoriaServicio, EstadoServicio
from .contratacion import Contratacion, EstadoContratacion, MetodoPago
from .calificacion import Calificacion
from .resena import Resena
from .notificacion import Notificacion, TipoNotificacion, EstadoNotificacion
from .pago import Pago, MetodoPago as MetodoPagoPago, EstadoPago
from .carrito import CarritoItem, EstadoCarritoItem

__all__ = [
    'Usuario', 'RolUsuario',
    'Evento', 'EstadoEvento', 'TipoEvento',
    'Servicio', 'CategoriaServicio', 'EstadoServicio',
    'Contratacion', 'EstadoContratacion', 'MetodoPago',
    'Calificacion',
    'Resena',
    'Notificacion', 'TipoNotificacion', 'EstadoNotificacion',
    'Pago', 'MetodoPagoPago', 'EstadoPago',
    'CarritoItem', 'EstadoCarritoItem'
]







