"""
Blueprint: Predicción de Costos de Reparación
Usa service layer → cost_predictor.py (Gradient Boosting Regressor)
"""
from flask import Blueprint, render_template, redirect, session, flash

from database.db import conectar
from routes.auth import requiere_login

costos_bp = Blueprint("costos", __name__)


@costos_bp.route("/costos")
@requiere_login
def panel():
    conn = conectar()

    from ai.services.cost_service import (
        obtener_predicciones_costo_existentes, obtener_metricas_costos_srv
    )

    predicciones = obtener_predicciones_costo_existentes(conn)
    metricas = obtener_metricas_costos_srv()

    total = len(predicciones)
    costo_total = sum(float(p[3]) for p in predicciones) if predicciones else 0
    costo_promedio = costo_total / total if total > 0 else 0

    conn.close()

    return render_template("costos.html",
                           predicciones=predicciones,
                           metricas=metricas,
                           total=total,
                           costo_total=round(costo_total, 2),
                           costo_promedio=round(costo_promedio, 2))


@costos_bp.route("/costos/ejecutar", methods=["POST"])
@requiere_login
def ejecutar():
    try:
        conn = conectar()
        from ai.services.cost_service import predecir_costos_srv
        resultados = predecir_costos_srv(conn)
        conn.close()
        flash(f"✅ {len(resultados)} predicciones de costo generadas")
    except Exception as e:
        flash(f"⚠️ Error: {str(e)}")

    return redirect("/costos")


@costos_bp.route("/costos/entrenar", methods=["POST"])
@requiere_login
def entrenar():
    if session.get("rol") != "admin":
        flash("⚠️ Solo administradores pueden entrenar modelos")
        return redirect("/costos")

    try:
        conn = conectar()
        from ai.services.cost_service import entrenar_modelo_costos_srv
        resultado = entrenar_modelo_costos_srv(conn)
        conn.close()

        if resultado.get("exito"):
            flash(f"✅ Modelo entrenado — R²: {resultado['r2']}, MAE: ${resultado['mae']}")
        else:
            flash(f"⚠️ {resultado.get('mensaje', 'Error desconocido')}")
    except Exception as e:
        flash(f"⚠️ Error: {str(e)}")

    return redirect("/costos")
