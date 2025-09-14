# rutas de notificaciones
# rutas para gestion de notificaciones

from flask import Blueprint
from controllers.notificacion_controller import NotificacionController

notificacion_bp = Blueprint('notificacion', __name__, url_prefix='/notificaciones')

# Rutas para gestión de notificaciones
notificacion_bp.route('/')(NotificacionController.listar_notificaciones)
notificacion_bp.route('/marcar-leida/<int:notificacion_id>')(NotificacionController.marcar_como_leida)
notificacion_bp.route('/archivar/<int:notificacion_id>')(NotificacionController.archivar_notificacion)
notificacion_bp.route('/marcar-todas-leidas')(NotificacionController.marcar_todas_como_leidas)
notificacion_bp.route('/api/no-leidas')(NotificacionController.obtener_notificaciones_no_leidas)
