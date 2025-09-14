# models/calificacion.py
from database import db
from datetime import datetime

class Calificacion(db.Model):
    """Modelo para calificaciones y reseñas de servicios"""
    __tablename__ = "calificaciones"
    
    id = db.Column(db.Integer, primary_key=True)
    puntuacion = db.Column(db.Integer, nullable=False)  # 1-5 estrellas
    comentario = db.Column(db.Text, nullable=True)
    fecha_calificacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    contratacion_id = db.Column(db.Integer, db.ForeignKey('contrataciones.id'), nullable=False)
    contratacion = db.relationship('Contratacion', backref=db.backref('calificacion', uselist=False))
    
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)
    servicio = db.relationship('Servicio', backref=db.backref('calificaciones', lazy=True))
    
    organizador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    organizador = db.relationship('Usuario', foreign_keys=[organizador_id], backref=db.backref('calificaciones_hechas', lazy=True))
    
    proveedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    proveedor = db.relationship('Usuario', foreign_keys=[proveedor_id], backref=db.backref('calificaciones_recibidas', lazy=True))
    
    def __init__(self, puntuacion, contratacion_id, servicio_id, organizador_id, proveedor_id, comentario=None):
        self.puntuacion = puntuacion
        self.contratacion_id = contratacion_id
        self.servicio_id = servicio_id
        self.organizador_id = organizador_id
        self.proveedor_id = proveedor_id
        self.comentario = comentario
    
    def es_valida(self):
        """Verifica si la calificación es válida (1-5 estrellas)"""
        return 1 <= self.puntuacion <= 5
    
    def obtener_estrellas(self):
        """Retorna la representación en estrellas de la puntuación"""
        return "★" * self.puntuacion + "☆" * (5 - self.puntuacion)
    
    def to_dict(self):
        """Convierte la calificación a diccionario para APIs"""
        return {
            'id': self.id,
            'puntuacion': self.puntuacion,
            'comentario': self.comentario,
            'estrellas': self.obtener_estrellas(),
            'fecha_calificacion': self.fecha_calificacion.isoformat() if self.fecha_calificacion else None,
            'contratacion_id': self.contratacion_id,
            'servicio_id': self.servicio_id,
            'organizador_id': self.organizador_id,
            'proveedor_id': self.proveedor_id
        }
    
    def __repr__(self):
        return f"<Calificacion {self.puntuacion}★ - {self.servicio_id}>"
