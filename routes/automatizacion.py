"""
Blueprint: Auto-Programación de Mantenimiento Preventivo
Usa service layer → maintenance_scheduler.py (Orquestador)
"""
from flask import Blueprint, render_template, request, redirect, session, flash, jsonify

from database.db import conectar
from routes.auth import requiere_login, requiere_rol

automatizacion_bp = Blueprint("automatizacion", __name__)


@automatizacion_bp.route("/automatizacion")
@requiere_login
def panel():
    conn = conectar()
    from ai.services.scheduler_service import obtener_plan_actual, obtener_historial_planes

    plan = obtener_plan_actual(conn)
    historial = obtener_historial_planes(conn)

    total_propuestos = len(plan)
    criticos = sum(1 for p in plan if p[4] == 'Crítica')
    costo_total = sum(float(p[6] or 0) for p in plan)

    conn.close()

    return render_template("automatizacion.html",
                           plan=plan,
                           historial=historial,
                           total_propuestos=total_propuestos,
                           criticos=criticos,
                           costo_total=round(costo_total, 2))


@automatizacion_bp.route("/automatizacion/generar", methods=["POST"])
@requiere_login
def generar():
    semanas = int(request.form.get("semanas", 4))

    try:
        conn = conectar()
        from ai.services.scheduler_service import generar_plan_preventivo_srv
        items = generar_plan_preventivo_srv(conn, semanas)
        conn.close()
        flash(f"✅ Plan generado: {len(items)} acciones preventivas propuestas")
    except Exception as e:
        flash(f"⚠️ Error al generar plan: {str(e)}")

    return redirect("/automatizacion")


@automatizacion_bp.route("/automatizacion/aprobar", methods=["POST"])
@requiere_rol("admin")
def aprobar():
    plan_ids = request.form.getlist("plan_ids")
    if not plan_ids:
        flash("⚠️ Selecciona al menos un item del plan")
        return redirect("/automatizacion")

    plan_ids = [int(pid) for pid in plan_ids]

    try:
        conn = conectar()
        from ai.services.scheduler_service import aprobar_plan_srv
        resultado = aprobar_plan_srv(conn, plan_ids, session.get("user", "admin"))
        conn.close()

        creadas = resultado.get("ordenes_creadas", 0)
        flash(f"✅ {creadas} órdenes de mantenimiento creadas desde el plan")
    except Exception as e:
        flash(f"⚠️ Error: {str(e)}")

    return redirect("/automatizacion")


@automatizacion_bp.route("/automatizacion/generar-demo", methods=["POST"])
@requiere_login
def generar_demo():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM habitaciones")
    habitaciones = cursor.fetchall()

    tipos_equipo = [
        ("Aire Acondicionado", "2020-01-15", 1825),
        ("Sistema de Calefacción", "2016-06-01", 3650),
        ("Fontanería", "2018-03-10", 2555),
    ]

    total = 0
    for (hab_id,) in habitaciones:
        for tipo, fecha_inst, vida_util in tipos_equipo:
            cursor.execute(
                "SELECT id FROM equipos WHERE habitacion_id = %s AND tipo = %s",
                (hab_id, tipo)
            )
            row = cursor.fetchone()
            if row is None:
                cursor.execute("""
                    INSERT INTO equipos (habitacion_id, tipo, fecha_instalacion, vida_util_dias)
                    VALUES (%s, %s, %s, %s)
                """, (hab_id, tipo, fecha_inst, vida_util))
            else:
                cursor.execute("""
                    UPDATE equipos SET fecha_instalacion = %s, vida_util_dias = %s
                    WHERE id = %s
                """, (fecha_inst, vida_util, row[0]))
            total += 1

    conn.commit()
    cursor.close()
    conn.close()
    flash(f"✅ {total} equipos configurados para demo. Ahora genera el plan preventivo.")
    return redirect("/automatizacion")


@automatizacion_bp.route("/automatizacion/rechazar", methods=["POST"])
@requiere_rol("admin")
def rechazar():
    plan_ids = request.form.getlist("plan_ids")
    motivo = request.form.get("motivo", "")

    if not plan_ids:
        flash("⚠️ Selecciona al menos un item")
        return redirect("/automatizacion")

    plan_ids = [int(pid) for pid in plan_ids]

    try:
        conn = conectar()
        from ai.services.scheduler_service import rechazar_plan_srv
        resultado = rechazar_plan_srv(conn, plan_ids, motivo)
        conn.close()
        flash(f"✅ {resultado.get('rechazados', 0)} items rechazados")
    except Exception as e:
        flash(f"⚠️ Error: {str(e)}")

    return redirect("/automatizacion")


@automatizacion_bp.route("/automatizacion/eliminar-historial/<int:plan_id>", methods=["POST"])
@requiere_rol("admin")
def eliminar_historial(plan_id):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM planes_mantenimiento WHERE id = %s", (plan_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("✅ Registro eliminado del historial.")
    except Exception as e:
        flash(f"⚠️ Error al eliminar: {str(e)}")
    return redirect("/automatizacion")


@automatizacion_bp.route("/automatizacion/eventos")
@requiere_login
def eventos_calendario():
    """Retorna planes_mantenimiento como eventos JSON para FullCalendar."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pm.id, h.numero, pm.tipo_equipo, pm.fecha_sugerida,
               pm.prioridad, pm.costo_estimado, pm.tecnico_recomendado_nombre
        FROM planes_mantenimiento pm
        JOIN habitaciones h ON pm.habitacion_id = h.id
        WHERE pm.estado = 'Propuesto'
        ORDER BY pm.fecha_sugerida
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    COLOR_MAP = {
        "Crítica": "#ef4444",
        "Alta":    "#f59e0b",
        "Media":   "#3b82f6",
        "Baja":    "#22c55e",
    }

    eventos = []
    for pm_id, hab_num, tipo, fecha, prioridad, costo, tecnico in rows:
        eventos.append({
            "id": pm_id,
            "title": f"Hab #{hab_num} — {tipo}",
            "start": fecha.isoformat() if fecha else None,
            "color": COLOR_MAP.get(prioridad, "#6b7280"),
            "extendedProps": {
                "prioridad": prioridad,
                "tecnico": tecnico or "Sin asignar",
                "costo": float(costo) if costo else 0,
            },
        })

    return jsonify(eventos)
