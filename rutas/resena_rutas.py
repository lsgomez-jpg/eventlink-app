# rutas de reseñas
# rutas para gestion de reseñas

from flask import Blueprint
from controllers.resena_controller import ResenaController

resena_bp = Blueprint('resena', __name__, url_prefix='/resenas')

# Rutas para gestión de reseñas
resena_bp.route('/crear/<int:contratacion_id>', methods=['GET', 'POST'])(ResenaController.crear_resena)
resena_bp.route('/ver/<int:resena_id>')(ResenaController.ver_resena)
resena_bp.route('/servicio/<int:servicio_id>')(ResenaController.listar_resenas_servicio)
resena_bp.route('/proveedor')(ResenaController.listar_resenas_proveedor)
resena_bp.route('/editar/<int:resena_id>', methods=['GET', 'POST'])(ResenaController.editar_resena)
resena_bp.route('/eliminar/<int:resena_id>')(ResenaController.eliminar_resena)
