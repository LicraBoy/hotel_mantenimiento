"""
Crear tablas de IA en PostgreSQL
Ejecutar: python database/init_schema_ai.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.db import conectar


def crear_tablas_ai():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id SERIAL PRIMARY KEY,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            tipo VARCHAR(50) NOT NULL,
            marca TEXT,
            fecha_instalacion DATE,
            vida_util_dias INTEGER DEFAULT 1825
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_fallas (
            id SERIAL PRIMARY KEY,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            tipo_falla TEXT NOT NULL,
            fecha_falla DATE NOT NULL,
            fecha_reparacion DATE,
            costo NUMERIC(10,2) DEFAULT 0,
            tecnico_id INTEGER,
            tiempo_reparacion_horas NUMERIC(5,1),
            severidad TEXT DEFAULT 'Media'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predicciones (
            id SERIAL PRIMARY KEY,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            prob_7_dias NUMERIC(5,4),
            prob_14_dias NUMERIC(5,4),
            prob_30_dias NUMERIC(5,4),
            fecha_prediccion TIMESTAMP DEFAULT NOW(),
            modelo_usado TEXT,
            nivel_riesgo TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detecciones_visuales (
            id SERIAL PRIMARY KEY,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            limpieza_id INTEGER,
            imagen_original TEXT NOT NULL,
            imagen_anotada TEXT,
            score_estado TEXT,
            detecciones_json TEXT,
            confianza_promedio NUMERIC(5,4),
            empleado TEXT,
            fecha TIMESTAMP DEFAULT NOW()
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS limpieza_habitaciones (
            id SERIAL PRIMARY KEY,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            fecha_checkout TIMESTAMP,
            fecha_checkin_siguiente TIMESTAMP,
            fecha_ultima_limpieza_profunda DATE,
            categoria_habitacion TEXT DEFAULT 'Estándar',
            urgency_score NUMERIC(6,2) DEFAULT 0,
            nivel_urgencia TEXT,
            asignado_a TEXT,
            estado_limpieza TEXT DEFAULT 'Pendiente',
            fecha_actualizado TIMESTAMP DEFAULT NOW()
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_limpieza (
            id SERIAL PRIMARY KEY,
            habitacion_id INTEGER,
            numero_habitacion VARCHAR(20),
            categoria VARCHAR(50),
            fecha_checkout TIMESTAMP,
            fecha_completada TIMESTAMP DEFAULT NOW(),
            empleado VARCHAR(100),
            imagen_evidencia TEXT,
            estado_ia VARCHAR(50),
            urgencia_inicial VARCHAR(50)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("[OK] Tablas de IA creadas correctamente")


if __name__ == "__main__":
    crear_tablas_ai()
