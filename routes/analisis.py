from flask import Blueprint, render_template, redirect, session
from database.db import conectar

analisis_bp = Blueprint("analisis", __name__)


@analisis_bp.route("/analisis")
def analisis():
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    # KPIs generales
    cursor.execute("SELECT COUNT(*) FROM mantenimiento")
    total_fallas = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(costo),0) FROM mantenimiento")
    costo_total = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(AVG(costo),0) FROM mantenimiento")
    costo_promedio = round(float(cursor.fetchone()[0]), 2)

    # Top 5 fallas más frecuentes
    cursor.execute("""
        SELECT elemento, COUNT(*) as veces
        FROM mantenimiento
        WHERE elemento IS NOT NULL AND elemento != ''
        GROUP BY elemento
        ORDER BY veces DESC LIMIT 5
    """)
    top_fallas = cursor.fetchall()

    # Tendencia mensual
    cursor.execute("""
        SELECT TO_CHAR(fecha::date, 'YYYY-MM') as mes, COUNT(*) as total
        FROM mantenimiento
        WHERE fecha IS NOT NULL
        GROUP BY mes ORDER BY mes DESC LIMIT 12
    """)
    tendencia_mensual = cursor.fetchall()

    # Costo promedio por tipo de falla
    cursor.execute("""
        SELECT elemento, COUNT(*) as veces,
               ROUND(AVG(costo)::numeric, 2) as costo_prom,
               ROUND(SUM(costo)::numeric, 2) as costo_total
        FROM mantenimiento
        WHERE elemento IS NOT NULL AND elemento != ''
        GROUP BY elemento
        ORDER BY costo_total DESC LIMIT 5
    """)
    costo_por_tipo = cursor.fetchall()

    # Habitaciones reincidentes
    cursor.execute("""
        SELECT h.numero, m.elemento, COUNT(*) as veces
        FROM mantenimiento m
        JOIN habitaciones h ON m.habitacion_id = h.id
        WHERE m.elemento IS NOT NULL AND m.elemento != ''
        GROUP BY m.habitacion_id, h.numero, m.elemento
        HAVING COUNT(*) >= 2
        ORDER BY veces DESC LIMIT 10
    """)
    reincidentes = cursor.fetchall()

    # Fallas por habitación (ranking)
    cursor.execute("""
        SELECT h.numero, COUNT(*) as fallas
        FROM mantenimiento m
        JOIN habitaciones h ON m.habitacion_id = h.id
        GROUP BY m.habitacion_id, h.numero
        ORDER BY fallas DESC LIMIT 10
    """)
    fallas_por_hab = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("analisis.html",
                           total_fallas=total_fallas,
                           costo_total=costo_total,
                           costo_promedio=costo_promedio,
                           top_fallas=top_fallas,
                           tendencia_mensual=tendencia_mensual,
                           costo_por_tipo=costo_por_tipo,
                           reincidentes=reincidentes,
                           fallas_por_hab=fallas_por_hab)

@analisis_bp.route("/analisis/exportar")
def exportar_csv():
    if "user" not in session:
        return redirect("/login")
        
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.numero, m.fecha, m.tipo, m.elemento, COALESCE(m.costo, 0), m.estado
        FROM mantenimiento m
        JOIN habitaciones h ON m.habitacion_id = h.id
        ORDER BY m.fecha DESC
    """)
    filas = cursor.fetchall()
    cursor.close()
    conn.close()

    import csv
    from flask import Response
    from io import StringIO

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Habitacion', 'Fecha', 'Tipo', 'Elemento', 'Costo', 'Estado'])
    cw.writerows(filas)
    
    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=analisis_historico.csv"}
    )
