# 🏨 Sistema de Mantenimiento Inteligente para Hoteles — Diagrama y Planteamiento

## Arquitectura General del Sistema

```mermaid
graph TB
    subgraph CLIENTE["🖥️ Cliente (Navegador)"]
        BASE["base.html — Layout + Sidebar"]
        CSS["global.css — Tema Claro"]
        AOS["AOS.js — Animaciones"]
        LUCIDE["Lucide Icons"]
        CHARTJS["Chart.js — Gráficas"]
        TEMPLATES["30 Templates HTML<br/>Jinja2"]
    end

    subgraph SERVIDOR["⚙️ Servidor Flask"]
        APP["app.py<br/>Bootstrap + Migración"]
        CONFIG["config.py<br/>Configuración"]
        EXT["extensions.py<br/>SocketIO Init"]
        SOCK["Flask-SocketIO<br/>WebSocket Tiempo Real"]

        subgraph BLUEPRINTS["📦 Blueprints (routes/) — 11 módulos"]
            AUTH["🔐 auth.py"]
            DASH["📊 dashboard.py"]
            HAB["🏠 habitaciones.py"]
            MANT["🔧 mantenimiento.py"]
            INSP["🔍 inspecciones.py"]
            ANAL["📈 analisis.py"]
            REP["📄 reportes.py"]
            ADM["⚡ admin.py"]
            BP_PRED["🤖 predicciones.py"]
            BP_VIS["📸 vision.py"]
            BP_LIMP["🧹 limpieza.py"]
        end

        subgraph IA["🧠 Módulos de IA (ai/)"]
            DATASET["dataset_generator.py"]
            TRAIN["train_model.py"]
            PREDICT["predictor.py"]
            DETECT["detector.py"]
            SCORING["scoring_engine.py"]
            MODELS["models/*.pkl"]
        end
    end

    subgraph INFRA["🐳 Infraestructura"]
        DOCKER["Docker Compose"]
        PG["PostgreSQL 16<br/>hotel_mantenimiento"]
    end

    subgraph BD["💾 PostgreSQL — 11 Tablas"]
        T1["usuarios"]
        T2["habitaciones"]
        T3["mantenimiento"]
        T4["inspecciones"]
        T5["historial_habitaciones"]
        T6["equipos"]
        T7["historial_fallas"]
        T8["predicciones"]
        T9["detecciones_visuales"]
        T10["limpieza_habitaciones"]
        T11["historial_limpieza"]
    end

    CLIENTE <--> BLUEPRINTS
    BLUEPRINTS --> IA
    BP_PRED --> PREDICT
    BP_VIS --> DETECT
    BP_LIMP --> SCORING
    TRAIN --> MODELS
    PREDICT --> MODELS
    DATASET --> PG
    IA --> PG
    DOCKER --> PG
    EXT --> SOCK
    SOCK <--> CLIENTE
    BLUEPRINTS --> SOCK
```

---

## Estructura Completa del Proyecto

```
hotel_mantenimiento/
├── app.py                        ← Bootstrap + auto-migración
├── config.py                     ← SECRET_KEY, DATABASE_URL
├── extensions.py                 ← Flask-SocketIO (init)
├── requirements.txt              ← Dependencias Python
├── docker-compose.yml            ← PostgreSQL 16
├── .env                          ← Variables de entorno
├── diagrama_sistema.md           ← Este documento
│
├── database/
│   ├── __init__.py
│   ├── db.py                     ← Conexión PostgreSQL (psycopg2)
│   ├── init_schema.py            ← 5 tablas base
│   ├── init_schema_ai.py         ← 5 tablas de IA
│   └── migrate_data.py           ← Migrador SQLite → PostgreSQL
│
├── routes/                       ← 11 Flask Blueprints
│   ├── __init__.py               ← registrar_blueprints(app)
│   ├── auth.py                   ← Login, logout, decoradores
│   ├── dashboard.py              ← Dashboard + predicciones
│   ├── habitaciones.py           ← CRUD habitaciones + detalle
│   ├── mantenimiento.py          ← Registro de mantenimientos
│   ├── inspecciones.py           ← Inspecciones + cola
│   ├── reportes.py               ← PDF con ReportLab
│   ├── analisis.py               ← Inteligencia analítica
│   ├── admin.py                  ← Usuarios, perfil, historial
│   ├── predicciones.py           ← [IA] Predicción ML
│   ├── vision.py                 ← [IA] Detección visual
│   └── limpieza.py               ← [IA] Priorización limpieza
│
├── ai/                           ← Módulos de Inteligencia Artificial
│   ├── __init__.py
│   ├── dataset_generator.py      ← Genera datos sintéticos (2 años)
│   ├── train_model.py            ← Entrena Decision Tree + Random Forest
│   ├── predictor.py              ← Ejecuta predicciones de falla
│   ├── detector.py               ← YOLOv8 + OpenCV para fotos
│   ├── scoring_engine.py         ← Scoring de urgencia de limpieza
│   └── models/                   ← Modelos entrenados (.pkl)
│
├── templates/                    ← 24 plantillas Jinja2
│   ├── base.html                 ← Layout maestro
│   ├── index.html, login.html, dashboard.html
│   ├── habitaciones.html, habitacion_form.html, habitacion_editar.html
│   ├── detalle_habitacion.html, mantenimientos.html, mantenimiento_form.html
│   ├── inspeccion.html, analisis.html, historial.html
│   ├── reporte_form.html, perfil.html, admin_usuarios.html
│   ├── empleado_cola.html, acceso_denegado.html
│   ├── predicciones.html         ← [IA] Dashboard ML
│   ├── vision.html               ← [IA] Upload + resultados + lightbox
│   ├── vision_historial.html     ← [IA] Historial detecciones
│   ├── limpieza.html             ← [IA] Cola priorizada
│   ├── limpieza_mapa.html        ← [IA] Mapa de calor
│   └── limpieza_checkout.html    ← [IA] Formulario check-out
│
├── static/
│   ├── css/global.css            ← Sistema de diseño (~550 líneas)
│   └── uploads/                  ← Fotos subidas + anotadas
│
└── venv/                         ← Entorno virtual Python
```

---

## Diagrama Entidad-Relación (10 Tablas PostgreSQL)

```mermaid
erDiagram
    usuarios {
        SERIAL id PK
        VARCHAR username
        TEXT password
        TEXT rol "admin | empleado"
        TEXT nombre_completo
        TEXT email
        TEXT telefono
    }

    habitaciones {
        SERIAL id PK
        VARCHAR numero
        TEXT estado
        TEXT fecha_ultimo_mantenimiento
    }

    mantenimiento {
        SERIAL id PK
        INTEGER habitacion_id FK
        TEXT tipo
        TEXT elemento
        TEXT descripcion
        TEXT tecnico
        TEXT fecha
        TEXT estado
        NUMERIC costo
        TEXT prioridad
    }

    inspecciones {
        SERIAL id PK
        INTEGER habitacion_id FK
        TEXT empleado
        TEXT observaciones
        DATE fecha
        INTEGER genera_mantenimiento
    }

    historial_habitaciones {
        SERIAL id PK
        INTEGER habitacion_id FK
        TEXT accion
        TEXT descripcion
        TEXT usuario
        TIMESTAMP fecha
    }

    equipos {
        SERIAL id PK
        INTEGER habitacion_id FK
        VARCHAR tipo "AC TV Plomeria Electricidad Calefaccion"
        TEXT marca
        DATE fecha_instalacion
        INTEGER vida_util_dias
    }

    historial_fallas {
        SERIAL id PK
        INTEGER equipo_id FK
        INTEGER habitacion_id FK
        TEXT tipo_falla
        DATE fecha_falla
        DATE fecha_reparacion
        NUMERIC costo
        INTEGER tecnico_id FK
        NUMERIC tiempo_reparacion_horas
        TEXT severidad
    }

    predicciones {
        SERIAL id PK
        INTEGER equipo_id FK
        INTEGER habitacion_id FK
        NUMERIC prob_7_dias
        NUMERIC prob_14_dias
        NUMERIC prob_30_dias
        TIMESTAMP fecha_prediccion
        TEXT modelo_usado
        TEXT nivel_riesgo
    }

    detecciones_visuales {
        SERIAL id PK
        INTEGER habitacion_id FK
        INTEGER limpieza_id FK
        TEXT imagen_original
        TEXT imagen_anotada
        TEXT score_estado
        TEXT detecciones_json
        NUMERIC confianza_promedio
        TEXT empleado
        TIMESTAMP fecha
    }

    limpieza_habitaciones {
        SERIAL id PK
        INTEGER habitacion_id FK
        TIMESTAMP fecha_checkout
        TIMESTAMP fecha_checkin_siguiente
        DATE fecha_ultima_limpieza_profunda
        TEXT categoria_habitacion
        NUMERIC urgency_score
        TEXT nivel_urgencia
        TEXT asignado_a
        TEXT estado_limpieza
    }

    historial_limpieza {
        SERIAL id PK
        INTEGER habitacion_id FK
        VARCHAR numero_habitacion
        TEXT categoria
        TIMESTAMP fecha_checkout
        TIMESTAMP fecha_completada
        TEXT empleado
        TEXT imagen_evidencia
        TEXT estado_ia
        TEXT urgencia_inicial
    }

    habitaciones ||--o{ mantenimiento : "tiene"
    habitaciones ||--o{ inspecciones : "recibe"
    habitaciones ||--o{ historial_habitaciones : "registra"
    habitaciones ||--o{ equipos : "contiene"
    habitaciones ||--o{ limpieza_habitaciones : "limpieza"
    habitaciones ||--o{ detecciones_visuales : "fotos"
    habitaciones ||--o{ historial_limpieza : "archiva"
    equipos ||--o{ historial_fallas : "falla"
    equipos ||--o{ predicciones : "predicción"
    limpieza_habitaciones ||--o{ detecciones_visuales : "análisis visual"
```

---

## Módulos de Inteligencia Artificial — Explicación Detallada

### 🤖 Módulo 1: Predicción de Fallas (Predictive Maintenance)

**¿Qué hace?**
Analiza el historial de mantenimiento de cada equipo para predecir cuándo fallará nuevamente. Genera probabilidades a 7, 14 y 30 días y clasifica el riesgo.

**¿Cómo funciona?**

```mermaid
flowchart LR
    A["📊 dataset_generator.py<br/>Genera historial de 2 años"] --> B["🧠 train_model.py<br/>Entrena 2 modelos ML"]
    B --> C["📦 models/*.pkl<br/>Modelos guardados"]
    C --> D["🔮 predictor.py<br/>Calcula probabilidades"]
    D --> E["💾 Tabla: predicciones<br/>Resultados por equipo"]
    E --> F["🖥️ predicciones.html<br/>Dashboard con semáforo"]
```

**Feature Engineering (variables que alimentan el modelo):**

| Feature | Descripción | Por qué es útil |
|---------|-------------|-----------------|
| `tipo_equipo_enc` | Tipo de equipo codificado numéricamente | Cada equipo tiene patrones de falla distintos |
| `mes` | Mes del año | AC falla más en verano, calefacción en invierno |
| `dia_semana` | Día de la semana | Patrones semanales de uso |
| `edad_equipo_dias` | Días desde la instalación | Equipos viejos fallan más |
| `dias_desde_anterior` | Días desde la última falla | Ciclos de falla repetitivos |
| `fallas_previas` | Número total de fallas | Equipos problemáticos acumulan fallas |
| `costo_promedio` | Costo promedio de reparaciones | Fallas costosas indican problemas graves |
| `severidad_enc` | Severidad codificada | Fallas críticas predicen más fallas |

**Modelos utilizados:**

| Modelo | Descripción | Ventaja |
|--------|-------------|---------|
| **Decision Tree** | Árbol de decisión — divide los datos en reglas IF/THEN | Interpretable: puedes explicar a gerencia POR QUÉ falló |
| **Random Forest** | Ensamble de 100 árboles que votan | Mayor precisión (reduce overfitting del árbol individual) |

**Métricas de evaluación:**

| Métrica | Qué mide |
|---------|----------|
| **Accuracy** | % de predicciones correctas (tanto falla como no-falla) |
| **Precision** | De las fallas predichas, ¿cuántas realmente ocurrieron? (evita falsas alarmas) |
| **Recall** | De las fallas reales, ¿cuántas detectaron? (evita fallas no detectadas) |
| **F1-Score** | Balance armónico entre precision y recall |

**Niveles de riesgo:**
- `prob ≥ 0.7` → 🔴 **CRÍTICO** — Acción inmediata
- `prob ≥ 0.5` → 🟠 **ALTO** — Planificar mantenimiento
- `prob ≥ 0.3` → 🟡 **MEDIO** — Monitorear
- `prob < 0.3` → 🟢 **BAJO** — Sin acción

---

### 📸 Módulo 2: Detección Visual de Problemas (Computer Vision)

**¿Qué hace?**
El personal toma una foto de la habitación con el celular. El sistema detecta automáticamente problemas (suciedad, manchas, daños) y genera un reporte visual con las áreas marcadas.

**¿Cómo funciona?**

```mermaid
flowchart LR
    A["📱 Empleado sube<br/>foto desde celular"] --> B["🖼️ OpenCV<br/>Preprocesamiento"]
    B --> C{"¿YOLOv8 disponible?"}
    C -->|Sí| D["YOLOv8<br/>Detección de objetos"]
    C -->|No| E["OpenCV básico<br/>Análisis de color/textura"]
    D --> F["📊 Resultados:<br/>bounding boxes + score"]
    E --> F
    F --> G["🖥️ vision.html<br/>Imagen anotada + lightbox"]
```

**Clases que detecta:**

| Clase | Descripción | Método de detección |
|-------|-------------|---------------------|
| `suciedad` | Áreas oscuras anómalas | Threshold en escala de grises < 50 |
| `mancha` | Manchas de color marrón/café | Rango HSV [10-20, 100-255, 20-200] |
| `daño_pared` | Alta densidad de bordes (grietas, rasguños) | Canny edge detection > 15% densidad |
| `daño_mueble` | Daño en mobiliario | YOLOv8 (si disponible) |
| `objeto_fuera_lugar` | Objetos que no deberían estar | YOLOv8 mapea clases COCO al contexto hotel |
| `fuga_agua` | Evidencia de agua/humedad | YOLOv8 + análisis de color |

**Score de estado:**
- **LIMPIA** — Sin detecciones o confianza muy baja (< 30%)
- **REQUIERE_LIMPIEZA** — Suciedad, manchas u objetos detectados
- **REQUIERE_MANTENIMIENTO** — Daños estructurales o fugas detectados con alta confianza

**Lightbox:** Al hacer clic en la imagen anotada, se amplía a pantalla completa con fondo oscuro para inspeccionar los detalles.

---

### 🧹 Módulo 3: Priorización de Limpieza Urgente

**¿Qué hace?**
En lugar de limpiar en orden numérico, el sistema calcula qué habitación necesita limpieza MÁS URGENTE usando una fórmula ponderada, y genera una cola priorizada.

**Fórmula de scoring:**

```
urgency_score = (hours_since_checkout × 0.4) +
                (days_since_deep_clean × 0.3) +
                (next_checkin_proximity × 0.2) +
                (room_category_weight × 0.1)
```

| Factor | Peso | Lógica |
|--------|------|--------|
| **Horas desde check-out** | 40% | Más tiempo sin limpiar = más urgente |
| **Días sin limpieza profunda** | 30% | Limpieza profunda vieja = más urgente |
| **Proximidad del check-in** | 20% | Huésped llega pronto = más urgente (inverso) |
| **Categoría de habitación** | 10% | Presidencial (10) > Suite (8) > Superior (6) > Estándar (4) |

**Niveles de urgencia:** `≥ 8` → CRÍTICO, `≥ 6` → ALTO, `≥ 4` → MEDIO, `< 4` → BAJO

**Mapa de calor:** Representación visual tipo grid del hotel donde cada habitación tiene color según su urgencia (rojo, ámbar, amarillo, verde, teal).

---

## Librerías y Tecnologías — ¿Qué es cada una y para qué se usa?

### Backend y Servidor

| Librería | ¿Qué es? | ¿Para qué la usamos? |
|----------|----------|---------------------|
| **Flask** | Micro-framework web de Python | Servidor web, rutas, sesiones, templates |
| **psycopg2-binary** | Driver de PostgreSQL para Python | Conectar y ejecutar SQL en la base de datos |
| **python-dotenv** | Carga variables desde archivo `.env` | Configuración segura (DATABASE_URL, SECRET_KEY) |
| **ReportLab** | Generador de PDFs | Crear reportes PDF profesionales con gráficas |
| **Jinja2** | Motor de templates (viene con Flask) | Generar HTML dinámico con datos del servidor |

### Machine Learning (Módulo 1)

| Librería | ¿Qué es? | ¿Para qué la usamos? |
|----------|----------|---------------------|
| **scikit-learn** | Librería de ML más popular de Python | Entrenar Decision Tree y Random Forest, evaluar métricas |
| **pandas** | Manipulación de datos tabulares | Cargar datos de PostgreSQL como DataFrame, feature engineering |
| **numpy** | Operaciones numéricas y arrays | Cálculos matemáticos, promedios, arrays de features |
| **joblib** | Serialización eficiente de objetos Python | Guardar y cargar modelos entrenados (.pkl) |

### Computer Vision (Módulo 2)

| Librería | ¿Qué es? | ¿Para qué la usamos? |
|----------|----------|---------------------|
| **ultralytics** | Framework de YOLO (You Only Look Once) v8 | Detección de objetos en fotos en una sola pasada |
| **opencv-python** | Librería de visión por computadora | Preprocesamiento: conversión de color, threshold, detección de bordes, contornos |
| **Pillow** | Manipulación de imágenes | Soporte de formatos de imagen (JPG, PNG, WebP) |

### Frontend (CDN)

| Librería | ¿Qué es? | ¿Para qué la usamos? |
|----------|----------|---------------------|
| **Inter** (Google Fonts) | Tipografía moderna | Fuente principal del sistema |
| **AOS.js** | Animate On Scroll | Animaciones suaves al hacer scroll (fade-up, fade-down) |
| **Lucide Icons** | Set de iconos SVG | Iconos del sidebar y la interfaz |
| **Chart.js** | Librería de gráficas | Gráficas doughnut (dashboard), línea (tendencias), barras (features) |

---

## Conceptos de IA Utilizados

### ¿Qué es Machine Learning?
Es cuando un programa **aprende de datos** en lugar de seguir reglas escritas a mano. Le das ejemplos del pasado y el programa descubre patrones para predecir el futuro.

### ¿Qué es un Decision Tree?
Imagina un diagrama de flujo: "¿El equipo tiene más de 3 fallas? → Sí → ¿Últiima falla fue hace menos de 60 días? → Sí → **ALTO RIESGO**". El algoritmo crea este árbol automáticamente a partir de los datos.

### ¿Qué es Random Forest?
En lugar de un solo árbol, crea **100 árboles** cada uno con una muestra diferente de los datos. Cada árbol vota y gana la mayoría. Es más preciso porque reduce errores individuales.

### ¿Qué es YOLOv8?
YOLO = "You Only Look Once". Es un modelo de detección de objetos que puede encontrar y clasificar múltiples objetos en una imagen en una sola pasada (en milisegundos). La versión 8 es la más reciente de Ultralytics.

### ¿Qué es OpenCV?
Open Computer Vision — librería que permite manipular imágenes: cambiar colores, detectar bordes, encontrar contornos, aplicar filtros. Funciona como los "ojos" del sistema.

### ¿Qué es un Scoring Engine?
Un sistema de puntuación que asigna un número a cada elemento basándose en múltiples factores con pesos diferentes. No es IA propiamente, pero es una técnica de decisión automatizada.

---

## Flujo de Usuarios y Roles

```mermaid
flowchart LR
    subgraph LOGIN["Acceso"]
        L["/login"]
    end

    subgraph ADMIN_ROLE["👑 Rol: Admin"]
        D1["Dashboard completo"]
        H1["CRUD Habitaciones"]
        M1["Ver mantenimientos"]
        A1["Análisis inteligente"]
        HI1["Historial"]
        AU["Gestionar usuarios"]
        R1["Reportes PDF"]
        P1["Perfil"]
    end

    subgraph EMP_ROLE["👷 Rol: Empleado"]
        D2["Dashboard limitado"]
        MT["Mis tareas"]
        INS["Realizar inspecciones"]
        P2["Perfil"]
    end

    subgraph IA_MODULOS["🧠 IA (Todos)"]
        PRED["Predicciones ML"]
        VIS["Visión por foto"]
        LIMP["Cola de limpieza"]
    end

    L -->|admin| D1
    L -->|empleado| D2

    D1 --> H1 & M1 & A1 & HI1 & AU & R1 & P1
    D2 --> MT & P2
    MT --> INS

    D1 & D2 --> IA_MODULOS
```

---

## Mapa de Rutas (Endpoints)

| Ruta | Método | Blueprint | Acceso | Template |
|------|--------|-----------|--------|----------|
| `/` | GET | dashboard | Público | index.html |
| `/login` | GET, POST | auth | Público | login.html |
| `/logout` | GET | auth | Login | — |
| `/dashboard` | GET | dashboard | Login | dashboard.html |
| `/habitaciones` | GET | habitaciones | Login | habitaciones.html |
| `/habitaciones/nueva` | GET, POST | habitaciones | Login | habitacion_form.html |
| `/habitaciones/editar/<id>` | GET, POST | habitaciones | Login | habitacion_editar.html |
| `/habitaciones/eliminar/<id>` | GET | habitaciones | Login | — |
| `/habitacion/<numero>` | GET | habitaciones | Login | detalle_habitacion.html |
| `/mantenimientos` | GET | mantenimiento | Login | mantenimientos.html |
| `/mantenimiento/nuevo/<id>` | GET, POST | mantenimiento | Login | mantenimiento_form.html |
| `/inspeccion/<id>` | GET, POST | inspecciones | Login | inspeccion.html |
| `/habitacion/marcar_pendiente/<id>` | POST | inspecciones | **Admin** | — |
| `/mis_tareas` | GET | inspecciones | Login | empleado_cola.html |
| `/reporte` | GET | reportes | Login | reporte_form.html |
| `/reporte/pdf` | GET | reportes | Login | — (descarga) |
| `/analisis` | GET | analisis | Login | analisis.html |
| `/historial` | GET | admin | Login | historial.html |
| `/perfil` | GET, POST | admin | Login | perfil.html |
| `/admin/usuarios` | GET | admin | **Admin** | admin_usuarios.html |
| `/admin/usuarios/nuevo` | POST | admin | **Admin** | — |
| `/admin/usuarios/eliminar/<id>` | GET | admin | **Admin** | — |
| `/predicciones` | GET | predicciones | Login | predicciones.html |
| `/predicciones/ejecutar` | POST | predicciones | Login | — |
| `/predicciones/entrenar` | POST | predicciones | **Admin** | — |
| `/predicciones/generar-dataset` | POST | predicciones | Login | — |
| `/vision` | GET | vision | Login | vision.html |
| `/vision/analizar` | POST | vision | Login | vision.html |
| `/vision/historial` | GET | vision | Login | vision_historial.html |
| `/limpieza` | GET | limpieza | Login | limpieza.html |
| `/limpieza/checkout/<id>` | POST | limpieza | Login | — |
| `/limpieza/completar/<id>` | POST | limpieza | Login | — |
| `/limpieza/recalcular` | POST | limpieza | Login | — |
| `/limpieza/generar-demo` | POST | limpieza | Login | — |
| `/limpieza/nuevo-checkout` | GET | limpieza | Login | limpieza_checkout.html |
| `/limpieza/mapa` | GET | limpieza | Login | limpieza_mapa.html |

---

## Flujo Operativo Completo

```mermaid
flowchart TD
    A["Admin marca habitación<br/>Pendiente de inspección"] --> B["Empleado ve tarea<br/>/mis_tareas"]
    B --> C["Inspección en sitio<br/>/inspeccion/<id>"]
    C -->|Sin novedad| D["Disponible"]
    C -->|Problema| E["Mantenimiento automático"]
    E --> F["En mantenimiento"]
    F --> G["Técnico repara"]
    G --> H["Disponible"]

    I["📸 Empleado sube foto<br/>/vision"] --> J["IA analiza imagen"]
    J -->|LIMPIA| D
    J -->|REQUIERE LIMPIEZA| K["Cola de limpieza"]
    J -->|REQUIERE MANT.| E

    L["🤖 Predicción ML<br/>/predicciones"] -->|CRÍTICO| M["Alerta preventiva"]
    M --> N["Mantenimiento preventivo<br/>antes de que falle"]

    O["🚪 Check-out<br/>/limpieza"] --> P["Scoring de urgencia"]
    P --> K
    K --> Q["Personal limpia"]
    Q --> D

    subgraph CONTINUO["📊 Análisis en Tiempo Real"]
        R["Dashboard KPIs"]
        S["Análisis inteligente"]
        T["Reportes PDF"]
    end

    D & F & H --> R
```

---

## Stack Tecnológico Completo

| Componente | Tecnología | Versión |
|-----------|------------|---------|
| Backend | Python | 3.12+ |
| Framework Web | Flask | 3.1.3 |
| WebSocket / Tiempo real | Flask-SocketIO | 5.6.1 |
| Base de datos | PostgreSQL | 16 |
| Conexión BD | psycopg2-binary | 2.9.11 |
| Seguridad | Werkzeug | 3.1.6 |
| Templates | Jinja2 (24 archivos) | — |
| Estilos | CSS vanilla (global.css) | — |
| Animaciones | AOS.js | 2.3.4 |
| Iconos | Lucide Icons | Latest |
| Gráficas | Chart.js | Latest |
| ML | scikit-learn | 1.8.0 |
| Data processing | pandas | 3.0.1 |
| Deep Learning | torch / torchvision | 2.10.0 / 0.25.0 |
| Computer Vision | ultralytics (YOLOv8) | 8.4.21 |
| Computer Vision | opencv-python | 4.13.0 |
| Serialización ML | joblib | — |
| Imágenes | Pillow | 12.1.1 |
| Reportes | ReportLab | 4.4.10 |
| Autenticación | Flask session | — |
| Infraestructura | Docker Compose | — |
| Config | python-dotenv | 1.2.2 |

---

## Configuración y Ejecución

### Variables de Entorno (`.env`)

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hotel_mantenimiento
SECRET_KEY=hotel_secret_key
```

### Comandos

```bash
# 1. Levantar PostgreSQL
docker compose up -d

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicación (crea tablas automáticamente)
python app.py

# 4. Flujo de IA (desde la app web o terminal):
python ai/dataset_generator.py     # Generar datos sintéticos
python ai/train_model.py           # Entrenar modelos ML
python ai/predictor.py             # Ejecutar predicciones
python ai/scoring_engine.py        # Demo de limpieza
```

### Usuarios por Defecto

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| admin | admin | admin |
| empleado1 | empleado1 | empleado |

---
---

# FASE 2: Expansión — Hotel AI Operations Platform

> Arquitectura de expansión diseñada para agregar nuevas funcionalidades de IA sin duplicar lógica existente. Todas las reglas: service layer obligatorio, no duplicar feature engineering, blueprints nunca llaman modelos ML directamente.

---

## Arquitectura Expandida

```mermaid
graph TB
    subgraph CLIENTE["🖥️ Cliente (Navegador)"]
        BASE2["base.html — Layout + Sidebar"]
        TEMPLATES2["30 Templates HTML<br/>Jinja2 (24 + 6 nuevos)"]
    end

    subgraph SERVIDOR["⚙️ Servidor Flask"]
        APP2["app.py<br/>Bootstrap + Migración V2"]

        subgraph BLUEPRINTS2["📦 Blueprints (routes/) — 15 módulos"]
            direction LR
            subgraph EXISTENTES["Existentes (11)"]
                AUTH2["auth.py"]
                DASH2["dashboard.py"]
                HAB2["habitaciones.py"]
                MANT2["mantenimiento.py"]
                INSP2["inspecciones.py"]
                ANAL2["analisis.py"]
                REP2["reportes.py"]
                ADM2["admin.py"]
                BP_PRED2["predicciones.py"]
                BP_VIS2["vision.py"]
                BP_LIMP2["limpieza.py"]
            end
            subgraph NUEVOS["Nuevos (4)"]
                BP_COST["💰 costos_ai.py"]
                BP_TEC["👷 tecnicos_ai.py"]
                BP_SCHED["📅 scheduler.py"]
                BP_OPS["🎯 operations.py"]
            end
        end

        subgraph SERVICES["🔌 Service Layer (ai/services/) — NUEVO"]
            SRV_PRED["prediction_service.py"]
            SRV_VIS["vision_service.py"]
            SRV_CLEAN["cleaning_service.py"]
            SRV_COST["cost_service.py"]
            SRV_TEC["technician_service.py"]
            SRV_SCHED["scheduler_service.py"]
            SRV_OPS["operations_service.py"]
        end

        subgraph IA2["🧠 Módulos de IA (ai/)"]
            subgraph IA_EXIST["Existentes"]
                PREDICT2["predictor.py"]
                DETECT2["detector.py"]
                SCORING2["scoring_engine.py"]
                TRAIN2["train_model.py"]
                DATASET2["dataset_generator.py"]
            end
            subgraph IA_NUEVO["Nuevos"]
                FEAT_UTILS["feature_utils.py"]
                COST_PRED["cost_predictor.py"]
                TEC_REC["technician_recommender.py"]
                MAINT_SCHED["maintenance_scheduler.py"]
            end
            MODELS2["models/*.pkl"]
        end
    end

    subgraph BD2["💾 PostgreSQL — 15 Tablas"]
        subgraph BD_EXIST["Existentes (11)"]
            TE1["usuarios"]
            TE2["habitaciones"]
            TE3["mantenimiento"]
            TE4["inspecciones"]
            TE5["historial_habitaciones"]
            TE6["equipos"]
            TE7["historial_fallas"]
            TE8["predicciones"]
            TE9["detecciones_visuales"]
            TE10["limpieza_habitaciones"]
            TE11["historial_limpieza"]
        end
        subgraph BD_NUEVO["Nuevas (4)"]
            TN1["predicciones_costo"]
            TN2["perfiles_tecnico"]
            TN3["planes_mantenimiento"]
            TN4["alertas_operaciones"]
        end
    end

    CLIENTE <--> BLUEPRINTS2
    BLUEPRINTS2 --> SERVICES
    SERVICES --> IA2
    IA2 --> BD2
    IA_NUEVO --> FEAT_UTILS
    MAINT_SCHED --> PREDICT2
    MAINT_SCHED --> COST_PRED
    MAINT_SCHED --> TEC_REC
    SRV_OPS --> SRV_PRED & SRV_COST & SRV_CLEAN & SRV_TEC & SRV_SCHED
```

---

## Regla Fundamental: Service Layer

```
❌ ANTES:  Route → import ai.predictor → ejecutar_predicciones() → DB directo
✅ AHORA:  Route → import ai.services.prediction_service → ejecutar_predicciones_srv(conn) → ai.predictor → DB
```

**Contrato del Service Layer:**
1. Funciones reciben `conn` como primer parámetro (inyectado por la ruta)
2. Retornan dicts/listas planos (nunca objetos Flask)
3. Nunca importan Flask (session, request, etc.)
4. Manejan toda la orquestación de módulos IA
5. Capturan excepciones y retornan dicts de error

---

## Estructura de Carpetas Expandida

```
hotel_mantenimiento/
├── app.py
├── config.py
├── extensions.py
├── requirements.txt
├── docker-compose.yml
├── .env
├── diagrama_sistema.md
│
├── database/
│   ├── __init__.py
│   ├── db.py
│   ├── init_schema.py                ← 5 tablas base
│   ├── init_schema_ai.py            ← 6 tablas IA (existentes)
│   ├── init_schema_ai_v2.py         ← NUEVO: 4 tablas + columnas nuevas
│   └── migrate_data.py
│
├── routes/                           ← 15 Flask Blueprints
│   ├── __init__.py                   ← Actualizar: registrar 4 blueprints nuevos
│   ├── auth.py                       ← (sin cambios)
│   ├── dashboard.py                  ← Refactorizar: usar operations_service
│   ├── habitaciones.py               ← (sin cambios)
│   ├── mantenimiento.py              ← Agregar: integración con technician_service
│   ├── inspecciones.py               ← (sin cambios)
│   ├── reportes.py                   ← (sin cambios)
│   ├── analisis.py                   ← (sin cambios)
│   ├── admin.py                      ← (sin cambios)
│   ├── predicciones.py               ← Refactorizar: usar prediction_service
│   ├── vision.py                     ← Refactorizar: usar vision_service
│   ├── limpieza.py                   ← Refactorizar: usar cleaning_service
│   ├── costos.py                     ← NUEVO: predicción de costos
│   ├── tecnicos.py                   ← NUEVO: recomendación de técnicos
│   ├── automatizacion.py             ← NUEVO: auto-programación
│   └── operaciones.py                ← NUEVO: dashboard unificado de IA
│
├── ai/
│   ├── __init__.py
│   ├── feature_utils.py              ← NUEVO: feature engineering compartido
│   ├── detector.py                   ← (sin cambios internos)
│   ├── scoring_engine.py             ← (sin cambios internos)
│   ├── predictor.py                  ← Refactorizar: importar feature_utils
│   ├── train_model.py                ← Refactorizar: importar feature_utils
│   ├── dataset_generator.py          ← (sin cambios)
│   ├── cost_predictor.py             ← NUEVO: modelo de predicción de costos
│   ├── technician_recommender.py     ← NUEVO: sistema de recomendación
│   ├── maintenance_scheduler.py      ← NUEVO: auto-programación preventiva
│   ├── services/                     ← NUEVO: capa de servicios completa
│   │   ├── __init__.py
│   │   ├── prediction_service.py     ← Envuelve predictor.py + train_model.py
│   │   ├── vision_service.py         ← Envuelve detector.py
│   │   ├── cleaning_service.py       ← Envuelve scoring_engine.py
│   │   ├── cost_service.py           ← Envuelve cost_predictor.py
│   │   ├── technician_service.py     ← Envuelve technician_recommender.py
│   │   ├── scheduler_service.py      ← Envuelve maintenance_scheduler.py
│   │   └── operations_service.py     ← Agregador de todos los servicios
│   └── models/                       ← Modelos entrenados (.pkl)
│       ├── decision_tree.pkl         (existente)
│       ├── random_forest.pkl         (existente)
│       ├── le_equipo.pkl             (existente)
│       ├── le_severidad.pkl          (existente)
│       ├── features.pkl              (existente)
│       ├── metricas.json             (existente)
│       └── cost_gbr.pkl             ← NUEVO: modelo de costos
│
├── templates/
│   ├── ... (24 existentes sin cambios)
│   ├── costos.html                   ← NUEVO: dashboard predicción costos
│   ├── tecnicos.html                 ← NUEVO: dashboard y ranking técnicos
│   ├── tecnicos_recomendar.html      ← NUEVO: recomendar técnico para orden
│   ├── tecnicos_perfil.html          ← NUEVO: perfil detallado de técnico
│   ├── automatizacion.html           ← NUEVO: panel auto-programación
│   └── operaciones.html              ← NUEVO: dashboard operaciones unificado
│
└── static/
    ├── css/global.css
    └── uploads/
```

---

## Feature Engineering Compartido — ai/feature_utils.py

Extrae la lógica duplicada entre `train_model.py` (líneas 46-80) y `predictor.py` (líneas 74-105) en funciones reutilizables.

```python
# ai/feature_utils.py

FEATURE_NAMES = [
    "tipo_equipo_enc", "mes", "dia_semana", "edad_equipo_dias",
    "dias_desde_anterior", "fallas_previas", "costo_promedio",
    "severidad_enc", "costo", "tiempo_reparacion_horas"
]

def preparar_features_desde_df(df: pd.DataFrame) -> tuple:
    """
    Pipeline compartido de feature engineering para entrenamiento.
    Extrae de train_model.py:cargar_datos().
    Input:  DataFrame crudo con columnas de historial_fallas + equipos
    Output: (X: DataFrame, encoders: dict, feature_names: list)
    """

def preparar_features_equipo(
    tipo_equipo, fecha_instalacion, fecha_ultima_falla,
    total_fallas, costo_promedio, ultimo_costo,
    ultimo_tiempo_rep, severidad, le_equipo, le_severidad
) -> dict:
    """
    Vector de features para un equipo individual (inferencia).
    Extrae de predictor.py:ejecutar_predicciones().
    Output: dict {feature_name: value}
    """
```

**Módulos que lo usan:**
- `ai/predictor.py` — reemplaza duplicación interna
- `ai/train_model.py` — reemplaza duplicación interna
- `ai/cost_predictor.py` — extiende con features adicionales
- `ai/maintenance_scheduler.py` — reutiliza para cálculos de riesgo

---

## Nuevos Módulos de IA

### 💰 Módulo 4: Predicción de Costos de Reparación

**¿Qué hace?**
Predice cuánto costará la próxima reparación de cada equipo ANTES de que ocurra la falla, permitiendo presupuestación proactiva.

**Modelo ML:** Gradient Boosting Regressor (scikit-learn)
- Elegido porque los datos son tabulares y el target (costo) es continuo
- Maneja relaciones no lineales entre tipo de equipo, edad y costos
- No requiere GPU
- Drop-in replacement futuro: XGBoost si el dataset crece

```mermaid
flowchart LR
    A["📊 historial_fallas<br/>+ equipos"] --> B["🔧 feature_utils.py<br/>Features base + extras"]
    B --> C["🧠 cost_predictor.py<br/>Gradient Boosting"]
    C --> D["📦 models/cost_gbr.pkl"]
    D --> E["💰 Predicción:<br/>costo ± rango"]
    E --> F["🖥️ costos_ai.html<br/>Dashboard de costos"]
```

**Features adicionales (sobre las base existentes):**

| Feature | Descripción | Fórmula |
|---------|-------------|---------|
| `vida_util_restante_pct` | % de vida útil restante | `(vida_util_dias - edad_equipo_dias) / vida_util_dias` |
| `fallas_recientes_90d` | Fallas en últimos 90 días | `COUNT(*) WHERE fecha_falla > NOW() - 90d` |

**Funciones:**

```python
# ai/cost_predictor.py

COST_FEATURES = FEATURE_NAMES + ["vida_util_restante_pct", "fallas_recientes_90d"]

def cargar_datos_costos(conn) -> tuple:
    """Carga historial_fallas con target=costo. Reutiliza preparar_features_desde_df()."""

def entrenar_costos(conn) -> dict:
    """Entrena GBR. Guarda en models/cost_gbr.pkl.
    Return: {r2, mae, rmse, feature_importance}"""

def predecir_costo(conn, equipo_id: int) -> dict:
    """Predice costo para un equipo.
    Return: {costo_estimado, rango_min, rango_max, confianza, factores_principales}"""

def predecir_costos_batch(conn) -> list:
    """Predice costos para todos los equipos activos."""
```

**Métricas:**

| Métrica | Qué mide |
|---------|----------|
| **R²** | % de varianza explicada (1.0 = perfecto) |
| **MAE** | Error absoluto medio en $ |
| **RMSE** | Error cuadrático medio (penaliza errores grandes) |

---

### 👷 Módulo 5: Recomendación de Técnicos

**¿Qué hace?**
Sugiere el mejor técnico para cada orden de mantenimiento basándose en especialización, rendimiento, carga de trabajo y costo.

**Modelo:** Sistema de scoring ponderado (NO ML entrenado)
- Con pocos técnicos (<20 usuarios), un modelo ML no tendría datos suficientes
- El scoring ponderado es transparente y explicable a gerencia
- Los pesos pueden ajustarse por A/B testing

```mermaid
flowchart LR
    A["🔧 Orden de<br/>mantenimiento"] --> B["📊 Analizar:<br/>tipo, elemento, prioridad"]
    B --> C["👷 Por cada técnico:<br/>calcular 5 sub-scores"]
    C --> D["⚖️ Score ponderado<br/>W1·esp + W2·rend + ..."]
    D --> E["🏆 Top 3<br/>recomendaciones"]
    E --> F["🖥️ tecnicos_ai.html<br/>Panel con razones"]
```

**Pesos de scoring:**

| Factor | Peso | Lógica |
|--------|------|--------|
| **Especialidad** | 35% | % de trabajos pasados que coinciden con este tipo de equipo |
| **Rendimiento** | 25% | Tiempo promedio de reparación vs. promedio general |
| **Carga actual** | 20% | Inverso del # de órdenes activas asignadas |
| **Disponibilidad** | 10% | 1.0 si no tiene tareas críticas, 0.5 si tiene |
| **Costo** | 10% | Costo promedio de sus reparaciones vs. promedio general |

**Funciones:**

```python
# ai/technician_recommender.py

W_ESPECIALIDAD = 0.35
W_RENDIMIENTO  = 0.25
W_CARGA        = 0.20
W_DISPONIBILIDAD = 0.10
W_COSTO        = 0.10

def recomendar_tecnico(conn, mantenimiento_id: int) -> list:
    """Scores todos los técnicos para una orden específica.
    Return: [{tecnico_id, nombre, score, razones, desglose}] ordenado DESC"""

def obtener_estadisticas_tecnico(conn, tecnico_id: int) -> dict:
    """Perfil de rendimiento.
    Return: {especialidades, avg_tiempo, avg_costo, total_trabajos, carga_actual}"""

def ranking_tecnicos(conn) -> list:
    """Todos los técnicos rankeados por score compuesto."""
```

---

### 📅 Módulo 6: Auto-Programación de Mantenimiento Preventivo

**¿Qué hace?**
Genera automáticamente un plan de mantenimiento preventivo combinando predicciones de falla, estimaciones de costo y recomendaciones de técnicos. El admin revisa y aprueba.

```mermaid
flowchart TD
    A["🤖 Predictor<br/>prob_30 por equipo"] --> D["📅 Scheduler<br/>Combina todo"]
    B["💰 Cost Predictor<br/>costo estimado"] --> D
    C["👷 Tech Recommender<br/>mejor técnico"] --> D
    E["⏰ Edad equipo<br/>vs vida_útil"] --> D
    D --> F["📋 Plan Propuesto<br/>planes_mantenimiento"]
    F --> G{"👑 Admin revisa"}
    G -->|Aprobar| H["🔧 Crear orden<br/>mantenimiento"]
    G -->|Rechazar| I["❌ Rechazado<br/>con motivo"]
    H --> J["📢 SocketIO<br/>alerta_global"]
```

**Algoritmo de auto-programación:**

```
1. Ejecutar predicciones de falla (reutiliza ai.predictor)
2. Filtrar equipos con prob_30 >= 0.4 (riesgo MEDIO+)
3. También incluir equipos donde edad > 80% de vida_útil
4. Para cada equipo filtrado:
   a. Verificar que NO exista ya mantenimiento preventivo pendiente
   b. Calcular fecha sugerida:
      - Base: hoy + (dias_desde_anterior × 0.7)
      - Ajuste: CRÍTICO = -7 días, ALTO = -3 días, MEDIO = 0
   c. Estimar costo (reutiliza ai.cost_predictor)
   d. Recomendar técnico (reutiliza ai.technician_recommender)
5. Guardar en planes_mantenimiento con estado='Propuesto'
6. Emitir notificación SocketIO
```

**Funciones:**

```python
# ai/maintenance_scheduler.py

def generar_plan_preventivo(conn, semanas_adelante: int = 4) -> list:
    """Genera plan completo. Orquesta predictor + cost + technician.
    Return: [{equipo_id, habitacion, tipo, fecha_sugerida, prioridad,
              razon, costo_estimado, tecnico_recomendado}]"""

def aprobar_plan(conn, plan_ids: list, aprobado_por: str) -> dict:
    """Convierte items aprobados en órdenes de mantenimiento reales.
    Return: {ordenes_creadas, ids}"""

def rechazar_plan(conn, plan_ids: list, motivo: str) -> dict:
    """Marca items como rechazados con motivo."""
```

---

### 🎯 Módulo 7: Dashboard de Operaciones Unificado

**¿Qué hace?**
Agrega todos los subsistemas de IA en un solo panel con KPIs operacionales, alertas cruzadas y métricas industriales.

```mermaid
flowchart LR
    A["prediction_service"] --> G["🎯 operations_service"]
    B["cost_service"] --> G
    C["cleaning_service"] --> G
    D["technician_service"] --> G
    E["scheduler_service"] --> G
    G --> H["🖥️ operations.html<br/>Dashboard unificado"]
```

**KPIs Operacionales:**

| KPI | Fórmula | Significado |
|-----|---------|-------------|
| **MTBF** | Tiempo total operación / # fallas | Mean Time Between Failures |
| **MTTR** | Σ tiempo_reparacion / # reparaciones | Mean Time To Repair |
| **Disponibilidad** | MTBF / (MTBF + MTTR) × 100 | % del tiempo que el equipo funciona |
| **OEE** | Disponibilidad × Rendimiento × Calidad | Overall Equipment Effectiveness |

**Función principal:**

```python
# ai/services/operations_service.py

def obtener_resumen_operaciones(conn) -> dict:
    """Agrega todos los subsistemas IA.
    Return: {
        predicciones: {total, criticos, altos, medios},
        costos: {estimado_mensual, tendencia, top_equipos},
        limpieza: {pendientes, criticas, score_promedio},
        tecnicos: {total_activos, carga_promedio, top_performer},
        mantenimiento_auto: {proximas_ordenes, ahorro_estimado},
        alertas: [{tipo, mensaje, nivel, timestamp}],
        kpis: {mtbf, mttr, disponibilidad, oee}
    }"""
```

---

## Service Layer Completo — Funciones

### prediction_service.py

```python
def ejecutar_predicciones_srv(conn, modelo="random_forest") -> dict:
    """Return: {predicciones: [...], total, criticos, altos}"""

def entrenar_modelos_srv(conn) -> dict:
    """Return: {resultados: {...}, exito: bool, mensaje: str}"""

def obtener_metricas_srv() -> dict:
    """Lee metricas.json del disco."""

def obtener_predicciones_existentes(conn) -> list:
    """Lectura directa de tabla predicciones."""
```

### vision_service.py

```python
def analizar_imagen_srv(conn, ruta: str, hab_id: int, empleado: str) -> dict:
    """Return: {id, score_estado, detecciones, ...} o {error: str}"""

def obtener_habitaciones_con_limpieza_activa(conn) -> list:
    """Habitaciones con ciclo de limpieza activo (para dropdown)."""
```

### cleaning_service.py

```python
def recalcular_scores_srv(conn) -> list:
    """Envuelve scoring_engine.recalcular_scores()."""

def registrar_checkout_srv(conn, hab_id: int, checkin, categoria: str) -> bool:
    """Envuelve scoring_engine.registrar_checkout()."""

def completar_limpieza_srv(conn, limpieza_id: int) -> bool:
    """Envuelve scoring_engine.completar_limpieza()."""
```

### cost_service.py

```python
def predecir_costos_srv(conn, habitacion_id: int = None) -> list:
    """Predicción de costos para todos o una habitación."""

def entrenar_modelo_costos_srv(conn) -> dict:
    """Entrena modelo GBR. Return: {r2, mae, rmse, exito}"""

def obtener_historico_costos(conn, habitacion_id: int = None) -> list:
    """Historial de costos por tipo de equipo y mes."""
```

### technician_service.py

```python
def recomendar_tecnico_srv(conn, mantenimiento_id: int) -> dict:
    """Return: {recomendaciones: [{tecnico_id, nombre, score, razones, carga}]}"""

def obtener_perfil_tecnico(conn, tecnico_id: int) -> dict:
    """Perfil de rendimiento del técnico."""

def ranking_tecnicos_srv(conn) -> list:
    """Ranking de todos los técnicos."""
```

### scheduler_service.py

```python
def generar_plan_preventivo_srv(conn, semanas: int = 4) -> list:
    """Genera plan completo de mantenimiento preventivo."""

def aprobar_plan_srv(conn, plan_ids: list, aprobado_por: str) -> dict:
    """Convierte plan en órdenes reales. Return: {ordenes_creadas, ids}"""

def obtener_plan_actual(conn) -> list:
    """Plan pendiente actual."""

def ejecutar_ciclo_automatico(conn) -> dict:
    """Ciclo completo: predecir → estimar costos → recomendar → generar plan."""
```

---

## Nuevos Endpoints Flask

### Blueprint: costos_ai_bp

| Método | Ruta | Acceso | Template | Descripción |
|--------|------|--------|----------|-------------|
| GET | `/costos-ai` | Login | costos_ai.html | Dashboard de predicción de costos |
| POST | `/costos-ai/predecir` | Login | — | Ejecutar predicciones de costo |
| POST | `/costos-ai/entrenar` | **Admin** | — | Entrenar modelo de costos |
| GET | `/costos-ai/equipo/<id>` | Login | — | Detalle de costo por equipo |
| GET | `/api/costos-ai/resumen` | Login | — (JSON) | API para widgets del dashboard |

### Blueprint: tecnicos_ai_bp

| Método | Ruta | Acceso | Template | Descripción |
|--------|------|--------|----------|-------------|
| GET | `/tecnicos-ai` | Login | tecnicos_ai.html | Dashboard de rendimiento |
| GET | `/tecnicos-ai/recomendar/<mant_id>` | Login | — | Recomendación para una orden |
| POST | `/tecnicos-ai/asignar` | **Admin** | — | Aceptar y asignar técnico |
| GET | `/tecnicos-ai/perfil/<tec_id>` | Login | — | Perfil detallado del técnico |
| GET | `/api/tecnicos-ai/ranking` | Login | — (JSON) | Ranking JSON |

### Blueprint: scheduler_bp

| Método | Ruta | Acceso | Template | Descripción |
|--------|------|--------|----------|-------------|
| GET | `/scheduler` | **Admin** | scheduler.html | Panel de auto-programación |
| POST | `/scheduler/generar` | **Admin** | — | Generar plan preventivo |
| POST | `/scheduler/aprobar` | **Admin** | — | Aprobar items del plan |
| POST | `/scheduler/rechazar` | **Admin** | — | Rechazar items con motivo |
| GET | `/scheduler/historial` | **Admin** | — | Planes pasados y resultados |
| GET | `/api/scheduler/plan-actual` | Login | — (JSON) | Plan actual JSON |

### Blueprint: operations_bp

| Método | Ruta | Acceso | Template | Descripción |
|--------|------|--------|----------|-------------|
| GET | `/operations` | **Admin** | operations.html | Dashboard unificado de IA |
| GET | `/api/operations/resumen` | Login | — (JSON) | Resumen completo JSON |
| GET | `/api/operations/alertas` | Login | — (JSON) | Alertas activas JSON |
| GET | `/api/operations/kpis` | Login | — (JSON) | KPIs operacionales JSON |

---

## Cambios en Base de Datos

### Nuevas Tablas (database/init_schema_v2.py)

#### predicciones_costo

```sql
CREATE TABLE IF NOT EXISTS predicciones_costo (
    id SERIAL PRIMARY KEY,
    equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
    habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
    costo_estimado NUMERIC(10,2) NOT NULL,
    rango_min NUMERIC(10,2),
    rango_max NUMERIC(10,2),
    confianza NUMERIC(5,4),
    factores_json TEXT,
    modelo_usado TEXT DEFAULT 'cost_gbr',
    fecha_prediccion TIMESTAMP DEFAULT NOW()
);
```

#### perfiles_tecnico

```sql
CREATE TABLE IF NOT EXISTS perfiles_tecnico (
    id SERIAL PRIMARY KEY,
    tecnico_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    especialidades_json TEXT,
    total_trabajos INTEGER DEFAULT 0,
    tiempo_promedio_horas NUMERIC(6,2) DEFAULT 0,
    costo_promedio NUMERIC(10,2) DEFAULT 0,
    calificacion NUMERIC(3,2) DEFAULT 5.0,
    carga_actual INTEGER DEFAULT 0,
    fecha_actualizado TIMESTAMP DEFAULT NOW()
);
```

#### planes_mantenimiento

```sql
CREATE TABLE IF NOT EXISTS planes_mantenimiento (
    id SERIAL PRIMARY KEY,
    equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
    habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
    tipo_equipo TEXT NOT NULL,
    fecha_sugerida DATE NOT NULL,
    prioridad TEXT DEFAULT 'Media',
    razon TEXT NOT NULL,
    costo_estimado NUMERIC(10,2),
    tecnico_recomendado_id INTEGER REFERENCES usuarios(id),
    tecnico_recomendado_nombre TEXT,
    estado TEXT DEFAULT 'Propuesto',
    motivo_rechazo TEXT,
    mantenimiento_id INTEGER REFERENCES mantenimiento(id),
    aprobado_por TEXT,
    fecha_creado TIMESTAMP DEFAULT NOW(),
    fecha_resuelto TIMESTAMP
);
```

#### alertas_operaciones

```sql
CREATE TABLE IF NOT EXISTS alertas_operaciones (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL,
    nivel TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    entidad_tipo TEXT,
    entidad_id INTEGER,
    metadata_json TEXT,
    leida BOOLEAN DEFAULT FALSE,
    fecha TIMESTAMP DEFAULT NOW()
);
```

### Columnas nuevas en tablas existentes

```sql
-- Agregar especialización a usuarios
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS especialidad TEXT DEFAULT '';
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE;

-- Agregar tracking de asignación a mantenimiento
ALTER TABLE mantenimiento ADD COLUMN IF NOT EXISTS tecnico_id INTEGER REFERENCES usuarios(id);
ALTER TABLE mantenimiento ADD COLUMN IF NOT EXISTS tiempo_estimado_horas NUMERIC(5,1);
ALTER TABLE mantenimiento ADD COLUMN IF NOT EXISTS costo_estimado NUMERIC(10,2);
ALTER TABLE mantenimiento ADD COLUMN IF NOT EXISTS origen TEXT DEFAULT 'manual';
```

> **Nota:** La columna existente `mantenimiento.tecnico` (TEXT libre) coexiste con la nueva `tecnico_id` (FK). Código nuevo usa `tecnico_id`; el display cae a `tecnico` cuando `tecnico_id` es NULL.

---

## Diagrama ER Expandido (15 Tablas)

```mermaid
erDiagram
    usuarios {
        SERIAL id PK
        VARCHAR username
        TEXT password
        TEXT rol
        TEXT nombre_completo
        TEXT email
        TEXT telefono
        TEXT especialidad "NUEVO"
        BOOLEAN activo "NUEVO"
    }

    mantenimiento {
        SERIAL id PK
        INTEGER habitacion_id FK
        TEXT tipo
        TEXT elemento
        TEXT descripcion
        TEXT tecnico
        TEXT fecha
        TEXT estado
        NUMERIC costo
        TEXT prioridad
        INTEGER tecnico_id FK "NUEVO"
        NUMERIC tiempo_estimado_horas "NUEVO"
        NUMERIC costo_estimado "NUEVO"
        TEXT origen "NUEVO: manual/auto/inspeccion"
    }

    predicciones_costo {
        SERIAL id PK
        INTEGER equipo_id FK
        INTEGER habitacion_id FK
        NUMERIC costo_estimado
        NUMERIC rango_min
        NUMERIC rango_max
        NUMERIC confianza
        TEXT factores_json
        TEXT modelo_usado
        TIMESTAMP fecha_prediccion
    }

    perfiles_tecnico {
        SERIAL id PK
        INTEGER tecnico_id FK
        TEXT especialidades_json
        INTEGER total_trabajos
        NUMERIC tiempo_promedio_horas
        NUMERIC costo_promedio
        NUMERIC calificacion
        INTEGER carga_actual
        TIMESTAMP fecha_actualizado
    }

    planes_mantenimiento {
        SERIAL id PK
        INTEGER equipo_id FK
        INTEGER habitacion_id FK
        TEXT tipo_equipo
        DATE fecha_sugerida
        TEXT prioridad
        TEXT razon
        NUMERIC costo_estimado
        INTEGER tecnico_recomendado_id FK
        TEXT estado "Propuesto/Aprobado/Rechazado/Ejecutado"
        TEXT motivo_rechazo
        INTEGER mantenimiento_id FK
        TEXT aprobado_por
        TIMESTAMP fecha_creado
        TIMESTAMP fecha_resuelto
    }

    alertas_operaciones {
        SERIAL id PK
        TEXT tipo
        TEXT nivel
        TEXT mensaje
        TEXT entidad_tipo
        INTEGER entidad_id
        TEXT metadata_json
        BOOLEAN leida
        TIMESTAMP fecha
    }

    equipos ||--o{ predicciones_costo : "costo predicho"
    usuarios ||--o{ perfiles_tecnico : "perfil"
    usuarios ||--o{ mantenimiento : "asignado via tecnico_id"
    equipos ||--o{ planes_mantenimiento : "plan preventivo"
    planes_mantenimiento ||--o| mantenimiento : "genera orden"
```

---

## Flujo de Automatización Completo

```mermaid
flowchart TD
    START["📅 Admin: Generar Plan Preventivo<br/>/scheduler/generar"]
    START --> PRED["🤖 ejecutar_predicciones()<br/>prob_7, prob_14, prob_30"]
    PRED --> FILTER["🔍 Filtrar: prob_30 >= 0.4<br/>O edad > 80% vida_útil"]
    FILTER --> COST["💰 predecir_costos_batch()<br/>Costo estimado por equipo"]
    COST --> TEC["👷 recomendar_tecnico()<br/>Mejor técnico por orden"]
    TEC --> PLAN["📋 INSERT planes_mantenimiento<br/>estado = 'Propuesto'"]
    PLAN --> NOTIFY["📢 SocketIO: alerta_global<br/>'N items generados'"]
    NOTIFY --> REVIEW["👑 Admin revisa plan<br/>/scheduler"]
    REVIEW -->|Aprobar| APPROVE["✅ aprobar_plan()<br/>INSERT mantenimiento"]
    REVIEW -->|Rechazar| REJECT["❌ rechazar_plan()<br/>Con motivo"]
    APPROVE --> ORDER["🔧 Orden preventiva creada<br/>tipo='Preventivo', origen='auto'"]
    ORDER --> SOCKET["📢 SocketIO: alerta_global<br/>'Orden preventiva creada'"]

    subgraph INTEGRACION["🔗 Integración con Flujos Existentes"]
        ORDER --> MANT["mantenimiento.py<br/>Flujo normal de seguimiento"]
        MANT --> COMPLETE["Técnico completa → Disponible"]
    end
```

---

## Plan de Refactorización (Migración Segura)

### Orden de implementación (sin romper nada)

| Fase | Archivos | Dependencias | Riesgo |
|------|----------|-------------|--------|
| 1 | `ai/feature_utils.py` | Ninguna (nuevo) | Bajo |
| 2 | `database/init_schema_v2.py` | Ninguna (CREATE IF NOT EXISTS) | Bajo |
| 3 | `ai/cost_predictor.py` | feature_utils | Bajo |
| 4 | `ai/technician_recommender.py` | Solo DB existente | Bajo |
| 5 | `ai/maintenance_scheduler.py` | predictor + cost + technician | Medio |
| 6 | `ai/services/*.py` (7 archivos) | Todos los módulos IA | Medio |
| 7 | `routes/costos_ai.py` + `routes/tecnicos_ai.py` | Services | Bajo |
| 8 | `routes/scheduler.py` + `routes/operations.py` | Services | Bajo |
| 9 | `routes/__init__.py` + `app.py` | Registrar blueprints V2 | Bajo |
| 10 | Refactorizar rutas existentes → Services | Reemplazar imports | **Alto** |
| 11 | Refactorizar `train_model.py` + `predictor.py` → feature_utils | Reemplazar duplicación | Medio |

### Migración de rutas existentes (Fase 10)

```python
# ANTES (routes/predicciones.py):
from ai.predictor import ejecutar_predicciones
resultado = ejecutar_predicciones("random_forest")

# DESPUÉS:
from ai.services.prediction_service import ejecutar_predicciones_srv
conn = conectar()
resultado = ejecutar_predicciones_srv(conn, "random_forest")
conn.close()
```

```python
# ANTES (routes/vision.py):
from ai.detector import analizar_imagen
resultado = analizar_imagen(ruta, habitacion_id, username)

# DESPUÉS:
from ai.services.vision_service import analizar_imagen_srv
conn = conectar()
resultado = analizar_imagen_srv(conn, ruta, habitacion_id, username)
conn.close()
```

```python
# ANTES (routes/limpieza.py):
from ai.scoring_engine import registrar_checkout
registrar_checkout(hab_id, checkin, categoria)

# DESPUÉS:
from ai.services.cleaning_service import registrar_checkout_srv
conn = conectar()
registrar_checkout_srv(conn, hab_id, checkin, categoria)
conn.close()
```

---

## Recomendaciones de Arquitectura

### 1. Decisiones de Diseño Clave

| Decisión | Justificación |
|----------|--------------|
| **GBR para costos** (no deep learning) | Datos tabulares moderados. GBR supera DL aquí sin GPU |
| **Scoring ponderado para técnicos** (no ML) | <20 técnicos = muy pocos datos. Scoring es transparente y tunable |
| **Plan → Aprobación** (no auto-crear órdenes) | Supervisión humana sobre sugerencias de IA. Evita flood de órdenes |
| **Service layer con conn inyectado** | Desacopla DB de IA. Permite testing con mocks |
| **feature_utils.py compartido** | Elimina duplicación entre 4+ módulos. Single source of truth |

### 2. Navegación del Sidebar (actualizar base.html)

```
🧠 Inteligencia Artificial
├── Predicciones          (existente)
├── Visión                (existente)
├── Limpieza              (existente)
├── Costos AI             (NUEVO)
├── Técnicos AI           (NUEVO)
├── Scheduler             (NUEVO, solo admin)
└── Operaciones           (NUEVO, solo admin)
```

### 3. Evolución Futura

| Siguiente paso | Prioridad | Complejidad |
|----------------|-----------|-------------|
| Caching con Redis para predicciones | Media | Baja |
| Async con Celery para entrenamiento | Alta | Media |
| API REST completa (JWT auth) | Media | Media |
| Modelo de satisfacción del huésped | Baja | Alta |
| Integración con PMS (Property Management System) | Alta | Alta |
