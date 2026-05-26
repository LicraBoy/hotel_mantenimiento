"""
Service: Recomendación de Técnicos — Envuelve technician_recommender.py
"""
from ai.services.logger import get_service_logger

logger = get_service_logger(__name__)


def recomendar_tecnico_srv(conn, mantenimiento_id):
    """Recomienda técnicos para una orden de mantenimiento."""
    try:
        from ai.technician_recommender import recomendar_tecnico
        recs = recomendar_tecnico(conn, mantenimiento_id)
        return {"recomendaciones": recs, "total": len(recs)}
    except Exception as e:
        logger.error("recomendar_tecnico_srv falló (mant_id=%s): %s", mantenimiento_id, e, exc_info=True)
        return {"recomendaciones": [], "total": 0, "error": str(e)}


def obtener_perfil_tecnico_srv(conn, tecnico_id):
    """Perfil de rendimiento de un técnico."""
    try:
        from ai.technician_recommender import obtener_estadisticas_tecnico
        return obtener_estadisticas_tecnico(conn, tecnico_id)
    except Exception as e:
        logger.error("obtener_perfil_tecnico_srv falló (tec_id=%s): %s", tecnico_id, e, exc_info=True)
        return None


def ranking_tecnicos_srv(conn):
    """Ranking global de técnicos."""
    try:
        from ai.technician_recommender import ranking_tecnicos
        return ranking_tecnicos(conn)
    except Exception as e:
        logger.error("ranking_tecnicos_srv falló: %s", e, exc_info=True)
        return []
