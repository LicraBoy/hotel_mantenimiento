from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Inicialización central de extensiones para evitar importaciones circulares
socketio = SocketIO(cors_allowed_origins=["http://127.0.0.1:5000", "http://localhost:5000"])
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
