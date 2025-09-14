# controllers/servicio_controller.py
"""
Controlador para gestión de servicios
Principio SOLID: Single Responsibility - Responsabilidad única para servicios
"""

from flask import request, session, flash, redirect, url_for, render_template, jsonify
from models.servicio import Servicio, CategoriaServicio, EstadoServicio
from models.usuario import Usuario, RolUsuario
from models.contratacion import Contratacion
from models.evento import Evento
from database import db
from datetime import datetime
# from patterns.factory import ServicioFactoryManager
# from patterns.observer import sistema_notificaciones
# from patterns.strategy import busqueda_manager
import re

class ServicioController:
    
    @staticmethod
    def _manejar_error_db():
        """Maneja errores de base de datos haciendo rollback"""
        try:
            db.session.rollback()
        except Exception:
            pass
    
    @staticmethod
    def crear_servicio():
        """Crea un nuevo servicio"""
        if not ServicioController._usuario_autenticado():
            return ServicioController._acceso_no_autorizado()
        
        if session['user_rol'] != 'proveedor':
            flash('Solo los proveedores pueden crear servicios', 'error')
            return redirect(url_for('index'))
        
        if request.method == 'GET':
            return render_template('servicios/crear_servicio.html', 
                                 categorias=CategoriaServicio)
        
        # Obtener datos del formulario
        datos = ServicioController._obtener_datos_formulario()
        errores = ServicioController._validar_datos_servicio(datos)
        
        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('servicios/crear_servicio.html', 
                                 categorias=CategoriaServicio, 
                                 datos=datos)
        
        try:
            # Crear servicio directamente (sin factory por ahora)
            nuevo_servicio = Servicio(
                nombre=datos['nombre'],
                descripcion=datos['descripcion'],
                categoria=CategoriaServicio(datos['categoria']),
                precio_base=float(datos['precio_base']),
                ciudad=datos['ciudad'],
                proveedor_id=session['user_id'],
                precio_por_hora=float(datos['precio_por_hora']) if datos['precio_por_hora'] else None,
                precio_por_persona=float(datos['precio_por_persona']) if datos['precio_por_persona'] else None,
                duracion_minima=int(datos['duracion_minima']) if datos['duracion_minima'] else None,
                duracion_maxima=int(datos['duracion_maxima']) if datos['duracion_maxima'] else None,
                capacidad_maxima=int(datos['capacidad_maxima']) if datos['capacidad_maxima'] else None,
                incluye_materiales=datos['incluye_materiales'],
                incluye_transporte=datos['incluye_transporte'],
                incluye_montaje=datos['incluye_montaje'],
                incluye_desmontaje=datos['incluye_desmontaje'],
                requiere_deposito=datos['requiere_deposito'],
                porcentaje_deposito=float(datos['porcentaje_deposito']) if datos['porcentaje_deposito'] else None,
                radio_cobertura=int(datos['radio_cobertura']) if datos['radio_cobertura'] else 50
            )
            
            db.session.add(nuevo_servicio)
            db.session.commit()
            
            flash('¡Servicio creado exitosamente!', 'success')
            return redirect(url_for('servicio.listar_servicios'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el servicio. Intenta nuevamente.', 'error')
            return render_template('servicios/crear_servicio.html', 
                                 categorias=CategoriaServicio, 
                                 datos=datos)
    
    @staticmethod
    def listar_servicios():
        """Lista los servicios del proveedor (solo para proveedores)"""
        if not ServicioController._usuario_autenticado():
            return ServicioController._acceso_no_autorizado()
        
        if session['user_rol'] != 'proveedor':
            flash('Solo los proveedores pueden ver sus servicios', 'error')
            return redirect(url_for('index'))
        
        servicios = Servicio.query.filter_by(proveedor_id=session['user_id']).order_by(
            Servicio.fecha_creacion.desc()
        ).all()
        
        return render_template('servicios/listar_servicios.html', servicios=servicios)
    
    @staticmethod
    def catalogo_servicios():
        """Muestra el catálogo de servicios disponibles para todos los usuarios"""
        if not ServicioController._usuario_autenticado():
            return ServicioController._acceso_no_autorizado()
        
        # CURSOR IA: Lógica diferenciada por rol
        if session['user_rol'] == 'proveedor':
            # El proveedor ve solo sus servicios
            servicios = Servicio.query.filter_by(proveedor_id=session['user_id']).order_by(
                Servicio.fecha_creacion.desc()
            ).all()
        else:
            # El organizador ve todos los servicios activos
            servicios = Servicio.query.filter_by(estado=EstadoServicio.disponible).order_by(
                Servicio.fecha_creacion.desc()
            ).all()
        
        # Obtener categorías para filtros
        categorias = list(CategoriaServicio)
        
        # CURSOR IA: Determinar si el usuario es organizador para mostrar botones de agregar al carrito
        es_organizador = session.get('user_rol') == 'organizador'
        
        return render_template('servicios/catalogo_servicios.html', 
                             servicios=servicios, 
                             categorias=categorias,
                             es_organizador=es_organizador)
    
    @staticmethod
    def detalle_servicio(servicio_id):
        """Muestra el detalle de un servicio"""
        servicio = Servicio.query.get_or_404(servicio_id)
        
        # CURSOR IA: Verificar permisos para edición (solo proveedores)
        puede_editar = (ServicioController._usuario_autenticado() and 
                       session['user_rol'] == 'proveedor' and
                       session['user_id'] == servicio.proveedor_id)
        
        # CURSOR IA: Verificar si el usuario puede agregar al carrito (solo organizadores)
        puede_agregar_carrito = (ServicioController._usuario_autenticado() and 
                                session['user_rol'] == 'organizador')
        
        # Obtener contrataciones del servicio (solo para proveedores)
        contrataciones = []
        if puede_editar:
            contrataciones = Contratacion.query.filter_by(servicio_id=servicio_id).all()
        
        # CURSOR IA: Obtener eventos del organizador si puede agregar al carrito
        eventos = []
        if puede_agregar_carrito:
            from models.evento import Evento
            eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
        
        return render_template('servicios/detalle_servicio.html', 
                             servicio=servicio, 
                             contrataciones=contrataciones,
                             puede_editar=puede_editar,
                             puede_agregar_carrito=puede_agregar_carrito,
                             eventos=eventos)
    
    @staticmethod
    def agregar_al_carrito_desde_detalle(servicio_id):
        """Agrega un servicio al carrito y redirige directamente a MercadoPago"""
        if not ServicioController._usuario_autenticado():
            return ServicioController._acceso_no_autorizado()
        
        if session['user_rol'] != 'organizador':
            flash('Solo los organizadores pueden agregar servicios al carrito', 'error')
            return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
        
        servicio = Servicio.query.get_or_404(servicio_id)
        
        if request.method == 'GET':
            # Obtener eventos del organizador
            from models.evento import Evento
            eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
            return render_template('servicios/agregar_al_carrito.html', 
                                 servicio=servicio, eventos=eventos)
        
        # Obtener datos del formulario
        evento_id = request.form.get('evento_id', '').strip()
        fecha_evento = request.form.get('fecha_evento', '').strip()
        duracion_horas = request.form.get('duracion_horas', '').strip()
        numero_personas = request.form.get('numero_personas', '').strip()
        ubicacion = request.form.get('ubicacion', '').strip()
        notas_especiales = request.form.get('notas_especiales', '').strip()
        
        # Validaciones
        errores = []
        
        if not evento_id:
            errores.append('Debes seleccionar un evento')
        
        if not fecha_evento:
            errores.append('La fecha del servicio es obligatoria')
        
        if not duracion_horas:
            errores.append('La duración es obligatoria')
        
        if not ubicacion:
            errores.append('La ubicación es obligatoria')
        
        if errores:
            for error in errores:
                flash(error, 'error')
            from models.evento import Evento
            eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
            return render_template('servicios/agregar_al_carrito.html', 
                                 servicio=servicio, eventos=eventos)
        
        try:
            # Verificar que el evento pertenece al organizador
            from models.evento import Evento
            evento = Evento.query.filter_by(
                id=evento_id, 
                organizador_id=session['user_id']
            ).first()
            
            if not evento:
                flash('El evento seleccionado no es válido', 'error')
                return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
            
            # Crear item del carrito
            from controllers.carrito_controller import CarritoController
            resultado = CarritoController.agregar_al_carrito_desde_detalle(
                servicio_id, evento_id, fecha_evento, duracion_horas, 
                numero_personas, ubicacion, notas_especiales
            )
            
            # Si se agregó correctamente, redirigir al carrito para agregar más servicios
            if hasattr(resultado, 'status_code') and resultado.status_code == 302:
                # Redirigir al carrito para que pueda agregar más servicios
                return redirect(url_for('carrito.ver_carrito'))
            
            return resultado
            
        except Exception as e:
            flash(f'Error al agregar el servicio al carrito: {str(e)}', 'error')
            from models.evento import Evento
            eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
            return render_template('servicios/agregar_al_carrito.html', 
                                 servicio=servicio, eventos=eventos)
    
    @staticmethod
    def obtener_datos_evento(evento_id):
        """API para obtener datos del evento para autocompletado"""
        if not ServicioController._usuario_autenticado():
            return jsonify({'error': 'No autorizado'}), 401
        
        if session['user_rol'] != 'organizador':
            return jsonify({'error': 'Solo organizadores pueden acceder'}), 403
        
        try:
            from models.evento import Evento
            evento = Evento.query.filter_by(
                id=evento_id, 
                organizador_id=session['user_id']
            ).first()
            
            if not evento:
                return jsonify({'error': 'Evento no encontrado'}), 404
            
            return jsonify({
                'fecha_inicio': evento.fecha_inicio.strftime('%Y-%m-%dT%H:%M') if evento.fecha_inicio else '',
                'fecha_fin': evento.fecha_fin.strftime('%Y-%m-%dT%H:%M') if evento.fecha_fin else '',
                'numero_invitados': evento.numero_invitados or '',
                'ubicacion': evento.ubicacion or '',
                'direccion': evento.direccion or ''
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    def editar_servicio(servicio_id):
        """Edita un servicio existente"""
        if not ServicioController._usuario_autenticado():
            return ServicioController._acceso_no_autorizado()
        
        servicio = Servicio.query.get_or_404(servicio_id)
        
        # Verificar permisos
        if not ServicioController._es_propietario_servicio(servicio):
            flash('Solo puedes editar tus propios servicios', 'error')
            return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
        
        if request.method == 'GET':
            return render_template('servicios/editar_servicio.html', 
                                 servicio=servicio, 
                                 categorias=CategoriaServicio)
        
        # Obtener datos del formulario
        datos = ServicioController._obtener_datos_formulario()
        errores = ServicioController._validar_datos_servicio(datos, servicio_id)
        
        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('servicios/editar_servicio.html', 
                                 servicio=servicio, 
                                 categorias=CategoriaServicio, 
                                 datos=datos)
        
        try:
            # CURSOR IA: Actualizar servicio con conversión correcta de tipos
            servicio.nombre = datos['nombre']
            servicio.descripcion = datos['descripcion']
            servicio.categoria = CategoriaServicio(datos['categoria'])
            servicio.precio_base = float(datos['precio_base'])
            servicio.precio_por_hora = float(datos['precio_por_hora']) if datos.get('precio_por_hora') else None
            servicio.precio_por_persona = float(datos['precio_por_persona']) if datos.get('precio_por_persona') else None
            servicio.duracion_minima = int(datos['duracion_minima']) if datos.get('duracion_minima') else None
            servicio.duracion_maxima = int(datos['duracion_maxima']) if datos.get('duracion_maxima') else None
            servicio.capacidad_maxima = int(datos['capacidad_maxima']) if datos.get('capacidad_maxima') else None
            servicio.incluye_materiales = datos.get('incluye_materiales', False)
            servicio.incluye_transporte = datos.get('incluye_transporte', False)
            servicio.incluye_montaje = datos.get('incluye_montaje', False)
            servicio.incluye_desmontaje = datos.get('incluye_desmontaje', False)
            servicio.requiere_deposito = datos.get('requiere_deposito', False)
            servicio.porcentaje_deposito = float(datos['porcentaje_deposito']) if datos.get('porcentaje_deposito') else None
            servicio.ciudad = datos['ciudad']
            servicio.radio_cobertura = int(datos['radio_cobertura']) if datos.get('radio_cobertura') else 50
            servicio.fecha_actualizacion = datetime.utcnow()
            
            db.session.commit()
            
            flash('Servicio actualizado exitosamente', 'success')
            return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el servicio', 'error')
            return render_template('servicios/editar_servicio.html', 
                                 servicio=servicio, 
                                 categorias=CategoriaServicio, 
                                 datos=datos)
    
    @staticmethod
    def activar_servicio(servicio_id):
        """Activa un servicio"""
        if not ServicioController._usuario_autenticado():
            return ServicioController._acceso_no_autorizado()
        
        servicio = Servicio.query.get_or_404(servicio_id)
        
        # Verificar permisos
        if not ServicioController._es_propietario_servicio(servicio):
            flash('Solo puedes activar tus propios servicios', 'error')
            return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
        
        try:
            servicio.activar()
            db.session.commit()
            
            flash('Servicio activado exitosamente', 'success')
            return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al activar el servicio', 'error')
            return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
    
    @staticmethod
    def desactivar_servicio(servicio_id):
        """Desactiva un servicio"""
        if not ServicioController._usuario_autenticado():
            return ServicioController._acceso_no_autorizado()
        
        servicio = Servicio.query.get_or_404(servicio_id)
        
        # Verificar permisos
        if not ServicioController._es_propietario_servicio(servicio):
            flash('Solo puedes desactivar tus propios servicios', 'error')
            return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
        
        try:
            servicio.desactivar()
            db.session.commit()
            
            flash('Servicio desactivado exitosamente', 'success')
            return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al desactivar el servicio', 'error')
            return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
    
    @staticmethod
    def buscar_servicios():
        """Busca servicios disponibles"""
        if not ServicioController._usuario_autenticado():
            return ServicioController._acceso_no_autorizado()
        
        # CURSOR IA: Permitir búsqueda a todos los usuarios autenticados
        # Los filtros se aplicarán según el rol del usuario
        
        # Obtener parámetros de búsqueda
        query_params = {
            'categoria': request.args.get('categoria', '').strip(),
            'ciudad': request.args.get('ciudad', '').strip(),
            'precio_min': request.args.get('precio_min', '').strip(),
            'precio_max': request.args.get('precio_max', '').strip(),
            'calificacion_min': request.args.get('calificacion_min', '').strip(),
            'radio_km': request.args.get('radio_km', '').strip(),
            'fecha_evento': request.args.get('fecha_evento', '').strip(),
            'duracion_horas': request.args.get('duracion_horas', '').strip(),
            'numero_personas': request.args.get('numero_personas', '').strip()
        }
        
        # Limpiar parámetros vacíos
        query_params = {k: v for k, v in query_params.items() if v}
        
        # Convertir tipos de datos
        if 'precio_min' in query_params:
            try:
                query_params['precio_min'] = float(query_params['precio_min'])
            except ValueError:
                query_params.pop('precio_min')
        
        if 'precio_max' in query_params:
            try:
                query_params['precio_max'] = float(query_params['precio_max'])
            except ValueError:
                query_params.pop('precio_max')
        
        if 'calificacion_min' in query_params:
            try:
                query_params['calificacion_min'] = float(query_params['calificacion_min'])
            except ValueError:
                query_params.pop('calificacion_min')
        
        if 'radio_km' in query_params:
            try:
                query_params['radio_km'] = int(query_params['radio_km'])
            except ValueError:
                query_params.pop('radio_km')
        
        if 'duracion_horas' in query_params:
            try:
                query_params['duracion_horas'] = int(query_params['duracion_horas'])
            except ValueError:
                query_params.pop('duracion_horas')
        
        if 'numero_personas' in query_params:
            try:
                query_params['numero_personas'] = int(query_params['numero_personas'])
            except ValueError:
                query_params.pop('numero_personas')
        
        # Determinar estrategia de búsqueda
        tipo_busqueda = request.args.get('tipo_busqueda', 'combinada')
        
        try:
            # CURSOR IA: Búsqueda diferenciada por rol
            if session['user_rol'] == 'proveedor':
                # El proveedor ve solo sus servicios
                servicios = Servicio.query.filter_by(proveedor_id=session['user_id']).order_by(
                    Servicio.fecha_creacion.desc()
                ).all()
            else:
                # El organizador ve todos los servicios disponibles
                servicios = Servicio.query.filter_by(estado=EstadoServicio.disponible).order_by(
                    Servicio.fecha_creacion.desc()
                ).all()
            
            # Aplicar filtros básicos
            if 'categoria' in query_params:
                servicios = [s for s in servicios if s.categoria.value == query_params['categoria']]
            if 'ciudad' in query_params:
                servicios = [s for s in servicios if query_params['ciudad'].lower() in s.ciudad.lower()]
            if 'precio_min' in query_params:
                servicios = [s for s in servicios if float(s.precio_base) >= query_params['precio_min']]
            if 'precio_max' in query_params:
                servicios = [s for s in servicios if float(s.precio_base) <= query_params['precio_max']]
                
        except Exception as e:
            # Si hay error de transacción, hacer rollback
            ServicioController._manejar_error_db()
            flash(f'Error en la búsqueda: {str(e)}', 'error')
            servicios = []
        
        return render_template('servicios/buscar_servicios.html', 
                             servicios=servicios,
                             categorias=CategoriaServicio,
                             filtros=query_params,
                             tipo_busqueda=tipo_busqueda)
    
    @staticmethod
    def solicitar_servicio(servicio_id):
        """Solicita un servicio para un evento"""
        if not ServicioController._usuario_autenticado():
            return ServicioController._acceso_no_autorizado()
        
        if session['user_rol'] != 'organizador':
            flash('Solo los organizadores pueden solicitar servicios', 'error')
            return redirect(url_for('index'))
        
        servicio = Servicio.query.get_or_404(servicio_id)
        
        if request.method == 'GET':
            # Obtener eventos del organizador
            eventos = Evento.query.filter_by(
                organizador_id=session['user_id'],
                estado='activo'
            ).order_by(Evento.fecha_inicio.asc()).all()
            
            return render_template('servicios/solicitar_servicio.html', 
                                 servicio=servicio, 
                                 eventos=eventos)
        
        # Obtener datos del formulario
        evento_id = request.form.get('evento_id', '').strip()
        fecha_evento = request.form.get('fecha_evento', '').strip()
        fecha_fin_servicio = request.form.get('fecha_fin_servicio', '').strip()
        duracion_horas = request.form.get('duracion_horas', '').strip()
        numero_personas = request.form.get('numero_personas', '').strip()
        ubicacion = request.form.get('ubicacion', '').strip()
        notas_especiales = request.form.get('notas_especiales', '').strip()
        
        # Validaciones
        errores = []
        
        if not evento_id:
            errores.append('Debes seleccionar un evento')
        
        if not fecha_evento:
            errores.append('La fecha del servicio es obligatoria')
        
        if not duracion_horas:
            errores.append('La duración es obligatoria')
        else:
            try:
                duracion = int(duracion_horas)
                if duracion < 1:
                    errores.append('La duración debe ser mayor a 0')
            except ValueError:
                errores.append('Formato de duración inválido')
        
        if not ubicacion:
            errores.append('La ubicación es obligatoria')
        
        if numero_personas:
            try:
                personas = int(numero_personas)
                if personas < 1:
                    errores.append('El número de personas debe ser mayor a 0')
            except ValueError:
                errores.append('Formato de número de personas inválido')
        
        if errores:
            for error in errores:
                flash(error, 'error')
            eventos = Evento.query.filter_by(
                organizador_id=session['user_id'],
                estado='activo'
            ).order_by(Evento.fecha_inicio.asc()).all()
            return render_template('servicios/solicitar_servicio.html', 
                                 servicio=servicio, 
                                 eventos=eventos)
        
        try:
            # Obtener evento
            evento = Evento.query.get_or_404(evento_id)
            
            # Verificar que el evento pertenece al organizador
            if evento.organizador_id != session['user_id']:
                flash('No tienes permisos para usar este evento', 'error')
                return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
            
            # Calcular precio total
            precio_total = servicio.calcular_precio_estimado(
                duracion_horas=int(duracion_horas),
                numero_personas=int(numero_personas) if numero_personas else None
            )
            
            # Convertir fecha del formulario
            fecha_servicio = datetime.fromisoformat(fecha_evento.replace('T', ' '))
            
            # Agregar al carrito en lugar de crear contratación directa
            from models.carrito import CarritoItem, EstadoCarritoItem
            
            # Verificar si ya existe en el carrito
            item_existente = CarritoItem.query.filter_by(
                servicio_id=servicio_id,
                evento_id=evento_id,
                organizador_id=session['user_id'],
                estado=EstadoCarritoItem.pendiente
            ).first()
            
            if item_existente:
                flash('Este servicio ya está en tu carrito para este evento', 'warning')
                return redirect(url_for('carrito.ver_carrito'))
            
            # Crear item del carrito
            nuevo_item = CarritoItem(
                servicio_id=servicio_id,
                evento_id=evento_id,
                organizador_id=session['user_id'],
                fecha_evento=fecha_servicio,
                duracion_horas=int(duracion_horas),
                numero_personas=int(numero_personas) if numero_personas else None,
                ubicacion=ubicacion,
                notas_especiales=notas_especiales,
                precio_total=precio_total
            )
            
            db.session.add(nuevo_item)
            db.session.commit()
            
            flash('Servicio agregado al carrito. Procede al pago para confirmar la contratación.', 'success')
            return redirect(url_for('carrito.ver_carrito'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al enviar la solicitud', 'error')
            eventos = Evento.query.filter_by(
                organizador_id=session['user_id'],
                estado='activo'
            ).order_by(Evento.fecha_inicio.asc()).all()
            return render_template('servicios/solicitar_servicio.html', 
                                 servicio=servicio, 
                                 eventos=eventos)
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    @staticmethod
    def _obtener_datos_formulario():
        """Obtiene y procesa los datos del formulario"""
        # Procesar imágenes
        imagenes_urls = []
        if 'imagenes' in request.files:
            archivos = request.files.getlist('imagenes')
            for archivo in archivos:
                if archivo and archivo.filename:
                    # En un entorno real, aquí subirías el archivo a un servicio de almacenamiento
                    # Por ahora, simulamos URLs de ejemplo
                    imagenes_urls.append(f"/static/images/servicios/{archivo.filename}")
        
        return {
            'nombre': request.form.get('nombre', '').strip(),
            'descripcion': request.form.get('descripcion', '').strip(),
            'categoria': request.form.get('categoria', '').strip(),
            'precio_base': request.form.get('precio_base', '').strip(),
            'precio_por_hora': request.form.get('precio_por_hora', '').strip(),
            'precio_por_persona': request.form.get('precio_por_persona', '').strip(),
            'duracion_minima': request.form.get('duracion_minima', '').strip(),
            'duracion_maxima': request.form.get('duracion_maxima', '').strip(),
            'capacidad_maxima': request.form.get('capacidad_maxima', '').strip(),
            'incluye_materiales': request.form.get('incluye_materiales') == 'on',
            'incluye_transporte': request.form.get('incluye_transporte') == 'on',
            'incluye_montaje': request.form.get('incluye_montaje') == 'on',
            'incluye_desmontaje': request.form.get('incluye_desmontaje') == 'on',
            'requiere_deposito': request.form.get('requiere_deposito') == 'on',
            'porcentaje_deposito': request.form.get('porcentaje_deposito', '').strip(),
            'ciudad': request.form.get('ciudad', '').strip(),
            'radio_cobertura': request.form.get('radio_cobertura', '').strip(),
            'imagenes_referencia': imagenes_urls
        }
    
    @staticmethod
    def _validar_datos_servicio(datos, servicio_id=None):
        """Valida los datos del servicio"""
        errores = []
        
        # Validar nombre
        if not datos['nombre'] or len(datos['nombre']) < 3:
            errores.append('El nombre debe tener al menos 3 caracteres')
        
        # Validar descripción
        if not datos['descripcion'] or len(datos['descripcion']) < 10:
            errores.append('La descripción debe tener al menos 10 caracteres')
        
        # Validar categoría
        try:
            if datos['categoria']:
                CategoriaServicio(datos['categoria'])
        except ValueError:
            errores.append('Categoría no válida')
        
        # Validar precio base
        if not datos['precio_base']:
            errores.append('El precio base es obligatorio')
        else:
            try:
                precio = float(datos['precio_base'])
                if precio < 0:
                    errores.append('El precio base no puede ser negativo')
            except ValueError:
                errores.append('Formato de precio base inválido')
        
        # Validar precios opcionales
        if datos['precio_por_hora']:
            try:
                precio = float(datos['precio_por_hora'])
                if precio < 0:
                    errores.append('El precio por hora no puede ser negativo')
            except ValueError:
                errores.append('Formato de precio por hora inválido')
        
        if datos['precio_por_persona']:
            try:
                precio = float(datos['precio_por_persona'])
                if precio < 0:
                    errores.append('El precio por persona no puede ser negativo')
            except ValueError:
                errores.append('Formato de precio por persona inválido')
        
        # Validar duraciones
        if datos['duracion_minima']:
            try:
                duracion = int(datos['duracion_minima'])
                if duracion < 1:
                    errores.append('La duración mínima debe ser mayor a 0')
            except ValueError:
                errores.append('Formato de duración mínima inválido')
        
        if datos['duracion_maxima']:
            try:
                duracion = int(datos['duracion_maxima'])
                if duracion < 1:
                    errores.append('La duración máxima debe ser mayor a 0')
            except ValueError:
                errores.append('Formato de duración máxima inválido')
        
        # Validar capacidad
        if datos['capacidad_maxima']:
            try:
                capacidad = int(datos['capacidad_maxima'])
                if capacidad < 1:
                    errores.append('La capacidad máxima debe ser mayor a 0')
            except ValueError:
                errores.append('Formato de capacidad máxima inválido')
        
        # Validar porcentaje de depósito
        if datos['porcentaje_deposito']:
            try:
                porcentaje = float(datos['porcentaje_deposito'])
                if porcentaje < 0 or porcentaje > 100:
                    errores.append('El porcentaje de depósito debe estar entre 0 y 100')
            except ValueError:
                errores.append('Formato de porcentaje de depósito inválido')
        
        # Validar ciudad
        if not datos['ciudad'] or len(datos['ciudad']) < 2:
            errores.append('La ciudad debe tener al menos 2 caracteres')
        
        # Validar radio de cobertura
        if datos['radio_cobertura']:
            try:
                radio = int(datos['radio_cobertura'])
                if radio < 1:
                    errores.append('El radio de cobertura debe ser mayor a 0')
            except ValueError:
                errores.append('Formato de radio de cobertura inválido')
        
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
    def _es_propietario_servicio(servicio):
        """Verifica si el usuario es el propietario del servicio"""
        return (ServicioController._usuario_autenticado() and 
                session['user_rol'] == 'proveedor' and
                session['user_id'] == servicio.proveedor_id)
