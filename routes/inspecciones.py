from flask import Blueprint, render_template, request, redirect, session
from database.db import conectar
from routes.auth import requiere_rol

inspecciones_bp = Blueprint("inspecciones", __name__)


# ===============================
# Registrar inspección
# ===============================
@inspecciones_bp.route("/inspeccion/<int:habitacion_id>", methods=["GET", "POST"])
def registrar(habitacion_id):
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        empleado = request.form["empleado"]
        observaciones = request.form["observaciones"]
        genera = request.form["genera"]
        prioridad = request.form.get("prioridad", "Media")

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO inspecciones
            (habitacion_id, empleado, observaciones, fecha, genera_mantenimiento)
            VALUES (%s, %s, %s, CURRENT_DATE, %s)
        """, (habitacion_id, empleado, observaciones, genera))

        if genera == "1":
            cursor.execute("""
                INSERT INTO mantenimiento
                (habitacion_id, elemento, descripcion, fecha, costo, prioridad)
                VALUES (%s, 'Inspección detectada', %s, CURRENT_DATE, 0, %s)
            """, (habitacion_id, observaciones, prioridad))

            cursor.execute("""
                UPDATE habitaciones SET estado='En mantenimiento' WHERE id=%s
            """, (habitacion_id,))
        else:
            cursor.execute("""
                UPDATE habitaciones SET estado='Disponible' WHERE id=%s
            """, (habitacion_id,))

        cursor.execute("""
            INSERT INTO historial_habitaciones
            (habitacion_id, accion, descripcion, usuario, fecha)
            VALUES (%s, %s, %s, %s, NOW())
        """, (habitacion_id, "INSPECCION", observaciones, session["user"]))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/dashboard")

    # GET
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, numero, estado FROM habitaciones WHERE id=%s", (habitacion_id,))
    habitacion = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template("inspeccion.html",
                           habitacion_id=habitacion_id,
                           habitacion=habitacion,
                           empleado_nombre=session.get('user', ''))


# ===============================
# Admin: Marcar Pendiente de Inspección
# ===============================
@inspecciones_bp.route("/habitacion/marcar_pendiente/<int:id>", methods=["POST"])
@requiere_rol('admin')
def marcar_pendiente(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE habitaciones SET estado='Pendiente de inspección' WHERE id=%s
    """, (id,))

    cursor.execute("""
        INSERT INTO historial_habitaciones
        (habitacion_id, accion, descripcion, usuario, fecha)
        VALUES (%s, %s, %s, %s, NOW())
    """, (id, "PENDIENTE_INSPECCION",
          "Admin marcó habitación como pendiente de inspección",
          session["user"]))

    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/habitaciones")


# ===============================
# Empleado: Cola de Trabajo
# ===============================
@inspecciones_bp.route("/mis_tareas")
def mis_tareas():
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT h.id, h.numero, h.estado
        FROM habitaciones h
        WHERE h.estado = 'Pendiente de inspección'
        ORDER BY h.numero
    """)
    pendientes = cursor.fetchall()

    cursor.execute("""
        SELECT m.id, h.numero, m.elemento, m.descripcion,
               m.prioridad, m.fecha, m.estado
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
    """)
    mantenimientos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("empleado_cola.html",
                           pendientes=pendientes,
                           mantenimientos=mantenimientos)
