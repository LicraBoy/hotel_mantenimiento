"""
Service: Auto-Programación — Envuelve maintenance_scheduler.py
"""
from ai.services.logger import get_service_logger

logger = get_service_logger(__name__)


def generar_plan_preventivo_srv(conn, semanas=4):
    """Genera plan de mantenimiento preventivo."""
    try:
        from ai.maintenance_scheduler import generar_plan_preventivo
        return generar_plan_preventivo(conn, semanas)
    except Exception as e:
        logger.error("generar_plan_preventivo_srv falló (semanas=%s): %s", semanas, e, exc_info=True)
        raise


def aprobar_plan_srv(conn, plan_ids, aprobado_por):
    """Aprueba items del plan y crea órdenes de mantenimiento."""
    try:
        from ai.maintenance_scheduler import aprobar_plan
        resultado = aprobar_plan(conn, plan_ids, aprobado_por)
        # Enviar emails en background (no bloquea la respuesta)
        _enviar_emails_aprobacion_async(plan_ids)
        return resultado
    except Exception as e:
        logger.error("aprobar_plan_srv falló: %s", e, exc_info=True)
        return {"ordenes_creadas": 0, "ids": [], "error": str(e)}


def rechazar_plan_srv(conn, plan_ids, motivo=""):
    """Rechaza items del plan."""
    try:
        from ai.maintenance_scheduler import rechazar_plan
        return rechazar_plan(conn, plan_ids, motivo)
    except Exception as e:
        logger.error("rechazar_plan_srv falló: %s", e, exc_info=True)
        return {"rechazados": 0, "error": str(e)}


def obtener_plan_actual(conn):
    """Retorna el plan pendiente actual."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pm.id, h.numero, pm.tipo_equipo, pm.fecha_sugerida,
               pm.prioridad, pm.razon, pm.costo_estimado,
               pm.tecnico_recomendado_nombre, pm.estado, pm.fecha_creado
        FROM planes_mantenimiento pm
        JOIN habitaciones h ON pm.habitacion_id = h.id
        WHERE pm.estado = 'Propuesto'
        ORDER BY
            CASE pm.prioridad
                WHEN 'Crítica' THEN 1 WHEN 'Alta' THEN 2
                WHEN 'Media' THEN 3 WHEN 'Baja' THEN 4 ELSE 5
            END,
            pm.fecha_sugerida
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def obtener_historial_planes(conn):
    """Retorna planes pasados (aprobados/rechazados)."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pm.id, h.numero, pm.tipo_equipo, pm.fecha_sugerida,
               pm.prioridad, pm.estado, pm.aprobado_por,
               pm.fecha_resuelto, pm.motivo_rechazo
        FROM planes_mantenimiento pm
        JOIN habitaciones h ON pm.habitacion_id = h.id
        WHERE pm.estado IN ('Aprobado', 'Rechazado')
        ORDER BY pm.fecha_resuelto DESC
        LIMIT 50
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def _enviar_emails_aprobacion_async(plan_ids):
    """Lanza el envío de emails en un thread separado para no bloquear la respuesta."""
    try:
        import eventlet
        eventlet.spawn(_enviar_emails_aprobacion, plan_ids)
    except ImportError:
        import threading
        t = threading.Thread(target=_enviar_emails_aprobacion, args=(plan_ids,), daemon=True)
        t.start()


def _enviar_emails_aprobacion(plan_ids):
    """Consulta BD y envía emails a los técnicos asignados. Fallo no afecta la aprobación."""
    from utils.email_sender import enviar_email_tecnico
    from database.db import conectar
    conn = None
    try:
        conn = conectar()
        cursor = conn.cursor()
        placeholders = ",".join(["%s"] * len(plan_ids))
        cursor.execute(f"""
            SELECT pm.tecnico_recomendado_nombre, u.email,
                   h.numero, pm.tipo_equipo, pm.fecha_sugerida, pm.prioridad
            FROM planes_mantenimiento pm
            JOIN habitaciones h ON pm.habitacion_id = h.id
            LEFT JOIN usuarios u ON pm.tecnico_recomendado_id = u.id
            WHERE pm.id IN ({placeholders})
        """, plan_ids)
        for nombre, email, hab, tipo, fecha, prioridad in cursor.fetchall():
            if email:
                enviar_email_tecnico(email, nombre or "Técnico",
                                     str(hab), tipo, str(fecha), prioridad or "Media")
            else:
                logger.info("Técnico '%s' sin email. Orden: Hab #%s / %s", nombre, hab, tipo)
        cursor.close()
    except Exception as e:
        logger.error("_enviar_emails_aprobacion falló: %s", e, exc_info=True)
    finally:
        if conn:
            conn.close()
