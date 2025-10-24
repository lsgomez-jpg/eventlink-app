
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from models.notificacion import Notificacion, TipoNotificacion
from models.usuario import Usuario
from database import db

class NotificacionObserver(ABC):
    """Interfaz abstracta para observadores de notificaciones"""
    
    @abstractmethod
    def actualizar(self, notificacion: Notificacion):
        """Método que se ejecuta cuando se crea una notificación"""
        pass

class EmailObserver(NotificacionObserver):
    """Observer para enviar notificaciones por email"""
    
    def actualizar(self, notificacion: Notificacion):
        """Envía notificación por email si el usuario lo tiene habilitado"""
        usuario = Usuario.query.get(notificacion.usuario_id)
        
        if usuario and usuario.notificaciones_email:
            # Aquí se implementaría el envío real de email
            print(f"[EMAIL] Email enviado a {usuario.correo}: {notificacion.titulo}")
            # TODO: Implementar envío real con Flask-Mail

class PushObserver(NotificacionObserver):
    """Observer para enviar notificaciones push"""
    
    def actualizar(self, notificacion: Notificacion):
        """Envía notificación push si el usuario lo tiene habilitado"""
        usuario = Usuario.query.get(notificacion.usuario_id)
        
        if usuario and usuario.notificaciones_push:
            # Aquí se implementaría el envío real de push notification
            print(f"[PUSH] Push notification enviada a {usuario.nombre}: {notificacion.titulo}")
            # TODO: Implementar envío real con Firebase o similar

class DatabaseObserver(NotificacionObserver):
    """Observer para guardar notificaciones en base de datos"""
    
    def actualizar(self, notificacion: Notificacion):
        """Guarda la notificación en la base de datos"""
        try:
            db.session.add(notificacion)
            db.session.commit()
            print(f"[DB] Notificación guardada en BD: {notificacion.titulo}")
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Error al guardar notificación: {e}")

class LogObserver(NotificacionObserver):
    """Observer para logging de notificaciones"""
    
    def actualizar(self, notificacion: Notificacion):
        """Registra la notificación en logs"""
        print(f"📝 LOG: Notificación {notificacion.tipo.value} para usuario {notificacion.usuario_id}")

class SistemaNotificaciones:
    """Sistema central de notificaciones que implementa el patrón Observer"""
    
    def __init__(self):
        self._observadores: List[NotificacionObserver] = []
        self._configuracion_global = {
            'enviar_email': True,
            'enviar_push': True,
            'guardar_bd': True,
            'logging': True
        }
    
    def registrar_observador(self, observador: NotificacionObserver):
        """Registra un nuevo observador"""
        if observador not in self._observadores:
            self._observadores.append(observador)
            print(f"[OK] Observador registrado: {type(observador).__name__}")
    
    def desregistrar_observador(self, observador: NotificacionObserver):
        """Desregistra un observador"""
        if observador in self._observadores:
            self._observadores.remove(observador)
            print(f"[OK] Observador desregistrado: {type(observador).__name__}")
    
    def notificar_observadores(self, notificacion: Notificacion):
        """Notifica a todos los observadores registrados"""
        print(f"[NOTIFY] Notificando a {len(self._observadores)} observadores...")
        
        for observador in self._observadores:
            try:
                observador.actualizar(notificacion)
            except Exception as e:
                print(f"[ERROR] Error en observador {type(observador).__name__}: {e}")
    
    def crear_notificacion(self, titulo: str, mensaje: str, tipo: TipoNotificacion, 
                          usuario_id: int, **kwargs) -> Notificacion:
        """Crea una nueva notificación y notifica a los observadores"""
        
        # Crear la notificación
        notificacion = Notificacion(
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            usuario_id=usuario_id,
            **kwargs
        )
        
        # Notificar a todos los observadores
        self.notificar_observadores(notificacion)
        
        return notificacion
    
    def configurar_sistema(self):
        """Configura el sistema con los observadores por defecto"""
        # Limpiar observadores existentes
        self._observadores.clear()
        
        # Registrar observadores según configuración
        if self._configuracion_global['guardar_bd']:
            self.registrar_observador(DatabaseObserver())
        
        if self._configuracion_global['enviar_email']:
            self.registrar_observador(EmailObserver())
        
        if self._configuracion_global['enviar_push']:
            self.registrar_observador(PushObserver())
        
        if self._configuracion_global['logging']:
            self.registrar_observador(LogObserver())
        
        print("[OK] Sistema de notificaciones configurado")
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de notificaciones"""
        return {
            'observadores_registrados': len(self._observadores),
            'tipos_observadores': [type(obs).__name__ for obs in self._observadores],
            'configuracion': self._configuracion_global
        }

# Instancia global del sistema de notificaciones
sistema_notificaciones = SistemaNotificaciones()

# Configurar el sistema al importar el módulo
sistema_notificaciones.configurar_sistema()
