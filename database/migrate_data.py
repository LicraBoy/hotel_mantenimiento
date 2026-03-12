"""
Script para migrar datos de SQLite (hotel.db) a PostgreSQL.
Ejecutar después de init_schema.py.
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.db import conectar


def migrar():
    # Conectar a SQLite
    sqlite_path = os.path.join(os.path.dirname(__file__), "hotel.db")
    if not os.path.exists(sqlite_path):
        sqlite_path = os.path.join(os.path.dirname(__file__), "..", "database", "hotel.db")

    if not os.path.exists(sqlite_path):
        print("⚠️  No se encontró hotel.db — no hay datos que migrar")
        return

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cur = sqlite_conn.cursor()

    # Conectar a PostgreSQL
    pg_conn = conectar()
    pg_cur = pg_conn.cursor()

    # Limpiar tablas existentes (en orden correcto por FK)
    print("🧹 Limpiando tablas existentes...")
    pg_cur.execute("DELETE FROM inspecciones")
    pg_cur.execute("DELETE FROM historial_habitaciones")
    pg_cur.execute("DELETE FROM mantenimiento")
    pg_cur.execute("DELETE FROM habitaciones")
    pg_cur.execute("DELETE FROM usuarios")
    pg_conn.commit()

    # ── Migrar usuarios ──
    sqlite_cur.execute("SELECT id, username, password, rol, nombre_completo, email, telefono FROM usuarios")
    rows = sqlite_cur.fetchall()
    for row in rows:
        pg_cur.execute("""
            INSERT INTO usuarios (id, username, password, rol, nombre_completo, email, telefono)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, row)
    if rows:
        pg_cur.execute("SELECT setval('usuarios_id_seq', (SELECT COALESCE(MAX(id),1) FROM usuarios))")
    pg_conn.commit()
    print(f"  ✅ usuarios: {len(rows)} registros")

    # ── Migrar habitaciones ──
    sqlite_cur.execute("SELECT id, numero, estado, fecha_ultimo_mantenimiento FROM habitaciones")
    rows = sqlite_cur.fetchall()
    for row in rows:
        pg_cur.execute("""
            INSERT INTO habitaciones (id, numero, estado, fecha_ultimo_mantenimiento)
            VALUES (%s, %s, %s, %s)
        """, row)
    if rows:
        pg_cur.execute("SELECT setval('habitaciones_id_seq', (SELECT COALESCE(MAX(id),1) FROM habitaciones))")
    pg_conn.commit()
    print(f"  ✅ habitaciones: {len(rows)} registros")

    # ── Migrar mantenimiento ──
    sqlite_cur.execute("""
        SELECT id, habitacion_id, tipo, descripcion, tecnico, fecha, estado, costo, elemento, prioridad 
        FROM mantenimiento
        WHERE habitacion_id IN (SELECT id FROM habitaciones)
    """)
    rows = sqlite_cur.fetchall()
    for row in rows:
        pg_cur.execute("""
            INSERT INTO mantenimiento (id, habitacion_id, tipo, descripcion, tecnico, fecha, estado, costo, elemento, prioridad)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, row)
    if rows:
        pg_cur.execute("SELECT setval('mantenimiento_id_seq', (SELECT COALESCE(MAX(id),1) FROM mantenimiento))")
    pg_conn.commit()
    print(f"  ✅ mantenimiento: {len(rows)} registros")

    # ── Migrar historial_habitaciones ──
    sqlite_cur.execute("""
        SELECT id, habitacion_id, accion, descripcion, usuario, fecha 
        FROM historial_habitaciones
        WHERE habitacion_id IN (SELECT id FROM habitaciones)
    """)
    rows = sqlite_cur.fetchall()
    for row in rows:
        pg_cur.execute("""
            INSERT INTO historial_habitaciones (id, habitacion_id, accion, descripcion, usuario, fecha)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, row)
    if rows:
        pg_cur.execute("SELECT setval('historial_habitaciones_id_seq', (SELECT COALESCE(MAX(id),1) FROM historial_habitaciones))")
    pg_conn.commit()
    print(f"  ✅ historial_habitaciones: {len(rows)} registros")

    # ── Migrar inspecciones ──
    sqlite_cur.execute("""
        SELECT id, habitacion_id, empleado, observaciones, fecha, genera_mantenimiento 
        FROM inspecciones
        WHERE habitacion_id IN (SELECT id FROM habitaciones)
    """)
    rows = sqlite_cur.fetchall()
    for row in rows:
        pg_cur.execute("""
            INSERT INTO inspecciones (id, habitacion_id, empleado, observaciones, fecha, genera_mantenimiento)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, row)
    if rows:
        pg_cur.execute("SELECT setval('inspecciones_id_seq', (SELECT COALESCE(MAX(id),1) FROM inspecciones))")
    pg_conn.commit()
    print(f"  ✅ inspecciones: {len(rows)} registros")

    pg_cur.close()
    pg_conn.close()
    sqlite_conn.close()

    print("\n🎉 Migración completada exitosamente!")


if __name__ == "__main__":
    migrar()
