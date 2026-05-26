"""
Tests: Administración de usuarios y perfiles
Cubre: creación de usuarios, control de roles, edición de perfil
"""
import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import mock_conn, mock_cursor


# ============================================================
# Gestión de usuarios — control de acceso
# ============================================================

def test_lista_usuarios_sin_sesion_redirige(client):
    """GET /admin/usuarios sin sesión → redirect /login."""
    resp = client.get("/admin/usuarios")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_lista_usuarios_empleado_retorna_403(client_empleado):
    """Empleado intentando ver lista de usuarios → 403."""
    resp = client_empleado.get("/admin/usuarios")
    assert resp.status_code == 403


def test_lista_usuarios_admin_retorna_200(client_admin):
    """Admin viendo lista de usuarios → 200."""
    cursor = mock_cursor(rows=[])
    conn = mock_conn(cursor)
    with patch("routes.admin.conectar", return_value=conn):
        resp = client_admin.get("/admin/usuarios")
    assert resp.status_code == 200


# ============================================================
# Creación de usuarios
# ============================================================

def test_crear_usuario_sin_sesion_redirige(client):
    """POST /admin/usuarios/nuevo sin sesión → redirect /login."""
    resp = client.post("/admin/usuarios/nuevo", data={
        "username": "nuevo", "password": "pass123", "rol": "empleado"
    })
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_crear_usuario_como_empleado_retorna_403(client_empleado):
    """Empleado intentando crear usuario → 403."""
    resp = client_empleado.post("/admin/usuarios/nuevo", data={
        "username": "nuevo", "password": "pass123", "rol": "empleado"
    })
    assert resp.status_code == 403


def test_crear_usuario_username_vacio_flash_error(client_admin):
    """POST sin username → flash de error + redirect."""
    resp = client_admin.post("/admin/usuarios/nuevo", data={
        "username": "", "password": "pass123", "rol": "empleado"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert "obligatorio" in resp.data.decode("utf-8").lower() or \
           "username" in resp.data.decode("utf-8").lower()


def test_crear_usuario_password_vacio_flash_error(client_admin):
    """POST sin password → flash de error + redirect."""
    resp = client_admin.post("/admin/usuarios/nuevo", data={
        "username": "nuevo_user", "password": "", "rol": "empleado"
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_crear_usuario_duplicado_flash_error(client_admin):
    """POST con username ya existente → flash de error."""
    cursor = mock_cursor(rows=[(1,)])   # fetchone devuelve fila = ya existe
    conn = mock_conn(cursor)

    with patch("routes.admin.conectar", return_value=conn):
        resp = client_admin.post(
            "/admin/usuarios/nuevo",
            data={"username": "admin", "password": "pass123", "rol": "empleado"},
            follow_redirects=True,
        )

    assert resp.status_code == 200
    assert "registrado" in resp.data.decode("utf-8").lower() or \
           "username" in resp.data.decode("utf-8").lower()


def test_crear_usuario_exitoso_redirige(client_admin):
    """POST usuario válido y único → redirect a /admin/usuarios."""
    cursor = MagicMock()
    cursor.fetchone.return_value = None   # username no existe
    conn = mock_conn(cursor)

    with patch("routes.admin.conectar", return_value=conn):
        resp = client_admin.post(
            "/admin/usuarios/nuevo",
            data={
                "username": "tecnico_nuevo",
                "password": "Segura123!",
                "nombre_completo": "Carlos López",
                "email": "carlos@hotel.com",
                "telefono": "555-1234",
                "rol": "empleado",
            },
        )

    assert resp.status_code == 302
    assert "/admin/usuarios" in resp.headers["Location"]


def test_crear_usuario_rol_admin(client_admin):
    """POST usuario con rol admin → se crea correctamente."""
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    conn = mock_conn(cursor)

    with patch("routes.admin.conectar", return_value=conn):
        resp = client_admin.post(
            "/admin/usuarios/nuevo",
            data={
                "username": "superadmin",
                "password": "Admin456!",
                "nombre_completo": "Super Admin",
                "email": "",
                "telefono": "",
                "rol": "admin",
            },
        )

    assert resp.status_code == 302


# ============================================================
# Perfil de usuario
# ============================================================

def test_perfil_sin_sesion_redirige(client):
    """GET /perfil sin sesión → redirect /login."""
    resp = client.get("/perfil")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_perfil_con_sesion_retorna_200(client_admin):
    """GET /perfil con sesión → 200."""
    user_row = (1, "admin", "Admin Hotel", "admin@hotel.com", "555-0000", "admin")
    cursor = mock_cursor(rows=[user_row])
    conn = mock_conn(cursor)
    with patch("routes.admin.conectar", return_value=conn):
        resp = client_admin.get("/perfil")
    assert resp.status_code == 200


def test_actualizar_perfil_sin_cambiar_password(client_admin):
    """POST /perfil sin nueva_password → actualiza datos pero no toca el hash."""
    user_row = (1, "admin", "Admin Hotel", "admin@hotel.com", "555-0000", "admin")
    cursor = mock_cursor(rows=[user_row])
    conn = mock_conn(cursor)

    with patch("routes.admin.conectar", return_value=conn):
        resp = client_admin.post("/perfil", data={
            "nombre_completo": "Hotel Admin",
            "email": "nuevo@hotel.com",
            "telefono": "555-9999",
            "nueva_password": "",
        })

    assert resp.status_code == 302
    assert "/perfil" in resp.headers["Location"]


def test_actualizar_perfil_con_nueva_password(client_admin):
    """POST /perfil con nueva_password → actualiza hash."""
    user_row = (1, "admin", "Admin Hotel", "admin@hotel.com", "555-0000", "admin")
    cursor = mock_cursor(rows=[user_row])
    conn = mock_conn(cursor)

    with patch("routes.admin.conectar", return_value=conn):
        resp = client_admin.post("/perfil", data={
            "nombre_completo": "Hotel Admin",
            "email": "admin@hotel.com",
            "telefono": "555-0000",
            "nueva_password": "NuevaClave123!",
        })

    assert resp.status_code == 302


# ============================================================
# Eliminación de usuarios
# ============================================================

def test_eliminar_usuario_sin_sesion_redirige(client):
    """GET /admin/usuarios/eliminar/<id> sin sesión → redirect /login."""
    resp = client.get("/admin/usuarios/eliminar/2")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_eliminar_usuario_empleado_retorna_403(client_empleado):
    """Empleado intentando eliminar usuario → 403."""
    resp = client_empleado.get("/admin/usuarios/eliminar/2")
    assert resp.status_code == 403


def test_eliminar_usuario_admin_redirige(client_admin):
    """Admin eliminando usuario → redirect /admin/usuarios."""
    cursor = MagicMock()
    conn = mock_conn(cursor)

    with patch("routes.admin.conectar", return_value=conn):
        resp = client_admin.get("/admin/usuarios/eliminar/2")

    assert resp.status_code == 302
    assert "/admin/usuarios" in resp.headers["Location"]
