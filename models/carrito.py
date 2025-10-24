# models/carrito.py
from database import db
from datetime import datetime
from sqlalchemy import Enum
import enum

class EstadoCarritoItem(enum.Enum):
    """Estados de un item del carrito"""
    pendiente = "pendiente"
    confirmado = "confirmado"
    procesando = "procesando"
    completado = "completado"
    cancelado = "cancelado"

class CarritoItem(db.Model):
    """Modelo para items del carrito de compras"""
    __tablename__ = "carrito_items"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Información del servicio
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)
    servicio = db.relationship('Servicio', backref=db.backref('carrito_items', lazy=True))
    
    # Información del evento
    evento_id = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=False)
    evento = db.relationship('Evento', backref=db.backref('carrito_items', lazy=True))
    
    # Usuario que agregó el item
    organizador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    organizador = db.relationship('Usuario', backref=db.backref('carrito_items', lazy=True))
    
    # Detalles del servicio solicitado
    fecha_evento = db.Column(db.DateTime, nullable=False)
    duracion_horas = db.Column(db.Integer, nullable=False, default=4)
    numero_personas = db.Column(db.Integer, nullable=True)
    ubicacion = db.Column(db.String(500), nullable=False)
    notas_especiales = db.Column(db.Text, nullable=True)
    
    # Precios
    precio_base = db.Column(db.Numeric(10, 2), nullable=False)
    precio_por_hora = db.Column(db.Numeric(10, 2), nullable=True)
    precio_por_persona = db.Column(db.Numeric(10, 2), nullable=True)
    precio_total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Estado del item
    estado = db.Column(Enum(EstadoCarritoItem), default=EstadoCarritoItem.pendiente)
    
    # Tipo de item para diferenciar entre servicios y contrataciones
    tipo_item = db.Column(db.String(20), default='servicio', nullable=False)
    
    # Campos de auditoría
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, servicio_id, evento_id, organizador_id, fecha_evento, 
                 duracion_horas=4, numero_personas=None, ubicacion="", 
                 notas_especiales="", tipo_item='servicio', **kwargs):
        self.servicio_id = servicio_id
        self.evento_id = evento_id
        self.organizador_id = organizador_id
        self.fecha_evento = fecha_evento
        self.duracion_horas = duracion_horas
        self.numero_personas = numero_personas
        self.ubicacion = ubicacion
        self.notas_especiales = notas_especiales
        self.tipo_item = tipo_item  # aseguramos el tipo

        # Asignar campos opcionales
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # Inicializar precios con valores por defecto
        self.precio_base = 0
        self.precio_por_hora = None
        self.precio_por_persona = None
        self.precio_total = 0
    
    def _calcular_precios(self):
        """Calcula los precios del item del carrito"""
        if self.servicio:
            self.precio_base = self.servicio.precio_base or 0
            self.precio_por_hora = self.servicio.precio_por_hora
            self.precio_por_persona = self.servicio.precio_por_persona
            
            # Calcular precio total
            total = float(self.precio_base)
            
            if self.precio_por_hora:
                total += float(self.precio_por_hora) * self.duracion_horas
            
            if self.precio_por_persona and self.numero_personas:
                total += float(self.precio_por_persona) * self.numero_personas
            
            self.precio_total = total
        else:
            # Si no hay servicio, usar valores por defecto
            self.precio_base = 0
            self.precio_por_hora = None
            self.precio_por_persona = None
            self.precio_total = 0
    
    def calcular_precios(self):
        """Método público para calcular precios después de la creación"""
        self._calcular_precios()
    
    def confirmar(self):
        """Confirma el item del carrito"""
        self.estado = EstadoCarritoItem.confirmado
        self.fecha_actualizacion = datetime.utcnow()
    
    def procesar(self):
        """Marca el item como procesando"""
        self.estado = EstadoCarritoItem.procesando
        self.fecha_actualizacion = datetime.utcnow()
    
    def completar(self):
        """Marca el item como completado"""
        self.estado = EstadoCarritoItem.completado
        self.fecha_actualizacion = datetime.utcnow()
    
    def cancelar(self):
        """Cancela el item del carrito"""
        self.estado = EstadoCarritoItem.cancelado
        self.fecha_actualizacion = datetime.utcnow()
    
    def esta_pendiente(self):
        """Verifica si el item está pendiente"""
        return self.estado == EstadoCarritoItem.pendiente
    
    def esta_confirmado(self):
        """Verifica si el item está confirmado"""
        return self.estado == EstadoCarritoItem.confirmado
    
    def puede_editar(self):
        """Verifica si el item puede ser editado"""
        return self.estado in [EstadoCarritoItem.pendiente, EstadoCarritoItem.confirmado]
    
    def to_dict(self):
        """Convierte el item a diccionario"""
        return {
            'id': self.id,
            'servicio_id': self.servicio_id,
            'evento_id': self.evento_id,
            'organizador_id': self.organizador_id,
            'fecha_evento': self.fecha_evento.isoformat() if self.fecha_evento else None,
            'duracion_horas': self.duracion_horas,
            'numero_personas': self.numero_personas,
            'ubicacion': self.ubicacion,
            'notas_especiales': self.notas_especiales,
            'precio_base': float(self.precio_base) if self.precio_base else 0,
            'precio_por_hora': float(self.precio_por_hora) if self.precio_por_hora else 0,
            'precio_por_persona': float(self.precio_por_persona) if self.precio_por_persona else 0,
            'precio_total': float(self.precio_total) if self.precio_total else 0,
            'estado': self.estado.value if self.estado else None,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'servicio': {
                'id': self.servicio.id if self.servicio else None,
                'nombre': self.servicio.nombre if self.servicio else None,
                'categoria': self.servicio.categoria.value if self.servicio and self.servicio.categoria else None,
                'proveedor': {
                    'id': self.servicio.proveedor.id if self.servicio and self.servicio.proveedor else None,
                    'nombre': self.servicio.proveedor.nombre if self.servicio and self.servicio.proveedor else None
                } if self.servicio and self.servicio.proveedor else None
            } if self.servicio else None,
            'evento': {
                'id': self.evento.id if self.evento else None,
                'titulo': self.evento.titulo if self.evento else None,
                'fecha_inicio': self.evento.fecha_inicio.isoformat() if self.evento and self.evento.fecha_inicio else None
            } if self.evento else None
        }
    
    @staticmethod
    def obtener_carrito_usuario(user_id, tipo='servicio'):
        """Obtiene todos los items tipo 'servicio' pendientes del carrito de un usuario"""
        items = CarritoItem.query.filter_by(
            organizador_id=user_id,
            tipo_item=tipo,
            estado=EstadoCarritoItem.pendiente
        ).all()

        # Aseguramos que todos los precios estén calculados
        for item in items:
            item.calcular_precios()
        
        return items
    
    @staticmethod
    def calcular_total_carrito(user_id, tipo='servicio'):
        """Calcula el total del carrito de un usuario"""
        items = CarritoItem.obtener_carrito_usuario(user_id, tipo)
        return sum(float(item.precio_total) for item in items)
    
    @staticmethod
    def limpiar_carrito_usuario(user_id):
        """Limpia el carrito de un usuario (marca como completados)"""
        items = CarritoItem.obtener_carrito_usuario(user_id)
        for item in items:
            item.completar()
        db.session.commit()
    
    def __repr__(self):
        return f"<CarritoItem {self.servicio.nombre if self.servicio else 'N/A'} - {self.precio_total}>"

