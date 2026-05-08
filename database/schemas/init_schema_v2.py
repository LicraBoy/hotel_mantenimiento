"""
Crear tablas V2 en PostgreSQL — Expansión Hotel AI Operations Platform
Tablas: predicciones_costo, perfiles_tecnico, planes_mantenimiento, alertas_operaciones
Columnas nuevas: usuarios (especialidad, activo), mantenimiento (tecnico_id, tiempo_estimado, costo_estimado, origen)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.db import conectar


def crear_tablas_v2():
    conn = conectar()
    cursor = conn.cursor()

    # =============================================
    # Nuevas tablas
    # =============================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predicciones_costo (
            id SERIAL PRIMARY KEY,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            costo_estimado NUMERIC(10,2) NOT NULL,
            rango_min NUMERIC(10,2),
            rango_max NUMERIC(10,2),
            confianza NUMERIC(5,4),
            factores_json TEXT,
            modelo_usado TEXT DEFAULT 'cost_gbr',
            fecha_prediccion TIMESTAMP DEFAULT NOW()
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfiles_tecnico (
            id SERIAL PRIMARY KEY,
            tecnico_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
            especialidades_json TEXT,
            total_trabajos INTEGER DEFAULT 0,
            tiempo_promedio_horas NUMERIC(6,2) DEFAULT 0,
            costo_promedio NUMERIC(10,2) DEFAULT 0,
            calificacion NUMERIC(3,2) DEFAULT 5.0,
            carga_actual INTEGER DEFAULT 0,
            fecha_actualizado TIMESTAMP DEFAULT NOW()
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS planes_mantenimiento (
            id SERIAL PRIMARY KEY,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            tipo_equipo TEXT NOT NULL,
            fecha_sugerida DATE NOT NULL,
            prioridad TEXT DEFAULT 'Media',
            razon TEXT NOT NULL,
            costo_estimado NUMERIC(10,2),
            tecnico_recomendado_id INTEGER REFERENCES usuarios(id),
            tecnico_recomendado_nombre TEXT,
            estado TEXT DEFAULT 'Propuesto',
            motivo_rechazo TEXT,
            mantenimiento_id INTEGER REFERENCES mantenimiento(id),
            aprobado_por TEXT,
            fecha_creado TIMESTAMP DEFAULT NOW(),
            fecha_resuelto TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertas_operaciones (
            id SERIAL PRIMARY KEY,
            tipo TEXT NOT NULL,
            nivel TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            entidad_tipo TEXT,
            entidad_id INTEGER,
            metadata_json TEXT,
            leida BOOLEAN DEFAULT FALSE,
            fecha TIMESTAMP DEFAULT NOW()
        )
    """)

    # =============================================
    # Columnas nuevas en tablas existentes
    # =============================================

    # Usuarios: especialidad, activo
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'usuarios'
    """)
    cols_usuarios = [r[0] for r in cursor.fetchall()]

    if 'especialidad' not in cols_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN especialidad TEXT DEFAULT ''")

    if 'activo' not in cols_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN activo BOOLEAN DEFAULT TRUE")

    # Mantenimiento: tecnico_id, tiempo_estimado_horas, costo_estimado, origen
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'mantenimiento'
    """)
    cols_mant = [r[0] for r in cursor.fetchall()]

    if 'tecnico_id' not in cols_mant:
        cursor.execute("ALTER TABLE mantenimiento ADD COLUMN tecnico_id INTEGER REFERENCES usuarios(id)")

    if 'tiempo_estimado_horas' not in cols_mant:
        cursor.execute("ALTER TABLE mantenimiento ADD COLUMN tiempo_estimado_horas NUMERIC(5,1)")

    if 'costo_estimado' not in cols_mant:
        cursor.execute("ALTER TABLE mantenimiento ADD COLUMN costo_estimado NUMERIC(10,2)")

    if 'origen' not in cols_mant:
        cursor.execute("ALTER TABLE mantenimiento ADD COLUMN origen TEXT DEFAULT 'manual'")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tablas V2 creadas correctamente (4 nuevas + columnas expandidas)")


if __name__ == "__main__":
    crear_tablas_v2()
