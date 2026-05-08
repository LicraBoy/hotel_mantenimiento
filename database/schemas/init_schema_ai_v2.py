"""
Crear tablas de IA v2 en PostgreSQL — Cost Prediction, Technician, Scheduler, Operations
Ejecutar: python database/init_schema_ai_v2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.db import conectar


def crear_tablas_ai_v2():
    conn = conectar()
    cursor = conn.cursor()

    # --- Predicción de costos ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predicciones_costo (
            id SERIAL PRIMARY KEY,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            costo_estimado NUMERIC(10,2) DEFAULT 0,
            rango_min NUMERIC(10,2) DEFAULT 0,
            rango_max NUMERIC(10,2) DEFAULT 0,
            confianza NUMERIC(5,4) DEFAULT 0,
            factores_json TEXT,
            fecha_prediccion TIMESTAMP DEFAULT NOW()
        )
    """)

    # --- Planes de mantenimiento preventivo ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS planes_mantenimiento (
            id SERIAL PRIMARY KEY,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            tipo_equipo TEXT,
            fecha_sugerida DATE,
            prioridad TEXT DEFAULT 'Media',
            razon TEXT,
            costo_estimado NUMERIC(10,2),
            tecnico_recomendado_id INTEGER,
            tecnico_recomendado_nombre TEXT,
            estado TEXT DEFAULT 'Propuesto',
            mantenimiento_id INTEGER,
            aprobado_por TEXT,
            motivo_rechazo TEXT,
            fecha_creado TIMESTAMP DEFAULT NOW(),
            fecha_resuelto TIMESTAMP
        )
    """)

    # --- Alertas de operaciones ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertas_operaciones (
            id SERIAL PRIMARY KEY,
            tipo TEXT NOT NULL,
            nivel TEXT DEFAULT 'INFO',
            mensaje TEXT NOT NULL,
            entidad_tipo TEXT,
            entidad_id INTEGER,
            leida BOOLEAN DEFAULT FALSE,
            fecha TIMESTAMP DEFAULT NOW()
        )
    """)

    # --- Columnas nuevas en tablas existentes ---
    # usuarios: especialidad, activo
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'usuarios'
    """)
    cols_usuarios = [c[0] for c in cursor.fetchall()]

    if 'especialidad' not in cols_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN especialidad TEXT DEFAULT ''")

    if 'activo' not in cols_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN activo BOOLEAN DEFAULT TRUE")

    # mantenimiento: tecnico_id, costo_estimado, origen
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'mantenimiento'
    """)
    cols_mant = [c[0] for c in cursor.fetchall()]

    if 'tecnico_id' not in cols_mant:
        cursor.execute("ALTER TABLE mantenimiento ADD COLUMN tecnico_id INTEGER")

    if 'costo_estimado' not in cols_mant:
        cursor.execute("ALTER TABLE mantenimiento ADD COLUMN costo_estimado NUMERIC(10,2)")

    if 'origen' not in cols_mant:
        cursor.execute("ALTER TABLE mantenimiento ADD COLUMN origen TEXT DEFAULT 'manual'")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tablas de IA v2 creadas correctamente")


if __name__ == "__main__":
    crear_tablas_ai_v2()
