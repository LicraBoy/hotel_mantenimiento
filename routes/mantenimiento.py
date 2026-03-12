from flask import Blueprint, render_template, request, redirect, session
from database.db import conectar

mantenimiento_bp = Blueprint("mantenimiento", __name__)


# ===============================
# Listar mantenimientos
# ===============================
@mantenimiento_bp.route("/mantenimientos")
def lista():
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT h.numero, m.id, m.fecha, m.tipo, m.elemento,
               m.descripcion, m.tecnico, m.estado, m.costo
        FROM mantenimiento m
        JOIN habitaciones h ON m.habitacion_id = h.id
        WHERE m.estado != 'Completado' OR m.estado IS NULL
        ORDER BY h.numero, m.fecha DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Agrupar por habitación
    habitaciones_mant = {}
    for row in rows:
        numero = row[0]
        if numero not in habitaciones_mant:
            habitaciones_mant[numero] = []
        habitaciones_mant[numero].append(row[1:])

    habitaciones_ordenadas = sorted(habitaciones_mant.items(), key=lambda x: str(x[0]))

    return render_template("mantenimientos.html", habitaciones_mant=habitaciones_ordenadas)


# ===============================
# Nuevo mantenimiento
# ===============================
@mantenimiento_bp.route("/mantenimiento/nuevo/<int:habitacion_id>", methods=["GET", "POST"])
def nuevo(habitacion_id):
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        tipo = request.form["tipo"]
        elemento = request.form["elemento"]
        descripcion = request.form["descripcion"]
        tecnico = request.form["tecnico"]
        fecha = request.form["fecha"]
        estado = request.form["estado"]
        costo = request.form["costo"]

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO mantenimiento
            (habitacion_id, tipo, elemento, descripcion, tecnico, fecha, estado, costo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (habitacion_id, tipo, elemento, descripcion, tecnico, fecha, estado, costo))

        # Sincronización automática de estado de la habitación
        nuevo_estado_hab = "En mantenimiento"
        if estado == "Completado":
            # Verificar si quedan otros mantenimientos pendientes para esta habitación
            cursor.execute("""
                SELECT COUNT(*) FROM mantenimiento 
                WHERE habitacion_id = %s AND estado != 'Completado'
            """, (habitacion_id,))
            pendientes_count = cursor.fetchone()[0]
            
            if pendientes_count == 0:
                nuevo_estado_hab = "Disponible"

        cursor.execute("""
            UPDATE habitaciones 
            SET estado = %s, fecha_ultimo_mantenimiento = CURRENT_DATE
            WHERE id = %s
        """, (nuevo_estado_hab, habitacion_id))

        conn.commit()
        cursor.close()
        conn.close()
        
        from extensions import socketio
        socketio.emit('alerta_global', {
            'tipo': 'mantenimiento',
            'habitacion_id': habitacion_id,
            'mensaje': f'Nueva orden de mantenimiento ({elemento})'
        })

        return redirect("/mantenimientos")

    return render_template("mantenimiento_form.html", habitacion_id=habitacion_id)


# ===============================
# Editar mantenimiento
# ===============================
@mantenimiento_bp.route("/mantenimiento/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        tipo = request.form.get("tipo", "Correctivo")
        elemento = request.form.get("elemento", "Inspección detectada")
        descripcion = request.form.get("descripcion", "")
        tecnico = request.form.get("tecnico", "")
        fecha = request.form.get("fecha", "")
        estado = request.form.get("estado", "Pendiente")
        costo = request.form.get("costo", 0)
        prioridad = request.form.get("prioridad", "Media")

        cursor.execute("SELECT habitacion_id FROM mantenimiento WHERE id=%s", (id,))
        hab_row = cursor.fetchone()
        
        if hab_row:
            habitacion_id = hab_row[0]

            cursor.execute("""
                UPDATE mantenimiento
                SET tipo=%s, elemento=%s, descripcion=%s, tecnico=%s, fecha=%s, estado=%s, costo=%s, prioridad=%s
                WHERE id=%s
            """, (tipo, elemento, descripcion, tecnico, fecha, estado, costo, prioridad, id))

            # Sincronización automática de estado de la habitación
            nuevo_estado_hab = "En mantenimiento"
            if estado == "Completado":
                # Verificar si quedan otros mantenimientos pendientes para esta habitación
                cursor.execute("""
                    SELECT COUNT(*) FROM mantenimiento 
                    WHERE habitacion_id = %s AND estado != 'Completado'
                """, (habitacion_id,))
                pendientes_count = cursor.fetchone()[0]
                
                if pendientes_count == 0:
                    nuevo_estado_hab = "Disponible"

            cursor.execute("""
                UPDATE habitaciones 
                SET estado = %s, fecha_ultimo_mantenimiento = CURRENT_DATE
                WHERE id = %s
            """, (nuevo_estado_hab, habitacion_id))

            conn.commit()
            
        cursor.close()
        conn.close()
        
        from extensions import socketio
        socketio.emit('alerta_global', {
            'tipo': 'mantenimiento',
            'habitacion_id': habitacion_id,
            'mensaje': f'Orden de mantenimiento actualizada ({estado})'
        })
        
        # Redirigir dependiendo del rol (si es empleado mandarlo a su cola)
        if session.get("rol") == "empleado":
            return redirect("/mis_tareas")
        return redirect("/mantenimientos")

    cursor.execute("SELECT id, tipo, elemento, descripcion, tecnico, fecha, estado, costo, prioridad FROM mantenimiento WHERE id=%s", (id,))
    mantenimiento = cursor.fetchone()
    cursor.close()
    conn.close()

    if not mantenimiento:
        return redirect("/mantenimientos")

    return render_template("mantenimiento_editar.html", mantenimiento=mantenimiento)
