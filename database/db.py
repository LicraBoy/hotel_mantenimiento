import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hotel_mantenimiento")


def conectar():
    """Retorna una conexión a PostgreSQL."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn
