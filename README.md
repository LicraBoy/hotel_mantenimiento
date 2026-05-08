# 🏨 Hotel Mantenimiento

> Sistema integral de gestión de mantenimiento hotelero con **Inteligencia Artificial** integrada.

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?logo=postgresql)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📌 Descripción

**Hotel Mantenimiento** es una plataforma web completa para la gestión operacional de hoteles. Permite controlar habitaciones, reportar y hacer seguimiento de fallas, gestionar técnicos, planificar inspecciones y generar reportes analíticos. Incluye módulos de **IA y visión computacional** para detección de problemas, predicción de mantenimiento y priorización inteligente de tareas.

---

## ✨ Funcionalidades Principales

| Módulo | Descripción |
|---|---|
| 🏠 **Habitaciones** | Gestión completa del estado de habitaciones |
| 🔧 **Mantenimiento** | Registro, seguimiento y cierre de órdenes de trabajo |
| 🔍 **Inspecciones** | Control de calidad e inspecciones programadas |
| 🧹 **Limpieza** | Hoja de limpieza con priorización por IA |
| 🤖 **Predicciones** | Mantenimiento predictivo con Machine Learning |
| 👁️ **Visión IA** | Detección visual de daños con YOLOv8 |
| 💰 **Costos** | Análisis y predicción de costos de mantenimiento |
| 👷 **Técnicos** | Gestión de técnicos con recomendación automática |
| ⚙️ **Automatización** | Flujos y reglas de trabajo automatizados |
| 📊 **Análisis** | Dashboard de inteligencia analítica y KPIs |
| 🛠️ **Equipos** | Inventario y seguimiento de equipos/activos |

---

## 🛠️ Stack Tecnológico

- **Backend**: Flask 3.x (Blueprints, SocketIO, CSRF, Rate Limiting)
- **Base de datos**: PostgreSQL 16 (via psycopg2)
- **IA / ML**: Ultralytics YOLOv8, scikit-learn
- **Tiempo real**: Flask-SocketIO (WebSockets)
- **Seguridad**: Werkzeug password hashing, Flask-WTF, Flask-Limiter
- **Reportes**: ReportLab (PDF)
- **Contenedores**: Docker & Docker Compose

---

## 📋 Requisitos Previos

- [Python 3.12+](https://www.python.org/downloads/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para PostgreSQL)
- [Git](https://git-scm.com/downloads)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/LicraBoy/hotel_mantenimiento.git
cd hotel_mantenimiento
```

### 2. Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # Linux / macOS
```

Edita `.env` con tus valores:

```env
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/hotel_mantenimiento
SECRET_KEY=tu_clave_secreta_segura
```

> 💡 Genera una `SECRET_KEY` segura con:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 5. Levantar la base de datos (Docker)

```bash
docker-compose up -d
```

### 6. Ejecutar la aplicación

```bash
python app.py
```

Las tablas se crean automáticamente al iniciar. La aplicación estará disponible en:
**http://localhost:5000**

---

## 📁 Estructura del Proyecto

```
hotel_mantenimiento/
│
├── 📄 app.py                   # Entry point + Application Factory
├── 📄 config.py                # Configuración (SECRET_KEY, DB, seguridad)
├── 📄 extensions.py            # SocketIO, CSRF, Limiter (extensiones Flask)
├── 📄 docker-compose.yml       # Contenedor PostgreSQL
├── 📄 requirements.txt         # Dependencias Python
├── 📄 .env.example             # Plantilla de variables de entorno
│
├── 📂 routes/                  # 🌐 Blueprints Flask (lógica de vistas)
│   ├── auth.py                 # Login / Logout
│   ├── dashboard.py            # Panel principal
│   ├── habitaciones.py         # Gestión de habitaciones
│   ├── mantenimiento.py        # Órdenes de mantenimiento ← flujo principal
│   ├── inspecciones.py         # Inspecciones de calidad
│   ├── limpieza.py             # Hoja de limpieza
│   ├── equipos.py              # Activos y equipos
│   ├── tecnicos.py             # Gestión de técnicos
│   ├── costos.py               # Análisis de costos
│   ├── analisis.py             # Dashboard analítico / KPIs
│   ├── reportes.py             # Generación de reportes PDF/Excel
│   ├── automatizacion.py       # Flujos automatizados
│   ├── operaciones.py          # Vista operacional
│   ├── predicciones.py         # AI: mantenimiento predictivo
│   ├── vision.py               # AI: detección visual
│   └── admin.py                # Administración de usuarios
│
├── 📂 templates/               # 🎨 Vistas HTML (Jinja2)
│   └── *.html                  # 34 templates
│
├── 📂 static/                  # 📁 Archivos estáticos
│   ├── css/                    # Estilos CSS
│   └── uploads/                # Imágenes subidas (gitignored)
│
├── 📂 ai/                      # 🤖 Módulos de Inteligencia Artificial
│   ├── predictor.py            # Predicción de fallas (ML)
│   ├── cost_predictor.py       # Predicción de costos
│   ├── detector.py             # Detección visual (YOLOv8)
│   ├── scoring_engine.py       # Motor de puntuación
│   ├── maintenance_scheduler.py# Planificador de mantenimiento
│   ├── technician_recommender.py# Recomendación de técnicos
│   ├── feature_utils.py        # Utilidades de features ML
│   ├── services/               # Capa de servicio (bridge routes ↔ AI)
│   │   ├── prediction_service.py
│   │   ├── cost_service.py
│   │   ├── cleaning_service.py
│   │   ├── technician_service.py
│   │   ├── vision_service.py
│   │   ├── scheduler_service.py
│   │   └── operations_service.py
│   └── models/                 # Modelos entrenados .pkl (gitignored)
│
├── 📂 database/                # 🗄️ Capa de datos
│   ├── db.py                   # Conexión PostgreSQL
│   └── schemas/                # Scripts de creación de tablas
│       ├── init_schema.py      # Schema principal
│       ├── init_schema_v2.py   # Schema v2 (equipos, historial)
│       ├── init_schema_ai.py   # Schema módulos IA v1
│       ├── init_schema_ai_v2.py# Schema módulos IA v2
│       └── migrate_data.py     # Migración de datos
│
├── 📂 scripts/                 # ⚙️ Scripts de administración (no son parte del servidor)
│   ├── train_model.py          # Entrenar modelos ML (ejecutar una sola vez)
│   └── dataset_generator.py   # Generar datos sintéticos de prueba
│
├── 📂 utils/                   # 🔧 Utilidades compartidas
│   └── email_sender.py         # Envío de emails
│
├── 📂 tests/                   # 🧪 Suite de pruebas
│   ├── conftest.py             # Fixtures pytest
│   ├── test_auth.py
│   ├── test_habitaciones.py
│   ├── test_mantenimiento.py
│   ├── test_admin.py
│   └── test_limpieza_ia.py
│
└── 📂 docs/                    # 📚 Documentación
    ├── GUIA_PRESENTACION_CEO.md# Guía de presentación para directivos
    └── diagrama_sistema.md     # Diagrama completo del sistema
```

---

## 🔐 Seguridad

- ✅ Passwords hasheados con Werkzeug (scrypt/pbkdf2)
- ✅ Protección CSRF en todos los formularios
- ✅ Rate limiting por IP
- ✅ Security headers (X-Frame-Options, XSS Protection, etc.)
- ✅ Control de acceso por roles (`admin` / `empleado`)
- ✅ Sesiones seguras con HttpOnly y SameSite cookies

> ⚠️ **Nunca subas tu archivo `.env` al repositorio.** Ya está excluido en `.gitignore`.

---

## 🤝 Contribuciones

1. Haz fork del proyecto
2. Crea tu rama (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -m 'Add: nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.