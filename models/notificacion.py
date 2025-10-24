# models/notificacion.py
from database import db
from datetime import datetime
from sqlalchemy import Enum
import enum

class TipoNotificacion(enum.Enum):
    """Tipos de notificaciones"""
    nueva_contratacion = "nueva_contratacion"
    pago_recibido = "pago_recibido"
    pago_pendiente = "pago_pendiente"
    pago_fallido = "pago_fallido"
    servicio_aprobado = "servicio_aprobado"
    servicio_rechazado = "servicio_rechazado"
    nueva_resena = "nueva_resena"
    evento_cancelado = "evento_cancelado"

class EstadoNotificacion(enum.Enum):
    """Estados de notificaciones"""
    no_leida = "no_leida"
    leida = "leida"
    archivada = "archivada"

class Notificacion(db.Model):
    """Modelo para notificaciones del sistema"""
    __tablename__ = "notificaciones"
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    tipo = db.Column(Enum(TipoNotificacion), nullable=False)
    estado = db.Column(Enum(EstadoNotificacion), default=EstadoNotificacion.no_leida)
    
    # Relaciones
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=True)
    contratacion_id = db.Column(db.Integer, db.ForeignKey('contrataciones.id'), nullable=True)
    pago_id = db.Column(db.Integer, db.ForeignKey('pagos.id'), nullable=True)
    
    # Campos de auditoría
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_lectura = db.Column(db.DateTime, nullable=True)
    datos_adicionales = db.Column(db.JSON, nullable=True)
    
    # Relaciones
    usuario = db.relationship('Usuario', backref=db.backref('notificaciones', lazy=True))
    servicio = db.relationship('Servicio', backref=db.backref('notificaciones', lazy=True))
    contratacion = db.relationship('Contratacion', backref=db.backref('notificaciones', lazy=True))
    pago = db.relationship('Pago', backref=db.backref('notificaciones', lazy=True))
    
    def __init__(self, titulo, mensaje, tipo, usuario_id, servicio_id=None, contratacion_id=None, pago_id=None):
        self.titulo = titulo
        self.mensaje = mensaje
        self.tipo = tipo
        self.usuario_id = usuario_id
        self.servicio_id = servicio_id
        self.contratacion_id = contratacion_id
        self.pago_id = pago_id
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        self.estado = EstadoNotificacion.leida
        self.fecha_lectura = datetime.utcnow()
    
    def archivar(self):
        """Archiva la notificación"""
        self.estado = EstadoNotificacion.archivada
    
    def to_dict(self):
        """Convierte la notificación a diccionario para APIs"""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'mensaje': self.mensaje,
            'tipo': self.tipo.value if self.tipo else None,
            'estado': self.estado.value if self.estado else None,
            'usuario_id': self.usuario_id,
            'servicio_id': self.servicio_id,
            'contratacion_id': self.contratacion_id,
            'pago_id': self.pago_id,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_lectura': self.fecha_lectura.isoformat() if self.fecha_lectura else None
        }
    
    def __repr__(self):
        return f"<Notificacion {self.id}: {self.titulo}>"