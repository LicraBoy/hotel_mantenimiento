"""
Crear tablas del módulo Inventario de Activos — Hotel Mantenimiento
Tablas: categorias_activos, activos, documentos_activo
Columna nueva: mantenimiento.activo_id (FK a activos)
"""
from database.db import conectar


CATEGORIAS_INICIALES = [
    ('Línea Blanca',    'fas fa-snowflake',  '#3B82F6', 'Refrigeradores, lavadoras, secadoras'),
    ('Climatización',   'fas fa-wind',       '#06B6D4', 'Aire acondicionado, calefacción, ventilación'),
    ('Electricidad',    'fas fa-bolt',       '#EAB308', 'Tableros, plantas, UPS, cableado'),
    ('Plomería',        'fas fa-faucet',     '#6366F1', 'Tuberías, bombas, calentadores de agua'),
    ('Mobiliario',      'fas fa-couch',      '#8B5CF6', 'Muebles, camas, escritorios'),
    ('Tecnología',      'fas fa-tv',         '#EC4899', 'Televisores, routers, teléfonos'),
    ('Seguridad',       'fas fa-shield-alt', '#EF4444', 'Cámaras, alarmas, cerraduras electrónicas'),
    ('Cocina',          'fas fa-utensils',   '#F97316', 'Hornos, campanas, refrigeradores comerciales'),
    ('Elevación',       'fas fa-elevator',   '#14B8A6', 'Elevadores, escaleras eléctricas'),
    ('Otros',           'fas fa-box',        '#6B7280', 'Activos sin categoría específica'),
]


def crear_tablas_inventario():
    conn = conectar()
    cursor = conn.cursor()

    # ── Tabla: categorias_activos ─────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias_activos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            icono VARCHAR(50),
            color VARCHAR(20),
            descripcion TEXT,
            activo BOOLEAN DEFAULT TRUE,
            creado_en TIMESTAMP DEFAULT NOW()
        )
    """)

    # ── Tabla: activos ────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activos (
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(50) UNIQUE,
            nombre VARCHAR(150) NOT NULL,
            categoria_id INTEGER REFERENCES categorias_activos(id),
            subcategoria VARCHAR(100),
            marca VARCHAR(100),
            modelo VARCHAR(100),
            numero_serie VARCHAR(100),
            fecha_compra DATE,
            fecha_instalacion DATE,
            garantia_hasta DATE,
            proveedor VARCHAR(150),
            costo_adquisicion NUMERIC(10,2),
            vida_util_anos INTEGER,
            ubicacion VARCHAR(200),
            habitacion_id INTEGER REFERENCES habitaciones(id) ON DELETE SET NULL,
            estado VARCHAR(30) DEFAULT 'operativo',
            foto_url VARCHAR(255),
            codigo_qr VARCHAR(255),
            notas TEXT,
            creado_por INTEGER REFERENCES usuarios(id),
            creado_en TIMESTAMP DEFAULT NOW(),
            actualizado_en TIMESTAMP DEFAULT NOW()
        )
    """)

    # ── Tabla: documentos_activo ──────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentos_activo (
            id SERIAL PRIMARY KEY,
            activo_id INTEGER REFERENCES activos(id) ON DELETE CASCADE,
            tipo VARCHAR(50),
            nombre_archivo VARCHAR(255),
            ruta_archivo VARCHAR(255),
            subido_en TIMESTAMP DEFAULT NOW()
        )
    """)

    # ── Columna FK en mantenimiento ───────────────
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'mantenimiento'
    """)
    cols_mant = [r[0] for r in cursor.fetchall()]

    if 'activo_id' not in cols_mant:
        cursor.execute("""
            ALTER TABLE mantenimiento
            ADD COLUMN activo_id INTEGER REFERENCES activos(id) ON DELETE SET NULL
        """)

    # ── Datos iniciales de categorías ─────────────
    cursor.execute("SELECT COUNT(*) FROM categorias_activos")
    if cursor.fetchone()[0] == 0:
        for nombre, icono, color, desc in CATEGORIAS_INICIALES:
            cursor.execute("""
                INSERT INTO categorias_activos (nombre, icono, color, descripcion)
                VALUES (%s, %s, %s, %s)
            """, (nombre, icono, color, desc))

    conn.commit()
    cursor.close()
    conn.close()
    print("[OK] Tablas de Inventario creadas correctamente")


if __name__ == "__main__":
    crear_tablas_inventario()
