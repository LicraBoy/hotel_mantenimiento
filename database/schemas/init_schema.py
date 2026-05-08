"""
Script para crear las tablas en PostgreSQL.
Ejecutar una vez para inicializar el esquema.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.db import conectar


def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT,
            password TEXT,
            rol TEXT DEFAULT 'empleado',
            nombre_completo TEXT DEFAULT '',
            email TEXT DEFAULT '',
            telefono TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habitaciones (
            id SERIAL PRIMARY KEY,
            numero TEXT,
            estado TEXT,
            fecha_ultimo_mantenimiento TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mantenimiento (
            id SERIAL PRIMARY KEY,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            tipo TEXT,
            descripcion TEXT,
            tecnico TEXT,
            fecha TEXT,
            estado TEXT,
            costo NUMERIC(10,2),
            elemento TEXT DEFAULT '',
            prioridad TEXT DEFAULT 'Media'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_habitaciones (
            id SERIAL PRIMARY KEY,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            accion TEXT,
            descripcion TEXT,
            usuario TEXT,
            fecha TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspecciones (
            id SERIAL PRIMARY KEY,
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE CASCADE,
            empleado TEXT,
            observaciones TEXT,
            fecha DATE,
            genera_mantenimiento INTEGER
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tablas creadas correctamente en PostgreSQL")


if __name__ == "__main__":
    crear_tablas()
