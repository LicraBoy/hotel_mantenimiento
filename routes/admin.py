from flask import Blueprint, render_template, request, redirect, session, flash
from database.db import conectar
from werkzeug.security import generate_password_hash
from routes.auth import requiere_rol, requiere_login

admin_bp = Blueprint("admin", __name__)


# ===============================
# Perfil de Usuario
# ===============================
@admin_bp.route("/perfil", methods=["GET", "POST"])
@requiere_login
def perfil():
    conn = conectar()
    cursor = conn.cursor()
    user_id = session.get("user_id")

    if request.method == "POST":
        nombre_completo = request.form.get("nombre_completo", "")
        email = request.form.get("email", "")
        telefono = request.form.get("telefono", "")
        nueva_password = request.form.get("nueva_password", "")

        if nueva_password.strip():
            hashed_pw = generate_password_hash(nueva_password)
            cursor.execute("""
                UPDATE usuarios
                SET nombre_completo=%s, email=%s, telefono=%s, password=%s
                WHERE id=%s
            """, (nombre_completo, email, telefono, hashed_pw, user_id))
        else:
            cursor.execute("""
                UPDATE usuarios
                SET nombre_completo=%s, email=%s, telefono=%s
                WHERE id=%s
            """, (nombre_completo, email, telefono, user_id))

        conn.commit()
        cursor.close()
        conn.close()
        flash("✅ Perfil actualizado correctamente")
        return redirect("/perfil")

    cursor.execute("""
        SELECT id, username, nombre_completo, email, telefono, rol
        FROM usuarios WHERE id=%s
    """, (user_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template("perfil.html", usuario=usuario)


# ===============================
# Gestión de Usuarios
# ===============================
@admin_bp.route("/admin/usuarios")
@requiere_rol("admin")
def lista_usuarios():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, nombre_completo, email, telefono, rol
        FROM usuarios ORDER BY id
    """)
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin_usuarios.html", usuarios=usuarios)


@admin_bp.route("/admin/usuarios/nuevo", methods=["GET", "POST"])
@requiere_rol("admin")
def nuevo_usuario():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        nombre_completo = request.form.get("nombre_completo", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()
        rol = request.form.get("rol", "empleado")

        if not username or not password:
            flash("⚠️ Username y contraseña son obligatorios")
            return redirect("/admin/usuarios")

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM usuarios WHERE username=%s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash("⚠️ El username ya está registrado")
            return redirect("/admin/usuarios")

        hashed_pw = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO usuarios (username, password, nombre_completo, email, telefono, rol)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (username, hashed_pw, nombre_completo, email, telefono, rol))

        conn.commit()
        cursor.close()
        conn.close()
        flash(f"✅ Usuario '{username}' registrado exitosamente como {rol}")
        return redirect("/admin/usuarios")

    return redirect("/admin/usuarios")


@admin_bp.route("/admin/usuarios/eliminar/<int:id>")
@requiere_rol("admin")
def eliminar_usuario(id):
    if id == session.get("user_id"):
        flash("⚠️ No puedes eliminarte a ti mismo")
        return redirect("/admin/usuarios")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Usuario eliminado correctamente")
    return redirect("/admin/usuarios")


# ===============================
# Historial global cronológico
# ===============================
@admin_bp.route("/historial")
def historial():
    if "user" not in session:
        return redirect("/login")

    from datetime import datetime
    
    # Filtro de fecha
    fecha_filtro = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))

    conn = conectar()
    cursor = conn.cursor()

    # Extraer tareas completadas en la fecha seleccionada
    cursor.execute("""
        SELECT h.numero, i.fecha::text, 'Inspección' as tipo,
               i.observaciones as detalle, i.empleado as responsable,
               CASE WHEN i.genera_mantenimiento = 1
                    THEN 'Generó Mantenimiento' ELSE 'Completada Libre'
               END as estado_final
        FROM inspecciones i
        JOIN habitaciones h ON i.habitacion_id = h.id
        WHERE i.fecha = %s

        UNION ALL

        SELECT h.numero, m.fecha::text, 'Mantenimiento ' || COALESCE(m.tipo, 'Correctivo') as tipo,
               COALESCE(m.elemento, '') || ' — ' || COALESCE(m.descripcion, '') as detalle,
               m.tecnico as responsable,
               COALESCE(m.estado, 'Completado') as estado_final
        FROM mantenimiento m
        JOIN habitaciones h ON m.habitacion_id = h.id
        WHERE m.fecha = %s AND (m.estado = 'Completado' OR m.estado = 'Cerrado')

        ORDER BY fecha DESC, numero ASC
    """, (fecha_filtro, fecha_filtro))

    eventos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("historial.html", eventos=eventos, fecha_actual=fecha_filtro)
