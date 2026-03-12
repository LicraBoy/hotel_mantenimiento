"""
Entrenamiento de Modelos ML — Decision Tree + Random Forest
Ejecutar: python ai/train_model.py
"""
import os, sys, json, warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import LabelEncoder

from database.db import conectar

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def cargar_datos():
    """Carga historial de fallas desde PostgreSQL y prepara features."""
    conn = conectar()

    df = pd.read_sql_query("""
        SELECT hf.equipo_id, hf.habitacion_id, hf.tipo_falla, hf.fecha_falla,
               hf.costo, hf.tiempo_reparacion_horas, hf.severidad,
               e.tipo as tipo_equipo, e.fecha_instalacion, e.vida_util_dias
        FROM historial_fallas hf
        JOIN equipos e ON hf.equipo_id = e.id
        ORDER BY hf.equipo_id, hf.fecha_falla
    """, conn)

    conn.close()

    if df.empty:
        print("⚠️  Sin datos. Ejecuta primero: python ai/dataset_generator.py")
        return None, None, None

    # Feature engineering
    df["fecha_falla"] = pd.to_datetime(df["fecha_falla"])
    df["fecha_instalacion"] = pd.to_datetime(df["fecha_instalacion"])
    df["mes"] = df["fecha_falla"].dt.month
    df["dia_semana"] = df["fecha_falla"].dt.dayofweek
    df["edad_equipo_dias"] = (df["fecha_falla"] - df["fecha_instalacion"]).dt.days

    # Días desde la falla anterior (por equipo)
    df["dias_desde_anterior"] = df.groupby("equipo_id")["fecha_falla"].diff().dt.days.fillna(365)

    # Conteo acumulado de fallas
    df["fallas_previas"] = df.groupby("equipo_id").cumcount()

    # Costo promedio acumulado
    df["costo_promedio"] = df.groupby("equipo_id")["costo"].expanding().mean().reset_index(level=0, drop=True)

    # Target: ¿hubo falla dentro de los próximos 30 días?
    # Para cada registro, verificamos si el siguiente fallo está dentro de 30 días
    df["dias_hasta_siguiente"] = df.groupby("equipo_id")["fecha_falla"].shift(-1)
    df["dias_hasta_siguiente"] = (df["dias_hasta_siguiente"] - df["fecha_falla"]).dt.days
    df["falla_pronto"] = (df["dias_hasta_siguiente"].fillna(999) <= 30).astype(int)

    # Encodings
    le_equipo = LabelEncoder()
    df["tipo_equipo_enc"] = le_equipo.fit_transform(df["tipo_equipo"])

    le_severidad = LabelEncoder()
    df["severidad_enc"] = le_severidad.fit_transform(df["severidad"])

    features = [
        "tipo_equipo_enc", "mes", "dia_semana", "edad_equipo_dias",
        "dias_desde_anterior", "fallas_previas", "costo_promedio",
        "severidad_enc", "costo", "tiempo_reparacion_horas"
    ]

    X = df[features].fillna(0)
    y = df["falla_pronto"]

    # Guardar encoders
    joblib.dump(le_equipo, os.path.join(MODELS_DIR, "le_equipo.pkl"))
    joblib.dump(le_severidad, os.path.join(MODELS_DIR, "le_severidad.pkl"))
    joblib.dump(features, os.path.join(MODELS_DIR, "features.pkl"))

    return X, y, df


def entrenar():
    """Entrena Decision Tree y Random Forest, guarda modelos y métricas."""
    print("📊 Cargando datos...")
    X, y, df = cargar_datos()

    if X is None:
        return None

    print(f"   {len(X)} registros, {y.sum()} positivos ({y.mean()*100:.1f}%)")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    resultados = {}

    # Decision Tree
    print("\n🌳 Entrenando Decision Tree...")
    dt = DecisionTreeClassifier(max_depth=8, min_samples_leaf=5, random_state=42)
    dt.fit(X_train, y_train)
    y_pred_dt = dt.predict(X_test)

    resultados["decision_tree"] = {
        "accuracy":  round(accuracy_score(y_test, y_pred_dt), 4),
        "precision": round(precision_score(y_test, y_pred_dt, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred_dt, zero_division=0), 4),
        "f1_score":  round(f1_score(y_test, y_pred_dt, zero_division=0), 4),
    }
    joblib.dump(dt, os.path.join(MODELS_DIR, "decision_tree.pkl"))
    print(f"   Accuracy: {resultados['decision_tree']['accuracy']}")
    print(f"   Precision: {resultados['decision_tree']['precision']}")
    print(f"   Recall: {resultados['decision_tree']['recall']}")
    print(f"   F1-Score: {resultados['decision_tree']['f1_score']}")

    # Random Forest
    print("\n🌲 Entrenando Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_leaf=3, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)

    resultados["random_forest"] = {
        "accuracy":  round(accuracy_score(y_test, y_pred_rf), 4),
        "precision": round(precision_score(y_test, y_pred_rf, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred_rf, zero_division=0), 4),
        "f1_score":  round(f1_score(y_test, y_pred_rf, zero_division=0), 4),
    }
    joblib.dump(rf, os.path.join(MODELS_DIR, "random_forest.pkl"))
    print(f"   Accuracy: {resultados['random_forest']['accuracy']}")
    print(f"   Precision: {resultados['random_forest']['precision']}")
    print(f"   Recall: {resultados['random_forest']['recall']}")
    print(f"   F1-Score: {resultados['random_forest']['f1_score']}")

    # Feature importance
    importances = dict(zip(
        joblib.load(os.path.join(MODELS_DIR, "features.pkl")),
        rf.feature_importances_.tolist()
    ))
    resultados["feature_importance"] = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))

    # Guardar métricas
    with open(os.path.join(MODELS_DIR, "metricas.json"), "w") as f:
        json.dump(resultados, f, indent=2)

    print(f"\n✅ Modelos guardados en {MODELS_DIR}/")
    print(f"📈 Métricas guardadas en metricas.json")

    return resultados


if __name__ == "__main__":
    entrenar()
