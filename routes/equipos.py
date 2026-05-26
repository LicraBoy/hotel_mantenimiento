from flask import Blueprint, render_template, request, redirect, session, flash
from datetime import date
from database.db import conectar
from routes.auth import requiere_login, requiere_rol

equipos_bp = Blueprint("equipos", __name__)

TIPOS_EQUIPO = [
    "Aire Acondicionado",
    "Sistema de Calefacción",
    "Fontanería",
    "Elevador / Ascensor",
    "Sistema Eléctrico",
    "Iluminación",
    "Calentador de Agua",
    "Extractor de Aire",
    "Sistema Contra Incendios",
    "Otro",
]


@equipos_bp.route("/equipos")
@requiere_login
def lista():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.id, h.numero, e.tipo, e.fecha_instalacion, e.vida_util_dias
        FROM equipos e
        JOIN habitaciones h ON e.habitacion_id = h.id
        ORDER BY h.numero, e.tipo
    """)
    equipos_raw = cursor.fetchall()

    cursor.execute("SELECT id, numero FROM habitaciones ORDER BY numero")
    habitaciones = cursor.fetchall()

    cursor.close()
    conn.close()

    hoy = date.today()
    equipos = []
    for eq_id, hab_num, tipo, fecha_inst, vida_util in equipos_raw:
        if fecha_inst and vida_util and vida_util > 0:
            edad_dias = (hoy - fecha_inst).days
            pct = round((edad_dias / vida_util) * 100, 1)
        else:
            pct = None
        equipos.append({
            "id": eq_id,
            "habitacion": hab_num,
            "tipo": tipo,
            "fecha_instalacion": fecha_inst,
            "vida_util_dias": vida_util,
            "vida_util_anos": round(vida_util / 365, 1) if vida_util else None,
            "pct_vida": pct,
        })

    return render_template("equipos.html",
                           equipos=equipos,
                           habitaciones=habitaciones,
                           tipos=TIPOS_EQUIPO)


@equipos_bp.route("/equipos/nuevo", methods=["POST"])
@requiere_rol("admin")
def nuevo():
    hab_id = request.form.get("habitacion_id")
    tipo = request.form.get("tipo")
    tipo_otro = request.form.get("tipo_otro", "").strip()
    fecha_inst = request.form.get("fecha_instalacion")
    vida_anos = request.form.get("vida_util_anos")

    if tipo == "Otro" and tipo_otro:
        tipo = tipo_otro

    if not all([hab_id, tipo, fecha_inst, vida_anos]):
        flash("⚠️ Completa todos los campos.")
        return redirect("/equipos")

    vida_dias = int(float(vida_anos) * 365)

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO equipos (habitacion_id, tipo, fecha_instalacion, vida_util_dias)
        VALUES (%s, %s, %s, %s)
    """, (hab_id, tipo, fecha_inst, vida_dias))
    conn.commit()
    cursor.close()
    conn.close()

    flash(f"✅ Equipo '{tipo}' registrado correctamente.")
    return redirect("/equipos")


@equipos_bp.route("/equipos/editar/<int:eq_id>", methods=["GET", "POST"])
@requiere_rol("admin")
def editar(eq_id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        tipo = request.form.get("tipo")
        tipo_otro = request.form.get("tipo_otro", "").strip()
        fecha_inst = request.form.get("fecha_instalacion")
        vida_anos = request.form.get("vida_util_anos")
        hab_id = request.form.get("habitacion_id")

        if tipo == "Otro" and tipo_otro:
            tipo = tipo_otro

        vida_dias = int(float(vida_anos) * 365)

        cursor.execute("""
            UPDATE equipos
            SET habitacion_id = %s, tipo = %s, fecha_instalacion = %s, vida_util_dias = %s
            WHERE id = %s
        """, (hab_id, tipo, fecha_inst, vida_dias, eq_id))
        conn.commit()
        cursor.close()
        conn.close()

        flash("✅ Equipo actualizado.")
        return redirect("/equipos")

    cursor.execute("""
        SELECT e.id, e.habitacion_id, h.numero, e.tipo, e.fecha_instalacion, e.vida_util_dias
        FROM equipos e
        JOIN habitaciones h ON e.habitacion_id = h.id
        WHERE e.id = %s
    """, (eq_id,))
    equipo = cursor.fetchone()

    cursor.execute("SELECT id, numero FROM habitaciones ORDER BY numero")
    habitaciones = cursor.fetchall()

    cursor.close()
    conn.close()

    if not equipo:
        flash("⚠️ Equipo no encontrado.")
        return redirect("/equipos")

    return render_template("equipos_editar.html",
                           equipo=equipo,
                           habitaciones=habitaciones,
                           tipos=TIPOS_EQUIPO)


@equipos_bp.route("/equipos/eliminar/<int:eq_id>", methods=["POST"])
@requiere_rol("admin")
def eliminar(eq_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM equipos WHERE id = %s", (eq_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("✅ Equipo eliminado.")
    return redirect("/equipos")


@equipos_bp.route("/equipos/<int:eq_id>/historial")
@requiere_login
def historial(eq_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.id, e.tipo, h.numero, e.fecha_instalacion, e.vida_util_dias, e.habitacion_id
        FROM equipos e
        JOIN habitaciones h ON e.habitacion_id = h.id
        WHERE e.id = %s
    """, (eq_id,))
    equipo_row = cursor.fetchone()

    if not equipo_row:
        cursor.close()
        conn.close()
        flash("⚠️ Equipo no encontrado.")
        return redirect("/equipos")

    hab_id = equipo_row[5]
    tipo_equipo = equipo_row[1]

    # Calcular % vida consumida
    from datetime import date
    pct_vida = None
    if equipo_row[3] and equipo_row[4]:
        edad = (date.today() - equipo_row[3]).days
        pct_vida = round((edad / equipo_row[4]) * 100, 1)

    # Historial de fallas registradas en historial_fallas
    cursor.execute("""
        SELECT hf.fecha_falla, hf.tipo_falla, hf.severidad,
               hf.costo, hf.tiempo_reparacion_horas,
               COALESCE(u.nombre_completo, u.username, 'Sin asignar')
        FROM historial_fallas hf
        LEFT JOIN usuarios u ON hf.tecnico_id = u.id
        WHERE hf.equipo_id = %s
        ORDER BY hf.fecha_falla DESC
    """, (eq_id,))
    fallas = cursor.fetchall()

    # Órdenes de mantenimiento relacionadas (habitación + tipo de equipo)
    cursor.execute("""
        SELECT m.fecha, m.tipo, m.elemento, m.descripcion,
               m.tecnico, m.estado, m.costo, m.prioridad
        FROM mantenimiento m
        WHERE m.habitacion_id = %s
          AND m.elemento ILIKE %s
        ORDER BY m.fecha DESC
        LIMIT 50
    """, (hab_id, f"%{tipo_equipo}%"))
    ordenes = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("equipo_historial.html",
                           equipo=equipo_row,
                           pct_vida=pct_vida,
                           fallas=fallas,
                           ordenes=ordenes)
