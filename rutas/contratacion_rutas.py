# rutas de contrataciones
from flask import Blueprint
from controllers.contratacion_controller import ContratacionController

contratacion_bp = Blueprint('contratacion', __name__, url_prefix='/contrataciones')

# rutas para gestion de contrataciones
contratacion_bp.route('/listar')(ContratacionController.listar_contrataciones)
contratacion_bp.route('/<int:contratacion_id>')(ContratacionController.detalle_contratacion)
contratacion_bp.route('/<int:contratacion_id>/aceptar', methods=['GET', 'POST'])(ContratacionController.aceptar_contratacion)
contratacion_bp.route('/<int:contratacion_id>/rechazar', methods=['GET', 'POST'])(ContratacionController.rechazar_contratacion)
contratacion_bp.route('/<int:contratacion_id>/confirmar', methods=['POST'])(ContratacionController.confirmar_contratacion)
contratacion_bp.route('/<int:contratacion_id>/iniciar', methods=['POST'])(ContratacionController.iniciar_servicio)
contratacion_bp.route('/<int:contratacion_id>/completar', methods=['POST'])(ContratacionController.completar_servicio)
contratacion_bp.route('/<int:contratacion_id>/cancelar', methods=['GET', 'POST'])(ContratacionController.cancelar_contratacion)
contratacion_bp.route('/<int:contratacion_id>/calificar', methods=['GET', 'POST'])(ContratacionController.calificar_servicio)












