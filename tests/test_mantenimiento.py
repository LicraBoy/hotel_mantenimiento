"""
Tests: Órdenes de mantenimiento
Cubre: función de validación (unitarios) y rutas HTTP (integración)
"""
import pytest
from unittest.mock import patch
from tests.conftest import mock_conn, mock_cursor

from routes.mantenimiento import _validar_mantenimiento, TIPOS_MANT_VALIDOS


# ============================================================
# Pruebas unitarias: _validar_mantenimiento()
# ============================================================

def test_validar_tipo_invalido():
    """Tipo que no existe → error de tipo."""
    errores = _validar_mantenimiento({
        "tipo": "Capricho",
        "elemento": "Aire acondicionado",
        "fecha": "2026-03-01",
        "costo": "200"
    })
    assert any("tipo" in e.lower() for e in errores)


@pytest.mark.parametrize("tipo", list(TIPOS_MANT_VALIDOS))
def test_validar_tipos_validos_sin_error(tipo):
    """Cada tipo válido no debe generar error de tipo."""
    errores = _validar_mantenimiento({
        "tipo": tipo,
        "elemento": "Calefacción",
        "fecha": "2026-03-01",
        "costo": ""
    })
    assert not any("tipo" in e.lower() for e in errores)


def test_validar_elemento_vacio():
    """Elemento vacío → error de elemento."""
    errores = _validar_mantenimiento({
        "tipo": "Correctivo",
        "elemento": "",
        "fecha": "2026-03-01",
        "costo": ""
    })
    assert any("elemento" in e.lower() for e in errores)


def test_validar_elemento_supera_200_caracteres():
    """Elemento con más de 200 caracteres → error."""
    errores = _validar_mantenimiento({
        "tipo": "Correctivo",
        "elemento": "x" * 201,
        "fecha": "2026-03-01",
        "costo": ""
    })
    assert any("elemento" in e.lower() for e in errores)


def test_validar_fecha_vacia():
    """Fecha vacía → error de fecha."""
    errores = _validar_mantenimiento({
        "tipo": "Correctivo",
        "elemento": "Tubería",
        "fecha": "",
        "costo": ""
    })
    assert any("fecha" in e.lower() for e in errores)


def test_validar_fecha_formato_incorrecto():
    """Fecha con formato dd/mm/yyyy → error de formato."""
    errores = _validar_mantenimiento({
        "tipo": "Correctivo",
        "elemento": "Tubería",
        "fecha": "01-03-2026",   # formato incorrecto
        "costo": ""
    })
    assert any("fecha" in e.lower() for e in errores)


def test_validar_fecha_texto_libre():
    """Texto libre como fecha → error."""
    errores = _validar_mantenimiento({
        "tipo": "Correctivo",
        "elemento": "Tubería",
        "fecha": "mañana",
        "costo": ""
    })
    assert any("fecha" in e.lower() for e in errores)


def test_validar_costo_negativo():
    """Costo negativo → error."""
    errores = _validar_mantenimiento({
        "tipo": "Correctivo",
        "elemento": "Tubería",
        "fecha": "2026-03-01",
        "costo": "-50"
    })
    assert any("costo" in e.lower() for e in errores)


def test_validar_costo_texto():
    """Costo con texto → error."""
    errores = _validar_mantenimiento({
        "tipo": "Correctivo",
        "elemento": "Tubería",
        "fecha": "2026-03-01",
        "costo": "mucho"
    })
    assert any("costo" in e.lower() for e in errores)


def test_validar_costo_cero_es_valido():
    """Costo de 0 es válido."""
    errores = _validar_mantenimiento({
        "tipo": "Correctivo",
        "elemento": "Tubería",
        "fecha": "2026-03-01",
        "costo": "0"
    })
    assert not any("costo" in e.lower() for e in errores)


def test_validar_costo_vacio_es_valido():
    """Costo vacío (campo opcional) no genera error."""
    errores = _validar_mantenimiento({
        "tipo": "Preventivo",
        "elemento": "Calefacción",
        "fecha": "2026-04-15",
        "costo": ""
    })
    assert not any("costo" in e.lower() for e in errores)


def test_validar_todo_correcto_retorna_lista_vacia():
    """Todos los campos válidos → sin errores."""
    errores = _validar_mantenimiento({
        "tipo": "Preventivo",
        "elemento": "Sistema eléctrico",
        "fecha": "2026-05-10",
        "costo": "350.50"
    })
    assert errores == []


# ============================================================
# Tests de integración: rutas HTTP
# ============================================================

def test_lista_mantenimientos_sin_sesion_redirige(client):
    """GET /mantenimientos sin login → redirect /login."""
    resp = client.get("/mantenimientos")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_lista_mantenimientos_con_sesion(client_admin):
    """GET /mantenimientos con sesión → 200."""
    cursor = mock_cursor(rows=[])
    conn = mock_conn(cursor)
    with patch("routes.mantenimiento.conectar", return_value=conn):
        resp = client_admin.get("/mantenimientos")
    assert resp.status_code == 200


def test_form_nuevo_mantenimiento_get(client_admin):
    """GET /mantenimiento/nuevo/<id> → 200 con formulario."""
    habitacion_row = (1, "101", "Disponible", None)
    cursor = mock_cursor(rows=[habitacion_row])
    conn = mock_conn(cursor)
    with patch("routes.mantenimiento.conectar", return_value=conn):
        resp = client_admin.get("/mantenimiento/nuevo/1")
    assert resp.status_code == 200


def test_crear_mantenimiento_valido_redirige(client_admin):
    """POST orden válida → redirect /mantenimientos."""
    habitacion_row = (1, "101", "Disponible", None)
    cursor = mock_cursor(rows=[habitacion_row])
    conn = mock_conn(cursor)

    with patch("routes.mantenimiento.conectar", return_value=conn):
        resp = client_admin.post(
            "/mantenimiento/nuevo/1",
            data={
                "tipo": "Correctivo",
                "elemento": "Aire acondicionado",
                "descripcion": "No enfría",
                "tecnico": "Juan",
                "fecha": "2026-03-01",
                "estado": "Pendiente",
                "costo": "300",
                "prioridad": "Alta",
            },
        )

    assert resp.status_code == 302
    assert "/mantenimientos" in resp.headers["Location"]


def test_crear_mantenimiento_tipo_invalido_muestra_error(client_admin):
    """POST con tipo inválido → 200 con errores."""
    habitacion_row = (1, "101", "Disponible", None)
    cursor = mock_cursor(rows=[habitacion_row])
    conn = mock_conn(cursor)

    with patch("routes.mantenimiento.conectar", return_value=conn):
        resp = client_admin.post(
            "/mantenimiento/nuevo/1",
            data={
                "tipo": "TipoFalso",
                "elemento": "Tubería",
                "descripcion": "",
                "tecnico": "",
                "fecha": "2026-03-01",
                "estado": "Pendiente",
                "costo": "",
                "prioridad": "Media",
            },
        )

    assert resp.status_code == 200


def test_nuevo_mantenimiento_sin_sesion_redirige(client):
    """GET /mantenimiento/nuevo/<id> sin login → redirect /login."""
    resp = client.get("/mantenimiento/nuevo/1")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
