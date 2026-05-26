"""
Fixtures compartidos para la suite de tests.
- TestConfig desactiva CSRF, rate limiting y BD real.
- `client` provee un Flask test client con sesión.
- `client_admin` y `client_empleado` simulan usuarios autenticados.
"""
import pytest
from unittest.mock import MagicMock, patch
from config import Config


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SECRET_KEY = "test-secret-key"


@pytest.fixture(scope="session")
def app():
    """Crea la app Flask en modo test (sin BD real, sin CSRF, sin rate limit)."""
    from app import crear_app
    application = crear_app(TestConfig)
    application.config["WTF_CSRF_CHECK_DEFAULT"] = False
    return application


@pytest.fixture
def client(app):
    """Test client de Flask — sin sesión activa."""
    return app.test_client()


@pytest.fixture
def client_admin(app):
    """Test client con sesión de administrador ya activa."""
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user_id"] = 1
            sess["user"] = "admin"
            sess["rol"] = "admin"
        yield c


@pytest.fixture
def client_empleado(app):
    """Test client con sesión de empleado ya activa."""
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user_id"] = 2
            sess["user"] = "empleado1"
            sess["rol"] = "empleado"
        yield c


def mock_cursor(rows=None, rowcount=1):
    """Devuelve un cursor mock con fetchone/fetchall configurables."""
    cursor = MagicMock()
    cursor.fetchone.return_value = rows[0] if rows and len(rows) == 1 else (rows[0] if rows else None)
    cursor.fetchall.return_value = rows if rows else []
    cursor.rowcount = rowcount
    return cursor


def mock_conn(cursor_mock):
    """Devuelve una conexión mock que retorna el cursor dado."""
    conn = MagicMock()
    conn.cursor.return_value = cursor_mock
    return conn
