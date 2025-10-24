#!/usr/bin/env node

/**
 * EventLink File Cleanup Script
 * Elimina archivos duplicados, temporales e innecesarios
 * Prepara el proyecto para GitHub
 */

const fs = require('fs-extra');
const path = require('path');

class EventLinkFileCleaner {
    constructor() {
        this.removedFiles = [];
        this.removedDirs = [];
        this.stats = {
            filesRemoved: 0,
            dirsRemoved: 0,
            spaceSaved: 0
        };
    }

    async init() {
        console.log('🧹 EventLink File Cleanup iniciado');
        console.log('📊 Eliminando archivos duplicados e innecesarios...');
    }

    async removeDuplicateFiles() {
        console.log('\n🗑️ Eliminando archivos duplicados...');
        
        // Archivos duplicados identificados
        const duplicates = [
            // Archivos de build duplicados
            'views/static/css/bundle.min.css',
            'views/static/css/critical.min.css', 
            'views/static/js/bundle.min.js',
            'views/static/sw.js',
            'views/templates/index_optimized.html',
            
            // Archivos de reportes temporales
            'cleanup_report.json',
            'detailed_analysis.json',
            'integration_report.json',
            'optimized_routes.py',
            
            // Directorio clean/ (código limpio ya integrado)
            'clean/'
        ];
        
        for (const file of duplicates) {
            if (await fs.pathExists(file)) {
                const stats = await fs.stat(file);
                if (stats.isDirectory()) {
                    await fs.remove(file);
                    this.removedDirs.push(file);
                    this.stats.dirsRemoved++;
                    console.log(`  ✅ Directorio eliminado: ${file}`);
                } else {
                    await fs.remove(file);
                    this.removedFiles.push(file);
                    this.stats.filesRemoved++;
                    this.stats.spaceSaved += stats.size;
                    console.log(`  ✅ Archivo eliminado: ${file} (${(stats.size / 1024).toFixed(2)} KB)`);
                }
            }
        }
    }

    async removeBuildFiles() {
        console.log('\n🗑️ Eliminando archivos de build...');
        
        const buildFiles = [
            'dist/',
            'node_modules/',
            'package-lock.json'
        ];
        
        for (const file of buildFiles) {
            if (await fs.pathExists(file)) {
                const stats = await fs.stat(file);
                if (stats.isDirectory()) {
                    await fs.remove(file);
                    this.removedDirs.push(file);
                    this.stats.dirsRemoved++;
                    console.log(`  ✅ Directorio de build eliminado: ${file}`);
                } else {
                    await fs.remove(file);
                    this.removedFiles.push(file);
                    this.stats.filesRemoved++;
                    this.stats.spaceSaved += stats.size;
                    console.log(`  ✅ Archivo de build eliminado: ${file}`);
                }
            }
        }
    }

    async removeCacheFiles() {
        console.log('\n🗑️ Eliminando archivos de cache...');
        
        const cachePatterns = [
            '**/__pycache__/',
            '**/*.pyc',
            '**/*.pyo',
            '**/*.pyd',
            '**/.pytest_cache/',
            '**/.coverage',
            '**/htmlcov/',
            '**/.mypy_cache/',
            '**/.tox/',
            '**/.venv/',
            '**/venv/',
            '**/env/',
            '**/.env'
        ];
        
        for (const pattern of cachePatterns) {
            const files = await this.findFiles(pattern);
            for (const file of files) {
                if (await fs.pathExists(file)) {
                    const stats = await fs.stat(file);
                    if (stats.isDirectory()) {
                        await fs.remove(file);
                        this.removedDirs.push(file);
                        this.stats.dirsRemoved++;
                        console.log(`  ✅ Cache eliminado: ${file}`);
                    } else {
                        await fs.remove(file);
                        this.removedFiles.push(file);
                        this.stats.filesRemoved++;
                        this.stats.spaceSaved += stats.size;
                        console.log(`  ✅ Cache eliminado: ${file}`);
                    }
                }
            }
        }
    }

    async findFiles(pattern) {
        const files = [];
        const dirs = ['.'];
        
        for (const dir of dirs) {
            if (await fs.pathExists(dir)) {
                const items = await fs.readdir(dir);
                for (const item of items) {
                    const fullPath = path.join(dir, item);
                    const stat = await fs.stat(fullPath);
                    
                    if (stat.isDirectory()) {
                        if (item.includes('__pycache__') || item.includes('.pytest_cache') || 
                            item.includes('.mypy_cache') || item.includes('.tox') ||
                            item.includes('venv') || item.includes('env')) {
                            files.push(fullPath);
                        }
                    } else if (item.endsWith('.pyc') || item.endsWith('.pyo') || 
                               item.endsWith('.pyd') || item.endsWith('.coverage')) {
                        files.push(fullPath);
                    }
                }
            }
        }
        
        return files;
    }

    async removeUnnecessaryFiles() {
        console.log('\n🗑️ Eliminando archivos innecesarios...');
        
        const unnecessary = [
            // Archivos de desarrollo
            'src/',
            'package.json',
            'package-lock.json',
            
            // Archivos de reportes
            'LIMPIEZA_PROFUNDA_REPORTE.md',
            
            // Archivos temporales
            '*.tmp',
            '*.temp',
            '*.log',
            '*.bak',
            '*.swp',
            '*.swo',
            '*~'
        ];
        
        for (const file of unnecessary) {
            if (await fs.pathExists(file)) {
                const stats = await fs.stat(file);
                if (stats.isDirectory()) {
                    await fs.remove(file);
                    this.removedDirs.push(file);
                    this.stats.dirsRemoved++;
                    console.log(`  ✅ Directorio innecesario eliminado: ${file}`);
                } else {
                    await fs.remove(file);
                    this.removedFiles.push(file);
                    this.stats.filesRemoved++;
                    this.stats.spaceSaved += stats.size;
                    console.log(`  ✅ Archivo innecesario eliminado: ${file}`);
                }
            }
        }
    }

    async createGitIgnore() {
        console.log('\n📝 Creando .gitignore optimizado...');
        
        const gitignoreContent = `# EventLink - .gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# EventLink specific
uploads/
*.db
*.sqlite
*.sqlite3

# Build files
dist/
build/
*.min.js
*.min.css

# Node.js (if used)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
*.bak
*.swp
*.swo
*~

# Reports
*.json
!package.json
!package-lock.json
`;

        await fs.writeFile('.gitignore', gitignoreContent);
        console.log('  ✅ .gitignore creado');
    }

    async createReadme() {
        console.log('\n📝 Creando README.md para GitHub...');
        
        const readmeContent = `# 🎉 EventLink - Plataforma de Gestión de Eventos

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
\`\`\`bash
git clone https://github.com/tu-usuario/eventlink.git
cd eventlink
\`\`\`

2. **Crear entorno virtual**
\`\`\`bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\\Scripts\\activate
\`\`\`

3. **Instalar dependencias**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. **Configurar base de datos**
\`\`\`bash
# Crear base de datos PostgreSQL
createdb eventlink

# Configurar variables de entorno
export DATABASE_URL=postgresql://usuario:password@localhost/eventlink
export SECRET_KEY=tu-clave-secreta-aqui
export MERCADOPAGO_ACCESS_TOKEN=tu-token-mercadopago
\`\`\`

5. **Inicializar base de datos**
\`\`\`bash
python app.py
\`\`\`

6. **Ejecutar aplicación**
\`\`\`bash
python app.py
\`\`\`

## 🏗️ Estructura del Proyecto

\`\`\`
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
\`\`\`

## 🔧 Configuración

### Variables de Entorno
\`\`\`bash
DATABASE_URL=postgresql://usuario:password@localhost/eventlink
SECRET_KEY=tu-clave-secreta-aqui
MERCADOPAGO_ACCESS_TOKEN=tu-token-mercadopago
FLASK_ENV=development  # o production
\`\`\`

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
- \`POST /registro\` - Registro de usuarios
- \`POST /login\` - Inicio de sesión
- \`GET /perfil\` - Perfil de usuario

### Eventos
- \`GET /eventos\` - Listar eventos
- \`POST /eventos/crear\` - Crear evento
- \`PUT /eventos/<id>/editar\` - Editar evento

### Servicios
- \`GET /servicios\` - Listar servicios
- \`POST /servicios/crear\` - Crear servicio
- \`GET /servicios/buscar\` - Buscar servicios

### Pagos
- \`POST /pagos/mercadopago\` - Procesar pago
- \`GET /pagos/historial\` - Historial de pagos

## 🧪 Testing

\`\`\`bash
# Ejecutar tests
python -m pytest

# Con cobertura
python -m pytest --cov=.
\`\`\`

## 📈 Performance

- **Optimización de assets**: CSS y JS minificados
- **Lazy loading**: Imágenes con carga diferida
- **Cache**: Service Worker para assets estáticos
- **CDN**: Recursos externos desde CDN

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (\`git checkout -b feature/AmazingFeature\`)
3. Commit tus cambios (\`git commit -m 'Add some AmazingFeature'\`)
4. Push a la rama (\`git push origin feature/AmazingFeature\`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver \`LICENSE\` para más detalles.

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
`;

        await fs.writeFile('README.md', readmeContent);
        console.log('  ✅ README.md creado');
    }

    async createLicense() {
        console.log('\n📝 Creando LICENSE...');
        
        const licenseContent = `MIT License

Copyright (c) 2024 EventLink

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
`;

        await fs.writeFile('LICENSE', licenseContent);
        console.log('  ✅ LICENSE creado');
    }

    async generateReport() {
        console.log('\n📊 Generando reporte de limpieza...');
        
        const report = {
            timestamp: new Date().toISOString(),
            stats: this.stats,
            removedFiles: this.removedFiles,
            removedDirs: this.removedDirs,
            spaceSaved: this.stats.spaceSaved,
            recommendations: [
                '1. Revisar archivos eliminados antes de commit',
                '2. Configurar variables de entorno',
                '3. Actualizar documentación si es necesario',
                '4. Probar la aplicación después de la limpieza'
            ]
        };
        
        await fs.writeFile('cleanup_files_report.json', JSON.stringify(report, null, 2));
        console.log('  ✅ Reporte generado en cleanup_files_report.json');
    }

    async run() {
        try {
            await this.init();
            await this.removeDuplicateFiles();
            await this.removeBuildFiles();
            await this.removeCacheFiles();
            await this.removeUnnecessaryFiles();
            await this.createGitIgnore();
            await this.createReadme();
            await this.createLicense();
            await this.generateReport();
            
            console.log('\n🎉 Limpieza de archivos completada!');
            console.log('\n📊 Estadísticas finales:');
            console.log(`  🗑️ Archivos eliminados: ${this.stats.filesRemoved}`);
            console.log(`  📁 Directorios eliminados: ${this.stats.dirsRemoved}`);
            console.log(`  💾 Espacio liberado: ${(this.stats.spaceSaved / 1024 / 1024).toFixed(2)} MB`);
            
            console.log('\n📁 Archivos creados para GitHub:');
            console.log('  ✅ .gitignore');
            console.log('  ✅ README.md');
            console.log('  ✅ LICENSE');
            console.log('  ✅ cleanup_files_report.json');
            
            console.log('\n🚀 Proyecto listo para GitHub!');
            console.log('\n📋 Próximos pasos:');
            console.log('1. git init');
            console.log('2. git add .');
            console.log('3. git commit -m "Initial commit"');
            console.log('4. git remote add origin https://github.com/tu-usuario/eventlink.git');
            console.log('5. git push -u origin main');
            
        } catch (error) {
            console.error('❌ Error durante la limpieza:', error);
            process.exit(1);
        }
    }
}

// Ejecutar limpiador
if (require.main === module) {
    const cleaner = new EventLinkFileCleaner();
    cleaner.run();
}

module.exports = EventLinkFileCleaner;
