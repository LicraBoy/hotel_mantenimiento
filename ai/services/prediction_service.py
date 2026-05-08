"""
Service: Predicción de Fallas — Envuelve predictor.py + train_model.py
"""
import os
import json
from ai.services.logger import get_service_logger

logger = get_service_logger(__name__)


def ejecutar_predicciones_srv(conn, modelo="random_forest"):
    """Ejecuta predicciones de falla para todos los equipos."""
    try:
        from ai.predictor import ejecutar_predicciones
        predicciones = ejecutar_predicciones(modelo)
        criticos = sum(1 for p in predicciones if p["nivel"] == "CRÍTICO")
        altos = sum(1 for p in predicciones if p["nivel"] == "ALTO")
        return {
            "predicciones": predicciones,
            "total": len(predicciones),
            "criticos": criticos,
            "altos": altos,
            "exito": True,
        }
    except Exception as e:
        logger.error("ejecutar_predicciones_srv falló (modelo=%s): %s", modelo, e, exc_info=True)
        return {"predicciones": [], "total": 0, "criticos": 0, "altos": 0,
                "exito": False, "error": str(e)}


def entrenar_modelos_srv(conn):
    """Entrena modelos Decision Tree y Random Forest."""
    try:
        from ai.train_model import entrenar
        resultados = entrenar()
        if resultados:
            return {"resultados": resultados, "exito": True, "mensaje": "Modelos entrenados correctamente"}
        return {"resultados": {}, "exito": False, "mensaje": "Sin datos para entrenar"}
    except Exception as e:
        logger.error("entrenar_modelos_srv falló: %s", e, exc_info=True)
        return {"resultados": {}, "exito": False, "mensaje": str(e)}


def obtener_metricas_srv():
    """Lee metricas.json del disco."""
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    path = os.path.join(models_dir, "metricas.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def obtener_predicciones_existentes(conn):
    """Lee predicciones existentes de la BD."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, h.numero, e.tipo, p.prob_7_dias, p.prob_14_dias,
               p.prob_30_dias, p.nivel_riesgo, p.modelo_usado
        FROM predicciones p
        JOIN habitaciones h ON p.habitacion_id = h.id
        JOIN equipos e ON p.equipo_id = e.id
        ORDER BY p.prob_30_dias DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows
