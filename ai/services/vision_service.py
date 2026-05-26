"""
Service: Visión por Computadora — Envuelve detector.py
"""
from ai.services.logger import get_service_logger

logger = get_service_logger(__name__)


def analizar_imagen_srv(conn, ruta_imagen, habitacion_id, empleado="Sistema"):
    """Analiza una imagen de habitación y retorna resultados."""
    try:
        from ai.detector import analizar_imagen
        resultado = analizar_imagen(ruta_imagen, habitacion_id, empleado)
        return resultado
    except Exception as e:
        logger.error("analizar_imagen_srv falló (hab=%s, ruta=%s): %s", habitacion_id, ruta_imagen, e, exc_info=True)
        return {"error": str(e)}


def obtener_habitaciones_con_limpieza_activa(conn):
    """Retorna habitaciones que tienen ciclo de limpieza activo."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT h.id, h.numero
        FROM habitaciones h
        JOIN limpieza_habitaciones l ON h.id = l.habitacion_id
        WHERE l.estado_limpieza != 'Completada'
        ORDER BY h.numero
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows
