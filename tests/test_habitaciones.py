"""
Tests: Gestión de habitaciones
Cubre: función de validación y rutas CRUD
"""
import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import mock_conn, mock_cursor


# Importamos la función de validación directamente (test unitario puro)
from routes.habitaciones import _validar_habitacion, ESTADOS_HAB_VALIDOS


# ============================================================
# Pruebas unitarias: _validar_habitacion()
# ============================================================

def test_validar_numero_vacio_retorna_error():
    """Número vacío debe generar error obligatorio."""
    errores = _validar_habitacion({"numero": "", "estado": "Disponible"})
    assert any("obligatorio" in e.lower() for e in errores)


def test_validar_numero_solo_espacios_retorna_error():
    """Número con solo espacios debe generar error."""
    errores = _validar_habitacion({"numero": "   ", "estado": "Disponible"})
    assert any("obligatorio" in e.lower() for e in errores)


def test_validar_estado_invalido_retorna_error():
    """Estado que no está en la lista válida debe generar error."""
    errores = _validar_habitacion({"numero": "101", "estado": "Destruida"})
    assert any("válid" in e.lower() for e in errores)


def test_validar_estado_vacio_retorna_error():
    """Estado vacío debe generar error."""
    errores = _validar_habitacion({"numero": "101", "estado": ""})
    assert len(errores) > 0


@pytest.mark.parametrize("estado", list(ESTADOS_HAB_VALIDOS))
def test_validar_estados_validos_sin_errores(estado):
    """Cada estado válido no debe generar errores."""
    errores = _validar_habitacion({"numero": "101", "estado": estado})
    assert errores == []


def test_validar_datos_correctos_sin_errores():
    """Número y estado correctos → lista de errores vacía."""
    errores = _validar_habitacion({"numero": "101", "estado": "Disponible"})
    assert errores == []


def test_validar_numero_con_letras_es_valido():
    """Números como '10A' o 'Suite-1' son válidos (solo se requiere que no esté vacío)."""
    errores = _validar_habitacion({"numero": "Suite-1", "estado": "Disponible"})
    assert errores == []


# ============================================================
# Tests de integración: rutas HTTP
# ============================================================

def test_lista_habitaciones_sin_sesion_redirige(client):
    """GET /habitaciones sin login → redirect /login."""
    resp = client.get("/habitaciones")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_lista_habitaciones_con_sesion_retorna_200(client_admin):
    """GET /habitaciones con sesión → 200."""
    cursor = mock_cursor(rows=[])
    conn = mock_conn(cursor)
    with patch("routes.habitaciones.conectar", return_value=conn):
        resp = client_admin.get("/habitaciones")
    assert resp.status_code == 200


def test_form_nueva_habitacion_get(client_admin):
    """GET /habitaciones/nueva → muestra formulario (200)."""
    resp = client_admin.get("/habitaciones/nueva")
    assert resp.status_code == 200


def test_crear_habitacion_valida_redirige(client_admin):
    """POST habitación válida → redirect /habitaciones."""
    cursor = mock_cursor(rows=None)
    cursor.fetchone.return_value = None   # número no existe todavía
    conn = mock_conn(cursor)

    with patch("routes.habitaciones.conectar", return_value=conn):
        resp = client_admin.post(
            "/habitaciones/nueva",
            data={"numero": "205", "estado": "Disponible"},
        )

    assert resp.status_code == 302
    assert "/habitaciones" in resp.headers["Location"]


def test_crear_habitacion_sin_numero_muestra_error(client_admin):
    """POST sin número → 200 con errores (no redirige)."""
    resp = client_admin.post(
        "/habitaciones/nueva",
        data={"numero": "", "estado": "Disponible"},
    )
    assert resp.status_code == 200


def test_crear_habitacion_estado_invalido_muestra_error(client_admin):
    """POST con estado inválido → 200 con errores."""
    resp = client_admin.post(
        "/habitaciones/nueva",
        data={"numero": "206", "estado": "Inexistente"},
    )
    assert resp.status_code == 200


def test_crear_habitacion_numero_duplicado_redirige_con_flash(client_admin):
    """POST con número ya existente → redirect /habitaciones (con flash de error)."""
    cursor = mock_cursor(rows=[(1,)])   # fetchone devuelve una fila = ya existe
    conn = mock_conn(cursor)

    with patch("routes.habitaciones.conectar", return_value=conn):
        resp = client_admin.post(
            "/habitaciones/nueva",
            data={"numero": "101", "estado": "Disponible"},
        )

    # La ruta hace redirect a /habitaciones con flash de error
    assert resp.status_code == 302
    assert "/habitaciones" in resp.headers["Location"]


def test_editar_habitacion_get_sin_sesion_redirige(client):
    """GET /habitaciones/editar/<id> sin login → redirect /login."""
    resp = client.get("/habitaciones/editar/1")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_eliminar_habitacion_sin_sesion_redirige(client):
    """POST /habitaciones/eliminar/<id> sin login → redirect /login."""
    resp = client.post("/habitaciones/eliminar/1")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
