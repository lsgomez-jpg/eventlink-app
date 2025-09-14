# models/pago.py
"""
Modelo para gestión de pagos
Principio SOLID: Single Responsibility - Responsabilidad única para pagos
"""

from database import db
from datetime import datetime
from enum import Enum
import json  # <-- Importar json para serializar dicts

class MetodoPago(Enum):
    """Métodos de pago disponibles"""
    mercadopago = "mercadopago"
    stripe = "stripe"
    tarjeta_credito = "tarjeta_credito"
    transferencia_bancaria = "transferencia_bancaria"
    efectivo = "efectivo"

class EstadoPago(Enum):
    """Estados de pago"""
    pendiente = "pendiente"
    aprobado = "aprobado"
    rechazado = "rechazado"
    cancelado = "cancelado"
    reembolsado = "reembolsado"

class Pago(db.Model):
    """Modelo para pagos"""
    __tablename__ = 'pagos'
    
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(db.Enum(MetodoPago), nullable=False)
    estado = db.Column(db.Enum(EstadoPago), default=EstadoPago.pendiente, nullable=False)
    
    # Información del pagador
    nombre_titular = db.Column(db.String(100), nullable=False)
    email_pagador = db.Column(db.String(100), nullable=False)
    telefono_pagador = db.Column(db.String(20))
    documento_pagador = db.Column(db.String(20))
    
    # Relaciones
    contratacion_id = db.Column(db.Integer, db.ForeignKey('contrataciones.id'), nullable=True)
    organizador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Datos de la transacción
    id_transaccion = db.Column(db.String(100))  # ID de MercadoPago, Stripe, etc.
    _datos_adicionales = db.Column("datos_adicionales", db.Text)  # Guardamos JSON como string
    
    # Fechas
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_aprobacion = db.Column(db.DateTime)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    contratacion = db.relationship('Contratacion', backref='pagos')
    organizador = db.relationship('Usuario', backref='pagos')
    
    def __repr__(self):
        return f'<Pago {self.id}: ${self.monto} - {self.estado.value}>'
    
    # Setter y getter para manejar dicts automáticamente
    @property
    def datos_adicionales(self):
        if self._datos_adicionales:
            return json.loads(self._datos_adicionales)
        return {}

    @datos_adicionales.setter
    def datos_adicionales(self, value):
        if isinstance(value, dict):
            self._datos_adicionales = json.dumps(value)
        elif isinstance(value, str):
            self._datos_adicionales = value
        else:
            self._datos_adicionales = None
    
    def to_dict(self):
        """Convierte el pago a diccionario"""
        return {
            'id': self.id,
            'monto': float(self.monto),
            'metodo_pago': self.metodo_pago.value,
            'estado': self.estado.value,
            'nombre_titular': self.nombre_titular,
            'email_pagador': self.email_pagador,
            'telefono_pagador': self.telefono_pagador,
            'documento_pagador': self.documento_pagador,
            'datos_adicionales': self.datos_adicionales,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_aprobacion': self.fecha_aprobacion.isoformat() if self.fecha_aprobacion else None
        }
