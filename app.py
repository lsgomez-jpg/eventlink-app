# aplicacion principal de eventlink
import os
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_mail import Mail
from config import config
from database import db
from dotenv import load_dotenv

# inicializar extensiones
migrate = Migrate()
mail = Mail()
load_dotenv()

def create_app(config_name=None):
    # factory function para crear la aplicacion flask
    app = Flask(__name__, template_folder='views/templates', static_folder='views/static')
    
    # configuracion
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # registrar blueprints
    register_blueprints(app)
    
    # registrar modelos para migraciones
    register_models()
    
    # configurar patrones de diseño
    configure_patterns()
    
    # rutas principales
    @app.route('/')
    def index():
        # pagina principal de eventlink
        return render_template('index.html')
    
    @app.route('/dashboard')
    def dashboard():
        # dashboard principal segun el rol del usuario
        from flask import session, redirect, url_for
        if 'user_id' not in session:
            return redirect(url_for('usuario.login'))
        
        if session['user_rol'] == 'organizador':
            return redirect(url_for('servicio.buscar_servicios'))
        elif session['user_rol'] == 'proveedor':
            return redirect(url_for('servicio.listar_servicios'))
        else:
            return redirect(url_for('index'))
    
    # manejo de errores
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from database import db
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # context processors
    @app.context_processor
    def inject_user():
        # inyecta informacion del usuario en todas las plantillas
        from flask import session
        if 'user_id' in session:
            try:
                from models.usuario import Usuario
                user = Usuario.query.get(session['user_id'])
                return dict(current_user=user)
            except Exception as e:
                # si hay error en la consulta no limpiar la sesion automaticamente
                print(f"Error en inject_user: {str(e)}")
                return dict(current_user=None)
        return dict(current_user=None)
    
    @app.context_processor
    def inject_config():
        # inyecta configuracion en todas las plantillas
        return dict(
            app_name="EventLink",
            app_version="1.0.0"
        )
    
    return app

def register_blueprints(app):
    # registra todos los blueprints de la aplicacion
    from rutas import (
        usuario_bp, evento_bp, servicio_bp, 
        contratacion_bp, pago_bp, carrito_bp,
        resena_bp, notificacion_bp
    )
    
    # registrar blueprints
    app.register_blueprint(usuario_bp)
    app.register_blueprint(evento_bp)
    app.register_blueprint(servicio_bp)
    app.register_blueprint(contratacion_bp)
    app.register_blueprint(pago_bp)
    app.register_blueprint(carrito_bp)
    app.register_blueprint(resena_bp)
    app.register_blueprint(notificacion_bp)

def register_models():
    # registra todos los modelos para las migraciones
    from models import (
        Usuario, Evento, Servicio, Contratacion, 
        Calificacion, Notificacion, Pago, CarritoItem
    )

def configure_patterns():
    # los patrones se configuran automaticamente al importar los modulos
    # factory observer singleton y strategy estan listos para usar
    pass

# crear la aplicacion
app = create_app()

if __name__ == "__main__":
    # crear tablas si no existen
    with app.app_context():
        from database import db
        db.create_all()
        print("✅ Base de datos inicializada")
    
    # ejecutar la aplicacion
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config['DEBUG']
    )
