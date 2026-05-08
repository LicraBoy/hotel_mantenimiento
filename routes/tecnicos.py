"""
Blueprint: Recomendación de Técnicos
Usa service layer → technician_recommender.py (Scoring Ponderado)
"""
from flask import Blueprint, render_template, request, redirect, session, flash

from database.db import conectar
from routes.auth import requiere_login

tecnicos_bp = Blueprint("tecnicos", __name__)


@tecnicos_bp.route("/tecnicos")
@requiere_login
def panel():
    conn = conectar()
    from ai.services.technician_service import ranking_tecnicos_srv
    ranking = ranking_tecnicos_srv(conn)
    conn.close()

    return render_template("tecnicos.html", ranking=ranking)


@tecnicos_bp.route("/tecnicos/recomendar/<int:mantenimiento_id>")
@requiere_login
def recomendar(mantenimiento_id):
    conn = conectar()
    from ai.services.technician_service import recomendar_tecnico_srv

    resultado = recomendar_tecnico_srv(conn, mantenimiento_id)

    # Obtener info de la orden
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, h.numero, m.tipo, m.elemento, m.prioridad, m.descripcion
        FROM mantenimiento m
        JOIN habitaciones h ON m.habitacion_id = h.id
        WHERE m.id = %s
    """, (mantenimiento_id,))
    orden = cursor.fetchone()
    cursor.close()
    conn.close()

    if not orden:
        flash("⚠️ Orden de mantenimiento no encontrada")
        return redirect("/mantenimientos")

    return render_template("tecnicos_recomendar.html",
                           orden=orden,
                           recomendaciones=resultado.get("recomendaciones", []))


@tecnicos_bp.route("/tecnicos/asignar", methods=["POST"])
@requiere_login
def asignar():
    mantenimiento_id = request.form.get("mantenimiento_id")
    tecnico_id = request.form.get("tecnico_id")
    tecnico_nombre = request.form.get("tecnico_nombre", "")

    if not mantenimiento_id or not tecnico_id:
        flash("⚠️ Datos incompletos")
        return redirect("/mantenimientos")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE mantenimiento
        SET tecnico = %s, tecnico_id = %s
        WHERE id = %s
    """, (tecnico_nombre, int(tecnico_id), int(mantenimiento_id)))
    conn.commit()
    cursor.close()
    conn.close()

    flash(f"✅ Técnico {tecnico_nombre} asignado a orden #{mantenimiento_id}")
    return redirect("/mantenimientos")


@tecnicos_bp.route("/tecnicos/perfil/<int:tecnico_id>")
@requiere_login
def perfil_tecnico(tecnico_id):
    conn = conectar()
    from ai.services.technician_service import obtener_perfil_tecnico_srv
    perfil = obtener_perfil_tecnico_srv(conn, tecnico_id)
    conn.close()

    if not perfil:
        flash("⚠️ Técnico no encontrado")
        return redirect("/tecnicos")

    return render_template("tecnicos_perfil.html", perfil=perfil)
