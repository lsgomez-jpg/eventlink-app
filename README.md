# EventLink

EventLink es una plataforma web que conecta organizadores de eventos con proveedores de servicios (catering, fotografía, sonido, decoración, logística, etc.). La plataforma permite a los usuarios buscar, comparar, contratar y pagar servicios de forma segura y centralizada.

## Características Principales

### Para Organizadores
- ✅ Registro y gestión de perfil
- ✅ Creación y gestión de eventos
- ✅ Búsqueda de servicios con filtros avanzados
- ✅ Contratación y pago seguro de servicios
- ✅ Sistema de calificaciones y reseñas
- ✅ Notificaciones en tiempo real

### Para Proveedores
- ✅ Registro y gestión de perfil de servicios
- ✅ Catálogo de servicios con precios flexibles
- ✅ Recepción de solicitudes y contrataciones
- ✅ Gestión de disponibilidad
- ✅ Sistema de pagos garantizados
- ✅ Construcción de reputación

### Funcionalidades Generales
- 🔐 Autenticación y autorización segura
- 💳 Pasarelas de pago integradas (Stripe, MercadoPago)
- 📱 Diseño responsive y moderno
- 🔔 Sistema de notificaciones
- ⭐ Sistema de calificaciones
- 📊 Dashboard con estadísticas

## Arquitectura y Principios

### Principios SOLID
- **S** - Single Responsibility: Cada módulo tiene una única responsabilidad
- **O** - Open/Closed: Abierto a extensión, cerrado a modificación
- **L** - Liskov Substitution: Las clases hijas pueden sustituir a las clases base
- **I** - Interface Segregation: Interfaces específicas para cada rol
- **D** - Dependency Inversion: Depende de abstracciones, no de implementaciones

### Patrones de Diseño Implementados
- **MVC**: Separación clara entre Modelo, Vista y Controlador
- **Factory Method**: Creación dinámica de servicios y notificaciones
- **Observer**: Sistema de notificaciones en tiempo real
- **Singleton**: Gestión de conexiones y pasarelas de pago
- **Strategy**: Diferentes estrategias de búsqueda de servicios

## Estructura del Proyecto

```
eventlink/
├── app.py                 # Aplicación principal
├── config.py             # Configuraciones
├── requirements.txt      # Dependencias
├── models/               # Modelos de datos
│   ├── __init__.py
│   ├── usuario.py
│   ├── evento.py
│   ├── servicio.py
│   ├── contratacion.py
│   ├── calificacion.py
│   └── notificacion.py
├── controllers/          # Controladores (Lógica de negocio)
│   ├── __init__.py
│   ├── usuario_controller.py
│   ├── evento_controller.py
│   ├── servicio_controller.py
│   ├── contratacion_controller.py
│   └── pago_controller.py
├── patterns/             # Patrones de diseño
│   ├── __init__.py
│   ├── factory.py
│   ├── observer.py
│   ├── singleton.py
│   └── strategy.py
├── rutas/               # Rutas y blueprints
│   ├── __init__.py
│   ├── usuario_rutas.py
│   ├── evento_rutas.py
│   ├── servicio_rutas.py
│   ├── contratacion_rutas.py
│   └── pago_rutas.py
└── views/               # Vistas y plantillas
    ├── templates/
    │   ├── base.html
    │   ├── index.html
    │   ├── login.html
    │   ├── registro.html
    │   └── errors/
    └── static/
        ├── css/
        └── js/
```

## Instalación y Configuración

### Requisitos Previos
- Python 3.8+
- PostgreSQL 12+
- pip

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd eventlink
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos**
```bash
# Crear base de datos PostgreSQL
createdb eventlink_db

# Configurar variables de entorno
export DATABASE_URL="postgresql://usuario:contraseña@localhost/eventlink_db"
export SECRET_KEY="tu-clave-secreta-aqui"
```

5. **Inicializar base de datos**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. **Ejecutar la aplicación**
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## Configuración de Variables de Entorno

```bash
# Base de datos
DATABASE_URL=postgresql://usuario:contraseña@localhost/eventlink_db

# Seguridad
SECRET_KEY=tu-clave-secreta-muy-segura

# Email (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-contraseña-de-aplicacion

# Pagos (opcional)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
MERCADOPAGO_ACCESS_TOKEN=TEST-...

# Entorno
FLASK_ENV=development  # o production
```

## Uso de la Aplicación

### Registro de Usuarios
1. Acceder a `/usuario/registro`
2. Seleccionar rol (Organizador o Proveedor)
3. Completar información personal
4. Verificar email (si está configurado)

### Para Organizadores
1. **Crear Evento**: `/eventos/crear`
2. **Buscar Servicios**: `/servicios/buscar`
3. **Gestionar Contrataciones**: `/contrataciones/listar`
4. **Realizar Pagos**: `/pagos/procesar/<id>`

### Para Proveedores
1. **Crear Servicio**: `/servicios/crear`
2. **Buscar Eventos**: `/eventos/buscar`
3. **Gestionar Solicitudes**: `/contrataciones/listar`
4. **Ver Pagos**: `/pagos/historial`

## API Endpoints

### Autenticación
- `POST /usuario/registro` - Registro de usuario
- `POST /usuario/login` - Inicio de sesión
- `GET /usuario/logout` - Cerrar sesión

### Eventos
- `GET /eventos/listar` - Listar eventos del usuario
- `POST /eventos/crear` - Crear nuevo evento
- `GET /eventos/<id>` - Ver detalle de evento
- `PUT /eventos/<id>/editar` - Editar evento

### Servicios
- `GET /servicios/listar` - Listar servicios del proveedor
- `POST /servicios/crear` - Crear nuevo servicio
- `GET /servicios/buscar` - Buscar servicios
- `POST /servicios/<id>/solicitar` - Solicitar servicio

### Contrataciones
- `GET /contrataciones/listar` - Listar contrataciones
- `POST /contrataciones/<id>/aceptar` - Aceptar contratación
- `POST /contrataciones/<id>/rechazar` - Rechazar contratación
- `POST /contrataciones/<id>/completar` - Completar servicio

### Pagos
- `POST /pagos/procesar/<id>` - Procesar pago
- `GET /pagos/historial` - Historial de pagos
- `GET /pagos/estadisticas` - Estadísticas de pagos

## Tecnologías Utilizadas

### Backend
- **Flask**: Framework web
- **SQLAlchemy**: ORM para base de datos
- **PostgreSQL**: Base de datos relacional
- **Flask-Migrate**: Migraciones de base de datos
- **Flask-Mail**: Envío de emails

### Frontend
- **Bootstrap 5**: Framework CSS
- **Font Awesome**: Iconos
- **JavaScript**: Interactividad
- **Jinja2**: Motor de plantillas

### Pagos
- **Stripe**: Pasarela de pago internacional
- **MercadoPago**: Pasarela de pago latinoamericana

### Patrones y Arquitectura
- **MVC**: Arquitectura de aplicación
- **SOLID**: Principios de diseño
- **Factory Pattern**: Creación de objetos
- **Observer Pattern**: Notificaciones
- **Singleton Pattern**: Recursos compartidos
- **Strategy Pattern**: Algoritmos de búsqueda

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Para soporte técnico o preguntas:
- Email: soporte@eventlink.com
- Documentación: [docs.eventlink.com](https://docs.eventlink.com)
- Issues: [GitHub Issues](https://github.com/eventlink/issues)

## Roadmap

### Versión 1.1
- [ ] Integración con mapas
- [ ] Chat en tiempo real
- [ ] Aplicación móvil
- [ ] API REST completa

### Versión 1.2
- [ ] Sistema de subastas
- [ ] Paquetes de servicios
- [ ] Análisis avanzado
- [ ] Integración con redes sociales

---

**EventLink** - Conectando el mundo de los eventos 🎉












