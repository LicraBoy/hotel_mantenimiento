import sqlite3

def conectar():
    conn = sqlite3.connect("database/hotel.db")
    return conn

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        rol TEXT DEFAULT 'empleado'
    )
    """)

    conn.commit()
    conn.close()

crear_tablas()