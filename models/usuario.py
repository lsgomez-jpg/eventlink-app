# models/usuario.py
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import Enum
import enum

class RolUsuario(enum.Enum):
    """Roles disponibles en el sistema (compatibles con PostgreSQL)"""
    organizador = "organizador"
    proveedor = "proveedor"
    admin = "admin"

class Usuario(db.Model):
    """Modelo para usuarios del sistema (organizadores, proveedores y admins)"""
    __tablename__ = "usuarios"
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=True)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    contraseña = db.Column(db.String(200), nullable=False)
    rol = db.Column(Enum(RolUsuario, name="rolusuario", create_type=False), nullable=False)  
    activo = db.Column(db.Boolean, default=True)
    
    # Información adicional del perfil
    descripcion = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(200), nullable=True)
    ciudad = db.Column(db.String(100), nullable=True)
    direccion = db.Column(db.String(300), nullable=True)
    
    # Configuraciones de notificaciones
    notificaciones_email = db.Column(db.Boolean, default=True)
    notificaciones_push = db.Column(db.Boolean, default=True)
    
    # Campos de auditoría
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime, nullable=True)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, nombre, correo, contraseña, rol, **kwargs):
        self.nombre = nombre
        self.correo = correo
        self.rol = rol
        self.set_password(contraseña)
        
        # Asignar campos opcionales
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_password(self, contraseña):
        """Establece la contraseña encriptada"""
        self.contraseña = generate_password_hash(contraseña)

    def check_password(self, contraseña):
        """Verifica si la contraseña es correcta"""
        return check_password_hash(self.contraseña, contraseña)
    
    def actualizar_ultimo_acceso(self):
        """Actualiza la fecha del último acceso"""
        self.ultimo_acceso = datetime.utcnow()
        db.session.commit()
    
    def es_organizador(self):
        """Verifica si el usuario es organizador"""
        return self.rol == RolUsuario.organizador
    
    def es_proveedor(self):
        """Verifica si el usuario es proveedor"""
        return self.rol == RolUsuario.proveedor
    
    def es_admin(self):
        """Verifica si el usuario es administrador"""
        return self.rol == RolUsuario.admin
    
    def obtener_nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        if self.apellido:
            return f"{self.nombre} {self.apellido}"
        return self.nombre
    
    def obtener_calificacion_promedio(self):
        """Obtiene la calificación promedio del usuario (para proveedores)"""
        if not self.es_proveedor():
            return 0
        
        from models.calificacion import Calificacion
        calificaciones = Calificacion.query.filter_by(proveedor_id=self.id).all()
        
        if not calificaciones:
            return 0
        
        suma_calificaciones = sum(calif.puntuacion for calif in calificaciones)
        return round(suma_calificaciones / len(calificaciones), 1)
    
    def obtener_numero_servicios(self):
        """Obtiene el número de servicios del proveedor"""
        if not self.es_proveedor():
            return 0
        
        from models.servicio import Servicio
        return Servicio.query.filter_by(proveedor_id=self.id, estado='disponible').count()
    
    def obtener_numero_eventos(self):
        """Obtiene el número de eventos del organizador"""
        if not self.es_organizador():
            return 0
        
        from models.evento import Evento
        return Evento.query.filter_by(organizador_id=self.id).count()
    
    def obtener_notificaciones_no_leidas(self):
        """Obtiene el número de notificaciones no leídas"""
        from models.notificacion import Notificacion, EstadoNotificacion
        return Notificacion.query.filter_by(
            usuario_id=self.id, 
            estado=EstadoNotificacion.NO_LEIDA
        ).count()
    
    def desactivar_cuenta(self):
        """Desactiva la cuenta del usuario"""
        self.activo = False
        self.fecha_actualizacion = datetime.utcnow()
    
    def to_dict(self):
        """Convierte el usuario a diccionario para APIs"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'nombre_completo': self.obtener_nombre_completo(),
            'correo': self.correo,
            'telefono': self.telefono,
            'rol': self.rol.value if self.rol else None,
            'activo': self.activo,
            'descripcion': self.descripcion,
            'avatar': self.avatar,
            'ciudad': self.ciudad,
            'direccion': self.direccion,
            'notificaciones_email': self.notificaciones_email,
            'notificaciones_push': self.notificaciones_push,
            'calificacion_promedio': self.obtener_calificacion_promedio(),
            'numero_servicios': self.obtener_numero_servicios(),
            'numero_eventos': self.obtener_numero_eventos(),
            'notificaciones_no_leidas': self.obtener_notificaciones_no_leidas(),
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None
        }

    def __repr__(self):
        return f"<Usuario {self.obtener_nombre_completo()} ({self.rol.value})>"
