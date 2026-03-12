# 🏨 Hotel Mantenimiento

Sistema integral de gestión de mantenimiento hotelero construido con **Flask** y **PostgreSQL**. Este sistema permite gestionar habitaciones, reportar fallas, realizar inspecciones y generar reportes analíticos avanzados.

## 📋 Requisitos Previos

Antes de instalar el proyecto, asegúrate de tener instalado:

- [Python 3.12](https://www.python.org/downloads/) o superior.
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para la base de datos PostgreSQL).
- [Git](https://git-scm.com/downloads) (opcional, para clonar el repositorio).

---

## 🚀 Guía de Instalación en otra PC

Sigue estos pasos para poner en marcha el proyecto desde cero:

### 1. Preparar el Proyecto
Descarga el código o clona el repositorio:
```bash
git clone <url-del-repositorio>
cd hotel_mantenimiento
```

### 2. Crear y Activar Entorno Virtual
Es recomendable usar un entorno virtual para no interferir con otras instalaciones de Python:

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar Dependencias
Instala todas las librerías necesarias con el archivo que acabamos de actualizar:
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Crea un archivo llamado `.env` en la raíz del proyecto (puedes copiar el contenido de `.env.example` si existe):

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hotel_mantenimiento
SECRET_KEY=tu_clave_secreta_aqui
```

### 5. Levantar la Base de Datos (Docker)
Asegúrate de que Docker Desktop esté abierto y ejecuta:
```bash
docker-compose up -d
```
*Esto descargará la imagen de PostgreSQL y levantará el contenedor automáticamente.*

### 6. Inicializar la Base de Datos
Para crear las tablas necesarias, ejecuta:
```bash
python app.py
```
*El sistema detectará automáticamente si faltan tablas y las creará al iniciar.* 

---

## 💻 Uso de la Aplicación

Para ejecutar el servidor de desarrollo:
```bash
python app.py
```
La aplicación estará disponible en: [http://localhost:5000](http://localhost:5000)

### 👤 Usuarios de Prueba
| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `admin` | `admin` | Administrador |
| `empleado1` | `empleado1` | Empleado |

---

## 🛠️ Tecnologías Utilizadas

- **Backend**: Flask 3.x
- **Base de Datos**: PostgreSQL 16
- **Contenedores**: Docker & Docker Compose
- **IA/Visión**: OpenCV, Ultralytics (YOLOv8)
- **Reportes**: ReportLab (Generación de PDF)

---

## 📁 Estructura Principal
- `/ai`: Módulos de inteligencia artificial.
- `/database`: Configuración de conexión y modelos.
- `/routes`: Lógica de las diferentes secciones (Dashboard, Habitaciones, etc.).
- `/templates`: Vistas HTML con Jinja2.
- `/static`: Estilos CSS, scripts JS e imágenes.


Prueba de revisión automática con CodeRabbit
Actualización del proyecto con revisión de IA