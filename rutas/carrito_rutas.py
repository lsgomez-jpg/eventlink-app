# rutas del carrito de compras
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from controllers.carrito_controller import CarritoController

# crear blueprint para el carrito
carrito_bp = Blueprint('carrito', __name__, url_prefix='/carrito')

# rutas del carrito
@carrito_bp.route('/')
def ver_carrito():
    # muestra el carrito del usuario
    return CarritoController.ver_carrito()

@carrito_bp.route('/agregar/<int:servicio_id>', methods=['GET', 'POST'])
def agregar_al_carrito(servicio_id):
    # agrega un servicio al carrito
    return CarritoController.agregar_al_carrito(servicio_id)

@carrito_bp.route('/editar/<int:item_id>')
def editar_item(item_id):
    # muestra el formulario para editar un item del carrito
    return CarritoController.editar_item(item_id)

@carrito_bp.route('/actualizar/<int:item_id>', methods=['POST'])
def actualizar_item(item_id):
    # actualiza un item del carrito
    return CarritoController.actualizar_item(item_id)

@carrito_bp.route('/eliminar/<int:item_id>')
def eliminar_item(item_id):
    # elimina un item del carrito
    return CarritoController.eliminar_item(item_id)

@carrito_bp.route('/procesar-pago', methods=['GET', 'POST'])
def procesar_pago():
    # muestra el formulario de pago o procesa el pago
    return CarritoController.procesar_pago()

@carrito_bp.route('/limpiar')
def limpiar_carrito():
    # limpia todo el carrito
    return CarritoController.limpiar_carrito()

@carrito_bp.route('/pago-mercadopago/<int:item_id>', methods=['GET', 'POST'])
def procesar_pago_mercadopago(item_id):
    # procesa el pago de un item con mercadopago
    return CarritoController.procesar_pago_mercadopago(item_id)

@carrito_bp.route('/pagar/<int:item_id>')
def pago_mercadopago(item_id):
    # procesa el pago de un item del carrito con mercadopago
    return CarritoController.pago_mercadopago(item_id)

@carrito_bp.route('/pago-exitoso')
def pago_exitoso():
    # maneja la respuesta exitosa de mercadopago
    return CarritoController.pago_exitoso()

@carrito_bp.route('/pago-fallido')
def pago_fallido():
    # maneja la respuesta de fallo de mercadopago
    return CarritoController.pago_fallido()

@carrito_bp.route('/pago-pendiente')
def pago_pendiente():
    # maneja la respuesta de pago pendiente de mercadopago
    return CarritoController.pago_pendiente()

@carrito_bp.route('/pagar-directo-mercadopago')
def pagar_directo_mercadopago():
    # redirige directamente a mercadopago sin formularios
    return CarritoController.pagar_directo_mercadopago()
