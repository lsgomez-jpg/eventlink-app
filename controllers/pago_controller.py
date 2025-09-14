# controllers/pago_controller.py
"""
Controlador para gestión de pagos con MercadoPago
Principio SOLID: Single Responsibility - Responsabilidad única para pagos
"""

from flask import request, session, flash, redirect, url_for, render_template, jsonify, current_app
from models.pago import Pago, MetodoPago, EstadoPago
from models.contratacion import Contratacion
from models.usuario import Usuario
from database import db
from datetime import datetime
import requests
import json
import mercadopago

class PagoController:
    
    @staticmethod
    def procesar_pago(contratacion_id):
        """Procesa el pago de una contratación usando MercadoPago"""
        if not PagoController._usuario_autenticado():
            return PagoController._acceso_no_autorizado()
        
        contratacion = Contratacion.query.get_or_404(contratacion_id)
        
        # Verificar que el usuario es el organizador
        if session['user_id'] != contratacion.organizador_id:
            flash('No tienes permisos para pagar esta contratación', 'error')
            return redirect(url_for('index'))
        
        if request.method == 'GET':
            return render_template('pagos/procesar_pago.html', 
                                 contratacion=contratacion,
                                 items=None, total=None)
        
        # Obtener datos del formulario de MercadoPago
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
            return render_template('pagos/procesar_pago.html', 
                                 contratacion=contratacion,
                                 items=None, total=None)
        
        try:
            # Crear registro de pago (siempre MercadoPago)
            nuevo_pago = Pago(
                monto=contratacion.precio_total,
                metodo_pago=MetodoPago.mercadopago,
                contratacion_id=contratacion_id,
                organizador_id=session['user_id'],
                nombre_titular=nombre_titular,
                email_pagador=email_pagador,
                telefono_pagador=telefono_pagador,
                documento_pagador=documento_pagador
            )
            
            db.session.add(nuevo_pago)
            db.session.flush()  # Para obtener el ID
            
            # Procesar con MercadoPago
            resultado = PagoController._procesar_mercadopago(nuevo_pago)
            
            if resultado['success']:
                db.session.commit()
                flash('Pago procesado exitosamente', 'success')
                return redirect(url_for('pago.detalle_pago', pago_id=nuevo_pago.id))
            else:
                db.session.rollback()
                flash(f'Error en el pago: {resultado["message"]}', 'error')
                return render_template('pagos/procesar_pago.html', 
                                     contratacion=contratacion,
                                     items=None, total=None)
        except Exception as e:
            db.session.rollback()
            flash('Error al procesar el pago', 'error')
            return render_template('pagos/procesar_pago.html', 
                                 contratacion=contratacion,
                                 items=None, total=None)
    
    @staticmethod
    def detalle_pago(pago_id):
        """Muestra el detalle de un pago"""
        if not PagoController._usuario_autenticado():
            return PagoController._acceso_no_autorizado()
        
        pago = Pago.query.get_or_404(pago_id)
        
        # Verificar que el usuario es el organizador
        if session['user_id'] != pago.organizador_id:
            flash('No tienes permisos para ver este pago', 'error')
            return redirect(url_for('index'))
        
        return render_template('pagos/detalle_pago.html', pago=pago)
    
    @staticmethod
    def historial_pagos():
        """Muestra el historial de pagos del usuario"""
        if not PagoController._usuario_autenticado():
            return PagoController._acceso_no_autorizado()
        
        pagos = Pago.query.filter_by(organizador_id=session['user_id']).order_by(Pago.fecha_creacion.desc()).all()
        return render_template('pagos/listar_pagos.html', pagos=pagos)
    
    @staticmethod
    def webhook_mercadopago():
        """Webhook para notificaciones de MercadoPago"""
        try:
            data = request.get_json()
            print(f"🔔 WEBHOOK MERCADOPAGO: {json.dumps(data, indent=2)}")
            
            # Procesar notificación de MercadoPago
            if data.get('type') == 'payment':
                payment_id = data.get('data', {}).get('id')
                if payment_id:
                    # Buscar pago en la base de datos
                    pago = Pago.query.filter_by(id_transaccion=str(payment_id)).first()
                    if pago:
                        # Actualizar estado del pago
                        PagoController._actualizar_estado_pago(pago, payment_id)
            
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            print(f"❌ ERROR WEBHOOK: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    def _procesar_mercadopago(pago):
        """Procesa el pago con MercadoPago"""
        try:
            print(f"💳 MERCADOPAGO - Iniciando procesamiento para pago ID: {pago.id}")
            print(f"💳 MERCADOPAGO - Monto: ${pago.monto}")
            print(f"💳 MERCADOPAGO - Email: {pago.email_pagador}")
            
            # 1. Configurar SDK de MercadoPago
            access_token = current_app.config.get('MERCADOPAGO_ACCESS_TOKEN')
            print(f"🔑 MERCADOPAGO - Access Token: {access_token[:20] if access_token else 'None'}...")
            
            if not access_token:
                print("❌ MERCADOPAGO - No hay token configurado")
                return {"success": False, "message": "Token de MercadoPago no configurado"}
            
            sdk = mercadopago.SDK(access_token)
            
            # 2. Obtener datos del formulario
            payment_method_id = request.form.get('payment_method_id', 'visa')
            identification_number = request.form.get('documento_pagador', '12345678')
            installments = int(request.form.get('installments', 1))
            card_number = request.form.get('card_number', '').replace(' ', '')
            expiry_date = request.form.get('expiry_date', '')
            cvv = request.form.get('cvv', '')
            
            # Generar token simulado para pruebas
            token = f"TEST-CARD-TOKEN-{card_number[-4:]}-{expiry_date.replace('/', '')}-{cvv}"
            
            # Asegurar que el email del pagador sea válido
            payer_email = pago.email_pagador if pago.email_pagador else "test_user@test.com"
            
            # 3. Preparar datos para MercadoPago
            mp_payment_data = {
                "transaction_amount": float(pago.monto),
                "description": f"Pago para evento {getattr(pago.contratacion.evento, 'titulo', 'Evento')}",
                "token": token,
                "payment_method_id": payment_method_id,
                "payer": {
                    "email": payer_email,
                    "identification": {
                        "type": "DNI",
                        "number": identification_number
                    }
                },
                "installments": installments
            }
            
            # 4. Log de datos enviados
            print(f"📤 MERCADOPAGO - Datos enviados:")
            print(f"   - Monto: ${mp_payment_data['transaction_amount']}")
            print(f"   - Método: {mp_payment_data['payment_method_id']}")
            print(f"   - Email: {mp_payment_data['payer']['email']}")
            print(f"   - Cuotas: {mp_payment_data['installments']}")
            print(f"   - Token: {token[:20]}...")
            
            result = sdk.payment().create(mp_payment_data)
            
            # 5. Log del resultado
            print(f"📥 MERCADOPAGO - Respuesta:")
            print(f"   - Status: {result.get('status')}")
            print(f"   - Response: {json.dumps(result.get('response', {}), indent=2)}")
            
            status_code = result.get("status")
            response_data = result.get("response", {})
            
            # 6. Manejo de respuesta
            if status_code == 201:
                pago.id_transaccion = str(response_data.get("id"))
                pago.datos_adicionales = json.dumps(response_data)
                
                estado_mp = response_data.get("status", "rejected")
                print(f"✅ MERCADOPAGO - Pago creado. Estado: {estado_mp}")
                
                if estado_mp == "approved":
                    pago.estado = EstadoPago.aprobado
                    pago.fecha_aprobacion = datetime.utcnow()
                    return {"success": True, "message": "Pago aprobado con MercadoPago", "status": estado_mp}
                
                elif estado_mp == "pending":
                    pago.estado = EstadoPago.pendiente
                    return {"success": True, "message": "Pago pendiente de confirmación", "status": estado_mp}
                
                else:
                    pago.estado = EstadoPago.rechazado
                    status_detail = response_data.get('status_detail', 'Razón desconocida')
                    print(f"❌ MERCADOPAGO - Pago rechazado. Detalle: {status_detail}")
                    return {"success": False, "message": f"Pago rechazado: {status_detail}"}
            
            else:
                error_msg = response_data.get("message", "Error desconocido en MercadoPago")
                print(f"❌ MERCADOPAGO - Error: {error_msg}")
                pago.estado = EstadoPago.rechazado
                return {"success": False, "message": f"Error de MercadoPago: {error_msg}"}
        
        except Exception as e:
            print(f"💥 MERCADOPAGO - Excepción: {str(e)}")
            pago.estado = EstadoPago.rechazado
            return {"success": False, "message": f"Excepción en MercadoPago: {str(e)}"}
    
    @staticmethod
    def _actualizar_estado_pago(pago, payment_id):
        """Actualiza el estado de un pago desde MercadoPago"""
        try:
            access_token = current_app.config.get('MERCADOPAGO_ACCESS_TOKEN')
            sdk = mercadopago.SDK(access_token)
            
            # Obtener información actualizada del pago
            result = sdk.payment().get(payment_id)
            
            if result.get('status') == 200:
                response_data = result.get('response', {})
                estado_mp = response_data.get('status')
                
                if estado_mp == 'approved' and pago.estado != EstadoPago.aprobado:
                    pago.estado = EstadoPago.aprobado
                    pago.fecha_aprobacion = datetime.utcnow()
                    db.session.commit()
                    print(f"✅ Pago {pago.id} actualizado a APROBADO")
                
                elif estado_mp == 'rejected' and pago.estado != EstadoPago.rechazado:
                    pago.estado = EstadoPago.rechazado
                    db.session.commit()
                    print(f"❌ Pago {pago.id} actualizado a RECHAZADO")
        
        except Exception as e:
            print(f"❌ Error actualizando pago {pago.id}: {str(e)}")
    
    @staticmethod
    def _usuario_autenticado():
        """Verifica si el usuario está autenticado"""
        return 'user_id' in session
    
    @staticmethod
    def _acceso_no_autorizado():
        """Maneja el acceso no autorizado"""
        flash('Debes iniciar sesión para acceder a esta página', 'error')
        return redirect(url_for('usuario.login'))