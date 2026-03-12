"""
Predictor de Fallas — Usa modelos entrenados para generar predicciones
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import joblib
from datetime import datetime

from database.db import conectar

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


def ejecutar_predicciones(modelo="random_forest"):
    """Calcula probabilidad de falla para cada equipo activo."""
    model_path = os.path.join(MODELS_DIR, f"{modelo}.pkl")
    if not os.path.exists(model_path):
        print(f"⚠️  Modelo no encontrado: {model_path}")
        print("   Ejecuta primero: python ai/train_model.py")
        return []

    clf = joblib.load(model_path)
    le_equipo = joblib.load(os.path.join(MODELS_DIR, "le_equipo.pkl"))
    le_severidad = joblib.load(os.path.join(MODELS_DIR, "le_severidad.pkl"))
    features_list = joblib.load(os.path.join(MODELS_DIR, "features.pkl"))

    conn = conectar()
    cursor = conn.cursor()

    # Obtener última falla de cada equipo
    cursor.execute("""
        SELECT e.id as equipo_id, e.habitacion_id, e.tipo, h.numero,
               e.fecha_instalacion, e.vida_util_dias,
               hf.fecha_falla, hf.costo, hf.tiempo_reparacion_horas,
               hf.severidad, hf.tipo_falla,
               (SELECT COUNT(*) FROM historial_fallas WHERE equipo_id = e.id) as total_fallas,
               (SELECT COALESCE(AVG(costo), 0) FROM historial_fallas WHERE equipo_id = e.id) as costo_prom
        FROM equipos e
        JOIN habitaciones h ON e.habitacion_id = h.id
        LEFT JOIN LATERAL (
            SELECT * FROM historial_fallas
            WHERE equipo_id = e.id
            ORDER BY fecha_falla DESC LIMIT 1
        ) hf ON true
        ORDER BY h.numero, e.tipo
    """)
    rows = cursor.fetchall()

    if not rows:
        cursor.close()
        conn.close()
        return []

    # Limpiar predicciones anteriores
    cursor.execute("DELETE FROM predicciones WHERE modelo_usado = %s", (modelo,))

    predicciones = []
    hoy = datetime.now()

    for row in rows:
        equipo_id, hab_id, tipo_equipo, hab_num = row[0], row[1], row[2], row[3]
        fecha_inst = row[4]
        fecha_falla = row[6]
        costo = float(row[7] or 0)
        tiempo_rep = float(row[8] or 1)
        severidad = row[9] or "Media"
        total_fallas = int(row[11])
        costo_prom = float(row[12])

        # Preparar features
        try:
            tipo_enc = le_equipo.transform([tipo_equipo])[0]
        except ValueError:
            tipo_enc = 0

        try:
            sev_enc = le_severidad.transform([severidad])[0]
        except ValueError:
            sev_enc = 1

        if fecha_falla:
            dias_desde = (hoy.date() - fecha_falla).days
        else:
            dias_desde = 365

        if fecha_inst:
            edad = (hoy.date() - fecha_inst).days
        else:
            edad = 365

        feature_values = {
            "tipo_equipo_enc": tipo_enc,
            "mes": hoy.month,
            "dia_semana": hoy.weekday(),
            "edad_equipo_dias": edad,
            "dias_desde_anterior": dias_desde,
            "fallas_previas": total_fallas,
            "costo_promedio": costo_prom,
            "severidad_enc": sev_enc,
            "costo": costo,
            "tiempo_reparacion_horas": tiempo_rep,
        }

        X = np.array([[feature_values.get(f, 0) for f in features_list]])

        # Predecir probabilidades
        if hasattr(clf, "predict_proba"):
            proba = clf.predict_proba(X)[0]
            prob_falla = float(proba[1]) if len(proba) > 1 else 0.0
        else:
            prob_falla = float(clf.predict(X)[0])

        # Ajustar para 7/14/30 días
        prob_7 = round(min(prob_falla * 0.5, 1.0), 4)
        prob_14 = round(min(prob_falla * 0.75, 1.0), 4)
        prob_30 = round(min(prob_falla, 1.0), 4)

        # Nivel de riesgo
        if prob_30 >= 0.7:
            nivel = "CRÍTICO"
        elif prob_30 >= 0.5:
            nivel = "ALTO"
        elif prob_30 >= 0.3:
            nivel = "MEDIO"
        else:
            nivel = "BAJO"

        cursor.execute("""
            INSERT INTO predicciones (equipo_id, habitacion_id, prob_7_dias, prob_14_dias, prob_30_dias,
                                      modelo_usado, nivel_riesgo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (equipo_id, hab_id, prob_7, prob_14, prob_30, modelo, nivel))

        predicciones.append({
            "equipo_id": equipo_id,
            "habitacion": hab_num,
            "tipo_equipo": tipo_equipo,
            "prob_7": prob_7,
            "prob_14": prob_14,
            "prob_30": prob_30,
            "nivel": nivel,
            "ultima_falla": str(fecha_falla) if fecha_falla else "Sin registro",
            "total_fallas": total_fallas,
        })

    conn.commit()
    cursor.close()
    conn.close()

    predicciones.sort(key=lambda x: x["prob_30"], reverse=True)
    print(f"✅ {len(predicciones)} predicciones generadas con {modelo}")
    return predicciones


if __name__ == "__main__":
    resultados = ejecutar_predicciones()
    for r in resultados[:10]:
        print(f"  Hab #{r['habitacion']} — {r['tipo_equipo']}: {r['nivel']} ({r['prob_30']*100:.0f}%)")
