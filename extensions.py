from flask_socketio import SocketIO

# Inicialización central de SocketIO para evitar importaciones circulares
socketio = SocketIO(cors_allowed_origins="*")
