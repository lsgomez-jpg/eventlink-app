 
from abc import ABC, abstractmethod
from models.servicio import Servicio, CategoriaServicio
from models.notificacion import Notificacion, TipoNotificacion
from models.usuario import Usuario

class ServicioFactory(ABC):
    # factory abstracto para crear servicios
    
    @abstractmethod
    def crear_servicio(self, nombre, descripcion, precio_base, ciudad, proveedor_id, **kwargs):
        # metodo abstracto para crear servicios
        pass

class CateringFactory(ServicioFactory):
    # factory para servicios de catering
    
    def crear_servicio(self, nombre, descripcion, precio_base, ciudad, proveedor_id, **kwargs):
        # crea un servicio de catering
        defaults = {
            'categoria': CategoriaServicio.CATERING,
            'precio_por_persona': kwargs.get('precio_por_persona', 0),
            'capacidad_maxima': kwargs.get('capacidad_maxima', 100),
            'incluye_materiales': True,
            'incluye_montaje': True,
            'incluye_desmontaje': True,
            'duracion_minima': 2,
            'duracion_maxima': 12
        }
        defaults.update(kwargs)
        
        return Servicio(
            nombre=nombre,
            descripcion=descripcion,
            precio_base=precio_base,
            ciudad=ciudad,
            proveedor_id=proveedor_id,
            **defaults
        )

class FotografiaFactory(ServicioFactory):
    """Factory para servicios de fotografía"""
    
    def crear_servicio(self, nombre, descripcion, precio_base, ciudad, proveedor_id, **kwargs):
        """Crea un servicio de fotografía con configuraciones específicas"""
        defaults = {
            'categoria': CategoriaServicio.FOTOGRAFIA,
            'precio_por_hora': kwargs.get('precio_por_hora', 0),
            'duracion_minima': 1,
            'duracion_maxima': 8,
            'incluye_materiales': True,
            'incluye_transporte': kwargs.get('incluye_transporte', False),
            'requiere_deposito': True,
            'porcentaje_deposito': 30
        }
        defaults.update(kwargs)
        
        return Servicio(
            nombre=nombre,
            descripcion=descripcion,
            precio_base=precio_base,
            ciudad=ciudad,
            proveedor_id=proveedor_id,
            **defaults
        )

class SonidoFactory(ServicioFactory):
    """Factory para servicios de sonido"""
    
    def crear_servicio(self, nombre, descripcion, precio_base, ciudad, proveedor_id, **kwargs):
        """Crea un servicio de sonido con configuraciones específicas"""
        defaults = {
            'categoria': CategoriaServicio.SONIDO,
            'precio_por_hora': kwargs.get('precio_por_hora', 0),
            'duracion_minima': 2,
            'duracion_maxima': 12,
            'incluye_materiales': True,
            'incluye_montaje': True,
            'incluye_desmontaje': True,
            'incluye_transporte': True,
            'requiere_deposito': True,
            'porcentaje_deposito': 50
        }
        defaults.update(kwargs)
        
        return Servicio(
            nombre=nombre,
            descripcion=descripcion,
            precio_base=precio_base,
            ciudad=ciudad,
            proveedor_id=proveedor_id,
            **defaults
        )

class DecoracionFactory(ServicioFactory):
    """Factory para servicios de decoración"""
    
    def crear_servicio(self, nombre, descripcion, precio_base, ciudad, proveedor_id, **kwargs):
        """Crea un servicio de decoración con configuraciones específicas"""
        defaults = {
            'categoria': CategoriaServicio.DECORACION,
            'precio_por_hora': kwargs.get('precio_por_hora', 0),
            'duracion_minima': 1,
            'duracion_maxima': 6,
            'incluye_materiales': kwargs.get('incluye_materiales', False),
            'incluye_montaje': True,
            'incluye_desmontaje': True,
            'incluye_transporte': kwargs.get('incluye_transporte', False),
            'requiere_deposito': True,
            'porcentaje_deposito': 40
        }
        defaults.update(kwargs)
        
        return Servicio(
            nombre=nombre,
            descripcion=descripcion,
            precio_base=precio_base,
            ciudad=ciudad,
            proveedor_id=proveedor_id,
            **defaults
        )

class ServicioFactoryManager:
    # manager para obtener el factory apropiado segun la categoria
    
    _factories = {
        CategoriaServicio.catering: CateringFactory(),
        CategoriaServicio.fotografia: FotografiaFactory(),
        CategoriaServicio.sonido: SonidoFactory(),
        CategoriaServicio.decoracion: DecoracionFactory(),
    }
    
    @classmethod
    def obtener_factory(cls, categoria):
        # obtiene el factory apropiado para la categoria
        factory = cls._factories.get(categoria)
        if not factory:
            # factory generico para categorias no especificas
            return GenericServiceFactory()
        return factory
    
    @classmethod
    def registrar_factory(cls, categoria, factory):
        # registra un nuevo factory para una categoria
        cls._factories[categoria] = factory

class GenericServiceFactory(ServicioFactory):
    # factory generico para servicios no especificos
    
    def crear_servicio(self, nombre, descripcion, precio_base, ciudad, proveedor_id, **kwargs):
        # crea un servicio generico
        return Servicio(
            nombre=nombre,
            descripcion=descripcion,
            precio_base=precio_base,
            ciudad=ciudad,
            proveedor_id=proveedor_id,
            **kwargs
        )

class NotificacionFactory:
    # factory para crear diferentes tipos de notificaciones
    
    @staticmethod
    def crear_notificacion_bienvenida(usuario_id, rol):
        # crea notificacion de bienvenida
        mensaje = f"¡Bienvenido a EventLink! Tu cuenta de {rol} ha sido creada exitosamente."
        return Notificacion(
            titulo="¡Bienvenido a EventLink!",
            mensaje=mensaje,
            tipo=TipoNotificacion.BIENVENIDA,
            usuario_id=usuario_id
        )
    
    @staticmethod
    def crear_notificacion_solicitud(proveedor_id, evento_id, servicio_id):
        """Crea notificación de nueva solicitud"""
        return Notificacion(
            titulo="Nueva solicitud de servicio",
            mensaje="Has recibido una nueva solicitud de servicio para tu evento.",
            tipo=TipoNotificacion.NUEVA_SOLICITUD,
            usuario_id=proveedor_id,
            evento_id=evento_id,
            servicio_id=servicio_id
        )
    
    @staticmethod
    def crear_notificacion_aceptacion(organizador_id, contratacion_id):
        """Crea notificación de aceptación de contratación"""
        return Notificacion(
            titulo="Solicitud aceptada",
            mensaje="Tu solicitud de servicio ha sido aceptada por el proveedor.",
            tipo=TipoNotificacion.CONTRATACION_ACEPTADA,
            usuario_id=organizador_id,
            contratacion_id=contratacion_id
        )
    
    @staticmethod
    def crear_notificacion_rechazo(organizador_id, contratacion_id, motivo=None):
        """Crea notificación de rechazo de contratación"""
        mensaje = "Tu solicitud de servicio ha sido rechazada."
        if motivo:
            mensaje += f" Motivo: {motivo}"
        
        return Notificacion(
            titulo="Solicitud rechazada",
            mensaje=mensaje,
            tipo=TipoNotificacion.CONTRATACION_RECHAZADA,
            usuario_id=organizador_id,
            contratacion_id=contratacion_id
        )
    
    @staticmethod
    def crear_notificacion_pago(proveedor_id, contratacion_id, monto):
        """Crea notificación de pago recibido"""
        return Notificacion(
            titulo="Pago recibido",
            mensaje=f"Has recibido un pago de ${monto} por tu servicio.",
            tipo=TipoNotificacion.PAGO_RECIBIDO,
            usuario_id=proveedor_id,
            contratacion_id=contratacion_id,
            datos_adicionales={'monto': monto}
        )
    
    @staticmethod
    def crear_notificacion_evento_proximo(organizador_id, evento_id, dias_restantes):
        """Crea notificación de evento próximo"""
        return Notificacion(
            titulo="Evento próximo",
            mensaje=f"Tu evento está próximo. Faltan {dias_restantes} días.",
            tipo=TipoNotificacion.EVENTO_PROXIMO,
            usuario_id=organizador_id,
            evento_id=evento_id,
            datos_adicionales={'dias_restantes': dias_restantes}
        )
    
    @staticmethod
    def crear_notificacion_calificacion(proveedor_id, calificacion_id):
        """Crea notificación de nueva calificación"""
        return Notificacion(
            titulo="Nueva calificación recibida",
            mensaje="Has recibido una nueva calificación por tu servicio.",
            tipo=TipoNotificacion.NUEVA_CALIFICACION,
            usuario_id=proveedor_id,
            datos_adicionales={'calificacion_id': calificacion_id}
        )





