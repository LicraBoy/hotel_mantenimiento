from flask import Flask
from config import Config
from routes import registrar_blueprints
from database.db import conectar
from extensions import socketio

def crear_app():
    """Crea y configura la aplicación Flask."""
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY

    # Registrar todos los blueprints
    registrar_blueprints(app)

    # Ejecutar migración automática de BD
    migrar_bd()

    # Crear tablas de IA si no existen estas
    try:
        from database.init_schema_ai import crear_tablas_ai
        crear_tablas_ai()
    except Exception as e:
        print(f"⚠️ Tablas AI: {e}")

    # Inicializar SocketIO
    socketio.init_app(app)
    
    return app


def migrar_bd():
    """Migración automática: asegura que las columnas necesarias existan."""
    conn = conectar()
    cursor = conn.cursor()

    # Verificar columnas en usuarios
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='usuarios'
    """)
    columnas = [col[0] for col in cursor.fetchall()]

    if 'rol' not in columnas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN rol TEXT DEFAULT 'empleado'")
        cursor.execute("UPDATE usuarios SET rol='admin' WHERE id=(SELECT MIN(id) FROM usuarios)")
        conn.commit()

    if 'nombre_completo' not in columnas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN nombre_completo TEXT DEFAULT ''")
        conn.commit()

    if 'email' not in columnas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN email TEXT DEFAULT ''")
        conn.commit()

    if 'telefono' not in columnas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN telefono TEXT DEFAULT ''")
        conn.commit()

    # Verificar columnas en mantenimiento
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='mantenimiento'
    """)
    columnas_mant = [col[0] for col in cursor.fetchall()]

    if 'prioridad' not in columnas_mant:
        cursor.execute("ALTER TABLE mantenimiento ADD COLUMN prioridad TEXT DEFAULT 'Media'")
        conn.commit()

    # Crear usuario de prueba si no existe
    cursor.execute("SELECT id FROM usuarios WHERE username='empleado1'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO usuarios (username, password, rol)
            VALUES ('empleado1', 'empleado1', 'empleado')
        """)
        conn.commit()

    # ===============================
    # Encriptar passwords en texto plano
    # ===============================
    from werkzeug.security import generate_password_hash
    cursor.execute("SELECT id, password FROM usuarios")
    usuarios = cursor.fetchall()
    
    for u_id, upass in usuarios:
        if upass and not upass.startswith("scrypt:") and not upass.startswith("pbkdf2:"):
            # Es texto plano, hay que hashearlo
            hashed = generate_password_hash(upass)
            cursor.execute("UPDATE usuarios SET password=%s WHERE id=%s", (hashed, u_id))
    conn.commit()

    cursor.close()
    conn.close()


# ===============================
# Punto de entrada
# ===============================
app = crear_app()

if __name__ == "__main__":
    socketio.run(app, debug=True)