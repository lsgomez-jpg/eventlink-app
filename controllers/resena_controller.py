# controllers/resena_controller.py
"""
Controlador para gestión de reseñas
Principio SOLID: Single Responsibility - Responsabilidad única para reseñas
"""

from flask import render_template, redirect, url_for, flash, request, session, jsonify
from models.resena import Resena
from models.contratacion import Contratacion, EstadoContratacion
from models.servicio import Servicio
from models.usuario import Usuario
from database import db
from datetime import datetime

class ResenaController:
    
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
    def crear_resena(contratacion_id):
        """Muestra formulario para crear reseña (GET) o procesa la reseña (POST)"""
        if not ResenaController._usuario_autenticado():
            return ResenaController._acceso_no_autorizado()
        
        contratacion = Contratacion.query.get_or_404(contratacion_id)
        
        # Verificar que el usuario es el organizador de la contratación
        if session['user_id'] != contratacion.organizador_id:
            flash('No tienes permisos para reseñar esta contratación', 'error')
            return redirect(url_for('index'))
        
        # Verificar que la contratación está completada
        if contratacion.estado != EstadoContratacion.completada:
            flash('Solo puedes reseñar contrataciones completadas', 'error')
            return redirect(url_for('index'))
        
        # Verificar que no existe ya una reseña para esta contratación
        resena_existente = Resena.query.filter_by(contratacion_id=contratacion_id).first()
        if resena_existente:
            flash('Ya has reseñado esta contratación', 'error')
            return redirect(url_for('resena.ver_resena', resena_id=resena_existente.id))
        
        if request.method == 'POST':
            try:
                puntuacion = int(request.form.get('puntuacion'))
                comentario = request.form.get('comentario', '').strip()
                
                # Validar puntuación
                if puntuacion < 1 or puntuacion > 5:
                    flash('La puntuación debe estar entre 1 y 5 estrellas', 'error')
                    return render_template('resenas/crear_resena.html', contratacion=contratacion)
                
                # Crear reseña
                resena = Resena(
                    puntuacion=puntuacion,
                    comentario=comentario,
                    servicio_id=contratacion.servicio_id,
                    contratacion_id=contratacion_id,
                    organizador_id=session['user_id']
                )
                
                db.session.add(resena)
                db.session.commit()
                
                flash('¡Reseña creada exitosamente!', 'success')
                return redirect(url_for('resena.ver_resena', resena_id=resena.id))
                
            except ValueError:
                flash('La puntuación debe ser un número válido', 'error')
            except Exception as e:
                db.session.rollback()
                flash('Error al crear la reseña', 'error')
        
        return render_template('resenas/crear_resena.html', contratacion=contratacion)
    
    @staticmethod
    def ver_resena(resena_id):
        """Muestra el detalle de una reseña"""
        if not ResenaController._usuario_autenticado():
            return ResenaController._acceso_no_autorizado()
        
        resena = Resena.query.get_or_404(resena_id)
        
        # Verificar que el usuario puede ver esta reseña
        if (session['user_id'] != resena.organizador_id and 
            session['user_id'] != resena.servicio.proveedor_id):
            flash('No tienes permisos para ver esta reseña', 'error')
            return redirect(url_for('index'))
        
        return render_template('resenas/detalle_resena.html', resena=resena)
    
    @staticmethod
    def listar_resenas_servicio(servicio_id):
        """Lista todas las reseñas de un servicio"""
        servicio = Servicio.query.get_or_404(servicio_id)
        resenas = Resena.query.filter_by(servicio_id=servicio_id).order_by(Resena.fecha_creacion.desc()).all()
        
        return render_template('resenas/listar_resenas_servicio.html', 
                             servicio=servicio, resenas=resenas)
    
    @staticmethod
    def listar_resenas_proveedor():
        """Lista todas las reseñas de los servicios del proveedor"""
        if not ResenaController._usuario_autenticado():
            return ResenaController._acceso_no_autorizado()
        
        # Obtener servicios del proveedor
        servicios = Servicio.query.filter_by(proveedor_id=session['user_id']).all()
        servicio_ids = [s.id for s in servicios]
        
        # Obtener reseñas de esos servicios
        resenas = Resena.query.filter(Resena.servicio_id.in_(servicio_ids)).order_by(Resena.fecha_creacion.desc()).all()
        
        return render_template('resenas/listar_resenas_proveedor.html', resenas=resenas)
    
    @staticmethod
    def editar_resena(resena_id):
        """Muestra formulario para editar reseña (GET) o procesa la edición (POST)"""
        if not ResenaController._usuario_autenticado():
            return ResenaController._acceso_no_autorizado()
        
        resena = Resena.query.get_or_404(resena_id)
        
        # Verificar que el usuario es el organizador que creó la reseña
        if session['user_id'] != resena.organizador_id:
            flash('No tienes permisos para editar esta reseña', 'error')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            try:
                puntuacion = int(request.form.get('puntuacion'))
                comentario = request.form.get('comentario', '').strip()
                
                # Validar puntuación
                if puntuacion < 1 or puntuacion > 5:
                    flash('La puntuación debe estar entre 1 y 5 estrellas', 'error')
                    return render_template('resenas/editar_resena.html', resena=resena)
                
                # Actualizar reseña
                resena.puntuacion = puntuacion
                resena.comentario = comentario
                resena.fecha_actualizacion = datetime.utcnow()
                
                db.session.commit()
                
                flash('¡Reseña actualizada exitosamente!', 'success')
                return redirect(url_for('resena.ver_resena', resena_id=resena.id))
                
            except ValueError:
                flash('La puntuación debe ser un número válido', 'error')
            except Exception as e:
                db.session.rollback()
                flash('Error al actualizar la reseña', 'error')
        
        return render_template('resenas/editar_resena.html', resena=resena)
    
    @staticmethod
    def eliminar_resena(resena_id):
        """Elimina una reseña"""
        if not ResenaController._usuario_autenticado():
            return ResenaController._acceso_no_autorizado()
        
        resena = Resena.query.get_or_404(resena_id)
        
        # Verificar que el usuario es el organizador que creó la reseña
        if session['user_id'] != resena.organizador_id:
            flash('No tienes permisos para eliminar esta reseña', 'error')
            return redirect(url_for('index'))
        
        try:
            db.session.delete(resena)
            db.session.commit()
            flash('Reseña eliminada exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al eliminar la reseña', 'error')
        
        return redirect(url_for('usuario.perfil'))
