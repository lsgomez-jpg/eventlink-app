# controllers/carrito_controller.py
"""
Controlador para gestión del carrito de compras
Principio SOLID: Single Responsibility - Responsabilidad única para carrito
"""

from flask import request, session, flash, redirect, url_for, render_template, jsonify
from models.carrito import CarritoItem, EstadoCarritoItem
from models.servicio import Servicio
from models.evento import Evento
from models.usuario import Usuario
from database import db
from datetime import datetime
class CarritoController:

    @staticmethod
    def agregar_al_carrito(servicio_id):
        """Agrega un servicio al carrito"""
        if not CarritoController._usuario_autenticado():
            return CarritoController._acceso_no_autorizado()

        if session['user_rol'] != 'organizador':
            flash('Solo los organizadores pueden agregar servicios al carrito', 'error')
            return redirect(url_for('index'))

        servicio = Servicio.query.get_or_404(servicio_id)

        if request.method == 'GET':
            eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
            return render_template('servicios/solicitar_servicio.html', 
                                   servicio=servicio, eventos=eventos)

        evento_id = request.form.get('evento_id', '').strip()
        fecha_evento = request.form.get('fecha_evento', '').strip()
        duracion_horas = request.form.get('duracion_horas', '').strip()
        numero_personas = request.form.get('numero_personas', '').strip()
        ubicacion = request.form.get('ubicacion', '').strip()
        notas_especiales = request.form.get('notas_especiales', '').strip()

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
            eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
            return render_template('servicios/solicitar_servicio.html', 
                                   servicio=servicio, eventos=eventos)

        try:
            evento = Evento.query.filter_by(
                id=evento_id, 
                organizador_id=session['user_id']
            ).first()

            if not evento:
                flash('El evento seleccionado no es válido', 'error')
                return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))

            nuevo_item = CarritoItem(
                servicio_id=servicio_id,
                evento_id=evento_id,
                organizador_id=session['user_id'],
                fecha_evento=datetime.strptime(fecha_evento, '%Y-%m-%dT%H:%M'),
                duracion_horas=int(duracion_horas),
                numero_personas=int(numero_personas) if numero_personas else None,
                ubicacion=ubicacion,
                notas_especiales=notas_especiales,
                tipo_item='servicio'
            )

            db.session.add(nuevo_item)
            db.session.flush()
            db.session.commit()

            flash('Servicio agregado al carrito exitosamente', 'success')
            return redirect(url_for('carrito.ver_carrito'))

        except ValueError:
            db.session.rollback()
            flash('Error en el formato de fecha', 'error')
            eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
            return render_template('servicios/solicitar_servicio.html', 
                                   servicio=servicio, eventos=eventos)
        except Exception:
            db.session.rollback()
            flash('Error al agregar el servicio al carrito', 'error')
            eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
            return render_template('servicios/solicitar_servicio.html', 
                                   servicio=servicio, eventos=eventos)

    @staticmethod
    def ver_carrito():
        """Muestra el carrito del usuario"""
        if not CarritoController._usuario_autenticado():
            return CarritoController._acceso_no_autorizado()

        if session['user_rol'] != 'organizador':
            flash('Solo los organizadores pueden ver el carrito', 'error')
            return redirect(url_for('index'))

        user_id = session['user_id']
        items = CarritoItem.obtener_carrito_usuario(user_id)
        total = CarritoItem.calcular_total_carrito(user_id)
        return render_template('carrito/ver_carrito.html', items=items, total=total)

    @staticmethod
    def editar_item(item_id):
        """Muestra el formulario para editar un item del carrito"""
        if not CarritoController._usuario_autenticado():
            return CarritoController._acceso_no_autorizado()

        item = CarritoItem.query.get_or_404(item_id)

        if item.organizador_id != session['user_id']:
            flash('No tienes permisos para editar este item', 'error')
            return redirect(url_for('carrito.ver_carrito'))

        if not item.puede_editar():
            flash('Este item no puede ser editado', 'error')
            return redirect(url_for('carrito.ver_carrito'))

        eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
        return render_template('carrito/editar_item.html', item=item, eventos=eventos)

    @staticmethod
    def actualizar_item(item_id):
        """Actualiza un item del carrito"""
        if not CarritoController._usuario_autenticado():
            return CarritoController._acceso_no_autorizado()

        item = CarritoItem.query.get_or_404(item_id)

        if item.organizador_id != session['user_id']:
            flash('No tienes permisos para editar este item', 'error')
            return redirect(url_for('carrito.ver_carrito'))

        if not item.puede_editar():
            flash('Este item no puede ser editado', 'error')
            return redirect(url_for('carrito.ver_carrito'))

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
            eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
            return render_template('carrito/editar_item.html', item=item, eventos=eventos)

        try:
            # Verificar que el evento pertenezca al organizador
            evento = Evento.query.filter_by(
                id=evento_id, 
                organizador_id=session['user_id']
            ).first()

            if not evento:
                flash('El evento seleccionado no es válido', 'error')
                eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
                return render_template('carrito/editar_item.html', item=item, eventos=eventos)

            # Actualizar los campos del item
            item.evento_id = evento_id
            item.fecha_evento = datetime.strptime(fecha_evento, '%Y-%m-%dT%H:%M')
            item.duracion_horas = int(duracion_horas)
            item.numero_personas = int(numero_personas) if numero_personas else None
            item.ubicacion = ubicacion
            item.notas_especiales = notas_especiales
            
            # Recalcular precios
            item._calcular_precios()
            
            # Actualizar fecha de modificación
            item.fecha_actualizacion = datetime.utcnow()
            
            db.session.commit()
            flash('Item actualizado exitosamente', 'success')
            return redirect(url_for('carrito.ver_carrito'))

        except ValueError as e:
            db.session.rollback()
            flash('Error en el formato de fecha', 'error')
            eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
            return render_template('carrito/editar_item.html', item=item, eventos=eventos)
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el item: {str(e)}', 'error')
            eventos = Evento.query.filter_by(organizador_id=session['user_id']).all()
            return render_template('carrito/editar_item.html', item=item, eventos=eventos)

    @staticmethod
    def eliminar_item(item_id):
        """Elimina un item del carrito"""
        if not CarritoController._usuario_autenticado():
            return CarritoController._acceso_no_autorizado()

        item = CarritoItem.query.get_or_404(item_id)

        if item.organizador_id != session['user_id']:
            flash('No tienes permisos para eliminar este item', 'error')
            return redirect(url_for('carrito.ver_carrito'))

        if not item.puede_editar():
            flash('Este item no puede ser eliminado', 'error')
            return redirect(url_for('carrito.ver_carrito'))

        try:
            db.session.delete(item)
            db.session.commit()
            flash('Item eliminado del carrito', 'success')
            return redirect(url_for('carrito.ver_carrito'))

        except Exception:
            db.session.rollback()
            flash('Error al eliminar el item', 'error')
            return redirect(url_for('carrito.ver_carrito'))

    @staticmethod
    def _usuario_autenticado():
        return 'user_id' in session

    @staticmethod
    def _acceso_no_autorizado():
        flash('Debes iniciar sesión para acceder a esta página', 'error')
        return redirect(url_for('usuario.login'))
    
    @staticmethod
    def pago_mercadopago(item_id):
        """
        Redirige directamente a MercadoPago para un item específico del carrito
        
        Args:
            item_id (int): ID del item del carrito a procesar
            
        Returns:
            Response: Redirección a MercadoPago
        """
        # 1. Verificar autenticación
        if not CarritoController._usuario_autenticado():
            return CarritoController._acceso_no_autorizado()
        
        # 2. Verificar rol de organizador
        if session['user_rol'] != 'organizador':
            flash('Solo los organizadores pueden procesar pagos', 'error')
            return redirect(url_for('index'))
        
        try:
            # 3. Obtener el item del carrito
            item = CarritoItem.query.filter_by(
                id=item_id,
                organizador_id=session['user_id']
            ).first()
            
            if not item:
                flash('Item del carrito no encontrado', 'error')
                return redirect(url_for('carrito.ver_carrito'))
            
            # 4. Verificar que el usuario sea el dueño del item
            if item.organizador_id != session['user_id']:
                flash('No tienes permisos para procesar este item', 'error')
                return redirect(url_for('carrito.ver_carrito'))
            
            # 5. Verificar que el item esté en estado pendiente
            if not item.esta_pendiente():
                flash('Este item ya fue procesado o no está disponible', 'error')
                return redirect(url_for('carrito.ver_carrito'))
            
            # 6. Redirigir directamente a MercadoPago
            from patterns.singleton import PaymentGateway
            from models.pago import Pago, MetodoPago, EstadoPago
            from models.contratacion import Contratacion, EstadoContratacion
            
            # Crear contratación primero
            contratacion = Contratacion(
                servicio_id=item.servicio_id,
                evento_id=item.evento_id,
                organizador_id=item.organizador_id,
                proveedor_id=item.servicio.proveedor_id,
                fecha_evento=item.fecha_evento,
                duracion_horas=item.duracion_horas,
                numero_personas=item.numero_personas,
                ubicacion=item.ubicacion,
                notas_especiales=item.notas_especiales,
                precio_total=item.precio_total,
                deposito_requerido=0,
                estado=EstadoContratacion.solicitada
            )
            db.session.add(contratacion)
            db.session.flush()
            
            # Crear registro de pago
            pago = Pago(
                contratacion_id=contratacion.id,
                organizador_id=item.organizador_id,
                monto=item.precio_total,
                metodo_pago=MetodoPago.mercadopago,
                estado=EstadoPago.pendiente,
                nombre_titular=session.get('user_name', 'Usuario'),
                email_pagador=session.get('user_email', 'usuario@eventlink.com'),
                telefono_pagador=session.get('user_phone', ''),
                documento_pagador=session.get('user_document', ''),
                datos_adicionales={
                    'item_carrito_id': item.id,
                    'servicio_id': item.servicio_id,
                    'evento_id': item.evento_id
                }
            )
            db.session.add(pago)
            db.session.flush()
            
            # Procesar con MercadoPago
            payment_gateway = PaymentGateway()
            resultado_mp = payment_gateway.procesar_pago_mercadopago(
                monto=item.precio_total,
                descripcion=f"Servicio: {item.servicio.nombre} - Evento: {item.evento.titulo}",
                email_pagador=session.get('user_email', 'usuario@eventlink.com')
            )
            
            if resultado_mp.get('success'):
                # Guardar datos y redirigir
                pago.datos_adicionales['mercadopago_id'] = resultado_mp.get('payment_id')
                pago.datos_adicionales['url_pago'] = resultado_mp.get('url_pago')
                db.session.commit()
                
                # Redirigir directamente a MercadoPago
                return redirect(resultado_mp.get('url_pago'))
            else:
                pago.estado = EstadoPago.rechazado
                pago.datos_adicionales['error'] = resultado_mp.get('message', 'Error desconocido')
                db.session.commit()
                flash(f'Error al crear el pago: {resultado_mp.get("message", "Error desconocido")}', 'error')
                return redirect(url_for('carrito.ver_carrito'))
            
        except Exception as e:
            print(f"❌ Error en pago_mercadopago: {e}")
            flash(f'Error al procesar el pago: {str(e)}', 'error')
            return redirect(url_for('carrito.ver_carrito'))
    
    @staticmethod
    def checkout_api(item_id):
        """
        Muestra el formulario de pago personalizado con Checkout API
        
        Args:
            item_id (int): ID del item del carrito a procesar
            
        Returns:
            Response: Renderizado del formulario de pago personalizado
        """
        # 1. Verificar autenticación
        if not CarritoController._usuario_autenticado():
            return CarritoController._acceso_no_autorizado()
        
        # 2. Verificar rol de organizador
        if session['user_rol'] != 'organizador':
            flash('Solo los organizadores pueden procesar pagos', 'error')
            return redirect(url_for('index'))
        
        try:
            # 3. Obtener el item del carrito
            item = CarritoItem.query.filter_by(
                id=item_id,
                organizador_id=session['user_id']
            ).first()
            
            if not item:
                flash('Item del carrito no encontrado', 'error')
                return redirect(url_for('carrito.ver_carrito'))
            
            # 4. Verificar que el usuario sea el dueño del item
            if item.organizador_id != session['user_id']:
                flash('No tienes permisos para procesar este item', 'error')
                return redirect(url_for('carrito.ver_carrito'))
            
            # 5. Verificar que el item esté en estado pendiente
            if not item.esta_pendiente():
                flash('Este item ya fue procesado o no está disponible', 'error')
                return redirect(url_for('carrito.ver_carrito'))
            
            # 6. Crear una contratación real para el pago
            from models.contratacion import Contratacion, EstadoContratacion
            
            # Crear contratación real en la base de datos
            contratacion = Contratacion(
                servicio_id=item.servicio_id,
                evento_id=item.evento.id,
                organizador_id=item.organizador_id,
                proveedor_id=item.servicio.proveedor_id,
                fecha_evento=item.fecha_evento,
                duracion_horas=item.duracion_horas,
                numero_personas=item.numero_personas,
                ubicacion=item.ubicacion,
                notas_especiales=item.notas_especiales,
                precio_total=item.precio_total,
                deposito_requerido=0,
                estado=EstadoContratacion.solicitada
            )
            db.session.add(contratacion)
            db.session.commit()
            
            print(f"✅ Contratación creada con ID: {contratacion.id}")
            
            # Mostrar formulario de pago con MercadoPago Checkout API
            return render_template('pagos/procesar_pago.html', contratacion=contratacion, item=item)
            
        except Exception as e:
            print(f"❌ Error en checkout_api: {e}")
            flash(f'Error al cargar el formulario de pago: {str(e)}', 'error')
            return redirect(url_for('carrito.ver_carrito'))
    
    @staticmethod
    def procesar_pago_api(item_id):
        """
        Procesa el pago usando Checkout API (recibe token de tarjeta)
        
        Args:
            item_id (int): ID del item del carrito a procesar
            
        Returns:
            Response: JSON con el resultado del pago
        """
        from flask import jsonify
        from patterns.singleton import PaymentGateway
        from models.pago import Pago, MetodoPago, EstadoPago
        from models.contratacion import Contratacion, EstadoContratacion
        
        # 1. Verificar autenticación
        if not CarritoController._usuario_autenticado():
            return jsonify({'success': False, 'message': 'No autorizado'}), 401
        
        # 2. Verificar rol de organizador
        if session['user_rol'] != 'organizador':
            return jsonify({'success': False, 'message': 'Solo organizadores pueden procesar pagos'}), 403
        
        try:
            # 3. Obtener datos del request
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Datos de pago requeridos'}), 400
            
            # 4. Obtener el item del carrito
            item = CarritoItem.query.filter_by(
                id=item_id,
                organizador_id=session['user_id']
            ).first()
            
            if not item:
                return jsonify({'success': False, 'message': 'Item del carrito no encontrado'}), 404
            
            # 5. Verificar que el item esté en estado pendiente
            if not item.esta_pendiente():
                return jsonify({'success': False, 'message': 'Este item ya fue procesado'}), 400
            
            # 6. Crear contratación
            contratacion = Contratacion(
                servicio_id=item.servicio_id,
                evento_id=item.evento_id,
                organizador_id=item.organizador_id,
                proveedor_id=item.servicio.proveedor_id,
                fecha_evento=item.fecha_evento,
                duracion_horas=item.duracion_horas,
                numero_personas=item.numero_personas,
                ubicacion=item.ubicacion,
                notas_especiales=item.notas_especiales,
                precio_total=item.precio_total,
                deposito_requerido=0,
                estado=EstadoContratacion.solicitada
            )
            db.session.add(contratacion)
            db.session.flush()
            
            # 7. Crear registro de pago
            pago = Pago(
                contratacion_id=contratacion.id,
                organizador_id=item.organizador_id,
                monto=item.precio_total,
                metodo_pago=MetodoPago.mercadopago,
                estado=EstadoPago.pendiente,
                nombre_titular=data.get('payer', {}).get('email', session.get('user_name', 'Usuario')),
                email_pagador=data.get('payer', {}).get('email', session.get('user_email', 'usuario@eventlink.com')),
                telefono_pagador=session.get('user_phone', ''),
                documento_pagador=data.get('payer', {}).get('identification', {}).get('number', ''),
                datos_adicionales={
                    'item_carrito_id': item.id,
                    'servicio_id': item.servicio_id,
                    'evento_id': item.evento_id,
                    'payment_method_id': data.get('payment_method_id'),
                    'installments': data.get('installments', 1),
                    'issuer_id': data.get('issuer_id')
                }
            )
            db.session.add(pago)
            db.session.flush()
            
            # 8. Procesar pago con MercadoPago
            payment_gateway = PaymentGateway()
            resultado_mp = payment_gateway.procesar_pago_checkout_api(
                monto=item.precio_total,
                descripcion=f"Servicio: {item.servicio.nombre} - Evento: {item.evento.titulo}",
                token=data.get('token'),
                payment_method_id=data.get('payment_method_id'),
                installments=data.get('installments', 1),
                issuer_id=data.get('issuer_id'),
                payer=data.get('payer', {})
            )
            
            if resultado_mp.get('success'):
                # 9. Actualizar estado del pago
                payment_status = resultado_mp.get('estado', 'pending')
                if payment_status == 'approved':
                    pago.estado = EstadoPago.aprobado
                    item.estado = EstadoCarritoItem.procesando
                    message = '¡Pago procesado exitosamente!'
                elif payment_status == 'rejected':
                    pago.estado = EstadoPago.rechazado
                    message = 'El pago fue rechazado'
                else:
                    pago.estado = EstadoPago.pendiente
                    message = 'Pago pendiente de confirmación'
                
                # Guardar datos adicionales
                pago.datos_adicionales['mercadopago_id'] = resultado_mp.get('payment_id')
                pago.datos_adicionales['mercadopago_response'] = resultado_mp.get('response', {})
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'payment_id': resultado_mp.get('payment_id'),
                    'estado': payment_status
                })
            else:
                # Error en el pago
                pago.estado = EstadoPago.rechazado
                pago.datos_adicionales['error'] = resultado_mp.get('message', 'Error desconocido')
                db.session.commit()
                
                return jsonify({
                    'success': False,
                    'message': resultado_mp.get('message', 'Error al procesar el pago')
                }), 400
            
        except Exception as e:
            print(f"❌ Error en procesar_pago_api: {e}")
            return jsonify({
                'success': False,
                'message': f'Error interno: {str(e)}'
            }), 500
    
    @staticmethod
    def mercadopago_public_key():
        """
        Devuelve la public key de MercadoPago para el frontend
        
        Returns:
            Response: JSON con la public key
        """
        from flask import jsonify
        
        # Public key de prueba para sandbox
        # Public Key real de MercadoPago
        public_key = "TEST-f337044d-548b-4395-8b18-ee976a52ea42"
        
        return jsonify({
            'public_key': public_key,
            'mode': 'sandbox'
        })
    
    @staticmethod
    def procesar_pago():
        """
        Muestra el formulario de pago para todo el carrito o procesa el pago
        
        Returns:
            Response: Renderizado del formulario o redirección
        """
        # 1. Verificar autenticación
        if not CarritoController._usuario_autenticado():
            return CarritoController._acceso_no_autorizado()
        
        # 2. Verificar rol de organizador
        if session['user_rol'] != 'organizador':
            flash('Solo los organizadores pueden procesar pagos', 'error')
            return redirect(url_for('index'))
        
        try:
            # 3. Obtener items del carrito pendientes
            user_id = session['user_id']
            items_pendientes = CarritoItem.query.filter_by(
                organizador_id=user_id,
                estado=EstadoCarritoItem.pendiente
            ).all()
            
            if not items_pendientes:
                flash('No hay items pendientes de pago en tu carrito', 'warning')
                return redirect(url_for('carrito.ver_carrito'))
            
            # 4. Calcular total
            total = sum(item.precio_total for item in items_pendientes)
            
            if request.method == 'GET':
                # Mostrar formulario de pago
                return render_template('carrito/procesar_pago_carrito.html', 
                                     items=items_pendientes, 
                                     total=total)
            
            # 5. Procesar pago (POST)
            # Obtener datos del formulario
            nombre_titular = request.form.get('nombre_titular', '').strip()
            email_pagador = request.form.get('email_pagador', '').strip()
            telefono_pagador = request.form.get('telefono_pagador', '').strip()
            documento_pagador = request.form.get('documento_pagador', '').strip()
            
            # Datos de la tarjeta
            numero_tarjeta = request.form.get('numero_tarjeta', '').replace(' ', '')
            cvv = request.form.get('cvv', '').strip()
            fecha_vencimiento = request.form.get('fecha_vencimiento', '').strip()
            tipo_tarjeta = request.form.get('tipo_tarjeta', '').strip()
            
            # Validaciones
            errores = []
            if not nombre_titular:
                errores.append('El nombre del titular es obligatorio')
            if not email_pagador:
                errores.append('El email es obligatorio')
            if not documento_pagador:
                errores.append('El documento es obligatorio')
            if not numero_tarjeta:
                errores.append('El número de tarjeta es obligatorio')
            if not cvv:
                errores.append('El CVV es obligatorio')
            if not fecha_vencimiento:
                errores.append('La fecha de vencimiento es obligatoria')
            if not tipo_tarjeta:
                errores.append('El tipo de tarjeta es obligatorio')
            
            if errores:
                for error in errores:
                    flash(error, 'error')
                return render_template('carrito/procesar_pago_carrito.html', 
                                     items=items_pendientes, 
                                     total=total)
            
            # 6. Crear preferencia de pago con MercadoPago
            from patterns.singleton import PaymentGateway
            
            # Cambiar todos los items a procesando
            for item in items_pendientes:
                item.procesar()
            
            db.session.commit()
            
            # Crear preferencia de pago para todo el carrito
            payment_gateway = PaymentGateway()
            descripcion = f"EventLink - {len(items_pendientes)} servicio(s) - Total: ${total:.2f}"
            
            resultado_mp = payment_gateway.procesar_pago_mercadopago(
                monto=total,
                descripcion=descripcion,
                email_pagador=email_pagador,
                datos_tarjeta={
                    'numero_tarjeta': numero_tarjeta,
                    'cvv': cvv,
                    'fecha_vencimiento': fecha_vencimiento,
                    'tipo_tarjeta': tipo_tarjeta,
                    'nombre_titular': nombre_titular,
                    'documento': documento_pagador,
                    'telefono': telefono_pagador
                }
            )
            
            if resultado_mp.get('success'):
                # Guardar datos de pago en sesión para después del pago
                session['pago_pendiente'] = {
                    'items_ids': [item.id for item in items_pendientes],
                    'nombre_titular': nombre_titular,
                    'email_pagador': email_pagador,
                    'telefono_pagador': telefono_pagador,
                    'documento_pagador': documento_pagador,
                    'mercadopago_id': resultado_mp.get('payment_id'),
                    'total': float(total)
                }
                
                # Redirigir a MercadoPago
                return redirect(resultado_mp.get('url_pago'))
            else:
                # Si falla, volver items a pendiente
                for item in items_pendientes:
                    item.estado = EstadoCarritoItem.pendiente
                    item.fecha_actualizacion = datetime.utcnow()
                
                db.session.commit()
                
                error_msg = resultado_mp.get('message', 'Error desconocido en el pago')
                flash(f'Error al procesar el pago: {error_msg}', 'error')
                return render_template('carrito/procesar_pago_carrito.html', 
                                     items=items_pendientes, 
                                     total=total)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error en procesar_pago: {e}")
            flash(f'Error al procesar el pago: {str(e)}', 'error')
            return redirect(url_for('carrito.ver_carrito'))
    
    @staticmethod
    def limpiar_carrito():
        """
        Limpia todo el carrito del usuario
        
        Returns:
            Response: Redirección al carrito
        """
        # 1. Verificar autenticación
        if not CarritoController._usuario_autenticado():
            return CarritoController._acceso_no_autorizado()
        
        # 2. Verificar rol de organizador
        if session['user_rol'] != 'organizador':
            flash('Solo los organizadores pueden limpiar el carrito', 'error')
            return redirect(url_for('index'))
        
        try:
            # 3. Obtener items del carrito
            user_id = session['user_id']
            items = CarritoItem.query.filter_by(organizador_id=user_id).all()
            
            # 4. Eliminar solo items pendientes
            items_eliminados = 0
            for item in items:
                if item.estado == EstadoCarritoItem.pendiente:
                    db.session.delete(item)
                    items_eliminados += 1
            
            db.session.commit()
            
            if items_eliminados > 0:
                flash(f'Se eliminaron {items_eliminados} items del carrito', 'success')
            else:
                flash('No había items pendientes para eliminar', 'info')
            
            return redirect(url_for('carrito.ver_carrito'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error en limpiar_carrito: {e}")
            flash(f'Error al limpiar el carrito: {str(e)}', 'error')
            return redirect(url_for('carrito.ver_carrito'))
    
    @staticmethod
    def pagar_directo_mercadopago():
        """
        Redirige directamente a MercadoPago sin formularios intermedios
        """
        if not CarritoController._usuario_autenticado():
            return CarritoController._acceso_no_autorizado()
        
        if session['user_rol'] != 'organizador':
            flash('Solo los organizadores pueden procesar pagos', 'error')
            return redirect(url_for('index'))
        
        try:
            user_id = session['user_id']
            items_pendientes = CarritoItem.query.filter_by(
                organizador_id=user_id,
                estado=EstadoCarritoItem.pendiente
            ).all()
            
            if not items_pendientes:
                flash('No hay items pendientes de pago en tu carrito', 'warning')
                return redirect(url_for('carrito.ver_carrito'))
            
            # Calcular total
            total = sum(item.precio_total for item in items_pendientes)
            
            # Cambiar estado a procesando
            for item in items_pendientes:
                item.estado = EstadoCarritoItem.procesando
                item.fecha_actualizacion = datetime.utcnow()
            
            db.session.commit()
            
            # Crear preferencia de MercadoPago
            from patterns.singleton import PaymentGateway
            payment_gateway = PaymentGateway()
            
            descripcion = f"EventLink - {len(items_pendientes)} servicio(s) - Total: ${total:.2f}"
            email_pagador = session.get('user_email', 'usuario@eventlink.com')
            
            resultado_mp = payment_gateway.procesar_pago_mercadopago(
                monto=total,
                descripcion=descripcion,
                email_pagador=email_pagador
            )
            
            if resultado_mp.get('success'):
                # Guardar datos en sesión para después del pago
                session['pago_pendiente'] = {
                    'items_ids': [item.id for item in items_pendientes],
                    'total': float(total),
                    'mercadopago_id': resultado_mp.get('payment_id')
                }
                
                # Redirigir directamente a MercadoPago
                return redirect(resultado_mp.get('url_pago'))
            else:
                # Revertir estado si falla
                for item in items_pendientes:
                    item.estado = EstadoCarritoItem.pendiente
                    item.fecha_actualizacion = datetime.utcnow()
                db.session.commit()
                
                error_msg = resultado_mp.get('message', 'Error desconocido')
                flash(f'Error al crear el pago: {error_msg}', 'error')
                return redirect(url_for('carrito.ver_carrito'))
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error en pagar_directo_mercadopago: {e}")
            flash(f'Error al procesar el pago: {str(e)}', 'error')
            return redirect(url_for('carrito.ver_carrito'))
    
    @staticmethod
    def pago_exitoso():
        """Maneja la respuesta exitosa de MercadoPago"""
        try:
            # Obtener datos del pago pendiente de la sesión
            pago_data = session.get('pago_pendiente')
            if not pago_data:
                flash('No hay datos de pago pendiente', 'error')
                return redirect(url_for('carrito.ver_carrito'))
            
            # Obtener items del carrito
            items = CarritoItem.query.filter(
                CarritoItem.id.in_(pago_data['items_ids']),
                CarritoItem.organizador_id == session['user_id']
            ).all()
            
            if not items:
                flash('Items del carrito no encontrados', 'error')
                return redirect(url_for('carrito.ver_carrito'))
            
            # Crear contrataciones y pagos
            from models.contratacion import Contratacion, EstadoContratacion
            from models.pago import Pago, MetodoPago, EstadoPago
            
            contrataciones_creadas = 0
            
            for item in items:
                try:
                    # Crear contratación
                    contratacion = Contratacion(
                        servicio_id=item.servicio_id,
                        evento_id=item.evento_id,
                        organizador_id=item.organizador_id,
                        proveedor_id=item.servicio.proveedor_id,
                        fecha_evento=item.fecha_evento,
                        duracion_horas=item.duracion_horas,
                        numero_personas=item.numero_personas,
                        ubicacion=item.ubicacion,
                        notas_especiales=item.notas_especiales,
                        precio_total=item.precio_total,
                        deposito_requerido=0,
                        estado=EstadoContratacion.confirmada
                    )
                    
                    db.session.add(contratacion)
                    db.session.flush()
                    
                    # Crear pago
                    pago = Pago(
                        contratacion_id=contratacion.id,
                        organizador_id=item.organizador_id,
                        monto=item.precio_total,
                        metodo_pago=MetodoPago.mercadopago,
                        estado=EstadoPago.completado,
                        nombre_titular=pago_data['nombre_titular'],
                        email_pagador=pago_data['email_pagador'],
                        telefono_pagador=pago_data['telefono_pagador'],
                        documento_pagador=pago_data['documento_pagador'],
                        datos_adicionales={
                            'item_carrito_id': item.id,
                            'mercadopago_id': pago_data['mercadopago_id'],
                            'servicio_id': item.servicio_id,
                            'evento_id': item.evento_id
                        }
                    )
                    
                    db.session.add(pago)
                    
                    # Marcar item como completado
                    item.completar()
                    contrataciones_creadas += 1
                    
                    # Crear notificación para el proveedor
                    from controllers.notificacion_controller import NotificacionController
                    from models.notificacion import TipoNotificacion
                    
                    NotificacionController.crear_notificacion(
                        usuario_id=item.servicio.proveedor_id,
                        titulo="Nueva Contratación Recibida",
                        mensaje=f"Has recibido una nueva contratación para el servicio '{item.servicio.nombre}' del evento '{item.evento.nombre}' por ${item.precio_total:,.0f}",
                        tipo=TipoNotificacion.nueva_contratacion,
                        servicio_id=item.servicio_id,
                        contratacion_id=contratacion.id,
                        pago_id=pago.id
                    )
                    
                except Exception as e:
                    print(f"❌ Error creando contratación para item {item.id}: {e}")
                    continue
            
            db.session.commit()
            
            # Limpiar datos de sesión
            session.pop('pago_pendiente', None)
            
            flash(f'¡Pago procesado exitosamente! {contrataciones_creadas} servicios contratados.', 'success')
            return redirect(url_for('carrito.ver_carrito'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error en pago_exitoso: {e}")
            flash(f'Error al procesar el pago exitoso: {str(e)}', 'error')
            return redirect(url_for('carrito.ver_carrito'))
    
    @staticmethod
    def pago_fallido():
        """Maneja la respuesta de fallo de MercadoPago"""
        try:
            # Obtener datos del pago pendiente de la sesión
            pago_data = session.get('pago_pendiente')
            if pago_data:
                # Obtener items del carrito y volverlos a pendiente
                items = CarritoItem.query.filter(
                    CarritoItem.id.in_(pago_data['items_ids']),
                    CarritoItem.organizador_id == session['user_id']
                ).all()
                
                for item in items:
                    item.estado = EstadoCarritoItem.pendiente
                    item.fecha_actualizacion = datetime.utcnow()
                
                db.session.commit()
                
                # Limpiar datos de sesión
                session.pop('pago_pendiente', None)
            
            flash('El pago fue rechazado. Puedes intentar nuevamente.', 'error')
            return redirect(url_for('carrito.ver_carrito'))
            
        except Exception as e:
            print(f"❌ Error en pago_fallido: {e}")
            flash('Error al procesar la respuesta de pago fallido', 'error')
            return redirect(url_for('carrito.ver_carrito'))
    
    @staticmethod
    def pago_pendiente():
        """Maneja la respuesta de pago pendiente de MercadoPago"""
        try:
            # Obtener datos del pago pendiente de la sesión
            pago_data = session.get('pago_pendiente')
            if pago_data:
                # Los items ya están en estado procesando, mantenerlos así
                flash('El pago está pendiente de aprobación. Te notificaremos cuando sea procesado.', 'warning')
            else:
                flash('No hay datos de pago pendiente', 'error')
            
            return redirect(url_for('carrito.ver_carrito'))
            
        except Exception as e:
            print(f"❌ Error en pago_pendiente: {e}")
            flash('Error al procesar la respuesta de pago pendiente', 'error')
            return redirect(url_for('carrito.ver_carrito'))
    
    @staticmethod
    def agregar_al_carrito_desde_detalle(servicio_id, evento_id, fecha_evento, duracion_horas, 
                                        numero_personas, ubicacion, notas_especiales):
        """
        Agrega un servicio al carrito desde el detalle del servicio
        
        Args:
            servicio_id (int): ID del servicio
            evento_id (int): ID del evento
            fecha_evento (str): Fecha del evento en formato 'YYYY-MM-DDTHH:MM'
            duracion_horas (int): Duración en horas
            numero_personas (int): Número de personas
            ubicacion (str): Ubicación del servicio
            notas_especiales (str): Notas especiales
            
        Returns:
            Response: Redirección al carrito o al detalle del servicio
        """
        try:
            # Verificar autenticación
            if not CarritoController._usuario_autenticado():
                return CarritoController._acceso_no_autorizado()
            
            # Verificar rol de organizador
            if session['user_rol'] != 'organizador':
                flash('Solo los organizadores pueden agregar servicios al carrito', 'error')
                return redirect(url_for('index'))
            
            # Verificar que el evento pertenezca al organizador
            evento = Evento.query.filter_by(
                id=evento_id, 
                organizador_id=session['user_id']
            ).first()
            
            if not evento:
                flash('El evento seleccionado no es válido', 'error')
                return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
            
            # Crear item del carrito
            nuevo_item = CarritoItem(
                servicio_id=servicio_id,
                evento_id=evento_id,
                organizador_id=session['user_id'],
                fecha_evento=datetime.strptime(fecha_evento, '%Y-%m-%dT%H:%M'),
                duracion_horas=int(duracion_horas),
                numero_personas=int(numero_personas) if numero_personas else None,
                ubicacion=ubicacion,
                notas_especiales=notas_especiales,
                tipo_item='servicio'
            )
            
            db.session.add(nuevo_item)
            db.session.flush()  # Para que se cargue la relación con servicio
            
            # Calcular precios después de que la relación esté disponible
            nuevo_item.calcular_precios()
            db.session.commit()
            
            flash('Servicio agregado al carrito exitosamente. Puedes agregar más servicios o proceder al pago.', 'success')
            return redirect(url_for('carrito.ver_carrito'))
            
        except ValueError as e:
            db.session.rollback()
            flash('Error en el formato de fecha', 'error')
            return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar el servicio al carrito: {str(e)}', 'error')
            return redirect(url_for('servicio.detalle_servicio', servicio_id=servicio_id))
    
    @staticmethod
    def procesar_pago_mercadopago(item_id):
        """Procesa el pago de un item específico del carrito con MercadoPago"""
        if not CarritoController._usuario_autenticado():
            return CarritoController._acceso_no_autorizado()
        
        if session['user_rol'] != 'organizador':
            flash('Solo los organizadores pueden procesar pagos', 'error')
            return redirect(url_for('index'))
        
        try:
            # Obtener el item del carrito
            item = CarritoItem.query.filter_by(
                id=item_id,
                organizador_id=session['user_id'],
                estado=EstadoCarritoItem.pendiente
            ).first()
            
            if not item:
                flash('Item del carrito no encontrado o ya fue procesado', 'error')
                return redirect(url_for('carrito.ver_carrito'))
            
            # Verificar relaciones
            if not item.servicio or not item.evento:
                flash('Item incompleto: servicio o evento no disponible', 'error')
                return redirect(url_for('carrito.ver_carrito'))
            
            if request.method == 'GET':
                # Redirigir directamente a MercadoPago sin formulario
                from patterns.singleton import PaymentGateway
                from models.pago import Pago, MetodoPago, EstadoPago
                from models.contratacion import Contratacion, EstadoContratacion
                
                # Crear contratación primero
                contratacion = Contratacion(
                    servicio_id=item.servicio_id,
                    evento_id=item.evento_id,
                    organizador_id=item.organizador_id,
                    proveedor_id=item.servicio.proveedor_id,
                    fecha_evento=item.fecha_evento,
                    duracion_horas=item.duracion_horas,
                    numero_personas=item.numero_personas,
                    ubicacion=item.ubicacion,
                    notas_especiales=item.notas_especiales,
                    precio_total=item.precio_total,
                    deposito_requerido=0,
                    estado=EstadoContratacion.solicitada
                )
                db.session.add(contratacion)
                db.session.flush()
                
                # Crear registro de pago
                pago = Pago(
                    contratacion_id=contratacion.id,
                    organizador_id=item.organizador_id,
                    monto=item.precio_total,
                    metodo_pago=MetodoPago.mercadopago,
                    estado=EstadoPago.pendiente,
                    nombre_titular=session.get('user_name', 'Usuario'),
                    email_pagador=session.get('user_email', 'usuario@eventlink.com'),
                    telefono_pagador=session.get('user_phone', ''),
                    documento_pagador=session.get('user_document', ''),
                    datos_adicionales={
                        'item_carrito_id': item.id,
                        'servicio_id': item.servicio_id,
                        'evento_id': item.evento_id
                    }
                )
                db.session.add(pago)
                db.session.flush()
                
                # Procesar con MercadoPago
                payment_gateway = PaymentGateway()
                resultado_mp = payment_gateway.procesar_pago_mercadopago(
                    monto=item.precio_total,
                    descripcion=f"Servicio: {item.servicio.nombre} - Evento: {item.evento.titulo}",
                    email_pagador=session.get('user_email', 'usuario@eventlink.com')
                )
                
                if resultado_mp.get('success'):
                    # Guardar datos y redirigir
                    pago.datos_adicionales['mercadopago_id'] = resultado_mp.get('payment_id')
                    pago.datos_adicionales['url_pago'] = resultado_mp.get('url_pago')
                    db.session.commit()
                    
                    # Redirigir directamente a MercadoPago
                    return redirect(resultado_mp.get('url_pago'))
                else:
                    flash(f'Error al crear el pago: {resultado_mp.get("message", "Error desconocido")}', 'error')
                    return redirect(url_for('carrito.ver_carrito'))
            
            # Obtener datos del formulario
            nombre_titular = request.form.get('nombre_titular', '').strip()
            email_pagador = request.form.get('email_pagador', '').strip()
            telefono_pagador = request.form.get('telefono_pagador', '').strip()
            documento_pagador = request.form.get('documento_pagador', '').strip()
            
            # Validaciones
            errores = []
            if not nombre_titular:
                errores.append('El nombre del titular es obligatorio')
            if not email_pagador:
                errores.append('El email es obligatorio')
            if not documento_pagador:
                errores.append('El documento es obligatorio')
            
            if errores:
                for error in errores:
                    flash(error, 'error')
                return render_template('carrito/pago_mercadopago.html', 
                                       item=item, 
                                       total=item.precio_total)
            
            print(f"DEBUG: Iniciando pago de item {item.id} - Servicio: {item.servicio.nombre}")
            
            from patterns.singleton import PaymentGateway
            from models.pago import Pago, MetodoPago, EstadoPago
            from models.contratacion import Contratacion, EstadoContratacion
            
            # Crear contratación primero
            contratacion = Contratacion(
                servicio_id=item.servicio_id,
                evento_id=item.evento_id,
                organizador_id=item.organizador_id,
                proveedor_id=item.servicio.proveedor_id,
                fecha_evento=item.fecha_evento,
                duracion_horas=item.duracion_horas,
                numero_personas=item.numero_personas,
                ubicacion=item.ubicacion,
                notas_especiales=item.notas_especiales,
                precio_total=item.precio_total,
                deposito_requerido=0,
                estado=EstadoContratacion.solicitada
            )
            db.session.add(contratacion)
            db.session.flush()
            print(f"DEBUG: Contratación creada con ID {contratacion.id}")
            
            # Crear registro de pago
            pago = Pago(
                contratacion_id=contratacion.id,
                organizador_id=item.organizador_id,
                monto=item.precio_total,
                metodo_pago=MetodoPago.mercadopago,
                estado=EstadoPago.pendiente,
                nombre_titular=nombre_titular,
                email_pagador=email_pagador,
                telefono_pagador=telefono_pagador,
                documento_pagador=documento_pagador,
                datos_adicionales={
                    'item_carrito_id': item.id,
                    'servicio_id': item.servicio_id,
                    'evento_id': item.evento_id
                }
            )
            db.session.add(pago)
            db.session.flush()
            print(f"DEBUG: Pago creado con ID {pago.id}")
            
            # Procesar con MercadoPago
            payment_gateway = PaymentGateway()
            resultado_mp = payment_gateway.procesar_pago_mercadopago(
                monto=item.precio_total,
                descripcion=f"Servicio: {item.servicio.nombre} - Evento: {item.evento.titulo}",
                email_pagador=email_pagador
            )
            
            if resultado_mp.get('success'):
                # NO marcar como aprobado aún - solo guardar la preferencia
                pago.estado = EstadoPago.pendiente
                pago.datos_adicionales['mercadopago_id'] = resultado_mp.get('payment_id')
                pago.datos_adicionales['url_pago'] = resultado_mp.get('url_pago')
                db.session.commit()
                
                # Redirigir directamente a MercadoPago
                return redirect(resultado_mp.get('url_pago'))
            else:
                pago.estado = EstadoPago.rechazado
                pago.datos_adicionales['error'] = resultado_mp.get('message', 'Error desconocido')
                db.session.commit()
                flash(f'Error al procesar el pago: {resultado_mp.get("message", "Error desconocido")}', 'error')
                return render_template('carrito/pago_mercadopago.html', 
                                       item=item, 
                                       total=item.precio_total)
        
        except Exception as e:
            db.session.rollback()
            import traceback
            print(f"ERROR procesar_pago_mercadopago: {e}\n{traceback.format_exc()}")
            flash(f'Error al procesar el pago: {str(e)}', 'error')
            return render_template('carrito/pago_mercadopago.html', 
                                   item=item if 'item' in locals() else None, 
                                   total=item.precio_total if 'item' in locals() else 0)
