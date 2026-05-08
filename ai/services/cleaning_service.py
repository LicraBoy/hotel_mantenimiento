"""
Service: Limpieza — Envuelve scoring_engine.py
"""
from ai.services.logger import get_service_logger

logger = get_service_logger(__name__)


def recalcular_scores_srv(conn):
    """Recalcula urgency scores para todas las habitaciones."""
    try:
        from ai.scoring_engine import recalcular_scores
        return recalcular_scores()
    except Exception as e:
        logger.error("recalcular_scores_srv falló: %s", e, exc_info=True)
        return []


def registrar_checkout_srv(conn, habitacion_id, checkin_siguiente=None, categoria=None):
    """Registra un check-out."""
    try:
        from ai.scoring_engine import registrar_checkout
        return registrar_checkout(habitacion_id, checkin_siguiente, categoria)
    except Exception as e:
        logger.error("registrar_checkout_srv falló (hab=%s): %s", habitacion_id, e, exc_info=True)
        return False


def completar_limpieza_srv(conn, limpieza_id):
    """Marca limpieza como completada y archiva."""
    try:
        from ai.scoring_engine import completar_limpieza
        return completar_limpieza(limpieza_id)
    except Exception as e:
        logger.error("completar_limpieza_srv falló (limpieza_id=%s): %s", limpieza_id, e, exc_info=True)
        return False
