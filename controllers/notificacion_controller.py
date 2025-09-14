# controllers/notificacion_controller.py
"""
Controlador para gestión de notificaciones
Principio SOLID: Single Responsibility - Responsabilidad única para notificaciones
"""

from flask import render_template, redirect, url_for, flash, request, session, jsonify
from models.notificacion import Notificacion, TipoNotificacion, EstadoNotificacion
from models.usuario import Usuario
from database import db
from datetime import datetime

class NotificacionController:
    
    @staticmethod
    def _usuario_autenticado():
        """Verifica si el usuario está autenticado"""
        return 'user_id' in session
    
    @staticmethod
    def _acceso_no_autorizado():
        """Redirige a login si no está autenticado"""
        flash('Debes iniciar sesión para acceder a esta página', 'error')
        return redirect(url_for('usuario.login'))
    
    @staticmethod
    def listar_notificaciones():
        """Lista todas las notificaciones del usuario"""
        if not NotificacionController._usuario_autenticado():
            return NotificacionController._acceso_no_autorizado()
        
        notificaciones = Notificacion.query.filter_by(usuario_id=session['user_id']).order_by(Notificacion.fecha_creacion.desc()).all()
        
        return render_template('notificaciones/listar_notificaciones.html', notificaciones=notificaciones)
    
    @staticmethod
    def marcar_como_leida(notificacion_id):
        """Marca una notificación como leída"""
        if not NotificacionController._usuario_autenticado():
            return NotificacionController._acceso_no_autorizado()
        
        notificacion = Notificacion.query.get_or_404(notificacion_id)
        
        # Verificar que la notificación pertenece al usuario
        if notificacion.usuario_id != session['user_id']:
            flash('No tienes permisos para esta notificación', 'error')
            return redirect(url_for('notificacion.listar_notificaciones'))
        
        try:
            notificacion.marcar_como_leida()
            db.session.commit()
            flash('Notificación marcada como leída', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al marcar la notificación', 'error')
        
        return redirect(url_for('notificacion.listar_notificaciones'))
    
    @staticmethod
    def archivar_notificacion(notificacion_id):
        """Archiva una notificación"""
        if not NotificacionController._usuario_autenticado():
            return NotificacionController._acceso_no_autorizado()
        
        notificacion = Notificacion.query.get_or_404(notificacion_id)
        
        # Verificar que la notificación pertenece al usuario
        if notificacion.usuario_id != session['user_id']:
            flash('No tienes permisos para esta notificación', 'error')
            return redirect(url_for('notificacion.listar_notificaciones'))
        
        try:
            notificacion.archivar()
            db.session.commit()
            flash('Notificación archivada', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al archivar la notificación', 'error')
        
        return redirect(url_for('notificacion.listar_notificaciones'))
    
    @staticmethod
    def marcar_todas_como_leidas():
        """Marca todas las notificaciones del usuario como leídas"""
        if not NotificacionController._usuario_autenticado():
            return NotificacionController._acceso_no_autorizado()
        
        try:
            notificaciones = Notificacion.query.filter_by(
                usuario_id=session['user_id'],
                estado=EstadoNotificacion.no_leida
            ).all()
            
            for notificacion in notificaciones:
                notificacion.marcar_como_leida()
            
            db.session.commit()
            flash('Todas las notificaciones marcadas como leídas', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al marcar las notificaciones', 'error')
        
        return redirect(url_for('notificacion.listar_notificaciones'))
    
    @staticmethod
    def obtener_notificaciones_no_leidas():
        """API para obtener notificaciones no leídas (AJAX)"""
        if not NotificacionController._usuario_autenticado():
            return jsonify({'error': 'No autenticado'}), 401
        
        notificaciones = Notificacion.query.filter_by(
            usuario_id=session['user_id'],
            estado=EstadoNotificacion.no_leida
        ).order_by(Notificacion.fecha_creacion.desc()).limit(5).all()
        
        return jsonify([notif.to_dict() for notif in notificaciones])
    
    @staticmethod
    def crear_notificacion(usuario_id, titulo, mensaje, tipo, servicio_id=None, contratacion_id=None, pago_id=None):
        """Método estático para crear notificaciones desde otros controladores"""
        try:
            notificacion = Notificacion(
                titulo=titulo,
                mensaje=mensaje,
                tipo=tipo,
                usuario_id=usuario_id,
                servicio_id=servicio_id,
                contratacion_id=contratacion_id,
                pago_id=pago_id
            )
            
            db.session.add(notificacion)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creando notificación: {e}")
            return False
