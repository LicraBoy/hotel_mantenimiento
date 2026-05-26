"""
Blueprint: Dashboard de Operaciones — Vista unificada de todos los subsistemas IA
Usa service layer → operations_service.py (Agregador)
"""
from flask import Blueprint, render_template, request, redirect, session, flash, jsonify

from database.db import conectar
from routes.auth import requiere_login

operaciones_bp = Blueprint("operaciones", __name__)


@operaciones_bp.route("/operaciones")
@requiere_login
def panel():
    conn = conectar()
    from ai.services.operations_service import obtener_resumen_operaciones

    try:
        resumen = obtener_resumen_operaciones(conn)
    except Exception as e:
        resumen = {"error": str(e)}

    conn.close()

    return render_template("operaciones.html", resumen=resumen)


@operaciones_bp.route("/operaciones/alertas/leer/<int:alerta_id>", methods=["POST"])
@requiere_login
def leer_alerta(alerta_id):
    conn = conectar()
    from ai.services.operations_service import marcar_alerta_leida
    marcar_alerta_leida(conn, alerta_id)
    conn.close()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True})

    return redirect("/operaciones")


@operaciones_bp.route("/operaciones/api/resumen")
@requiere_login
def api_resumen():
    """Endpoint JSON para actualización en tiempo real."""
    conn = conectar()
    from ai.services.operations_service import obtener_resumen_operaciones

    try:
        resumen = obtener_resumen_operaciones(conn)
    except Exception as e:
        resumen = {"error": str(e)}

    conn.close()
    return jsonify(resumen)
