"""
Recomendación de Técnicos — Sistema de Scoring Ponderado
Sugiere el mejor técnico para cada orden de mantenimiento.
Factores: especialidad (35%), rendimiento (25%), carga (20%), disponibilidad (10%), costo (10%)
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.db import conectar

# Pesos de scoring
W_ESPECIALIDAD = 0.35
W_RENDIMIENTO = 0.25
W_CARGA = 0.20
W_DISPONIBILIDAD = 0.10
W_COSTO = 0.10


def recomendar_tecnico(conn, mantenimiento_id):
    """
    Scores todos los técnicos para una orden de mantenimiento específica.
    Retorna: lista de {tecnico_id, nombre, score, razones, desglose} ordenada DESC por score
    """
    cursor = conn.cursor()

    # 1. Obtener detalles de la orden
    cursor.execute("""
        SELECT m.id, m.habitacion_id, m.tipo, m.elemento, m.prioridad,
               h.numero
        FROM mantenimiento m
        JOIN habitaciones h ON m.habitacion_id = h.id
        WHERE m.id = %s
    """, (mantenimiento_id,))
    orden = cursor.fetchone()

    if not orden:
        cursor.close()
        return []

    _, hab_id, tipo_mant, elemento, prioridad, hab_num = orden
    elemento = elemento or ""

    # 2. Obtener todos los técnicos activos (empleados)
    cursor.execute("""
        SELECT id, username, nombre_completo, especialidad
        FROM usuarios
        WHERE rol IN ('empleado', 'tecnico')
        AND (activo IS NULL OR activo = TRUE)
    """)
    tecnicos = cursor.fetchall()

    if not tecnicos:
        cursor.close()
        return []

    # 3. Promedios globales para normalización
    cursor.execute("""
        SELECT COALESCE(AVG(tiempo_reparacion_horas), 4) as avg_tiempo,
               COALESCE(AVG(costo), 200) as avg_costo
        FROM historial_fallas
    """)
    global_stats = cursor.fetchone()
    avg_tiempo_global = float(global_stats[0])
    avg_costo_global = float(global_stats[1])

    recomendaciones = []

    for tec_id, username, nombre, especialidad in tecnicos:
        nombre_display = nombre or username
        razones = []

        # A. Score de especialidad (35%)
        # % de trabajos pasados que coinciden con el elemento de esta orden
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(*) FILTER (WHERE hf.tipo_falla ILIKE %s OR e.tipo ILIKE %s) as match
            FROM historial_fallas hf
            JOIN equipos e ON hf.equipo_id = e.id
            WHERE hf.tecnico_id = %s
        """, (f"%{elemento}%", f"%{elemento}%", tec_id))
        esp_row = cursor.fetchone()
        total_trabajos = int(esp_row[0])
        match_trabajos = int(esp_row[1])

        if total_trabajos > 0:
            esp_score = match_trabajos / total_trabajos
        elif especialidad and elemento.lower() in especialidad.lower():
            esp_score = 0.5
        else:
            esp_score = 0.2  # Sin historial, score base

        if esp_score > 0.5:
            razones.append(f"{match_trabajos}/{total_trabajos} trabajos similares")

        # B. Score de rendimiento (25%)
        # Tiempo promedio vs global (menor = mejor)
        cursor.execute("""
            SELECT COALESCE(AVG(tiempo_reparacion_horas), %s)
            FROM historial_fallas WHERE tecnico_id = %s
        """, (avg_tiempo_global, tec_id))
        avg_tiempo_tec = float(cursor.fetchone()[0])

        if avg_tiempo_tec > 0 and avg_tiempo_global > 0:
            rend_score = min(avg_tiempo_global / avg_tiempo_tec, 2.0) / 2.0
        else:
            rend_score = 0.5

        if rend_score > 0.6:
            razones.append(f"Tiempo promedio: {avg_tiempo_tec:.1f}h (vs {avg_tiempo_global:.1f}h global)")

        # C. Score de carga (20%)
        # Inverso del número de órdenes activas
        cursor.execute("""
            SELECT COUNT(*) FROM mantenimiento
            WHERE (tecnico = %s OR tecnico_id = %s)
            AND (estado IS NULL OR estado != 'Completado')
        """, (nombre_display, tec_id))
        carga = int(cursor.fetchone()[0])

        if carga == 0:
            carga_score = 1.0
            razones.append("Sin tareas pendientes")
        elif carga <= 2:
            carga_score = 0.7
        elif carga <= 5:
            carga_score = 0.4
        else:
            carga_score = 0.1

        # D. Score de disponibilidad (10%)
        # 1.0 si no tiene tareas críticas, 0.5 si tiene
        cursor.execute("""
            SELECT COUNT(*) FROM mantenimiento
            WHERE (tecnico = %s OR tecnico_id = %s)
            AND prioridad = 'Crítica'
            AND (estado IS NULL OR estado != 'Completado')
        """, (nombre_display, tec_id))
        criticas = int(cursor.fetchone()[0])

        disp_score = 0.5 if criticas > 0 else 1.0
        if criticas > 0:
            razones.append(f"Tiene {criticas} tarea(s) crítica(s)")

        # E. Score de costo (10%)
        # Costo promedio vs global (menor = mejor)
        cursor.execute("""
            SELECT COALESCE(AVG(costo), %s)
            FROM historial_fallas WHERE tecnico_id = %s
        """, (avg_costo_global, tec_id))
        avg_costo_tec = float(cursor.fetchone()[0])

        if avg_costo_tec > 0 and avg_costo_global > 0:
            costo_score = min(avg_costo_global / avg_costo_tec, 2.0) / 2.0
        else:
            costo_score = 0.5

        # Score total
        score_total = (
            W_ESPECIALIDAD * esp_score +
            W_RENDIMIENTO * rend_score +
            W_CARGA * carga_score +
            W_DISPONIBILIDAD * disp_score +
            W_COSTO * costo_score
        )

        recomendaciones.append({
            "tecnico_id": tec_id,
            "nombre": nombre_display,
            "score": round(score_total, 4),
            "razones": razones if razones else ["Sin historial previo"],
            "desglose": {
                "especialidad": round(esp_score, 3),
                "rendimiento": round(rend_score, 3),
                "carga": round(carga_score, 3),
                "disponibilidad": round(disp_score, 3),
                "costo": round(costo_score, 3),
            },
            "carga_actual": carga,
            "total_trabajos": total_trabajos,
        })

    cursor.close()

    recomendaciones.sort(key=lambda x: x["score"], reverse=True)
    return recomendaciones


def obtener_estadisticas_tecnico(conn, tecnico_id):
    """
    Perfil de rendimiento de un técnico.
    Retorna: {especialidades, avg_tiempo, avg_costo, total_trabajos, carga_actual, trabajos_por_tipo}
    """
    cursor = conn.cursor()

    # Info básica
    cursor.execute("""
        SELECT username, nombre_completo, especialidad
        FROM usuarios WHERE id = %s
    """, (tecnico_id,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        return None

    username, nombre, especialidad = user
    nombre_display = nombre or username

    # Estadísticas de historial_fallas
    cursor.execute("""
        SELECT COUNT(*) as total,
               COALESCE(AVG(tiempo_reparacion_horas), 0) as avg_tiempo,
               COALESCE(AVG(costo), 0) as avg_costo
        FROM historial_fallas WHERE tecnico_id = %s
    """, (tecnico_id,))
    stats = cursor.fetchone()

    # Trabajos por tipo de equipo
    cursor.execute("""
        SELECT e.tipo, COUNT(*) as cantidad
        FROM historial_fallas hf
        JOIN equipos e ON hf.equipo_id = e.id
        WHERE hf.tecnico_id = %s
        GROUP BY e.tipo
        ORDER BY cantidad DESC
    """, (tecnico_id,))
    por_tipo = {row[0]: row[1] for row in cursor.fetchall()}

    # Carga actual
    cursor.execute("""
        SELECT COUNT(*) FROM mantenimiento
        WHERE (tecnico = %s OR tecnico_id = %s)
        AND (estado IS NULL OR estado != 'Completado')
    """, (nombre_display, tecnico_id))
    carga = int(cursor.fetchone()[0])

    cursor.close()

    return {
        "tecnico_id": tecnico_id,
        "nombre": nombre_display,
        "especialidad": especialidad or "",
        "total_trabajos": int(stats[0]),
        "avg_tiempo": round(float(stats[1]), 2),
        "avg_costo": round(float(stats[2]), 2),
        "trabajos_por_tipo": por_tipo,
        "carga_actual": carga,
    }


def ranking_tecnicos(conn):
    """Todos los técnicos rankeados por score compuesto de rendimiento."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, nombre_completo
        FROM usuarios
        WHERE rol IN ('empleado', 'tecnico')
        AND (activo IS NULL OR activo = TRUE)
    """)
    tecnicos = cursor.fetchall()
    cursor.close()

    ranking = []
    for tec_id, username, nombre in tecnicos:
        stats = obtener_estadisticas_tecnico(conn, tec_id)
        if stats:
            # Score compuesto: eficiencia temporal + volumen + eficiencia en costos
            vol_score = min(stats["total_trabajos"] / 50.0, 1.0)
            tiempo_score = 1.0 / max(stats["avg_tiempo"] / 4.0, 0.5) if stats["avg_tiempo"] > 0 else 0.5
            carga_score = 1.0 / max(stats["carga_actual"], 1)

            score = (vol_score * 0.3) + (min(tiempo_score, 1.0) * 0.4) + (carga_score * 0.3)

            stats["score_global"] = round(score, 4)
            ranking.append(stats)

    ranking.sort(key=lambda x: x["score_global"], reverse=True)
    return ranking


if __name__ == "__main__":
    conn = conectar()
    rank = ranking_tecnicos(conn)
    conn.close()
    for r in rank:
        print(f"  {r['nombre']}: score={r['score_global']} | {r['total_trabajos']} trabajos | carga={r['carga_actual']}")
