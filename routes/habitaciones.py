from flask import Blueprint, render_template, request, redirect, session, flash
import os
from database.db import conectar
from werkzeug.security import check_password_hash
from routes.auth import requiere_rol

habitaciones_bp = Blueprint("habitaciones", __name__)


# ===============================
# Listar habitaciones
# ===============================
@habitaciones_bp.route("/habitaciones")
def lista():
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()
    # Modificado para incluir el mayor riesgo predictivo de la habitación
    cursor.execute("""
        SELECT h.id, h.numero, h.estado, h.fecha_ultimo_mantenimiento,
               COALESCE((
                   SELECT nivel_riesgo 
                   FROM predicciones 
                   WHERE habitacion_id = h.id 
                   ORDER BY prob_30_dias DESC 
                   LIMIT 1
               ), 'BAJO') as nivel_riesgo
        FROM habitaciones h
        ORDER BY h.numero
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("habitaciones.html", habitaciones=data)


# ===============================
# Nueva habitación
# ===============================
@habitaciones_bp.route("/habitaciones/nueva", methods=["GET", "POST"])
def nueva():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        numero = request.form["numero"]
        estado = request.form["estado"]

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM habitaciones WHERE numero=%s", (numero,))
        existe = cursor.fetchone()

        if existe:
            cursor.close()
            conn.close()
            return "⚠️ La habitación ya está registrada"

        cursor.execute("""
            INSERT INTO habitaciones(numero, estado, fecha_ultimo_mantenimiento)
            VALUES (%s, %s, %s)
        """, (numero, estado, ""))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/habitaciones")

    return render_template("habitacion_form.html")


# ===============================
# Editar habitación
# ===============================
@habitaciones_bp.route("/habitaciones/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM habitaciones WHERE id=%s", (id,))
    habitacion = cursor.fetchone()

    if request.method == "POST":
        numero = request.form["numero"]
        estado = request.form["estado"]

        cursor.execute("""
            UPDATE habitaciones SET numero=%s, estado=%s WHERE id=%s
        """, (numero, estado, id))

        cursor.execute("""
            INSERT INTO historial_habitaciones
            (habitacion_id, accion, descripcion, usuario, fecha)
            VALUES (%s, %s, %s, %s, NOW())
        """, (id, "EDICION", "Actualización de habitación", session["user"]))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/habitaciones")

    cursor.close()
    conn.close()
    return render_template("habitacion_editar.html", habitacion=habitacion)


# ===============================
# Eliminar habitación
# ===============================
@habitaciones_bp.route("/habitaciones/eliminar/<int:id>", methods=["POST"])
@requiere_rol("admin")
def eliminar(id):
    admin_pw = request.form.get("admin_password")
    user_id = session.get("user_id")

    if not admin_pw:
        flash("⚠️ Debes proporcionar la contraseña de administrador.")
        return redirect("/habitaciones")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT password FROM usuarios WHERE id=%s", (user_id,))
    row = cursor.fetchone()

    if not row or not check_password_hash(row[0], admin_pw):
        cursor.close()
        conn.close()
        flash("❌ Contraseña incorrecta. Eliminación cancelada.")
        return redirect("/habitaciones")

    cursor.execute("DELETE FROM habitaciones WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("✅ Habitación eliminada con éxito.")
    return redirect("/habitaciones")


# ===============================
# Detalle de habitación
# ===============================
@habitaciones_bp.route("/habitacion/<numero>")
def detalle(numero):
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, numero, estado FROM habitaciones WHERE numero=%s
    """, (numero,))
    habitacion_row = cursor.fetchone()

    if not habitacion_row:
        cursor.close()
        conn.close()
        return "Habitación no encontrada"

    habitacion_id = habitacion_row[0]
    habitacion = (habitacion_row[1], habitacion_row[2])

    # Línea de tiempo cronológica
    cursor.execute("""
        SELECT fecha::text, 'Inspección' as tipo, observaciones as detalle,
               CASE WHEN genera_mantenimiento = 1
                    THEN 'En mantenimiento' ELSE 'Disponible'
               END as estado_final
        FROM inspecciones WHERE habitacion_id=%s

        UNION ALL

        SELECT fecha::text, 'Mantenimiento' as tipo,
               COALESCE(elemento, '') || ' — ' || COALESCE(descripcion, '') as detalle,
               COALESCE(estado, 'Finalizado') as estado_final
        FROM mantenimiento WHERE habitacion_id=%s

        ORDER BY fecha DESC
    """, (habitacion_id, habitacion_id))
    timeline = cursor.fetchall()

    # Total gastado
    cursor.execute("""
        SELECT COALESCE(SUM(costo),0) FROM mantenimiento WHERE habitacion_id=%s
    """, (habitacion_id,))
    total_gastado = cursor.fetchone()[0]

    # Número total de fallas
    cursor.execute("SELECT COUNT(*) FROM mantenimiento WHERE habitacion_id=%s", (habitacion_id,))
    total_fallas = cursor.fetchone()[0]

    # Última fecha de mantenimiento
    cursor.execute("""
        SELECT fecha FROM mantenimiento
        WHERE habitacion_id=%s ORDER BY fecha DESC LIMIT 1
    """, (habitacion_id,))
    ultima_fecha = cursor.fetchone()
    ultima_fecha = ultima_fecha[0] if ultima_fecha else "Sin registros"

    cursor.close()
    conn.close()

    return render_template(
        "detalle_habitacion.html",
        habitacion=habitacion,
        habitacion_id=habitacion_id,
        timeline=timeline,
        total_gastado=total_gastado,
        total_fallas=total_fallas,
        ultima_fecha=ultima_fecha
    )
