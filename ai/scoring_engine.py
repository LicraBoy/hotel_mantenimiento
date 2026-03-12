"""
Scoring Engine — Priorización de Limpieza Urgente
Fórmula:
  urgency_score = (hours_since_checkout × 0.4) +
                  (days_since_deep_clean × 0.3) +
                  (next_checkin_proximity × 0.2) +
                  (room_category_weight × 0.1)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from database.db import conectar

CATEGORY_WEIGHTS = {
    "Presidencial": 10,
    "Suite": 8,
    "Superior": 6,
    "Estándar": 4,
}

MAX_HOURS = 48       # Máximo para normalización
MAX_DAYS_CLEAN = 30  # Máximo días sin limpieza profunda
MAX_PROXIMITY = 24   # Horas hasta próximo check-in


def recalcular_scores():
    """Recalcula urgency_score para todas las habitaciones con datos de limpieza."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT l.id, l.habitacion_id, h.numero, l.fecha_checkout,
               l.fecha_checkin_siguiente, l.fecha_ultima_limpieza_profunda,
               l.categoria_habitacion, l.estado_limpieza,
               (SELECT score_estado FROM detecciones_visuales 
                WHERE limpieza_id = l.id ORDER BY id DESC LIMIT 1) as ultimo_estado_visual,
               (SELECT confianza_promedio FROM detecciones_visuales 
                WHERE limpieza_id = l.id ORDER BY id DESC LIMIT 1) as confianza_visual
        FROM limpieza_habitaciones l
        JOIN habitaciones h ON l.habitacion_id = h.id
        WHERE l.estado_limpieza != 'Completada'
    """)
    rows = cursor.fetchall()

    ahora = datetime.now()
    resultados = []

    for row in rows:
        lid, hab_id, numero, checkout, checkin, ultima_limpieza, categoria, estado, estado_visual, confianza = row

        # 1. Horas desde check-out (0-10)
        if checkout:
            horas_checkout = (ahora - checkout).total_seconds() / 3600
            score_checkout = min(horas_checkout / MAX_HOURS * 10, 10)
        else:
            score_checkout = 5  # Valor medio si no hay dato

        # 2. Días desde última limpieza profunda (0-10)
        if ultima_limpieza:
            dias_limpieza = (ahora.date() - ultima_limpieza).days
            score_limpieza = min(dias_limpieza / MAX_DAYS_CLEAN * 10, 10)
        else:
            score_limpieza = 7  # Sin dato → urgente

        # 3. Proximidad del próximo check-in (0-10, inverso)
        if checkin:
            horas_hasta = (checkin - ahora).total_seconds() / 3600
            if horas_hasta <= 0:
                score_checkin = 10  # ¡Ya pasó!
            else:
                score_checkin = max(10 - (horas_hasta / MAX_PROXIMITY * 10), 0)
        else:
            score_checkin = 3  # Sin dato → baja urgencia

        # 4. Peso por categoría
        cat_weight = CATEGORY_WEIGHTS.get(categoria, 4)

        # Fórmula original
        urgency = (score_checkout * 0.4) + (score_limpieza * 0.3) + \
                  (score_checkin * 0.2) + (cat_weight * 0.1)
        
        # 5. Penalización por Análisis Visual (IA)
        score_visual = 0
        if estado_visual:
            conf_val = float(confianza) if confianza is not None else 0.8
            if estado_visual == 'REQUIERE_LIMPIEZA':
                score_visual = 3.0 * conf_val # Hasta +3 puntos si está sucia
            elif estado_visual == 'REQUIERE_MANTENIMIENTO':
                score_visual = 4.0 * conf_val # Hasta +4 puntos si hay daños
                
        urgency = min(urgency + score_visual, 10.0)
        urgency = round(urgency, 2)

        # Nivel
        if urgency >= 8:
            nivel = "CRÍTICO"
        elif urgency >= 6:
            nivel = "ALTO"
        elif urgency >= 4:
            nivel = "MEDIO"
        else:
            nivel = "BAJO"

        cursor.execute("""
            UPDATE limpieza_habitaciones
            SET urgency_score = %s, nivel_urgencia = %s, fecha_actualizado = NOW()
            WHERE id = %s
        """, (urgency, nivel, lid))

        resultados.append({
            "id": lid,
            "habitacion_id": hab_id,
            "numero": numero,
            "urgency_score": urgency,
            "nivel": nivel,
            "categoria": categoria,
            "estado": estado,
            "estado_visual": estado_visual,
            "confianza_visual": float(confianza) if confianza else 0.0,
            "horas_checkout": round(score_checkout / 10 * MAX_HOURS, 1) if checkout else None,
            "checkin": str(checkin) if checkin else None,
        })

    conn.commit()
    cursor.close()
    conn.close()

    resultados.sort(key=lambda x: x["urgency_score"], reverse=True)
    print(f"✅ {len(resultados)} scores de limpieza recalculados")
    return resultados


def registrar_checkout(habitacion_id, checkin_siguiente=None, categoria=None):
    """Registra un check-out y crea entrada en cola de limpieza usando la hora nativa de Postgres."""
    conn = conectar()
    cursor = conn.cursor()

    # Verificar si ya existe
    cursor.execute("SELECT id FROM limpieza_habitaciones WHERE habitacion_id=%s AND estado_limpieza != 'Completada'",
                   (habitacion_id,))
    existe = cursor.fetchone()

    if existe:
        cursor.execute("""
            UPDATE limpieza_habitaciones
            SET fecha_checkout = NOW(), fecha_checkin_siguiente = %s,
                categoria_habitacion = COALESCE(%s, categoria_habitacion),
                estado_limpieza = 'Pendiente', fecha_actualizado = NOW()
            WHERE id = %s
        """, (checkin_siguiente, categoria, existe[0]))
    else:
        cursor.execute("""
            INSERT INTO limpieza_habitaciones
            (habitacion_id, fecha_checkout, fecha_checkin_siguiente, categoria_habitacion)
            VALUES (%s, NOW(), %s, %s)
        """, (habitacion_id, checkin_siguiente, categoria or "Estándar"))

    conn.commit()
    cursor.close()
    conn.close()

    return True


def completar_limpieza(limpieza_id):
    """Marca una limpieza como completada y la archiva en el historial."""
    conn = conectar()
    cursor = conn.cursor()
    
    # Obtener info actual
    cursor.execute("""
        SELECT habitacion_id, categoria_habitacion, fecha_checkout, asignado_a, urgency_score
        FROM limpieza_habitaciones WHERE id = %s
    """, (limpieza_id,))
    limp = cursor.fetchone()
    if limp:
        hab_id, cat, f_check, emp, urg = limp
        
        cursor.execute("SELECT numero FROM habitaciones WHERE id=%s", (hab_id,))
        num_hab = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT imagen_anotada, score_estado 
            FROM detecciones_visuales 
            WHERE limpieza_id = %s 
            ORDER BY id DESC LIMIT 1
        """, (limpieza_id,))
        det = cursor.fetchone()
        img, score = (det[0], det[1]) if det else (None, "SIN_FOTO")
        
        cursor.execute("""
            INSERT INTO historial_limpieza
            (habitacion_id, numero_habitacion, categoria, fecha_checkout, empleado, imagen_evidencia, estado_ia, urgencia_inicial)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (hab_id, num_hab, cat, f_check, emp, img, score, str(urg)))
        
        cursor.execute("DELETE FROM limpieza_habitaciones WHERE id = %s", (limpieza_id,))
        
    conn.commit()
    cursor.close()
    conn.close()
    return True


def generar_datos_demo():
    """Genera datos de demostración para limpieza."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM limpieza_habitaciones")
    if cursor.fetchone()[0] > 0:
        cursor.close()
        conn.close()
        print("ℹ️  Ya existen datos de limpieza")
        return

    cursor.execute("SELECT id, numero FROM habitaciones")
    habitaciones = cursor.fetchall()

    import random
    categorias = ["Estándar", "Estándar", "Superior", "Suite", "Presidencial"]
    ahora = datetime.now()

    for hab_id, numero in habitaciones:
        cat = random.choice(categorias)
        checkout = ahora - timedelta(hours=random.uniform(1, 36))
        checkin = ahora + timedelta(hours=random.uniform(2, 48))
        limpieza = (ahora - timedelta(days=random.randint(1, 20))).date()

        cursor.execute("""
            INSERT INTO limpieza_habitaciones
            (habitacion_id, fecha_checkout, fecha_checkin_siguiente,
             fecha_ultima_limpieza_profunda, categoria_habitacion)
            VALUES (%s, %s, %s, %s, %s)
        """, (hab_id, checkout, checkin, limpieza, cat))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Datos demo de limpieza creados para {len(habitaciones)} habitaciones")


if __name__ == "__main__":
    generar_datos_demo()
    resultados = recalcular_scores()
    for r in resultados[:10]:
        print(f"  Hab #{r['numero']}: {r['nivel']} (score: {r['urgency_score']})")
