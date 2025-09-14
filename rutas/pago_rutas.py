# rutas de pagos
# rutas para gestion de pagos con mercadopago

from flask import Blueprint
from controllers.pago_controller import PagoController

pago_bp = Blueprint('pago', __name__, url_prefix='/pagos')

# Rutas para gestión de pagos (solo MercadoPago)
pago_bp.route('/procesar/<int:contratacion_id>', methods=['GET', 'POST'])(PagoController.procesar_pago)
pago_bp.route('/detalle/<int:pago_id>')(PagoController.detalle_pago)
pago_bp.route('/historial')(PagoController.historial_pagos)
pago_bp.route('/webhook/mercadopago', methods=['POST'])(PagoController.webhook_mercadopago)







