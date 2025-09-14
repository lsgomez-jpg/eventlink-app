# controllers/contratacion_controller.py
"""
Controlador para gestión de contrataciones
Principio SOLID: Single Responsibility - Responsabilidad única para contrataciones
"""

from flask import request, session, flash, redirect, url_for, render_template, jsonify
from models.contratacion import Contratacion, EstadoContratacion, MetodoPago
from models.usuario import Usuario, RolUsuario
from models.servicio import Servicio
from models.evento import Evento
from database import db
from datetime import datetime
from patterns.observer import sistema_notificaciones
from patterns.factory import NotificacionFactory
from patterns.singleton import payment_gateway

class ContratacionController:
    
    @staticmethod
    def listar_contrataciones():
        """Lista las contrataciones del usuario"""
        if not ContratacionController._usuario_autenticado():
            return ContratacionController._acceso_no_autorizado()
        
        user_id = session['user_id']
        user_rol = session['user_rol']
        
        # Obtener contrataciones según el rol
        if user_rol == RolUsuario.organizador.value:
            contrataciones = Contratacion.query.filter_by(organizador_id=user_id).order_by(
                Contratacion.fecha_creacion.desc()
            ).all()
        else:
            contrataciones = Contratacion.query.filter_by(proveedor_id=user_id).order_by(
                Contratacion.fecha_creacion.desc()
            ).all()
        
        return render_template('contrataciones/listar_contrataciones.html', 
                             contrataciones=contrataciones)
    
    @staticmethod
    def detalle_contratacion(contratacion_id):
        """Muestra el detalle de una contratación"""
        if not ContratacionController._usuario_autenticado():
            return ContratacionController._acceso_no_autorizado()
        
        contratacion = Contratacion.query.get_or_404(contratacion_id)
        
        # Verificar permisos
        if not ContratacionController._tiene_acceso_contratacion(contratacion):
            flash('No tienes permisos para ver esta contratación', 'error')
            return redirect(url_for('contratacion.listar_contrataciones'))
        
        # Obtener información relacionada
        evento = Evento.query.get(contratacion.evento_id)
        servicio = Servicio.query.get(contratacion.servicio_id)
        organizador = Usuario.query.get(contratacion.organizador_id)
        proveedor = Usuario.query.get(contratacion.proveedor_id)
        
        return render_template('contrataciones/detalle_contratacion.html',
                             contratacion=contratacion,
                             evento=evento,
                             servicio=servicio,
                             organizador=organizador,
                             proveedor=proveedor)
    
    @staticmethod
    def aceptar_contratacion(contratacion_id):
        """Acepta una contratación (solo proveedores)"""
        if not ContratacionController._usuario_autenticado():
            return ContratacionController._acceso_no_autorizado()
        
        if session['user_rol'] != RolUsuario.proveedor.value:
            flash('Solo los proveedores pueden aceptar contrataciones', 'error')
            return redirect(url_for('index'))
        
        contratacion = Contratacion.query.get_or_404(contratacion_id)
        
        # Verificar permisos
        if contratacion.proveedor_id != session['user_id']:
            flash('Solo puedes aceptar tus propias contrataciones', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        if contratacion.estado != EstadoContratacion.solicitada:
            flash('Esta contratación no puede ser aceptada', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        if request.method == 'GET':
            return render_template('contrataciones/aceptar_contratacion.html', 
                                 contratacion=contratacion)
        
        notas_adicionales = request.form.get('notas_adicionales', '').strip()
        
        try:
            # Aceptar contratación
            contratacion.aceptar(notas_adicionales)
            db.session.commit()
            
            # Crear notificación para el organizador
            notificacion = NotificacionFactory.crear_notificacion_aceptacion(
                contratacion.organizador_id, 
                contratacion_id
            )
            sistema_notificaciones.notificar_observadores(notificacion)
            
            flash('Contratación aceptada exitosamente', 'success')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al aceptar la contratación', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
    
    @staticmethod
    def rechazar_contratacion(contratacion_id):
        """Rechaza una contratación (solo proveedores)"""
        if not ContratacionController._usuario_autenticado():
            return ContratacionController._acceso_no_autorizado()
        
        if session['user_rol'] != RolUsuario.proveedor.value:
            flash('Solo los proveedores pueden rechazar contrataciones', 'error')
            return redirect(url_for('index'))
        
        contratacion = Contratacion.query.get_or_404(contratacion_id)
        
        # Verificar permisos
        if contratacion.proveedor_id != session['user_id']:
            flash('Solo puedes rechazar tus propias contrataciones', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        if contratacion.estado != EstadoContratacion.solicitada:
            flash('Esta contratación no puede ser rechazada', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        if request.method == 'GET':
            return render_template('contrataciones/rechazar_contratacion.html', 
                                 contratacion=contratacion)
        
        motivo = request.form.get('motivo', '').strip()
        
        if not motivo:
            flash('Debes proporcionar un motivo para el rechazo', 'error')
            return render_template('contrataciones/rechazar_contratacion.html', 
                                 contratacion=contratacion)
        
        try:
            # Rechazar contratación
            contratacion.rechazar(motivo)
            db.session.commit()
            
            # Crear notificación para el organizador
            notificacion = NotificacionFactory.crear_notificacion_rechazo(
                contratacion.organizador_id, 
                contratacion_id, 
                motivo
            )
            sistema_notificaciones.notificar_observadores(notificacion)
            
            flash('Contratación rechazada', 'success')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al rechazar la contratación', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
    
    @staticmethod
    def confirmar_contratacion(contratacion_id):
        """Confirma una contratación (pago realizado)"""
        if not ContratacionController._usuario_autenticado():
            return ContratacionController._acceso_no_autorizado()
        
        if session['user_rol'] != RolUsuario.organizador.value:
            flash('Solo los organizadores pueden confirmar contrataciones', 'error')
            return redirect(url_for('index'))
        
        contratacion = Contratacion.query.get_or_404(contratacion_id)
        
        # Verificar permisos
        if contratacion.organizador_id != session['user_id']:
            flash('Solo puedes confirmar tus propias contrataciones', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        if contratacion.estado != EstadoContratacion.aceptada:
            flash('Esta contratación no puede ser confirmada', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        try:
            # Confirmar contratación
            contratacion.confirmar()
            db.session.commit()
            
            flash('Contratación confirmada exitosamente', 'success')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al confirmar la contratación', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
    
    @staticmethod
    def iniciar_servicio(contratacion_id):
        """Inicia el servicio (solo proveedores)"""
        if not ContratacionController._usuario_autenticado():
            return ContratacionController._acceso_no_autorizado()
        
        if session['user_rol'] != RolUsuario.proveedor.value:
            flash('Solo los proveedores pueden iniciar servicios', 'error')
            return redirect(url_for('index'))
        
        contratacion = Contratacion.query.get_or_404(contratacion_id)
        
        # Verificar permisos
        if contratacion.proveedor_id != session['user_id']:
            flash('Solo puedes iniciar tus propios servicios', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        if contratacion.estado != EstadoContratacion.confirmada:
            flash('Esta contratación no puede ser iniciada', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        try:
            # Iniciar servicio
            contratacion.iniciar_servicio()
            db.session.commit()
            
            flash('Servicio iniciado exitosamente', 'success')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al iniciar el servicio', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
    
    @staticmethod
    def completar_servicio(contratacion_id):
        """Completa el servicio (solo proveedores)"""
        if not ContratacionController._usuario_autenticado():
            return ContratacionController._acceso_no_autorizado()
        
        if session['user_rol'] != RolUsuario.proveedor.value:
            flash('Solo los proveedores pueden completar servicios', 'error')
            return redirect(url_for('index'))
        
        contratacion = Contratacion.query.get_or_404(contratacion_id)
        
        # Verificar permisos
        if contratacion.proveedor_id != session['user_id']:
            flash('Solo puedes completar tus propios servicios', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        if contratacion.estado != EstadoContratacion.en_progreso:
            flash('Esta contratación no puede ser completada', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        try:
            # Completar servicio
            contratacion.completar()
            db.session.commit()
            
            flash('Servicio completado exitosamente', 'success')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al completar el servicio', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
    
    @staticmethod
    def cancelar_contratacion(contratacion_id):
        """Cancela una contratación"""
        if not ContratacionController._usuario_autenticado():
            return ContratacionController._acceso_no_autorizado()
        
        contratacion = Contratacion.query.get_or_404(contratacion_id)
        
        # Verificar permisos
        if not ContratacionController._tiene_acceso_contratacion(contratacion):
            flash('No tienes permisos para cancelar esta contratación', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        if request.method == 'GET':
            return render_template('contrataciones/cancelar_contratacion.html', 
                                 contratacion=contratacion)
        
        motivo = request.form.get('motivo', '').strip()
        
        if not motivo:
            flash('Debes proporcionar un motivo para la cancelación', 'error')
            return render_template('contrataciones/cancelar_contratacion.html', 
                                 contratacion=contratacion)
        
        try:
            # Cancelar contratación
            contratacion.cancelar(motivo)
            db.session.commit()
            
            flash('Contratación cancelada exitosamente', 'success')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al cancelar la contratación', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
    
    @staticmethod
    def calificar_servicio(contratacion_id):
        """Califica un servicio completado"""
        if not ContratacionController._usuario_autenticado():
            return ContratacionController._acceso_no_autorizado()
        
        if session['user_rol'] != RolUsuario.organizador.value:
            flash('Solo los organizadores pueden calificar servicios', 'error')
            return redirect(url_for('index'))
        
        contratacion = Contratacion.query.get_or_404(contratacion_id)
        
        # Verificar permisos
        if contratacion.organizador_id != session['user_id']:
            flash('Solo puedes calificar tus propias contrataciones', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        if not contratacion.puede_calificar():
            flash('Esta contratación no puede ser calificada', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
        
        if request.method == 'GET':
            return render_template('contrataciones/calificar_servicio.html', 
                                 contratacion=contratacion)
        
        puntuacion = request.form.get('puntuacion', '').strip()
        comentario = request.form.get('comentario', '').strip()
        
        # Validaciones
        errores = []
        
        if not puntuacion:
            errores.append('La puntuación es obligatoria')
        else:
            try:
                puntuacion_int = int(puntuacion)
                if puntuacion_int < 1 or puntuacion_int > 5:
                    errores.append('La puntuación debe estar entre 1 y 5')
            except ValueError:
                errores.append('Formato de puntuación inválido')
        
        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('contrataciones/calificar_servicio.html', 
                                 contratacion=contratacion)
        
        try:
            # Crear calificación
            from models.calificacion import Calificacion
            calificacion = Calificacion(
                puntuacion=int(puntuacion),
                comentario=comentario,
                contratacion_id=contratacion_id,
                servicio_id=contratacion.servicio_id,
                organizador_id=session['user_id'],
                proveedor_id=contratacion.proveedor_id
            )
            
            db.session.add(calificacion)
            db.session.commit()
            
            # Crear notificación para el proveedor
            notificacion = NotificacionFactory.crear_notificacion_calificacion(
                contratacion.proveedor_id, 
                calificacion.id
            )
            sistema_notificaciones.notificar_observadores(notificacion)
            
            flash('Calificación enviada exitosamente', 'success')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al enviar la calificación', 'error')
            return redirect(url_for('contratacion.detalle_contratacion', 
                                 contratacion_id=contratacion_id))
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    @staticmethod
    def _usuario_autenticado():
        """Verifica si el usuario está autenticado"""
        return 'user_id' in session
    
    @staticmethod
    def _acceso_no_autorizado():
        """Redirige cuando el acceso no está autorizado"""
        flash('Debes iniciar sesión para acceder a esta página', 'error')
        return redirect(url_for('usuario.login'))
    
    @staticmethod
    def _tiene_acceso_contratacion(contratacion):
        """Verifica si el usuario tiene acceso a la contratación"""
        if not ContratacionController._usuario_autenticado():
            return False
        
        user_id = session['user_id']
        return (contratacion.organizador_id == user_id or 
                contratacion.proveedor_id == user_id)
