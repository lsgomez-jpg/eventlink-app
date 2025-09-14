# rutas de usuarios
from flask import Blueprint
from controllers.usuario_controller import UsuarioController

usuario_bp = Blueprint('usuario', __name__, url_prefix='/usuario')

# rutas para gestion de usuarios
usuario_bp.route('/registro', methods=['GET', 'POST'])(UsuarioController.registro)
usuario_bp.route('/login', methods=['GET', 'POST'])(UsuarioController.login)
usuario_bp.route('/logout')(UsuarioController.logout)
usuario_bp.route('/perfil', methods=['GET', 'POST'])(UsuarioController.perfil)
usuario_bp.route('/cambiar-contraseña', methods=['GET', 'POST'])(UsuarioController.cambiar_contraseña)
usuario_bp.route('/estadisticas')(UsuarioController.estadisticas)
usuario_bp.route('/desactivar-cuenta', methods=['GET', 'POST'])(UsuarioController.desactivar_cuenta)
