# 🏨 Hotel Mantenimiento

Sistema de gestión de mantenimiento hotelero construido con Flask y PostgreSQL.

## 📁 Estructura del Proyecto

```
hotel_mantenimiento/
├── app.py                   # Punto de entrada — crea la app y registra blueprints
├── config.py                # Configuración centralizada (SECRET_KEY, DATABASE_URL)
├── requirements.txt         # Dependencias Python
├── docker-compose.yml       # PostgreSQL con Docker
├── .env                     # Variables de entorno (no se sube a git)
│
├── database/                # Módulo de base de datos
│   ├── db.py                # Conexión a PostgreSQL
│   ├── init_schema.py       # Script para crear tablas
│   └── migrate_data.py      # Migrador SQLite → PostgreSQL
│
├── routes/                  # Blueprints organizados por funcionalidad
│   ├── __init__.py          # Registra todos los blueprints
│   ├── auth.py              # Login, logout y decoradores de acceso
│   ├── dashboard.py         # Dashboard principal con estadísticas
│   ├── habitaciones.py      # CRUD de habitaciones + detalle
│   ├── mantenimiento.py     # Registro de mantenimientos
│   ├── inspecciones.py      # Inspecciones y cola de trabajo
│   ├── reportes.py          # Generación de reportes PDF
│   ├── analisis.py          # Inteligencia analítica
│   └── admin.py             # Gestión de usuarios, perfil e historial
│
├── templates/               # Plantillas HTML (Jinja2)
└── static/                  # Archivos estáticos (CSS, JS, imágenes)
```

## 🚀 Setup Rápido

### 1. Levantar PostgreSQL con Docker
```bash
docker compose up -d
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Crear tablas
```bash
python database/init_schema.py
```

### 4. (Opcional) Migrar datos desde SQLite
```bash
python database/migrate_data.py
```

### 5. Ejecutar la aplicación
```bash
python app.py
```

La app estará disponible en `http://localhost:5000`

## 👤 Usuarios por defecto

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| admin | admin | admin |
| empleado1 | empleado1 | empleado |

## 🛠️ Tecnologías

- **Backend**: Flask (Python)
- **Base de datos**: PostgreSQL 16
- **Reportes**: ReportLab (PDF)
- **Contenedor**: Docker
