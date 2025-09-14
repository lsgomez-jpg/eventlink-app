# models/servicio.py
from database import db
from datetime import datetime
from sqlalchemy import Enum
import enum

class CategoriaServicio(enum.Enum):
    """Categorías de servicios disponibles"""
    catering = "catering"
    fotografia = "fotografia"
    sonido = "sonido"
    decoracion = "decoracion"
    logistica = "logistica"
    seguridad = "seguridad"
    transporte = "transporte"
    entretenimiento = "entretenimiento"
    flores = "flores"
    invitaciones = "invitaciones"
    otro = "otro"


class EstadoServicio(enum.Enum):
    """Estados de un servicio"""
    disponible = "disponible"
    no_disponible = "no_disponible"
    en_revision = "en_revision"
    rechazado = "rechazado"


class Servicio(db.Model):
    """Modelo para servicios ofrecidos por proveedores"""
    __tablename__ = "servicios"
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    categoria = db.Column(Enum(CategoriaServicio), nullable=False)
    precio_base = db.Column(db.Numeric(10, 2), nullable=False)
    precio_por_hora = db.Column(db.Numeric(10, 2), nullable=True)
    precio_por_persona = db.Column(db.Numeric(10, 2), nullable=True)
    duracion_minima = db.Column(db.Integer, nullable=True)  # en horas
    duracion_maxima = db.Column(db.Integer, nullable=True)  # en horas
    capacidad_maxima = db.Column(db.Integer, nullable=True)  # número de personas
    incluye_materiales = db.Column(db.Boolean, default=False)
    incluye_transporte = db.Column(db.Boolean, default=False)
    incluye_montaje = db.Column(db.Boolean, default=False)
    incluye_desmontaje = db.Column(db.Boolean, default=False)
    requiere_deposito = db.Column(db.Boolean, default=False)
    porcentaje_deposito = db.Column(db.Numeric(5, 2), nullable=True)  # porcentaje del total
    estado = db.Column(Enum(EstadoServicio), default=EstadoServicio.disponible)
    
    # Información de ubicación
    ciudad = db.Column(db.String(100), nullable=False)
    radio_cobertura = db.Column(db.Integer, default=50)  # en kilómetros
    
    # Imágenes de referencia
    imagenes_referencia = db.Column(db.JSON, nullable=True)  # Lista de URLs de imágenes
    
    # Relaciones
    proveedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    proveedor = db.relationship('Usuario', backref=db.backref('servicios', lazy=True))
    
    # Campos de auditoría
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, nombre, descripcion, categoria, precio_base, ciudad, proveedor_id, **kwargs):
        self.nombre = nombre
        self.descripcion = descripcion
        self.categoria = categoria
        self.precio_base = precio_base
        self.ciudad = ciudad
        self.proveedor_id = proveedor_id
        
        # Asignar campos opcionales
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def calcular_precio_estimado(self, duracion_horas=None, numero_personas=None):
        """Calcula el precio estimado basado en los parámetros"""
        precio_total = float(self.precio_base)
        
        if self.precio_por_hora and duracion_horas:
            precio_total += float(self.precio_por_hora) * duracion_horas
        
        if self.precio_por_persona and numero_personas:
            precio_total += float(self.precio_por_persona) * numero_personas
        
        return precio_total
    
    def calcular_deposito(self, precio_total):
        """Calcula el monto del depósito requerido"""
        if not self.requiere_deposito or not self.porcentaje_deposito:
            return 
        
        return (float(precio_total) * float(self.porcentaje_deposito)) / 100
    
    def esta_disponible(self):
        """Verifica si el servicio está disponible"""
        return self.estado == EstadoServicio.disponible
    
    @property
    def calificacion_promedio(self):
        """Calcula la calificación promedio del servicio"""
        from models.calificacion import Calificacion
        calificaciones = Calificacion.query.filter_by(servicio_id=self.id).all()
        if not calificaciones:
            return 0.0
        return sum(c.puntuacion for c in calificaciones) / len(calificaciones)
    
    def activar(self):
        """Activa el servicio"""
        self.estado = EstadoServicio.disponible
        self.fecha_actualizacion = datetime.utcnow()
    
    def desactivar(self):
        """Desactiva el servicio"""
        self.estado = EstadoServicio.no_disponible
        self.fecha_actualizacion = datetime.utcnow()
    
    def obtener_calificacion_promedio(self):
        """Obtiene la calificación promedio del servicio"""
        from models.calificacion import Calificacion
        calificaciones = Calificacion.query.filter_by(servicio_id=self.id).all()
        
        if not calificaciones:
            return 0
        
        suma_calificaciones = sum(calif.puntuacion for calif in calificaciones)
        return round(suma_calificaciones / len(calificaciones), 1)
    
    def obtener_numero_resenas(self):
        """Obtiene el número de reseñas del servicio"""
        from models.calificacion import Calificacion
        return Calificacion.query.filter_by(servicio_id=self.id).count()
    
    def to_dict(self):
        """Convierte el servicio a diccionario para APIs"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'categoria': self.categoria.value if self.categoria else None,
            'precio_base': float(self.precio_base) if self.precio_base else None,
            'precio_por_hora': float(self.precio_por_hora) if self.precio_por_hora else None,
            'precio_por_persona': float(self.precio_por_persona) if self.precio_por_persona else None,
            'duracion_minima': self.duracion_minima,
            'duracion_maxima': self.duracion_maxima,
            'capacidad_maxima': self.capacidad_maxima,
            'incluye_materiales': self.incluye_materiales,
            'incluye_transporte': self.incluye_transporte,
            'incluye_montaje': self.incluye_montaje,
            'incluye_desmontaje': self.incluye_desmontaje,
            'requiere_deposito': self.requiere_deposito,
            'porcentaje_deposito': float(self.porcentaje_deposito) if self.porcentaje_deposito else None,
            'estado': self.estado.value if self.estado else None,
            'ciudad': self.ciudad,
            'radio_cobertura': self.radio_cobertura,
            'proveedor_id': self.proveedor_id,
            'calificacion_promedio': self.obtener_calificacion_promedio(),
            'numero_resenas': self.obtener_numero_resenas(),
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
    
    def __repr__(self):
        return f"<Servicio {self.nombre} ({self.categoria.value})>"
