"""
Tests: Autenticación y control de acceso
Cubre: login, logout, decoradores requiere_login y requiere_rol
"""
import pytest
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash
from tests.conftest import mock_conn, mock_cursor


# ============================================================
# GET /login
# ============================================================

def test_login_pagina_carga(client):
    """GET /login debe retornar 200 con el formulario."""
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Iniciar" in resp.data or b"login" in resp.data.lower()


# ============================================================
# POST /login — credenciales válidas
# ============================================================

def test_login_exitoso_redirige_dashboard(client):
    """Login con credenciales correctas → redirect a /dashboard."""
    hashed = generate_password_hash("admin123")
    user_row = (1, "admin", hashed, "admin")
    cursor = mock_cursor(rows=[user_row])
    conn = mock_conn(cursor)

    with patch("routes.auth.conectar", return_value=conn):
        resp = client.post("/login", data={"username": "admin", "password": "admin123"})

    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_login_exitoso_guarda_sesion(client, app):
    """Login correcto → sesión contiene user, user_id y rol."""
    hashed = generate_password_hash("admin123")
    user_row = (1, "admin", hashed, "admin")
    cursor = mock_cursor(rows=[user_row])
    conn = mock_conn(cursor)

    with patch("routes.auth.conectar", return_value=conn):
        with client.session_transaction() as pre_sess:
            assert "user" not in pre_sess

        client.post("/login", data={"username": "admin", "password": "admin123"})

        with client.session_transaction() as sess:
            assert sess["user"] == "admin"
            assert sess["rol"] == "admin"
            assert sess["user_id"] == 1


# ============================================================
# POST /login — credenciales inválidas
# ============================================================

def test_login_password_incorrecto_retorna_error(client):
    """Password incorrecto → 200 con mensaje de error."""
    hashed = generate_password_hash("correcta")
    user_row = (1, "admin", hashed, "admin")
    cursor = mock_cursor(rows=[user_row])
    conn = mock_conn(cursor)

    with patch("routes.auth.conectar", return_value=conn):
        resp = client.post("/login", data={"username": "admin", "password": "incorrecta"})

    assert resp.status_code == 200
    assert "incorrecta" in resp.data.decode("utf-8").lower() or "error" in resp.data.decode("utf-8").lower()


def test_login_usuario_no_existe_retorna_error(client):
    """Usuario no encontrado en BD → 200 con mensaje de error."""
    cursor = mock_cursor(rows=None)
    cursor.fetchone.return_value = None
    conn = mock_conn(cursor)

    with patch("routes.auth.conectar", return_value=conn):
        resp = client.post("/login", data={"username": "fantasma", "password": "cualquiera"})

    assert resp.status_code == 200


def test_login_incrementa_contador_intentos(client):
    """Cada fallo incrementa session['login_intentos']."""
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    conn = mock_conn(cursor)

    with patch("routes.auth.conectar", return_value=conn):
        client.post("/login", data={"username": "x", "password": "y"})
        client.post("/login", data={"username": "x", "password": "y"})

        with client.session_transaction() as sess:
            assert sess.get("login_intentos", 0) >= 2


def test_login_bloquea_tras_5_intentos(client):
    """Después de 5 intentos fallidos el login muestra bloqueo."""
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    conn = mock_conn(cursor)

    with patch("routes.auth.conectar", return_value=conn):
        for _ in range(5):
            client.post("/login", data={"username": "x", "password": "y"})

        resp = client.post("/login", data={"username": "x", "password": "y"})

    assert resp.status_code == 200
    assert "intent" in resp.data.decode("utf-8").lower() or "espera" in resp.data.decode("utf-8").lower()


# ============================================================
# GET /logout
# ============================================================

def test_logout_limpia_sesion_y_redirige(client_admin):
    """Logout → sesión vacía → redirect a /login."""
    resp = client_admin.get("/logout")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

    with client_admin.session_transaction() as sess:
        assert "user" not in sess
        assert "user_id" not in sess


# ============================================================
# Decorador @requiere_login
# ============================================================

def test_requiere_login_sin_sesion_redirige(client):
    """Acceder a ruta protegida sin sesión → redirect /login."""
    resp = client.get("/dashboard")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_requiere_login_con_sesion_permite_acceso(client_admin):
    """Acceder a /dashboard con sesión de admin → no redirige a login."""
    from unittest.mock import MagicMock
    cursor = MagicMock()
    # El dashboard llama fetchone() para totales y fetchall() para listas
    cursor.fetchone.return_value = (5,)   # total_habitaciones, etc.
    cursor.fetchall.return_value = []
    conn = MagicMock()
    conn.cursor.return_value = cursor

    with patch("routes.dashboard.conectar", return_value=conn):
        resp = client_admin.get("/dashboard")

    # Con sesión válida, el decorador NO debe redirigir a /login
    if resp.status_code == 302:
        assert "/login" not in resp.headers.get("Location", "")


# ============================================================
# Decorador @requiere_rol
# ============================================================

def test_requiere_rol_admin_con_empleado_retorna_403(client_empleado):
    """Empleado intentando acceder a ruta de admin → 403."""
    resp = client_empleado.get("/admin/usuarios")
    assert resp.status_code == 403


def test_requiere_rol_admin_con_admin_permite_paso(client_admin):
    """Admin accediendo a ruta de admin → no retorna 403."""
    cursor = mock_cursor(rows=[])
    conn = mock_conn(cursor)
    with patch("routes.admin.conectar", return_value=conn):
        resp = client_admin.get("/admin/usuarios")
    assert resp.status_code != 403


def test_requiere_login_ruta_habitaciones(client):
    """GET /habitaciones sin sesión → redirect /login."""
    resp = client.get("/habitaciones")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_requiere_login_ruta_mantenimientos(client):
    """GET /mantenimientos sin sesión → redirect /login."""
    resp = client.get("/mantenimientos")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
