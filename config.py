import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "hotel_secret_key")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hotel_mantenimiento")

    # Seguridad de sesión
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False       # Cambiar a True cuando se use HTTPS
    PERMANENT_SESSION_LIFETIME = 3600   # Sesión expira en 1 hora

    # Límite de tamaño de archivos subidos (5 MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # CSRF token válido por 1 hora
    WTF_CSRF_TIME_LIMIT = 3600
