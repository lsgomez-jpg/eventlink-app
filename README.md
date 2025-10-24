# 🎉 EventLink - Plataforma de Gestión de Eventos

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://postgresql.org)
[![MercadoPago](https://img.shields.io/badge/MercadoPago-API-orange.svg)](https://mercadopago.com)

## 📋 Descripción

EventLink es una plataforma web que conecta organizadores de eventos con proveedores de servicios, facilitando la contratación y gestión de eventos únicos.

## 🚀 Características

- **👥 Gestión de Usuarios**: Registro y autenticación para organizadores y proveedores
- **🎉 Gestión de Eventos**: Creación, edición y seguimiento de eventos
- **🛍️ Catálogo de Servicios**: Búsqueda y contratación de servicios
- **💳 Pagos Integrados**: Integración con MercadoPago para pagos seguros
- **📊 Estadísticas**: Dashboard con métricas y análisis
- **🔔 Notificaciones**: Sistema de notificaciones en tiempo real
- **⭐ Reseñas**: Sistema de calificaciones y comentarios

## 🛠️ Tecnologías

- **Backend**: Python, Flask, SQLAlchemy
- **Base de Datos**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Pagos**: MercadoPago API
- **Patrones**: MVC, Factory, Observer, Singleton, Strategy

## 📦 Instalación

### Requisitos
- Python 3.8+
- PostgreSQL 12+
- pip

### Pasos

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/eventlink.git
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
createdb eventlink

# Configurar variables de entorno
export DATABASE_URL=postgresql://usuario:password@localhost/eventlink
export SECRET_KEY=tu-clave-secreta-aqui
export MERCADOPAGO_ACCESS_TOKEN=tu-token-mercadopago
```

5. **Inicializar base de datos**
```bash
python app.py
```

6. **Ejecutar aplicación**
```bash
python app.py
```

## 🏗️ Estructura del Proyecto

```
eventlink/
├── app.py                 # Aplicación principal
├── config.py             # Configuraciones
├── database.py           # Configuración de BD
├── requirements.txt      # Dependencias
├── controllers/          # Controladores MVC
├── models/              # Modelos de datos
├── rutas/               # Rutas de la aplicación
├── views/               # Templates y assets
│   ├── templates/       # Plantillas HTML
│   └── static/         # CSS, JS, imágenes
└── patterns/           # Patrones de diseño
```

## 🔧 Configuración

### Variables de Entorno
```bash
DATABASE_URL=postgresql://usuario:password@localhost/eventlink
SECRET_KEY=tu-clave-secreta-aqui
MERCADOPAGO_ACCESS_TOKEN=tu-token-mercadopago
FLASK_ENV=development  # o production
```

### Base de Datos
El proyecto usa PostgreSQL con SQLAlchemy como ORM. Las tablas se crean automáticamente al ejecutar la aplicación.

## 🚀 Uso

1. **Registro**: Los usuarios pueden registrarse como organizadores o proveedores
2. **Eventos**: Los organizadores pueden crear y gestionar eventos
3. **Servicios**: Los proveedores pueden ofrecer servicios
4. **Contratación**: Los organizadores pueden contratar servicios
5. **Pagos**: Integración con MercadoPago para pagos seguros

## 📊 API Endpoints

### Usuarios
- `POST /registro` - Registro de usuarios
- `POST /login` - Inicio de sesión
- `GET /perfil` - Perfil de usuario

### Eventos
- `GET /eventos` - Listar eventos
- `POST /eventos/crear` - Crear evento
- `PUT /eventos/<id>/editar` - Editar evento

### Servicios
- `GET /servicios` - Listar servicios
- `POST /servicios/crear` - Crear servicio
- `GET /servicios/buscar` - Buscar servicios

### Pagos
- `POST /pagos/mercadopago` - Procesar pago
- `GET /pagos/historial` - Historial de pagos

## 🧪 Testing

```bash
# Ejecutar tests
python -m pytest

# Con cobertura
python -m pytest --cov=.
```

## 📈 Performance

- **Optimización de assets**: CSS y JS minificados
- **Lazy loading**: Imágenes con carga diferida
- **Cache**: Service Worker para assets estáticos
- **CDN**: Recursos externos desde CDN

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👥 Autores

- **Tu Nombre** - *Desarrollo inicial* - [tu-github](https://github.com/tu-usuario)

## 🙏 Agradecimientos

- Flask y SQLAlchemy por el framework
- Bootstrap por el diseño
- MercadoPago por la integración de pagos
- PostgreSQL por la base de datos

## 📞 Contacto

- **Email**: tu-email@ejemplo.com
- **GitHub**: [tu-usuario](https://github.com/tu-usuario)
- **LinkedIn**: [tu-perfil](https://linkedin.com/in/tu-perfil)

---

⭐ **¡Si te gusta este proyecto, dale una estrella!** ⭐
