# rutas de pagos
# rutas para gestion de pagos con mercadopago

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from controllers.pago_controller import PagoController
from models.contratacion import Contratacion

pago_bp = Blueprint('pagos', __name__, url_prefix='/pagos')

@pago_bp.route('/procesar/<int:contratacion_id>', methods=['GET', 'POST'])
def procesar_pago(contratacion_id):
    contratacion = Contratacion.query.get_or_404(contratacion_id)
    
    if request.method == 'GET':
        # mostrar formulario de pago con template mínimo
        return render_template('pagos/pago_sin_sdk.html', contratacion=contratacion)
    
    elif request.method == 'POST':
        try:
            if request.is_json:
                # datos enviados desde el frontend (MercadoPago Checkout API)
                datos_json = request.get_json()
                print(f"📥 Datos recibidos del frontend: {datos_json}")

                datos_form = {
                    'email_pagador': datos_json.get('email_pagador'),
                    'nombre_titular': datos_json.get('nombre_titular'),
                    'documento_pagador': datos_json.get('documento_pagador'),
                    'tipo_documento': datos_json.get('tipo_documento'),
                }

                # procesar con PagoController
                resultado = PagoController.procesar_pago(contratacion, datos_form, datos_json)
                print(f"📤 Resultado del procesamiento: {resultado}")
                return jsonify(resultado)

            else:
                # procesamiento tradicional (no se usa en Checkout API, pero lo dejo por compatibilidad)
                datos_form = {
                    'email_pagador': request.form.get('email_pagador'),
                    'nombre_titular': request.form.get('nombre_titular'),
                    'documento_pagador': request.form.get('documento_pagador'),
                    'tipo_documento': request.form.get('tipo_documento'),
                }

                # procesar con PagoController
                resultado = PagoController.procesar_pago(contratacion, datos_form, None)
                
                if resultado['success']:
                    flash('Pago procesado exitosamente', 'success')
                    return redirect(url_for('pagos.detalle_pago', pago_id=resultado['pago_id']))
                else:
                    flash(f'Error al procesar el pago: {resultado["message"]}', 'error')
                    return render_template('pagos/pago_sin_sdk.html', contratacion=contratacion)
                
        except Exception as e:
            if request.is_json:
                return jsonify({'success': False, 'message': f'Error interno: {str(e)}'})
            else:
                flash(f'Error interno: {str(e)}', 'error')
                return render_template('pagos/pago_sin_sdk.html', contratacion=contratacion)

@pago_bp.route('/detalle/<int:pago_id>')
def detalle_pago(pago_id):
    # detalle del pago (usando el mismo template que pago_exitoso)
    from models.pago import Pago
    pago = Pago.query.get_or_404(pago_id)
    return render_template('pagos/pago_exitoso.html', pago=pago)

@pago_bp.route('/historial')
def historial_pagos():
    # historial de pagos del usuario actual
    from flask import session
    from models.pago import Pago
    from models.contratacion import Contratacion
    
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tu historial de pagos', 'error')
        return redirect(url_for('usuario.login'))
    
    # obtener pagos del usuario actual (como organizador o proveedor)
    from models.servicio import Servicio
    
    # Pagos donde el usuario es el organizador (quien paga)
    pagos_organizador = Pago.query.filter_by(organizador_id=session['user_id']).all()
    
    # Pagos donde el usuario es el proveedor (quien recibe)
    pagos_proveedor = Pago.query.join(Contratacion).join(Servicio).filter(
        Servicio.proveedor_id == session['user_id']
    ).all()
    
    # Combinar y ordenar por fecha
    todos_pagos = pagos_organizador + pagos_proveedor
    pagos = sorted(todos_pagos, key=lambda p: p.fecha_creacion, reverse=True)
    
    return render_template('pagos/historial_pagos.html', pagos=pagos)

@pago_bp.route('/webhook/mercadopago', methods=['POST'])
def webhook_mercadopago():
    # implementar webhook de mercadopago
    return "Webhook de MercadoPago"

@pago_bp.route('/exito/<int:pago_id>')
def pago_exitoso(pago_id):
    # pagina de exito del pago
    from models.pago import Pago
    pago = Pago.query.get_or_404(pago_id)
    return render_template('pagos/pago_exitoso.html', pago=pago)
