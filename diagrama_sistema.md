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
        TEMPLATES["24 Templates HTML<br/>Jinja2"]
    end

    subgraph SERVIDOR["⚙️ Servidor Flask"]
        APP["app.py<br/>Bootstrap + Migración"]
        CONFIG["config.py<br/>Configuración"]
        
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

    subgraph BD["💾 PostgreSQL — 10 Tablas"]
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
```

---

## Estructura Completa del Proyecto

```
hotel_mantenimiento/
├── app.py                        ← Bootstrap (~85 líneas)
├── config.py                     ← SECRET_KEY, DATABASE_URL
├── requirements.txt              ← 11 dependencias
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

    habitaciones ||--o{ mantenimiento : "tiene"
    habitaciones ||--o{ inspecciones : "recibe"
    habitaciones ||--o{ historial_habitaciones : "registra"
    habitaciones ||--o{ equipos : "contiene"
    habitaciones ||--o{ limpieza_habitaciones : "limpieza"
    habitaciones ||--o{ detecciones_visuales : "fotos"
    equipos ||--o{ historial_fallas : "falla"
    equipos ||--o{ predicciones : "predicción"
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
| Backend | Python 3 + Flask | 3.11+ |
| Base de datos | PostgreSQL | 16 |
| Conexión BD | psycopg2-binary | — |
| Templates | Jinja2 (24 archivos) | — |
| Estilos | CSS vanilla (global.css) | — |
| Animaciones | AOS.js | 2.3.4 |
| Iconos | Lucide Icons | Latest |
| Gráficas | Chart.js | Latest |
| ML | scikit-learn, pandas, numpy | — |
| Computer Vision | ultralytics (YOLOv8), OpenCV | 8.x |
| Serialización ML | joblib | — |
| Imágenes | Pillow | — |
| Reportes | ReportLab | — |
| Autenticación | Flask session | — |
| Infraestructura | Docker Compose | — |
| Config | python-dotenv (.env) | — |

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
