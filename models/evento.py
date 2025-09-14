# models/evento.py
from database import db
from datetime import datetime
from sqlalchemy import Enum
import enum

class EstadoEvento(enum.Enum):
    """Estados posibles de un evento"""
    borrador = "borrador"
    activo = "activo"
    en_progreso = "en_progreso"
    en_curso = "en_curso"
    completado = "completado"
    cancelado = "cancelado"

class TipoEvento(enum.Enum):
    """Tipos de eventos disponibles"""
    corporativo = "corporativo"
    social = "social"
    deportivo = "deportivo"
    cultural = "cultural"
    religioso = "religioso"
    academico = "academico"
    otro = "otro"

class Evento(db.Model):
    """Modelo para eventos creados por organizadores"""
    __tablename__ = "eventos"
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    tipo = db.Column(Enum(TipoEvento), nullable=False)
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime, nullable=False)
    fecha_evento = db.Column(db.DateTime, nullable=True)  # Fecha específica del evento (puede ser igual a fecha_inicio)
    ubicacion = db.Column(db.String(300), nullable=False)
    direccion = db.Column(db.String(500), nullable=True)
    ciudad = db.Column(db.String(100), nullable=False)
    presupuesto_maximo = db.Column(db.Numeric(10, 2), nullable=True)
    numero_invitados = db.Column(db.Integer, nullable=True)
    estado = db.Column(Enum(EstadoEvento), default=EstadoEvento.borrador)
    
    # Campos para imágenes
    imagen_principal = db.Column(db.String(500), nullable=True)
    imagen_secundaria = db.Column(db.String(500), nullable=True)
    galeria_imagenes = db.Column(db.Text, nullable=True)  # JSON string con URLs de imágenes
    
    # Relaciones
    organizador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    organizador = db.relationship('Usuario', backref=db.backref('eventos', lazy=True))
    
    # Campos de auditoría
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, titulo, tipo, fecha_inicio, fecha_fin, ubicacion, ciudad, organizador_id, **kwargs):
        self.titulo = titulo
        self.tipo = tipo
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.fecha_evento = kwargs.get('fecha_evento', fecha_inicio)  # Por defecto usa fecha_inicio
        self.ubicacion = ubicacion
        self.ciudad = ciudad
        self.organizador_id = organizador_id
        
        # Asignar campos opcionales
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def activar(self):
        """Activa el evento para que sea visible a proveedores"""
        self.estado = EstadoEvento.activo
        self.fecha_actualizacion = datetime.utcnow()
    
    def iniciar_evento(self):
        """Marca el evento como en curso (cuando llega la fecha)"""
        self.estado = EstadoEvento.en_curso
        self.fecha_actualizacion = datetime.utcnow()
    
    def completar(self):
        """Marca el evento como completado (solo manualmente por el proveedor)"""
        self.estado = EstadoEvento.completado
        self.fecha_actualizacion = datetime.utcnow()
    
    def cancelar(self):
        """Cancela el evento"""
        self.estado = EstadoEvento.cancelado
        self.fecha_actualizacion = datetime.utcnow()
    
    def esta_activo(self):
        """Verifica si el evento está activo"""
        return self.estado == EstadoEvento.activo
    
    def esta_en_curso(self):
        """Verifica si el evento está en curso"""
        return self.estado == EstadoEvento.en_curso
    
    def esta_completado(self):
        """Verifica si el evento está completado"""
        return self.estado == EstadoEvento.completado
    
    def puede_ser_completado_manualmente(self):
        """Verifica si el evento puede ser completado manualmente (solo cuando está en curso)"""
        return self.estado == EstadoEvento.en_curso
    
    def verificar_estado_por_fecha(self):
        """Verifica y actualiza el estado del evento basado en la fecha actual"""
        from datetime import datetime
        ahora = datetime.utcnow()
        
        # Si el evento ya está completado o cancelado, no hacer nada
        if self.estado in [EstadoEvento.completado, EstadoEvento.cancelado]:
            return False
        
        # Marcar como "en_curso" cuando llegue la fecha de realización
        fecha_realizacion = self.fecha_evento or self.fecha_fin
        if fecha_realizacion and self.estado == EstadoEvento.activo:
            if ahora >= fecha_realizacion:
                self.estado = EstadoEvento.en_curso
                self.fecha_actualizacion = ahora
                return True  # Indica que hubo un cambio
        
        return False  # No hubo cambios
    
    def obtener_duracion_horas(self):
        """Calcula la duración del evento en horas"""
        if self.fecha_inicio and self.fecha_fin:
            duracion = self.fecha_fin - self.fecha_inicio
            return duracion.total_seconds() / 3600
        return 0
    
    def to_dict(self):
        """Convierte el evento a diccionario para APIs"""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'tipo': self.tipo.value if self.tipo else None,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'fecha_evento': self.fecha_evento.isoformat() if self.fecha_evento else None,
            'ubicacion': self.ubicacion,
            'direccion': self.direccion,
            'ciudad': self.ciudad,
            'presupuesto_maximo': float(self.presupuesto_maximo) if self.presupuesto_maximo else None,
            'numero_invitados': self.numero_invitados,
            'estado': self.estado.value if self.estado else None,
            'organizador_id': self.organizador_id,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
    
    def __repr__(self):
        return f"<Evento {self.titulo} ({self.tipo.value})>"
