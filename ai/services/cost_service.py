"""
Service: Predicción de Costos — Envuelve cost_predictor.py
"""
import os
import json
from ai.services.logger import get_service_logger

logger = get_service_logger(__name__)


def predecir_costos_srv(conn, habitacion_id=None):
    """Predicción de costos para todos o filtrado por habitación."""
    try:
        from ai.cost_predictor import predecir_costos_batch
        resultados = predecir_costos_batch(conn)
        if habitacion_id:
            resultados = [r for r in resultados if r.get("habitacion_id") == habitacion_id]
        return resultados
    except Exception as e:
        logger.error("predecir_costos_srv falló (hab=%s): %s", habitacion_id, e, exc_info=True)
        return []


def entrenar_modelo_costos_srv(conn):
    """Entrena el modelo Gradient Boosting de costos."""
    try:
        from ai.cost_predictor import entrenar_costos
        return entrenar_costos(conn)
    except Exception as e:
        logger.error("entrenar_modelo_costos_srv falló: %s", e, exc_info=True)
        return {"exito": False, "mensaje": str(e)}


def obtener_metricas_costos_srv():
    """Lee métricas del modelo de costos."""
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    path = os.path.join(models_dir, "metricas_costos.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def obtener_predicciones_costo_existentes(conn):
    """Lee predicciones de costo de la BD."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pc.id, h.numero, e.tipo, pc.costo_estimado,
               pc.rango_min, pc.rango_max, pc.confianza, pc.fecha_prediccion
        FROM predicciones_costo pc
        JOIN equipos e ON pc.equipo_id = e.id
        JOIN habitaciones h ON pc.habitacion_id = h.id
        ORDER BY pc.costo_estimado DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows
