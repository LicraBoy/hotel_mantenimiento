from flask import Flask
from config import Config
from routes import registrar_blueprints
from database.db import conectar
from extensions import socketio

def crear_app(config_class=None):
    """Crea y configura la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class if config_class else Config)

    # CSRF Protection + Rate Limiter
    from extensions import csrf, limiter
    csrf.init_app(app)
    limiter.init_app(app)

    # Headers de seguridad en todas las respuestas
    @app.after_request
    def agregar_headers_seguridad(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # Registrar todos los blueprints
    registrar_blueprints(app)

    if not app.config.get("TESTING"):
        # Ejecutar migración automática de BD
        migrar_bd()

        # Crear tablas de IA si no existen estas
        try:
            from database.schemas.init_schema_ai import crear_tablas_ai
            crear_tablas_ai()
        except Exception as e:
            print(f"⚠️ Tablas AI: {e}")

        # Crear tablas de IA v2 (costos, planes, alertas, columnas nuevas)
        try:
            from database.schemas.init_schema_ai_v2 import crear_tablas_ai_v2
            crear_tablas_ai_v2()
        except Exception as e:
            print(f"⚠️ Tablas AI v2: {e}")

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

    if 'foto_url' not in columnas_mant:
        cursor.execute("ALTER TABLE mantenimiento ADD COLUMN foto_url TEXT")
        conn.commit()

    if 'deteccion_id' not in columnas_mant:
        cursor.execute("ALTER TABLE mantenimiento ADD COLUMN deteccion_id INTEGER")
        conn.commit()

    # Usuario de prueba eliminado (contraseña débil)

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
    socketio.run(app, debug=False)