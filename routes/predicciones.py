import os, json
from flask import Blueprint, render_template, redirect, session, flash

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.db import conectar

predicciones_bp = Blueprint("predicciones", __name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai", "models")


@predicciones_bp.route("/predicciones")
def panel():
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, h.numero, e.tipo, p.prob_7_dias, p.prob_14_dias, p.prob_30_dias,
               p.nivel_riesgo, p.modelo_usado, p.fecha_prediccion
        FROM predicciones p
        JOIN habitaciones h ON p.habitacion_id = h.id
        JOIN equipos e ON p.equipo_id = e.id
        ORDER BY p.prob_30_dias DESC
    """)
    predicciones = cursor.fetchall()

    # Stats
    total = len(predicciones)
    criticos = sum(1 for p in predicciones if p[6] == "CRÍTICO")
    altos = sum(1 for p in predicciones if p[6] == "ALTO")

    cursor.close()
    conn.close()

    # Métricas del modelo
    metricas = {}
    metricas_path = os.path.join(MODELS_DIR, "metricas.json")
    if os.path.exists(metricas_path):
        with open(metricas_path) as f:
            metricas = json.load(f)

    return render_template("predicciones.html",
                           predicciones=predicciones,
                           total=total, criticos=criticos, altos=altos,
                           metricas=metricas)


@predicciones_bp.route("/predicciones/ejecutar", methods=["POST"])
def ejecutar():
    if "user" not in session:
        return redirect("/login")

    try:
        from ai.predictor import ejecutar_predicciones
        resultados = ejecutar_predicciones()
        flash(f"✅ {len(resultados)} predicciones generadas correctamente")
    except Exception as e:
        flash(f"⚠️ Error al ejecutar predicciones: {str(e)}")

    return redirect("/predicciones")


@predicciones_bp.route("/predicciones/entrenar", methods=["POST"])
def entrenar():
    if "user" not in session:
        return redirect("/login")
    if session.get("rol") != "admin":
        flash("⚠️ Solo administradores pueden re-entrenar modelos")
        return redirect("/predicciones")

    try:
        from scripts.train_model import entrenar as train
        resultados = train()
        if resultados:
            dt = resultados.get("decision_tree", {})
            rf = resultados.get("random_forest", {})
            flash(f"✅ Modelos entrenados — DT accuracy: {dt.get('accuracy', 'N/A')}, RF accuracy: {rf.get('accuracy', 'N/A')}")
        else:
            flash("⚠️ Sin datos suficientes para entrenar")
    except Exception as e:
        flash(f"⚠️ Error: {str(e)}")

    return redirect("/predicciones")


@predicciones_bp.route("/predicciones/generar-dataset", methods=["POST"])
def generar_dataset():
    if "user" not in session:
        return redirect("/login")

    try:
        from scripts.dataset_generator import generar_dataset as gen
        equipos, fallas = gen()
        flash(f"✅ Dataset generado: {equipos} equipos, {fallas} fallas")
    except Exception as e:
        flash(f"⚠️ Error: {str(e)}")

    return redirect("/predicciones")
