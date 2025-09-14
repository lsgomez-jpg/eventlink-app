# models/contratacion.py
from database import db
from datetime import datetime
from sqlalchemy import Enum
import enum

class EstadoContratacion(enum.Enum):
    """Estados de una contratación"""
    solicitada = "solicitada"
    en_revision = "en_revision"
    aceptada = "aceptada"
    rechazada = "rechazada"
    confirmada = "confirmada"
    en_progreso = "en_progreso"
    completada = "completada"
    cancelada = "cancelada"

class MetodoPago(enum.Enum):
    """Métodos de pago disponibles"""
    efectivo = "efectivo"
    transferencia = "transferencia"
    tarjeta_credito = "tarjeta_credito"
    tarjeta_debito = "tarjeta_debito"
    mercadopago = "mercadopago"
    stripe = "stripe"

class Contratacion(db.Model):
    """Modelo para contrataciones entre organizadores y proveedores"""
    __tablename__ = "contrataciones"
    
    id = db.Column(db.Integer, primary_key=True)
    fecha_evento = db.Column(db.DateTime, nullable=False)
    duracion_horas = db.Column(db.Integer, nullable=True)
    numero_personas = db.Column(db.Integer, nullable=True)
    precio_total = db.Column(db.Numeric(10, 2), nullable=False)
    deposito_requerido = db.Column(db.Numeric(10, 2), nullable=True)
    deposito_pagado = db.Column(db.Numeric(10, 2), default=0)
    saldo_pendiente = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(Enum(MetodoPago), nullable=True)
    estado = db.Column(Enum(EstadoContratacion), default=EstadoContratacion.solicitada)
    
    # Información adicional
    notas_especiales = db.Column(db.Text, nullable=True)
    direccion_evento = db.Column(db.String(500), nullable=True)
    contacto_organizador = db.Column(db.String(20), nullable=True)
    contacto_proveedor = db.Column(db.String(20), nullable=True)
    
    # Relaciones
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)
    evento = db.relationship('Evento', backref=db.backref('contrataciones', lazy=True))
    
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)
    servicio = db.relationship('Servicio', backref=db.backref('contrataciones', lazy=True))
    
    organizador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    organizador = db.relationship('Usuario', foreign_keys=[organizador_id], backref=db.backref('contrataciones_organizador', lazy=True))
    
    proveedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    proveedor = db.relationship('Usuario', foreign_keys=[proveedor_id], backref=db.backref('contrataciones_proveedor', lazy=True))
    
    # Campos de auditoría
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_aceptacion = db.Column(db.DateTime, nullable=True)
    fecha_completacion = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, evento_id, servicio_id, organizador_id, proveedor_id, fecha_evento, precio_total, **kwargs):
        self.evento_id = evento_id
        self.servicio_id = servicio_id
        self.organizador_id = organizador_id
        self.proveedor_id = proveedor_id
        self.fecha_evento = fecha_evento
        self.precio_total = precio_total
        self.saldo_pendiente = precio_total
        
        # Asignar campos opcionales
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def aceptar(self, notas_adicionales=None):
        """Acepta la contratación por parte del proveedor"""
        self.estado = EstadoContratacion.aceptada
        self.fecha_aceptacion = datetime.utcnow()
        self.fecha_actualizacion = datetime.utcnow()
        
        if notas_adicionales:
            if self.notas_especiales:
                self.notas_especiales += f"\n\nNotas del proveedor: {notas_adicionales}"
            else:
                self.notas_especiales = f"Notas del proveedor: {notas_adicionales}"
    
    def rechazar(self, motivo=None):
        """Rechaza la contratación"""
        self.estado = EstadoContratacion.rechazada
        self.fecha_actualizacion = datetime.utcnow()
        
        if motivo:
            if self.notas_especiales:
                self.notas_especiales += f"\n\nMotivo de rechazo: {motivo}"
            else:
                self.notas_especiales = f"Motivo de rechazo: {motivo}"
    
    def confirmar(self):
        """Confirma la contratación (pago realizado)"""
        self.estado = EstadoContratacion.confirmada
        self.fecha_actualizacion = datetime.utcnow()
    
    def iniciar_servicio(self):
        """Marca el servicio como en progreso"""
        self.estado = EstadoContratacion.en_progreso
        self.fecha_actualizacion = datetime.utcnow()
    
    def completar(self):
        """Marca la contratación como completada"""
        self.estado = EstadoContratacion.completada
        self.fecha_completacion = datetime.utcnow()
        self.fecha_actualizacion = datetime.utcnow()
    
    def cancelar(self, motivo=None):
        """Cancela la contratación"""
        self.estado = EstadoContratacion.cancelada
        self.fecha_actualizacion = datetime.utcnow()
        
        if motivo:
            if self.notas_especiales:
                self.notas_especiales += f"\n\nMotivo de cancelación: {motivo}"
            else:
                self.notas_especiales = f"Motivo de cancelación: {motivo}"
    
    def pagar_deposito(self, monto):
        """Registra el pago del depósito"""
        self.deposito_pagado = float(self.deposito_pagado) + float(monto)
        self.saldo_pendiente = float(self.precio_total) - float(self.deposito_pagado)
        self.fecha_actualizacion = datetime.utcnow()
    
    def pagar_saldo_completo(self):
        """Marca el saldo como pagado completamente"""
        self.saldo_pendiente = 0
        self.fecha_actualizacion = datetime.utcnow()
    
    def esta_aceptada(self):
        """Verifica si la contratación está aceptada"""
        return self.estado == EstadoContratacion.aceptada
    
    def esta_completada(self):
        """Verifica si la contratación está completada"""
        return self.estado == EstadoContratacion.completada
    
    def puede_calificar(self):
        """Verifica si se puede calificar (servicio completado)"""
        return self.estado == EstadoContratacion.completada
    
    def obtener_dias_restantes(self):
        """Calcula los días restantes hasta el evento"""
        if self.fecha_evento:
            dias_restantes = (self.fecha_evento - datetime.utcnow()).days
            return max(0, dias_restantes)
        return 0
    
    def to_dict(self):
        """Convierte la contratación a diccionario para APIs"""
        return {
            'id': self.id,
            'fecha_evento': self.fecha_evento.isoformat() if self.fecha_evento else None,
            'duracion_horas': self.duracion_horas,
            'numero_personas': self.numero_personas,
            'precio_total': float(self.precio_total) if self.precio_total else None,
            'deposito_requerido': float(self.deposito_requerido) if self.deposito_requerido else None,
            'deposito_pagado': float(self.deposito_pagado) if self.deposito_pagado else None,
            'saldo_pendiente': float(self.saldo_pendiente) if self.saldo_pendiente else None,
            'metodo_pago': self.metodo_pago.value if self.metodo_pago else None,
            'estado': self.estado.value if self.estado else None,
            'notas_especiales': self.notas_especiales,
            'direccion_evento': self.direccion_evento,
            'contacto_organizador': self.contacto_organizador,
            'contacto_proveedor': self.contacto_proveedor,
            'evento_id': self.evento_id,
            'servicio_id': self.servicio_id,
            'organizador_id': self.organizador_id,
            'proveedor_id': self.proveedor_id,
            'dias_restantes': self.obtener_dias_restantes(),
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_aceptacion': self.fecha_aceptacion.isoformat() if self.fecha_aceptacion else None,
            'fecha_completacion': self.fecha_completacion.isoformat() if self.fecha_completacion else None
        }
    
    def __repr__(self):
        return f"<Contratacion {self.id} - {self.estado.value}>"
