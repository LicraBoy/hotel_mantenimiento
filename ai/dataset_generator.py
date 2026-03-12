"""
Generador de Dataset Sintético
Crea 2 años de datos de mantenimiento para un hotel de 100 habitaciones
Ejecutar: python ai/dataset_generator.py
"""
import os, sys, random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.db import conectar


# Configuración
TIPOS_EQUIPO = [
    {"tipo": "Aire Acondicionado", "marca": "Carrier",   "vida_util": 1825, "frecuencia_falla_dias": 180, "varianza": 60},
    {"tipo": "TV",                 "marca": "Samsung",    "vida_util": 2555, "frecuencia_falla_dias": 365, "varianza": 120},
    {"tipo": "Plomería",           "marca": "Genérica",   "vida_util": 3650, "frecuencia_falla_dias": 300, "varianza": 90},
    {"tipo": "Electricidad",       "marca": "Genérica",   "vida_util": 3650, "frecuencia_falla_dias": 400, "varianza": 150},
    {"tipo": "Calefacción",        "marca": "Honeywell",  "vida_util": 2190, "frecuencia_falla_dias": 270, "varianza": 80},
]

FALLAS_POR_TIPO = {
    "Aire Acondicionado": ["No enfría", "Fuga de gas", "Ruido excesivo", "No enciende", "Sobrecalentamiento"],
    "TV":                 ["No enciende", "Sin señal", "Pantalla dañada", "Control remoto"],
    "Plomería":           ["Fuga de agua", "Desagüe tapado", "Baja presión", "Agua caliente falla"],
    "Electricidad":       ["Cortocircuito", "Apagón parcial", "Enchufe dañado", "Flickering"],
    "Calefacción":        ["No calienta", "Ruido", "Fuga", "Termostato averiado"],
}

SEVERIDADES = ["Baja", "Media", "Alta", "Crítica"]
COSTOS_BASE = {"Baja": 50, "Media": 150, "Alta": 400, "Crítica": 800}


def generar_dataset(num_habitaciones=None):
    """Genera datos sintéticos. Si num_habitaciones es None, usa las habitaciones existentes."""
    conn = conectar()
    cursor = conn.cursor()

    # Obtener habitaciones existentes
    cursor.execute("SELECT id, numero FROM habitaciones")
    habitaciones = cursor.fetchall()

    if not habitaciones:
        print("⚠️  No hay habitaciones en la BD. Creando 20 de ejemplo...")
        for i in range(1, 21):
            cursor.execute(
                "INSERT INTO habitaciones (numero, estado, fecha_ultimo_mantenimiento) VALUES (%s, %s, '')",
                (str(100 + i), "Disponible")
            )
        conn.commit()
        cursor.execute("SELECT id, numero FROM habitaciones")
        habitaciones = cursor.fetchall()

    # Obtener técnicos
    cursor.execute("SELECT id FROM usuarios")
    tecnicos = [r[0] for r in cursor.fetchall()] or [1]

    print(f"📊 Generando datos para {len(habitaciones)} habitaciones...")

    fecha_inicio = datetime.now() - timedelta(days=730)  # 2 años atrás
    equipos_creados = 0
    fallas_creadas = 0

    for hab_id, hab_num in habitaciones:
        # Verificar si ya tiene equipos
        cursor.execute("SELECT COUNT(*) FROM equipos WHERE habitacion_id=%s", (hab_id,))
        if cursor.fetchone()[0] > 0:
            continue

        for eq_config in TIPOS_EQUIPO:
            # Crear equipo
            fecha_inst = fecha_inicio - timedelta(days=random.randint(0, 365))
            cursor.execute("""
                INSERT INTO equipos (habitacion_id, tipo, marca, fecha_instalacion, vida_util_dias)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (hab_id, eq_config["tipo"], eq_config["marca"], fecha_inst.date(), eq_config["vida_util"]))
            equipo_id = cursor.fetchone()[0]
            equipos_creados += 1

            # Generar fallas para este equipo
            fecha_cursor = fecha_inicio + timedelta(days=random.randint(30, eq_config["frecuencia_falla_dias"]))

            while fecha_cursor < datetime.now():
                tipo_falla = random.choice(FALLAS_POR_TIPO[eq_config["tipo"]])
                severidad = random.choices(SEVERIDADES, weights=[30, 40, 20, 10])[0]
                costo = COSTOS_BASE[severidad] * random.uniform(0.7, 1.5)
                tiempo_rep = random.uniform(0.5, 8.0) if severidad != "Crítica" else random.uniform(4, 24)
                tecnico = random.choice(tecnicos)
                fecha_rep = fecha_cursor + timedelta(hours=random.uniform(1, 48))

                cursor.execute("""
                    INSERT INTO historial_fallas
                    (equipo_id, habitacion_id, tipo_falla, fecha_falla, fecha_reparacion,
                     costo, tecnico_id, tiempo_reparacion_horas, severidad)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (equipo_id, hab_id, tipo_falla, fecha_cursor.date(),
                      fecha_rep.date(), round(costo, 2), tecnico,
                      round(tiempo_rep, 1), severidad))
                fallas_creadas += 1

                # Siguiente falla
                intervalo = eq_config["frecuencia_falla_dias"] + random.randint(
                    -eq_config["varianza"], eq_config["varianza"]
                )
                fecha_cursor += timedelta(days=max(30, intervalo))

    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ Dataset generado: {equipos_creados} equipos, {fallas_creadas} fallas")
    return equipos_creados, fallas_creadas


if __name__ == "__main__":
    generar_dataset()
