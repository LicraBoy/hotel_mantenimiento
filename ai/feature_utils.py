"""
Feature Engineering Compartido — Single Source of Truth
Extrae lógica duplicada de train_model.py y predictor.py en funciones reutilizables.
Usado por: predictor.py, train_model.py, cost_predictor.py, maintenance_scheduler.py
"""
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.preprocessing import LabelEncoder

FEATURE_NAMES = [
    "tipo_equipo_enc", "mes", "dia_semana", "edad_equipo_dias",
    "dias_desde_anterior", "fallas_previas", "costo_promedio",
    "severidad_enc", "costo", "tiempo_reparacion_horas"
]


def preparar_features_desde_df(df):
    """
    Pipeline compartido de feature engineering para entrenamiento.
    Extrae de train_model.py:cargar_datos() líneas 46-80.

    Input:  DataFrame crudo con columnas de historial_fallas + equipos
            (equipo_id, fecha_falla, fecha_instalacion, tipo_equipo, severidad,
             costo, tiempo_reparacion_horas)
    Output: (X: DataFrame, y: Series, encoders: dict, feature_names: list)
    """
    df = df.copy()

    # Conversión de fechas
    df["fecha_falla"] = pd.to_datetime(df["fecha_falla"])
    df["fecha_instalacion"] = pd.to_datetime(df["fecha_instalacion"])

    # Features temporales
    df["mes"] = df["fecha_falla"].dt.month
    df["dia_semana"] = df["fecha_falla"].dt.dayofweek

    # Edad del equipo
    df["edad_equipo_dias"] = (df["fecha_falla"] - df["fecha_instalacion"]).dt.days

    # Días desde la falla anterior (por equipo)
    df["dias_desde_anterior"] = (
        df.groupby("equipo_id")["fecha_falla"].diff().dt.days.fillna(365)
    )

    # Conteo acumulado de fallas
    df["fallas_previas"] = df.groupby("equipo_id").cumcount()

    # Costo promedio acumulado
    df["costo_promedio"] = (
        df.groupby("equipo_id")["costo"]
        .expanding()
        .mean()
        .reset_index(level=0, drop=True)
    )

    # Target: ¿hubo falla dentro de los próximos 30 días?
    df["dias_hasta_siguiente"] = df.groupby("equipo_id")["fecha_falla"].shift(-1)
    df["dias_hasta_siguiente"] = (df["dias_hasta_siguiente"] - df["fecha_falla"]).dt.days
    df["falla_pronto"] = (df["dias_hasta_siguiente"].fillna(999) <= 30).astype(int)

    # Encodings
    le_equipo = LabelEncoder()
    df["tipo_equipo_enc"] = le_equipo.fit_transform(df["tipo_equipo"])

    le_severidad = LabelEncoder()
    df["severidad_enc"] = le_severidad.fit_transform(df["severidad"])

    X = df[FEATURE_NAMES].fillna(0)
    y = df["falla_pronto"]

    encoders = {
        "le_equipo": le_equipo,
        "le_severidad": le_severidad,
    }

    return X, y, encoders, FEATURE_NAMES, df


def preparar_features_equipo(
    tipo_equipo,
    fecha_instalacion,
    fecha_ultima_falla,
    total_fallas,
    costo_promedio,
    ultimo_costo,
    ultimo_tiempo_rep,
    severidad,
    le_equipo,
    le_severidad,
):
    """
    Vector de features para un equipo individual (inferencia).
    Extrae de predictor.py:ejecutar_predicciones() líneas 74-105.

    Output: dict {feature_name: value}
    """
    hoy = datetime.now()

    # Encode tipo equipo
    try:
        tipo_enc = le_equipo.transform([tipo_equipo])[0]
    except ValueError:
        tipo_enc = 0

    # Encode severidad
    try:
        sev_enc = le_severidad.transform([severidad])[0]
    except ValueError:
        sev_enc = 1

    # Días desde última falla
    if fecha_ultima_falla:
        dias_desde = (hoy.date() - fecha_ultima_falla).days
    else:
        dias_desde = 365

    # Edad del equipo
    if fecha_instalacion:
        edad = (hoy.date() - fecha_instalacion).days
    else:
        edad = 365

    return {
        "tipo_equipo_enc": tipo_enc,
        "mes": hoy.month,
        "dia_semana": hoy.weekday(),
        "edad_equipo_dias": edad,
        "dias_desde_anterior": dias_desde,
        "fallas_previas": total_fallas,
        "costo_promedio": costo_promedio,
        "severidad_enc": sev_enc,
        "costo": ultimo_costo,
        "tiempo_reparacion_horas": ultimo_tiempo_rep,
    }


def features_a_array(feature_dict, feature_names=None):
    """Convierte dict de features a numpy array en el orden correcto."""
    if feature_names is None:
        feature_names = FEATURE_NAMES
    return np.array([[feature_dict.get(f, 0) for f in feature_names]])
