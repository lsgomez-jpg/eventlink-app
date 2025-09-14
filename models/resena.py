# models/resena.py
from database import db
from datetime import datetime
from sqlalchemy import Enum
import enum

class Resena(db.Model):
    """Modelo para reseñas de servicios"""
    __tablename__ = "resenas"
    
    id = db.Column(db.Integer, primary_key=True)
    puntuacion = db.Column(db.Integer, nullable=False)  # 1-5 estrellas
    comentario = db.Column(db.Text, nullable=True)
    
    # Relaciones
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)
    contratacion_id = db.Column(db.Integer, db.ForeignKey('contrataciones.id'), nullable=False)
    organizador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Campos de auditoría
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    servicio = db.relationship('Servicio', backref=db.backref('resenas', lazy=True))
    contratacion = db.relationship('Contratacion', backref=db.backref('resenas', lazy=True))
    organizador = db.relationship('Usuario', backref=db.backref('resenas_dadas', lazy=True))
    
    def __init__(self, puntuacion, servicio_id, contratacion_id, organizador_id, comentario=None):
        self.puntuacion = puntuacion
        self.servicio_id = servicio_id
        self.contratacion_id = contratacion_id
        self.organizador_id = organizador_id
        self.comentario = comentario
    
    def to_dict(self):
        """Convierte la reseña a diccionario para APIs"""
        return {
            'id': self.id,
            'puntuacion': self.puntuacion,
            'comentario': self.comentario,
            'servicio_id': self.servicio_id,
            'contratacion_id': self.contratacion_id,
            'organizador_id': self.organizador_id,
            'organizador_nombre': self.organizador.nombre if self.organizador else None,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
    
    def __repr__(self):
        return f"<Resena {self.id}: {self.puntuacion} estrellas>"
