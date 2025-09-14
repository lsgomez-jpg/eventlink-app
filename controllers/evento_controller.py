# controllers/evento_controller.py
"""
Controlador para gestión de eventos
Principio SOLID: Single Responsibility - Responsabilidad única para eventos
"""

from flask import request, session, flash, redirect, url_for, render_template, jsonify
from models.evento import Evento, EstadoEvento, TipoEvento
from models.usuario import Usuario, RolUsuario
from models.contratacion import Contratacion, EstadoContratacion
from database import db
from datetime import datetime, timedelta
# from patterns.observer import sistema_notificaciones
# from patterns.factory import NotificacionFactory
import re
import os
import json
from werkzeug.utils import secure_filename

class EventoController:
    
    # Configuración para subida de archivos
    UPLOAD_FOLDER = 'views/static/uploads/eventos'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    @staticmethod
    def allowed_file(filename):
        """Verifica si el archivo tiene una extensión permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in EventoController.ALLOWED_EXTENSIONS
    
    @staticmethod
    def save_image(file, folder_name):
        """Guarda una imagen y retorna la ruta relativa"""
        if file and file.filename and EventoController.allowed_file(file.filename):
            try:
                # Crear directorio si no existe
                upload_path = os.path.join(EventoController.UPLOAD_FOLDER, folder_name)
                os.makedirs(upload_path, exist_ok=True)
                
                # Generar nombre único para el archivo
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                name, ext = os.path.splitext(filename)
                unique_filename = f"{name}_{timestamp}{ext}"
                
                # Guardar archivo
                file_path = os.path.join(upload_path, unique_filename)
                file.save(file_path)
                
                # Retornar ruta relativa para la base de datos
                return f"uploads/eventos/{folder_name}/{unique_filename}"
            except Exception as e:
                print(f"Error al guardar imagen: {str(e)}")
                return None
        return None
    
    @staticmethod
    def save_multiple_images(files, folder_name):
        """Guarda múltiples imágenes y retorna lista de rutas"""
        image_paths = []
        if files:
            for file in files:
                if file and EventoController.allowed_file(file.filename):
                    path = EventoController.save_image(file, folder_name)
                    if path:
                        image_paths.append(path)
        return image_paths
    
    @staticmethod
    def crear_evento():
        """Crea un nuevo evento"""
        if not EventoController._usuario_autenticado():
            return EventoController._acceso_no_autorizado()
        
        if session['user_rol'] != 'organizador':
            flash('Solo los organizadores pueden crear eventos', 'error')
            return redirect(url_for('index'))
        
        if request.method == 'GET':
            return render_template('eventos/crear_evento.html', tipos_evento=TipoEvento)
        
        # Obtener datos del formulario
        datos = EventoController._obtener_datos_formulario()
        errores = EventoController._validar_datos_evento(datos)
        
        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('eventos/crear_evento.html', tipos_evento=TipoEvento, datos=datos)
        
        try:
            # Procesar fechas
            fecha_inicio = datetime.strptime(datos['fecha_inicio'], '%Y-%m-%dT%H:%M')
            fecha_fin = datetime.strptime(datos['fecha_fin'], '%Y-%m-%dT%H:%M')
            
            # Procesar tipo de evento
            tipo_evento = TipoEvento(datos['tipo'])
            
            # Procesar presupuesto y número de invitados
            presupuesto = None
            if datos.get('presupuesto_maximo'):
                presupuesto = float(datos['presupuesto_maximo'])
            
            numero_invitados = None
            if datos.get('numero_invitados'):
                numero_invitados = int(datos['numero_invitados'])
            
            # Crear nuevo evento
            nuevo_evento = Evento(
                titulo=datos['titulo'],
                tipo=tipo_evento,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                ubicacion=datos['ubicacion'],
                ciudad=datos['ciudad'],
                organizador_id=session['user_id'],
                descripcion=datos.get('descripcion'),
                direccion=datos.get('direccion'),
                presupuesto_maximo=presupuesto,
                numero_invitados=numero_invitados,
                estado=EstadoEvento.activo  # Establecer estado como activo
            )
            
            db.session.add(nuevo_evento)
            db.session.flush()  # Para obtener el ID del evento
            
            # Manejar imágenes
            folder_name = f"evento_{nuevo_evento.id}"
            
            # Imagen principal
            if 'imagen_principal' in request.files:
                imagen_principal = request.files['imagen_principal']
                if imagen_principal and imagen_principal.filename:
                    nuevo_evento.imagen_principal = EventoController.save_image(imagen_principal, folder_name)
            
            # Imagen secundaria
            if 'imagen_secundaria' in request.files:
                imagen_secundaria = request.files['imagen_secundaria']
                if imagen_secundaria and imagen_secundaria.filename:
                    nuevo_evento.imagen_secundaria = EventoController.save_image(imagen_secundaria, folder_name)
            
            # Galería de imágenes
            if 'galeria_imagenes' in request.files:
                galeria_files = request.files.getlist('galeria_imagenes')
                if galeria_files and any(f.filename for f in galeria_files):
                    galeria_paths = EventoController.save_multiple_images(galeria_files, folder_name)
                    if galeria_paths:
                        nuevo_evento.galeria_imagenes = json.dumps(galeria_paths)
            
            db.session.commit()
            
            # Crear notificación (comentado por ahora)
            # notificacion = NotificacionFactory.crear_notificacion_bienvenida(
            #     session['user_id'], 
            #     'organizador'
            # )
            # sistema_notificaciones.notificar_observadores(notificacion)
            
            flash('¡Evento creado exitosamente!', 'success')
            return redirect(url_for('evento.detalle_evento', evento_id=nuevo_evento.id))
            
        except ValueError as e:
            db.session.rollback()
            flash(f'Error en los datos del formulario: {str(e)}', 'error')
            return render_template('eventos/crear_evento.html', tipos_evento=TipoEvento, datos=datos)
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear evento: {str(e)}")  # Para debugging
            flash('Error al crear el evento. Verifica que todos los campos estén correctos.', 'error')
            return render_template('eventos/crear_evento.html', tipos_evento=TipoEvento, datos=datos)
    
    @staticmethod
    def listar_eventos():
        """Lista los eventos del usuario"""
        if not EventoController._usuario_autenticado():
            return EventoController._acceso_no_autorizado()
        
        user_id = session['user_id']
        user_rol = session['user_rol']
        
        # Obtener eventos según el rol
        if user_rol == 'organizador':
            eventos = Evento.query.filter_by(organizador_id=user_id).order_by(Evento.fecha_creacion.desc()).all()
        else:
            # Para proveedores, mostrar eventos donde han sido contratados
            eventos = Evento.query.join(Contratacion).filter(
                Contratacion.proveedor_id == user_id
            ).order_by(Evento.fecha_inicio.desc()).all()
        
        return render_template('eventos/listar_eventos.html', eventos=eventos)
    
    @staticmethod
    def detalle_evento(evento_id):
        """Muestra el detalle de un evento"""
        if not EventoController._usuario_autenticado():
            return EventoController._acceso_no_autorizado()
        
        evento = Evento.query.get_or_404(evento_id)
        
        # Verificar permisos
        if not EventoController._tiene_acceso_evento(evento):
            flash('No tienes permisos para ver este evento', 'error')
            return redirect(url_for('evento.listar_eventos'))
        
        # Obtener contrataciones del evento
        contrataciones = Contratacion.query.filter_by(evento_id=evento_id).all()
        
        return render_template('eventos/detalle_evento.html', 
                             evento=evento, 
                             contrataciones=contrataciones)
    
    @staticmethod
    def editar_evento(evento_id):
        """Edita un evento existente"""
        if not EventoController._usuario_autenticado():
            return EventoController._acceso_no_autorizado()
        
        evento = Evento.query.get_or_404(evento_id)
        
        # Verificar permisos
        if not EventoController._es_organizador_evento(evento):
            flash('Solo el organizador puede editar este evento', 'error')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
        
        if request.method == 'GET':
            return render_template('eventos/editar_evento.html', 
                                 evento=evento, 
                                 tipos_evento=TipoEvento)
        
        # Obtener datos del formulario
        datos = EventoController._obtener_datos_formulario()
        errores = EventoController._validar_datos_evento(datos, evento_id)
        
        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('eventos/editar_evento.html', 
                                 evento=evento, 
                                 tipos_evento=TipoEvento, 
                                 datos=datos)
        
        try:
            # Actualizar evento
            evento.titulo = datos['titulo']
            evento.tipo = datos['tipo']
            evento.fecha_inicio = datos['fecha_inicio']
            evento.fecha_fin = datos['fecha_fin']
            evento.ubicacion = datos['ubicacion']
            evento.ciudad = datos['ciudad']
            evento.descripcion = datos.get('descripcion')
            evento.direccion = datos.get('direccion')
            evento.presupuesto_maximo = datos.get('presupuesto_maximo')
            evento.numero_invitados = datos.get('numero_invitados')
            evento.fecha_actualizacion = datetime.utcnow()
            
            db.session.commit()
            
            flash('Evento actualizado exitosamente', 'success')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el evento', 'error')
            return render_template('eventos/editar_evento.html', 
                                 evento=evento, 
                                 tipos_evento=TipoEvento, 
                                 datos=datos)
    
    @staticmethod
    def activar_evento(evento_id):
        """Activa un evento para que sea visible a proveedores"""
        if not EventoController._usuario_autenticado():
            return EventoController._acceso_no_autorizado()
        
        evento = Evento.query.get_or_404(evento_id)
        
        # Verificar permisos
        if not EventoController._es_organizador_evento(evento):
            flash('Solo el organizador puede activar este evento', 'error')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
        
        try:
            evento.activar()
            db.session.commit()
            
            flash('Evento activado exitosamente', 'success')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al activar el evento', 'error')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
    
    @staticmethod
    def cancelar_evento(evento_id):
        """Cancela un evento"""
        if not EventoController._usuario_autenticado():
            return EventoController._acceso_no_autorizado()
        
        evento = Evento.query.get_or_404(evento_id)
        
        # Verificar permisos
        if not EventoController._es_organizador_evento(evento):
            flash('Solo el organizador puede cancelar este evento', 'error')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
        
        motivo = request.form.get('motivo', 'Sin motivo especificado')
        
        try:
            evento.cancelar()
            
            # Cancelar contrataciones activas
            contrataciones = Contratacion.query.filter_by(
                evento_id=evento_id,
                estado='aceptada'
            ).all()
            
            for contratacion in contrataciones:
                contratacion.cancelar(f"Evento cancelado: {motivo}")
            
            db.session.commit()
            
            flash('Evento cancelado exitosamente', 'success')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al cancelar el evento', 'error')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
    
    @staticmethod
    def completar_evento(evento_id):
        """Marca un evento como completado (solo organizadores, cuando el evento está en curso)"""
        if not EventoController._usuario_autenticado():
            return EventoController._acceso_no_autorizado()
        
        evento = Evento.query.get_or_404(evento_id)
        
        # Verificar permisos
        if not EventoController._es_organizador_evento(evento):
            flash('Solo el organizador puede completar este evento', 'error')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
        
        try:
            # Verificar que el evento esté en curso
            if evento.estado != EstadoEvento.en_curso:
                flash('El evento debe estar en curso para poder completarlo', 'error')
                return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
            
            # Completar el evento
            evento.completar()
            
            # Completar todas las contrataciones asociadas
            contrataciones = Contratacion.query.filter_by(
                evento_id=evento_id,
                estado=EstadoContratacion.en_progreso
            ).all()
            
            for contratacion in contrataciones:
                contratacion.completar()
            
            db.session.commit()
            flash('Evento completado exitosamente. Ahora puedes calificar los servicios.', 'success')
            
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al completar el evento', 'error')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
    
    @staticmethod
    def finalizar_evento(evento_id):
        """Finaliza un evento (solo proveedores que tienen contrataciones en el evento)"""
        if not EventoController._usuario_autenticado():
            return EventoController._acceso_no_autorizado()
        
        if session['user_rol'] != 'proveedor':
            flash('Solo los proveedores pueden finalizar eventos', 'error')
            return redirect(url_for('index'))
        
        evento = Evento.query.get_or_404(evento_id)
        
        # Verificar que el proveedor tenga contrataciones en este evento
        contrataciones_proveedor = Contratacion.query.filter_by(
            evento_id=evento_id,
            proveedor_id=session['user_id']
        ).first()
        
        if not contrataciones_proveedor:
            flash('No tienes contrataciones en este evento', 'error')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
        
        try:
            # Verificar que el evento esté en curso
            if evento.estado != EstadoEvento.en_curso:
                flash('El evento debe estar en curso para poder finalizarlo', 'error')
                return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
            
            # Finalizar el evento
            evento.completar()
            
            # Completar todas las contrataciones del proveedor en este evento
            contrataciones = Contratacion.query.filter_by(
                evento_id=evento_id,
                proveedor_id=session['user_id'],
                estado=EstadoContratacion.en_progreso
            ).all()
            
            for contratacion in contrataciones:
                contratacion.completar()
            
            db.session.commit()
            flash('Evento finalizado exitosamente. El organizador ahora puede calificar tu servicio.', 'success')
            
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al finalizar el evento', 'error')
            return redirect(url_for('evento.detalle_evento', evento_id=evento_id))
    
    @staticmethod
    def buscar_eventos():
        """Busca eventos públicos (para proveedores)"""
        if not EventoController._usuario_autenticado():
            return EventoController._acceso_no_autorizado()
        
        if session['user_rol'] != 'proveedor':
            flash('Solo los proveedores pueden buscar eventos', 'error')
            return redirect(url_for('index'))
        
        # Obtener parámetros de búsqueda
        ciudad = request.args.get('ciudad', '').strip()
        tipo = request.args.get('tipo', '').strip()
        fecha_desde = request.args.get('fecha_desde', '').strip()
        fecha_hasta = request.args.get('fecha_hasta', '').strip()
        
        # Construir consulta
        consulta = Evento.query.filter_by(estado=EstadoEvento.activo)
        
        if ciudad:
            consulta = consulta.filter(Evento.ciudad.ilike(f'%{ciudad}%'))
        
        if tipo:
            consulta = consulta.filter(Evento.tipo == TipoEvento(tipo))
        
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
                consulta = consulta.filter(Evento.fecha_inicio >= fecha_desde_dt)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                consulta = consulta.filter(Evento.fecha_inicio <= fecha_hasta_dt)
            except ValueError:
                pass
        
        eventos = consulta.order_by(Evento.fecha_inicio.asc()).all()
        
        return render_template('eventos/buscar_eventos.html', 
                             eventos=eventos,
                             tipos_evento=TipoEvento,
                             filtros={
                                 'ciudad': ciudad,
                                 'tipo': tipo,
                                 'fecha_desde': fecha_desde,
                                 'fecha_hasta': fecha_hasta
                             })
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    @staticmethod
    def _obtener_datos_formulario():
        """Obtiene y procesa los datos del formulario"""
        return {
            'titulo': request.form.get('titulo', '').strip(),
            'descripcion': request.form.get('descripcion', '').strip(),
            'tipo': request.form.get('tipo', '').strip(),
            'fecha_inicio': request.form.get('fecha_inicio', '').strip(),
            'fecha_fin': request.form.get('fecha_fin', '').strip(),
            'ubicacion': request.form.get('ubicacion', '').strip(),
            'direccion': request.form.get('direccion', '').strip(),
            'ciudad': request.form.get('ciudad', '').strip(),
            'presupuesto_maximo': request.form.get('presupuesto_maximo', '').strip(),
            'numero_invitados': request.form.get('numero_invitados', '').strip()
        }
    
    @staticmethod
    def _validar_datos_evento(datos, evento_id=None):
        """Valida los datos del evento"""
        errores = []
        
        # Validar título
        if not datos['titulo'] or len(datos['titulo']) < 3:
            errores.append('El título debe tener al menos 3 caracteres')
        
        # Validar tipo
        try:
            if datos['tipo']:
                TipoEvento(datos['tipo'])
        except ValueError:
            errores.append('Tipo de evento no válido')
        
        # Validar fechas
        try:
            if datos['fecha_inicio']:
                fecha_inicio = datetime.strptime(datos['fecha_inicio'], '%Y-%m-%dT%H:%M')
                if fecha_inicio <= datetime.now():
                    errores.append('La fecha de inicio debe ser futura')
            else:
                errores.append('La fecha de inicio es obligatoria')
        except ValueError:
            errores.append('Formato de fecha de inicio inválido')
        
        try:
            if datos['fecha_fin']:
                fecha_fin = datetime.strptime(datos['fecha_fin'], '%Y-%m-%dT%H:%M')
                if datos['fecha_inicio']:
                    fecha_inicio = datetime.strptime(datos['fecha_inicio'], '%Y-%m-%dT%H:%M')
                    if fecha_fin <= fecha_inicio:
                        errores.append('La fecha de fin debe ser posterior a la fecha de inicio')
            else:
                errores.append('La fecha de fin es obligatoria')
        except ValueError:
            errores.append('Formato de fecha de fin inválido')
        
        # Validar ubicación
        if not datos['ubicacion'] or len(datos['ubicacion']) < 3:
            errores.append('La ubicación debe tener al menos 3 caracteres')
        
        # Validar ciudad
        if not datos['ciudad'] or len(datos['ciudad']) < 2:
            errores.append('La ciudad debe tener al menos 2 caracteres')
        
        # Validar presupuesto (opcional)
        if datos['presupuesto_maximo']:
            try:
                presupuesto = float(datos['presupuesto_maximo'])
                if presupuesto < 0:
                    errores.append('El presupuesto no puede ser negativo')
            except ValueError:
                errores.append('Formato de presupuesto inválido')
        
        # Validar número de invitados (opcional)
        if datos['numero_invitados']:
            try:
                invitados = int(datos['numero_invitados'])
                if invitados < 1:
                    errores.append('El número de invitados debe ser mayor a 0')
            except ValueError:
                errores.append('Formato de número de invitados inválido')
        
        return errores
    
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
    def _es_organizador_evento(evento):
        """Verifica si el usuario es el organizador del evento"""
        return (EventoController._usuario_autenticado() and 
                session['user_id'] == evento.organizador_id)
    
    @staticmethod
    def _tiene_acceso_evento(evento):
        """Verifica si el usuario tiene acceso al evento"""
        if not EventoController._usuario_autenticado():
            return False
        
        # El organizador siempre tiene acceso
        if EventoController._es_organizador_evento(evento):
            return True
        
        # Los proveedores tienen acceso si están contratados
        if session['user_rol'] == 'proveedor':
            contratacion = Contratacion.query.filter_by(
                evento_id=evento.id,
                proveedor_id=session['user_id']
            ).first()
            return contratacion is not None
        
        return False
