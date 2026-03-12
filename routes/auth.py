from flask import Blueprint, render_template, request, redirect, session, flash
from functools import wraps
from database.db import conectar

auth_bp = Blueprint("auth", __name__)


# ===============================
# Decoradores de acceso
# ===============================
def requiere_rol(rol):
    """Decorador para restringir rutas a un rol específico."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect('/login')
            if session.get('rol') != rol:
                return render_template('acceso_denegado.html'), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def requiere_login(f):
    """Decorador para verificar que el usuario esté logueado."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# ===============================
# Login
# ===============================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, password, rol FROM usuarios
            WHERE username=%s
        """, (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        from werkzeug.security import check_password_hash

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["user"] = user[1]
            session["rol"] = user[3] if user[3] else 'empleado'
            return redirect("/dashboard")

        return render_template("login.html", error="Usuario o contraseña incorrecta")

    return render_template("login.html")


# ===============================
# Logout
# ===============================
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
