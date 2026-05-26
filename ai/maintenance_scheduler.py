"""
Auto-Programación de Mantenimiento Preventivo
Orquesta: predictor + cost_predictor + technician_recommender
para generar planes de mantenimiento que el admin aprueba.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from database.db import conectar


def generar_plan_preventivo(conn, semanas_adelante=4):
    """
    Genera plan de mantenimiento preventivo combinando:
    1. Predicciones de falla (prob_30 >= 0.4)
    2. Equipos cercanos a fin de vida útil (>80%)
    3. Estimación de costos
    4. Recomendación de técnicos

    Retorna: lista de items del plan generado
    """
    from ai.predictor import ejecutar_predicciones
    from ai.cost_predictor import predecir_costo
    from ai.technician_recommender import recomendar_tecnico

    cursor = conn.cursor()
    hoy = datetime.now().date()
    fecha_limite = hoy + timedelta(weeks=semanas_adelante)

    # 1. Ejecutar predicciones de falla
    print("📅 Generando plan preventivo...")
    predicciones = ejecutar_predicciones("random_forest")

    # 2. Obtener equipos cercanos a fin de vida útil
    cursor.execute("""
        SELECT e.id, e.habitacion_id, e.tipo, h.numero,
               e.fecha_instalacion, e.vida_util_dias
        FROM equipos e
        JOIN habitaciones h ON e.habitacion_id = h.id
        WHERE e.fecha_instalacion IS NOT NULL
    """)
    equipos = cursor.fetchall()

    # Combinar equipos de riesgo
    equipos_riesgo = {}

    # De predicciones ML
    for pred in predicciones:
        if pred["prob_30"] >= 0.4:
            equipos_riesgo[pred["equipo_id"]] = {
                "fuente": "prediccion_ml",
                "prob_30": pred["prob_30"],
                "nivel": pred["nivel"],
                "habitacion": pred["habitacion"],
                "tipo_equipo": pred["tipo_equipo"],
            }

    # De edad vs vida útil
    for eq_id, hab_id, tipo, hab_num, fecha_inst, vida_util in equipos:
        if fecha_inst and vida_util:
            edad = (hoy - fecha_inst).days
            pct_vida = edad / vida_util
            if pct_vida >= 0.8 and eq_id not in equipos_riesgo:
                equipos_riesgo[eq_id] = {
                    "fuente": "fin_vida_util",
                    "prob_30": 0.0,
                    "nivel": "ALTO" if pct_vida >= 0.95 else "MEDIO",
                    "habitacion": hab_num,
                    "tipo_equipo": tipo,
                    "pct_vida": round(pct_vida, 2),
                }

    # 3. Para cada equipo, verificar si ya tiene mantenimiento preventivo pendiente
    plan_items = []

    for eq_id, info in equipos_riesgo.items():
        cursor.execute("""
            SELECT COUNT(*) FROM mantenimiento m
            JOIN equipos e ON m.habitacion_id = e.habitacion_id AND m.elemento ILIKE %s
            WHERE e.id = %s AND m.tipo = 'Preventivo'
            AND (m.estado IS NULL OR m.estado != 'Completado')
        """, (f"%{info['tipo_equipo']}%", eq_id))

        if cursor.fetchone()[0] > 0:
            continue  # Ya tiene preventivo pendiente

        # Verificar si ya tiene plan propuesto
        cursor.execute("""
            SELECT COUNT(*) FROM planes_mantenimiento
            WHERE equipo_id = %s AND estado = 'Propuesto'
        """, (eq_id,))
        if cursor.fetchone()[0] > 0:
            continue

        # Calcular fecha sugerida
        cursor.execute("""
            SELECT AVG(hf2.fecha_falla - hf1.fecha_falla)
            FROM historial_fallas hf1
            JOIN LATERAL (
                SELECT fecha_falla FROM historial_fallas
                WHERE equipo_id = hf1.equipo_id AND fecha_falla > hf1.fecha_falla
                ORDER BY fecha_falla LIMIT 1
            ) hf2 ON true
            WHERE hf1.equipo_id = %s
        """, (eq_id,))
        avg_intervalo = cursor.fetchone()[0]
        dias_base = int(float(avg_intervalo) * 0.7) if avg_intervalo else 30

        # Ajuste por nivel de riesgo
        if info["nivel"] == "CRÍTICO":
            dias_base = max(dias_base - 7, 3)
        elif info["nivel"] == "ALTO":
            dias_base = max(dias_base - 3, 5)

        fecha_sugerida = min(hoy + timedelta(days=dias_base), fecha_limite)

        # Prioridad
        if info["nivel"] == "CRÍTICO":
            prioridad = "Crítica"
        elif info["nivel"] == "ALTO":
            prioridad = "Alta"
        else:
            prioridad = "Media"

        # Razón
        if info["fuente"] == "prediccion_ml":
            razon = f"ML: prob_30={info['prob_30']:.0%}, nivel={info['nivel']}"
        else:
            razon = f"Vida útil: {info.get('pct_vida', 0):.0%} consumida"

        # Estimación de costo
        costo_est = None
        try:
            pred_costo = predecir_costo(conn, eq_id)
            if "error" not in pred_costo:
                costo_est = pred_costo["costo_estimado"]
        except Exception:
            pass

        # Obtener habitacion_id
        cursor.execute("SELECT habitacion_id FROM equipos WHERE id = %s", (eq_id,))
        hab_id = cursor.fetchone()[0]

        # Recomendar técnico (crear orden temporal para scoring)
        tec_nombre = None
        tec_id = None
        try:
            # Buscar una orden existente similar para recomendar
            cursor.execute("""
                SELECT id FROM mantenimiento
                WHERE habitacion_id = %s AND elemento ILIKE %s
                ORDER BY id DESC LIMIT 1
            """, (hab_id, f"%{info['tipo_equipo']}%"))
            mant_ref = cursor.fetchone()
            if mant_ref:
                recs = recomendar_tecnico(conn, mant_ref[0])
                if recs:
                    tec_id = recs[0]["tecnico_id"]
                    tec_nombre = recs[0]["nombre"]
        except Exception:
            pass

        # Insertar plan
        cursor.execute("""
            INSERT INTO planes_mantenimiento
            (equipo_id, habitacion_id, tipo_equipo, fecha_sugerida, prioridad,
             razon, costo_estimado, tecnico_recomendado_id, tecnico_recomendado_nombre)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (eq_id, hab_id, info["tipo_equipo"], fecha_sugerida, prioridad,
              razon, costo_est, tec_id, tec_nombre))
        plan_id = cursor.fetchone()[0]

        plan_items.append({
            "plan_id": plan_id,
            "equipo_id": eq_id,
            "habitacion": info["habitacion"],
            "tipo_equipo": info["tipo_equipo"],
            "fecha_sugerida": str(fecha_sugerida),
            "prioridad": prioridad,
            "razon": razon,
            "costo_estimado": costo_est,
            "tecnico": tec_nombre,
        })

    conn.commit()
    cursor.close()

    plan_items.sort(key=lambda x: x["prioridad"] == "Crítica", reverse=True)
    print(f"✅ Plan generado: {len(plan_items)} items de mantenimiento preventivo")
    return plan_items


def aprobar_plan(conn, plan_ids, aprobado_por):
    """
    Convierte items aprobados del plan en órdenes de mantenimiento reales.
    Retorna: {ordenes_creadas: int, ids: list}
    """
    cursor = conn.cursor()
    ordenes_ids = []

    for plan_id in plan_ids:
        cursor.execute("""
            SELECT equipo_id, habitacion_id, tipo_equipo, fecha_sugerida,
                   prioridad, costo_estimado, tecnico_recomendado_id,
                   tecnico_recomendado_nombre
            FROM planes_mantenimiento
            WHERE id = %s AND estado = 'Propuesto'
        """, (plan_id,))
        plan = cursor.fetchone()

        if not plan:
            continue

        eq_id, hab_id, tipo_eq, fecha, prioridad, costo_est, tec_id, tec_nombre = plan

        # Crear orden de mantenimiento
        cursor.execute("""
            INSERT INTO mantenimiento
            (habitacion_id, tipo, elemento, descripcion, tecnico, fecha,
             estado, prioridad, tecnico_id, costo_estimado, origen)
            VALUES (%s, 'Preventivo', %s, %s, %s, %s,
                    'Pendiente', %s, %s, %s, 'auto')
            RETURNING id
        """, (hab_id, tipo_eq,
              f"Mantenimiento preventivo auto-generado. {tipo_eq}",
              tec_nombre or "", str(fecha), prioridad, tec_id, costo_est))
        mant_id = cursor.fetchone()[0]
        ordenes_ids.append(mant_id)

        # Actualizar plan
        cursor.execute("""
            UPDATE planes_mantenimiento
            SET estado = 'Aprobado', mantenimiento_id = %s,
                aprobado_por = %s, fecha_resuelto = NOW()
            WHERE id = %s
        """, (mant_id, aprobado_por, plan_id))

        # Actualizar estado de la habitación
        cursor.execute("""
            UPDATE habitaciones SET estado = 'En mantenimiento' WHERE id = %s
        """, (hab_id,))

    conn.commit()
    cursor.close()

    print(f"✅ {len(ordenes_ids)} órdenes de mantenimiento creadas desde plan")
    return {"ordenes_creadas": len(ordenes_ids), "ids": ordenes_ids}


def rechazar_plan(conn, plan_ids, motivo=""):
    """Marca items del plan como rechazados."""
    cursor = conn.cursor()
    rechazados = 0

    for plan_id in plan_ids:
        cursor.execute("""
            UPDATE planes_mantenimiento
            SET estado = 'Rechazado', motivo_rechazo = %s, fecha_resuelto = NOW()
            WHERE id = %s AND estado = 'Propuesto'
        """, (motivo, plan_id))
        rechazados += cursor.rowcount

    conn.commit()
    cursor.close()

    return {"rechazados": rechazados}


if __name__ == "__main__":
    conn = conectar()
    items = generar_plan_preventivo(conn)
    conn.close()
    for it in items:
        print(f"  Hab #{it['habitacion']} — {it['tipo_equipo']}: {it['prioridad']} ({it['razon']})")
