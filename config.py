import os
from datetime import timedelta

class Config:
    # configuracion base de la aplicacion eventlink
    SECRET_KEY = os.environ.get("SECRET_KEY") or "eventlink-super-secret-key-2024"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # configuracion de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # configuracion de pagos
    MERCADOPAGO_ACCESS_TOKEN = os.environ.get("MERCADOPAGO_ACCESS_TOKEN")
    
    # configuracion de notificaciones
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    
    # configuracion de archivos
    UPLOAD_FOLDER = "static/uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}

class DevelopmentConfig(Config):
    # configuracion para desarrollo
    DEBUG = True
    SQLALCHEMY_ECHO = True
    # usar postgresql para desarrollo
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:Adrian0609@localhost/eventlink_db"

class TestingConfig(Config):
    # configuracion para testing
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

# diccionario de configuraciones
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}
