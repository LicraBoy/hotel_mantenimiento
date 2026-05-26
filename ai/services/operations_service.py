"""
Service: Operations Dashboard — Agrega todos los subsistemas IA
"""
from datetime import datetime
from ai.services.logger import get_service_logger

logger = get_service_logger(__name__)

_RESUMEN_VACIO = {
    "predicciones": {"total": 0, "criticos": 0, "altos": 0, "medios": 0},
    "costos": {"estimado_total": 0, "promedio": 0, "total_predicciones": 0, "top_equipos": []},
    "limpieza": {"pendientes": 0, "criticas": 0, "score_promedio": 0},
    "tecnicos": {"total_activos": 0, "carga_promedio": 0},
    "scheduler": {"planes_pendientes": 0, "costo_estimado_plan": 0},
    "kpis": {"mtbf_dias": 0, "mttr_horas": 0, "disponibilidad_pct": 100.0},
    "alertas": [],
}


def obtener_resumen_operaciones(conn):
    """
    Agrega todos los subsistemas de IA en un solo payload.
    Retorna: dict con predicciones, costos, limpieza, técnicos, scheduler, alertas, kpis
    """
    try:
        cursor = conn.cursor()
        resultado = {}

        # --- Predicciones de falla ---
        cursor.execute("SELECT COUNT(*) FROM predicciones")
        total_pred = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM predicciones WHERE nivel_riesgo = 'CRÍTICO'")
        criticos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM predicciones WHERE nivel_riesgo = 'ALTO'")
        altos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM predicciones WHERE nivel_riesgo = 'MEDIO'")
        medios = cursor.fetchone()[0]

        resultado["predicciones"] = {
            "total": total_pred, "criticos": criticos, "altos": altos, "medios": medios
        }

        # --- Costos estimados ---
        cursor.execute("""
            SELECT COALESCE(SUM(costo_estimado), 0), COALESCE(AVG(costo_estimado), 0),
                   COUNT(*)
            FROM predicciones_costo
        """)
        costo_row = cursor.fetchone()
        cursor.execute("""
            SELECT e.tipo, ROUND(AVG(pc.costo_estimado)::numeric, 2)
            FROM predicciones_costo pc
            JOIN equipos e ON pc.equipo_id = e.id
            GROUP BY e.tipo ORDER BY AVG(pc.costo_estimado) DESC LIMIT 5
        """)
        top_costos = [(r[0], float(r[1])) for r in cursor.fetchall()]

        resultado["costos"] = {
            "estimado_total": round(float(costo_row[0]), 2),
            "promedio": round(float(costo_row[1]), 2),
            "total_predicciones": costo_row[2],
            "top_equipos": top_costos,
        }

        # --- Limpieza ---
        cursor.execute("""
            SELECT COUNT(*),
                   COUNT(*) FILTER (WHERE nivel_urgencia = 'CRÍTICO'),
                   COALESCE(AVG(urgency_score), 0)
            FROM limpieza_habitaciones
            WHERE estado_limpieza != 'Completada'
        """)
        limp = cursor.fetchone()
        resultado["limpieza"] = {
            "pendientes": limp[0], "criticas": limp[1],
            "score_promedio": round(float(limp[2]), 2)
        }

        # --- Técnicos ---
        cursor.execute("""
            SELECT COUNT(*) FROM usuarios
            WHERE rol IN ('empleado', 'tecnico')
            AND (activo IS NULL OR activo = TRUE)
        """)
        total_tec = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COALESCE(AVG(cnt), 0) FROM (
                SELECT COUNT(*) as cnt FROM mantenimiento
                WHERE estado != 'Completado' OR estado IS NULL
                GROUP BY tecnico
            ) sub
        """)
        carga_prom = float(cursor.fetchone()[0])

        resultado["tecnicos"] = {
            "total_activos": total_tec,
            "carga_promedio": round(carga_prom, 1),
        }

        # --- Scheduler ---
        cursor.execute("SELECT COUNT(*) FROM planes_mantenimiento WHERE estado = 'Propuesto'")
        planes_pendientes = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COALESCE(SUM(costo_estimado), 0)
            FROM planes_mantenimiento WHERE estado = 'Propuesto'
        """)
        costo_plan = float(cursor.fetchone()[0])

        resultado["scheduler"] = {
            "planes_pendientes": planes_pendientes,
            "costo_estimado_plan": round(costo_plan, 2),
        }

        # --- KPIs operacionales ---
        cursor.execute("""
            SELECT COALESCE(AVG(intervalo), 0) FROM (
                SELECT equipo_id,
                       (fecha_falla - LAG(fecha_falla) OVER (
                           PARTITION BY equipo_id ORDER BY fecha_falla
                       )) AS intervalo
                FROM historial_fallas
            ) sub WHERE intervalo IS NOT NULL
        """)
        mtbf = round(float(cursor.fetchone()[0]), 1)

        cursor.execute("""
            SELECT COALESCE(AVG(tiempo_reparacion_horas), 0) FROM historial_fallas
        """)
        mttr_hours = float(cursor.fetchone()[0])
        mttr_days = mttr_hours / 24.0

        disponibilidad = round((mtbf / (mtbf + mttr_days)) * 100, 1) if (mtbf + mttr_days) > 0 else 100.0

        resultado["kpis"] = {
            "mtbf_dias": mtbf,
            "mttr_horas": round(mttr_hours, 1),
            "disponibilidad_pct": disponibilidad,
        }

        # --- Alertas activas ---
        cursor.execute("""
            SELECT tipo, nivel, mensaje, fecha
            FROM alertas_operaciones
            WHERE leida = FALSE
            ORDER BY fecha DESC LIMIT 10
        """)
        alertas = [{"tipo": r[0], "nivel": r[1], "mensaje": r[2], "fecha": str(r[3])}
                   for r in cursor.fetchall()]
        resultado["alertas"] = alertas

        cursor.close()
        return resultado

    except Exception as e:
        logger.error("obtener_resumen_operaciones falló: %s", e, exc_info=True)
        return _RESUMEN_VACIO.copy()


def obtener_alertas_activas(conn):
    """Retorna alertas no leídas."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tipo, nivel, mensaje, entidad_tipo, entidad_id, fecha
            FROM alertas_operaciones
            WHERE leida = FALSE
            ORDER BY fecha DESC
        """)
        alertas = []
        for r in cursor.fetchall():
            alertas.append({
                "id": r[0], "tipo": r[1], "nivel": r[2], "mensaje": r[3],
                "entidad_tipo": r[4], "entidad_id": r[5], "fecha": str(r[6])
            })
        cursor.close()
        return alertas
    except Exception as e:
        logger.error("obtener_alertas_activas falló: %s", e, exc_info=True)
        return []


def marcar_alerta_leida(conn, alerta_id):
    """Marca una alerta como leída."""
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE alertas_operaciones SET leida = TRUE WHERE id = %s", (alerta_id,))
        conn.commit()
        cursor.close()
    except Exception as e:
        logger.error("marcar_alerta_leida falló (alerta_id=%s): %s", alerta_id, e, exc_info=True)
