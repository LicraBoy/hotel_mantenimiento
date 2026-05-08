from flask import Blueprint, render_template, redirect, session
from database.db import conectar

dashboard_bp = Blueprint("dashboard", __name__)


def calcular_riesgo_simple(fallas, dias_sin_mantenimiento):
    riesgo = fallas * 20 + dias_sin_mantenimiento * 2
    if riesgo > 80:
        return "CRÍTICO"
    elif riesgo > 50:
        return "ALTO"
    elif riesgo > 30:
        return "MEDIO"
    return "BAJO"


def prediccion_estadistica(fallas, dias):
    score = (fallas * 0.7) + (dias * 0.3)
    if score >= 8:
        return score, "CRÍTICO", "red"
    elif score >= 5:
        return score, "ALTO", "orange"
    return score, "ESTABLE", "green"


# ===============================
# Página principal
# ===============================
@dashboard_bp.route("/")
def home():
    return render_template("index.html")


# ===============================
# Dashboard
# ===============================
@dashboard_bp.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    # Estadísticas generales
    cursor.execute("SELECT COUNT(*) FROM habitaciones")
    total_habitaciones = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM habitaciones WHERE estado='Disponible'")
    disponibles = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM habitaciones WHERE estado!='Disponible'")
    mantenimiento = cursor.fetchone()[0]

    # Costos totales
    cursor.execute("SELECT COALESCE(SUM(costo),0) FROM mantenimiento")
    costo_total = cursor.fetchone()[0]

    # Unificación: Predicciones de Riesgo basadas en Acumulación de Fallas Correctivas
    cursor.execute("""
        SELECT h.id, h.numero, COUNT(mc.id) as fallas_correctivas
        FROM habitaciones h
        LEFT JOIN LATERAL (
            SELECT MAX(fecha) as ultima_prevencion
            FROM mantenimiento
            WHERE habitacion_id = h.id AND tipo = 'Preventivo'
        ) prev ON true
        LEFT JOIN mantenimiento mc ON mc.habitacion_id = h.id 
            AND mc.tipo IN ('Correctivo', 'Emergencia')
            AND mc.estado = 'Completado'
            AND (prev.ultima_prevencion IS NULL OR mc.fecha > prev.ultima_prevencion)
        GROUP BY h.id, h.numero
    """)
    
    predicciones = []
    for row in cursor.fetchall():
        hab_id = row[0]
        numero = row[1]
        fallas = row[2]
        
        # Escala: 0 fallas -> 0.0 Bajo | 5 fallas -> 10.0 Crítico
        score = min(fallas * 2.0, 10.0)
        
        if score >= 8.0:
            nivel = "REQUIERE PREVENCIÓN"
            color = "red"
        elif score >= 6.0:
            nivel = "ALTO"
            color = "orange"
        elif score >= 4.0:
            nivel = "MEDIO"
            color = "yellow"
        else:
            nivel = "BAJO"
            color = "green"
            
        predicciones.append((numero, score, nivel, color, hab_id))
        
    # Ordenar las predicciones (de peor a mejor) y limitar a las 5 más importantes
    predicciones.sort(key=lambda x: x[1], reverse=True)
    predicciones = predicciones[:5]

    # Ranking habitaciones más costosas
    cursor.execute("""
        SELECT h.numero, COALESCE(SUM(m.costo),0) as total_gastado
        FROM habitaciones h
        LEFT JOIN mantenimiento m ON h.id = m.habitacion_id
        GROUP BY h.id, h.numero
        ORDER BY total_gastado DESC
        LIMIT 5
    """)
    ranking_costos = cursor.fetchall()

    # Costo mensual actual
    cursor.execute("""
        SELECT COALESCE(SUM(costo),0)
        FROM mantenimiento
        WHERE TO_CHAR(fecha::date, 'YYYY-MM') = TO_CHAR(CURRENT_DATE, 'YYYY-MM')
    """)
    costo_mensual = cursor.fetchone()[0]

    # Inspecciones - Pendientes
    cursor.execute("""
        SELECT COUNT(*) FROM habitaciones
        WHERE estado = 'Pendiente de inspección'
    """)
    inspecciones_pendientes = cursor.fetchone()[0]

    # Inspecciones - Últimas 5
    cursor.execute("""
        SELECT h.numero, i.empleado, i.fecha,
               CASE WHEN i.genera_mantenimiento = 1
                    THEN 'Generó mantenimiento'
                    ELSE 'Sin novedad'
               END as estado
        FROM inspecciones i
        JOIN habitaciones h ON i.habitacion_id = h.id
        ORDER BY i.fecha DESC, i.id DESC
        LIMIT 5
    """)
    ultimas_inspecciones = cursor.fetchall()
    
    alerta = ""
    alerta_inspecciones = ""
    if inspecciones_pendientes > 0:
        alerta_inspecciones = f"⚠️ Hay {inspecciones_pendientes} inspecciones pendientes de revisión"

    # Cola de inspecciones
    cursor.execute("""
        SELECT h.id, h.numero, h.estado
        FROM habitaciones h
        WHERE h.estado = 'Pendiente de inspección'
        ORDER BY h.numero
    """)
    cola_inspecciones = cursor.fetchall()

    # Mantenimientos activos
    cursor.execute("""
        SELECT h.numero, m.elemento, m.descripcion, m.prioridad, m.fecha
        FROM mantenimiento m
        JOIN habitaciones h ON m.habitacion_id = h.id
        WHERE m.estado != 'Completado' OR m.estado IS NULL
        ORDER BY
            CASE m.prioridad
                WHEN 'Crítica' THEN 1
                WHEN 'Alta' THEN 2
                WHEN 'Media' THEN 3
                WHEN 'Baja' THEN 4
                ELSE 5
            END,
            m.fecha DESC
        LIMIT 10
    """)
    mantenimientos_activos = cursor.fetchall()

    # Costos por mes (últimos 6 meses)
    cursor.execute("""
        SELECT TO_CHAR(DATE_TRUNC('month', fecha::date), 'Mon YYYY') as mes,
               COALESCE(SUM(costo), 0) as total
        FROM mantenimiento
        WHERE fecha::date >= CURRENT_DATE - INTERVAL '6 months'
        GROUP BY DATE_TRUNC('month', fecha::date)
        ORDER BY DATE_TRUNC('month', fecha::date)
    """)
    costos_mensuales = cursor.fetchall()
    labels_costos = [row[0] for row in costos_mensuales]
    valores_costos = [float(row[1]) for row in costos_mensuales]

    # Distribución por tipo de mantenimiento
    cursor.execute("""
        SELECT tipo, COUNT(*) as total
        FROM mantenimiento
        WHERE tipo IS NOT NULL
        GROUP BY tipo
        ORDER BY total DESC
    """)
    tipos_rows = cursor.fetchall()
    labels_tipos = [row[0] for row in tipos_rows]
    valores_tipos = [int(row[1]) for row in tipos_rows]

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_habitaciones=total_habitaciones,
        disponibles=disponibles,
        mantenimiento=mantenimiento,
        alerta=alerta,
        predicciones=predicciones,
        costo_total=costo_total,
        ranking_costos=ranking_costos,
        costo_mensual=costo_mensual,
        inspecciones_pendientes=inspecciones_pendientes,
        ultimas_inspecciones=ultimas_inspecciones,
        alerta_inspecciones=alerta_inspecciones,
        rol=session.get('rol', 'empleado'),
        cola_inspecciones=cola_inspecciones,
        mantenimientos_activos=mantenimientos_activos,
        labels_costos=labels_costos,
        valores_costos=valores_costos,
        labels_tipos=labels_tipos,
        valores_tipos=valores_tipos,
    )
