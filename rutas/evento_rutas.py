# rutas de eventos
from flask import Blueprint
from controllers.evento_controller import EventoController

evento_bp = Blueprint('evento', __name__, url_prefix='/eventos')

# rutas para gestion de eventos
evento_bp.route('/crear', methods=['GET', 'POST'])(EventoController.crear_evento)
evento_bp.route('/listar')(EventoController.listar_eventos)
evento_bp.route('/<int:evento_id>')(EventoController.detalle_evento)
evento_bp.route('/<int:evento_id>/editar', methods=['GET', 'POST'])(EventoController.editar_evento)
evento_bp.route('/<int:evento_id>/activar', methods=['GET', 'POST'])(EventoController.activar_evento)
evento_bp.route('/<int:evento_id>/cancelar', methods=['GET', 'POST'])(EventoController.cancelar_evento)
evento_bp.route('/<int:evento_id>/completar', methods=['POST'])(EventoController.completar_evento)
evento_bp.route('/<int:evento_id>/finalizar', methods=['POST'])(EventoController.finalizar_evento)
evento_bp.route('/buscar')(EventoController.buscar_eventos)








