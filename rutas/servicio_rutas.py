# rutas de servicios
from flask import Blueprint
from controllers.servicio_controller import ServicioController

servicio_bp = Blueprint('servicio', __name__, url_prefix='/servicios')

# rutas para gestion de servicios
servicio_bp.route('/crear', methods=['GET', 'POST'])(ServicioController.crear_servicio)
servicio_bp.route('/listar')(ServicioController.listar_servicios)
servicio_bp.route('/<int:servicio_id>')(ServicioController.detalle_servicio)
servicio_bp.route('/<int:servicio_id>/editar', methods=['GET', 'POST'])(ServicioController.editar_servicio)
servicio_bp.route('/<int:servicio_id>/activar', methods=['GET', 'POST'])(ServicioController.activar_servicio)
servicio_bp.route('/<int:servicio_id>/desactivar', methods=['GET', 'POST'])(ServicioController.desactivar_servicio)
servicio_bp.route('/<int:servicio_id>/solicitar', methods=['GET', 'POST'])(ServicioController.solicitar_servicio)
servicio_bp.route('/buscar', endpoint='buscar_servicios')(ServicioController.buscar_servicios)
servicio_bp.route('/catalogo', endpoint='catalogo_servicios')(ServicioController.catalogo_servicios)
servicio_bp.route('/<int:servicio_id>/agregar-carrito', methods=['GET', 'POST'])(ServicioController.agregar_al_carrito_desde_detalle)
servicio_bp.route('/api/evento/<int:evento_id>/datos')(ServicioController.obtener_datos_evento)




