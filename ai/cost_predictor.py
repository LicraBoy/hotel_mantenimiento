"""
Predictor de Costos — Gradient Boosting Regressor
Predice cuánto costará la próxima reparación de cada equipo.
Reutiliza feature_utils.py para features base + agrega features de costo.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta

from database.db import conectar
from ai.feature_utils import (
    FEATURE_NAMES, preparar_features_desde_df, preparar_features_equipo, features_a_array
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# Features adicionales para costos
COST_EXTRA_FEATURES = ["vida_util_restante_pct", "fallas_recientes_90d"]
COST_FEATURES = FEATURE_NAMES + COST_EXTRA_FEATURES


def cargar_datos_costos(conn=None):
    """
    Carga historial_fallas con target = costo.
    Reutiliza preparar_features_desde_df() para features base,
    luego agrega features específicas de costo.
    """
    close_conn = False
    if conn is None:
        conn = conectar()
        close_conn = True

    df = pd.read_sql_query("""
        SELECT hf.equipo_id, hf.habitacion_id, hf.tipo_falla, hf.fecha_falla,
               hf.costo, hf.tiempo_reparacion_horas, hf.severidad,
               e.tipo as tipo_equipo, e.fecha_instalacion, e.vida_util_dias
        FROM historial_fallas hf
        JOIN equipos e ON hf.equipo_id = e.id
        ORDER BY hf.equipo_id, hf.fecha_falla
    """, conn)

    if close_conn:
        conn.close()

    if df.empty or len(df) < 10:
        return None, None, None

    # Features base via feature_utils
    X_base, _, encoders, _, df_enriched = preparar_features_desde_df(df)

    # Features extra para costos
    df_enriched["fecha_instalacion"] = pd.to_datetime(df_enriched["fecha_instalacion"])
    df_enriched["fecha_falla"] = pd.to_datetime(df_enriched["fecha_falla"])

    # % de vida útil restante
    edad_dias = (df_enriched["fecha_falla"] - df_enriched["fecha_instalacion"]).dt.days
    vida_util = df_enriched["vida_util_dias"].fillna(1825)
    df_enriched["vida_util_restante_pct"] = ((vida_util - edad_dias) / vida_util).clip(0, 1)

    # Fallas recientes en 90 días (por equipo, ventana deslizante)
    fallas_90d = []
    for _, group in df_enriched.groupby("equipo_id"):
        counts = []
        for idx, row in group.iterrows():
            fecha = row["fecha_falla"]
            ventana = group[
                (group["fecha_falla"] >= fecha - timedelta(days=90)) &
                (group["fecha_falla"] < fecha)
            ]
            counts.append(len(ventana))
        fallas_90d.extend(counts)
    df_enriched["fallas_recientes_90d"] = fallas_90d

    X = df_enriched[COST_FEATURES].fillna(0)
    y = df_enriched["costo"].astype(float)

    return X, y, encoders


def entrenar_costos(conn=None):
    """
    Entrena Gradient Boosting Regressor para predicción de costos.
    Guarda modelo en models/cost_gbr.pkl
    """
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

    X, y, encoders = cargar_datos_costos(conn)

    if X is None:
        return {"exito": False, "mensaje": "Sin datos suficientes para entrenar"}

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("💰 Entrenando Gradient Boosting Regressor para costos...")
    gbr = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        min_samples_leaf=5,
        random_state=42,
    )
    gbr.fit(X_train, y_train)

    y_pred = gbr.predict(X_test)
    residuals = y_test.values - y_pred

    r2 = round(r2_score(y_test, y_pred), 4)
    mae = round(mean_absolute_error(y_test, y_pred), 2)
    rmse = round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2)

    # Feature importance
    importances = dict(zip(COST_FEATURES, gbr.feature_importances_.tolist()))
    importances = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))

    # Guardar modelo y residuales por tipo de equipo para rangos
    joblib.dump(gbr, os.path.join(MODELS_DIR, "cost_gbr.pkl"))
    joblib.dump(COST_FEATURES, os.path.join(MODELS_DIR, "cost_features.pkl"))

    # Calcular std de residuales para rangos de confianza
    residual_std = float(np.std(residuals))
    joblib.dump(residual_std, os.path.join(MODELS_DIR, "cost_residual_std.pkl"))

    # Guardar métricas de costos
    metricas = {
        "r2": r2, "mae": mae, "rmse": rmse,
        "feature_importance": importances,
        "samples": len(X),
    }
    with open(os.path.join(MODELS_DIR, "metricas_costos.json"), "w") as f:
        json.dump(metricas, f, indent=2)

    print(f"   R²: {r2}  MAE: ${mae}  RMSE: ${rmse}")
    print(f"✅ Modelo de costos guardado en {MODELS_DIR}/cost_gbr.pkl")

    return {"exito": True, "r2": r2, "mae": mae, "rmse": rmse, "feature_importance": importances}


def predecir_costo(conn, equipo_id):
    """
    Predice el próximo costo de reparación para un equipo específico.
    Retorna: {costo_estimado, rango_min, rango_max, confianza, factores_principales}
    """
    model_path = os.path.join(MODELS_DIR, "cost_gbr.pkl")
    if not os.path.exists(model_path):
        return {"error": "Modelo de costos no entrenado. Ejecuta entrenar_costos() primero."}

    gbr = joblib.load(model_path)
    le_equipo = joblib.load(os.path.join(MODELS_DIR, "le_equipo.pkl"))
    le_severidad = joblib.load(os.path.join(MODELS_DIR, "le_severidad.pkl"))
    residual_std = joblib.load(os.path.join(MODELS_DIR, "cost_residual_std.pkl"))

    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.tipo, e.fecha_instalacion, e.vida_util_dias, h.numero,
               hf.fecha_falla, hf.costo, hf.tiempo_reparacion_horas, hf.severidad,
               (SELECT COUNT(*) FROM historial_fallas WHERE equipo_id = e.id) as total_fallas,
               (SELECT COALESCE(AVG(costo), 0) FROM historial_fallas WHERE equipo_id = e.id) as costo_prom,
               (SELECT COUNT(*) FROM historial_fallas
                WHERE equipo_id = e.id AND fecha_falla > CURRENT_DATE - 90) as fallas_90d
        FROM equipos e
        JOIN habitaciones h ON e.habitacion_id = h.id
        LEFT JOIN LATERAL (
            SELECT * FROM historial_fallas WHERE equipo_id = e.id
            ORDER BY fecha_falla DESC LIMIT 1
        ) hf ON true
        WHERE e.id = %s
    """, (equipo_id,))
    row = cursor.fetchone()
    cursor.close()

    if not row:
        return {"error": f"Equipo {equipo_id} no encontrado"}

    tipo_equipo = row[1]
    fecha_inst = row[2]
    vida_util = row[3] or 1825
    hab_numero = row[4]
    fecha_falla = row[5]
    costo = float(row[6] or 0)
    tiempo_rep = float(row[7] or 1)
    severidad = row[8] or "Media"
    total_fallas = int(row[9])
    costo_prom = float(row[10])
    fallas_90d = int(row[11])

    # Features base
    feat = preparar_features_equipo(
        tipo_equipo, fecha_inst, fecha_falla, total_fallas,
        costo_prom, costo, tiempo_rep, severidad,
        le_equipo, le_severidad
    )

    # Features extra de costo
    if fecha_inst:
        edad = (datetime.now().date() - fecha_inst).days
        feat["vida_util_restante_pct"] = max((vida_util - edad) / vida_util, 0)
    else:
        feat["vida_util_restante_pct"] = 0.5

    feat["fallas_recientes_90d"] = fallas_90d

    X = np.array([[feat.get(f, 0) for f in COST_FEATURES]])
    costo_pred = float(gbr.predict(X)[0])
    costo_pred = max(costo_pred, 0)

    rango_min = max(costo_pred - residual_std, 0)
    rango_max = costo_pred + residual_std

    # Confianza basada en cantidad de datos
    confianza = min(total_fallas / 10.0, 1.0)

    # Top 3 factores
    cost_features_list = joblib.load(os.path.join(MODELS_DIR, "cost_features.pkl"))
    importances = dict(zip(cost_features_list, gbr.feature_importances_))
    top_factores = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "equipo_id": equipo_id,
        "habitacion": hab_numero,
        "tipo_equipo": tipo_equipo,
        "costo_estimado": round(costo_pred, 2),
        "rango_min": round(rango_min, 2),
        "rango_max": round(rango_max, 2),
        "confianza": round(confianza, 4),
        "factores_principales": [{"nombre": f, "peso": round(p, 4)} for f, p in top_factores],
        "total_fallas": total_fallas,
    }


def predecir_costos_batch(conn):
    """Predice costos para todos los equipos activos."""
    model_path = os.path.join(MODELS_DIR, "cost_gbr.pkl")
    if not os.path.exists(model_path):
        return []

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM equipos ORDER BY id")
    equipos = cursor.fetchall()
    cursor.close()

    resultados = []
    for (equipo_id,) in equipos:
        pred = predecir_costo(conn, equipo_id)
        if "error" not in pred:
            resultados.append(pred)

    # Guardar en BD
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predicciones_costo")
    for r in resultados:
        cursor.execute("""
            INSERT INTO predicciones_costo
            (equipo_id, habitacion_id, costo_estimado, rango_min, rango_max,
             confianza, factores_json)
            VALUES (
                %s,
                (SELECT habitacion_id FROM equipos WHERE id = %s),
                %s, %s, %s, %s, %s
            )
        """, (r["equipo_id"], r["equipo_id"], r["costo_estimado"],
              r["rango_min"], r["rango_max"], r["confianza"],
              json.dumps(r["factores_principales"])))
    conn.commit()
    cursor.close()

    resultados.sort(key=lambda x: x["costo_estimado"], reverse=True)
    print(f"✅ {len(resultados)} predicciones de costo generadas")
    return resultados


if __name__ == "__main__":
    resultado = entrenar_costos()
    if resultado and resultado.get("exito"):
        conn = conectar()
        preds = predecir_costos_batch(conn)
        conn.close()
        for p in preds[:10]:
            print(f"  Equipo #{p['equipo_id']} ({p['tipo_equipo']}): ${p['costo_estimado']} [{p['rango_min']}-{p['rango_max']}]")
