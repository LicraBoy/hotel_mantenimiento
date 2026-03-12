from flask import Blueprint, render_template, request, redirect, session, flash
from datetime import datetime, timedelta

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.db import conectar

limpieza_bp = Blueprint("limpieza", __name__)


@limpieza_bp.route("/limpieza")
def panel():
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()
    # Seleccionamos sólo el registro más prioritario/reciente por habitación activa
    cursor.execute("""
        SELECT DISTINCT ON (h.id)
               l.id, h.numero, l.categoria_habitacion, l.urgency_score,
               l.nivel_urgencia, l.estado_limpieza, l.asignado_a,
               l.fecha_checkout, l.fecha_checkin_siguiente,
               l.fecha_ultima_limpieza_profunda,
               (SELECT score_estado FROM detecciones_visuales 
                WHERE limpieza_id = l.id ORDER BY id DESC LIMIT 1) as estado_visual,
               (SELECT confianza_promedio FROM detecciones_visuales 
                WHERE limpieza_id = l.id ORDER BY id DESC LIMIT 1) as conf_visual,
               (SELECT imagen_anotada FROM detecciones_visuales 
                WHERE limpieza_id = l.id ORDER BY id DESC LIMIT 1) as url_visual
        FROM limpieza_habitaciones l
        JOIN habitaciones h ON l.habitacion_id = h.id
        WHERE l.estado_limpieza != 'Completada'
        ORDER BY h.id, l.urgency_score DESC, l.fecha_checkout DESC
    """)
    
    # DISTINCT ON nos obliga a ordenar primero por la clave h.id
    # pero queremos que la tabla se muestre ordenada por urgencia, 
    # así que ordenamos el resultado final en Python
    cola_raw = cursor.fetchall()
    cola = sorted(cola_raw, key=lambda x: (x[3] or 0), reverse=True)

    total = len(cola)
    pendientes = sum(1 for c in cola if c[5] == "Pendiente")
    en_proceso = sum(1 for c in cola if c[5] == "En proceso")
    completadas = sum(1 for c in cola if c[5] == "Completada")
    criticos = sum(1 for c in cola if c[4] == "CRÍTICO")

    cursor.close()
    conn.close()

    return render_template("limpieza.html", cola=cola,
                           total=total, pendientes=pendientes,
                           en_proceso=en_proceso, completadas=completadas,
                           criticos=criticos)


@limpieza_bp.route("/limpieza/checkout/<int:hab_id>", methods=["POST"])
def registrar_checkout(hab_id):
    if "user" not in session:
        return redirect("/login")

    checkin_str = request.form.get("checkin_siguiente", "")
    categoria = request.form.get("categoria", "Estándar")

    checkin = None
    if checkin_str:
        try:
            checkin = datetime.strptime(checkin_str, "%Y-%m-%dT%H:%M")
        except Exception:
            try:
                checkin = datetime.strptime(checkin_str, "%Y-%m-%d")
            except Exception:
                pass

    from ai.scoring_engine import registrar_checkout as reg
    reg(hab_id, checkin, categoria)
    
    from extensions import socketio
    socketio.emit('alerta_global', {
        'tipo': 'limpieza',
        'mensaje': f'Check-out registrado en Habitación {hab_id}'
    })
    
    flash(f"✅ Check-out registrado para habitación")
    return redirect("/limpieza")


@limpieza_bp.route("/limpieza/completar/<int:lid>", methods=["POST"])
def completar(lid):
    if "user" not in session:
        return redirect("/login")

    from ai.scoring_engine import completar_limpieza
    completar_limpieza(lid)
    
    from extensions import socketio
    socketio.emit('alerta_global', {
        'tipo': 'limpieza',
        'mensaje': f'Limpieza completada por staff'
    })
    
    flash("✅ Limpieza marcada como completada")
    return redirect("/limpieza")


@limpieza_bp.route("/limpieza/recalcular", methods=["POST"])
def recalcular():
    if "user" not in session:
        return redirect("/login")

    from ai.scoring_engine import recalcular_scores
    resultados = recalcular_scores()
    flash(f"✅ {len(resultados)} scores recalculados")
    return redirect("/limpieza")


@limpieza_bp.route("/limpieza/generar-demo", methods=["POST"])
def generar_demo():
    if "user" not in session:
        return redirect("/login")

    from ai.scoring_engine import generar_datos_demo, recalcular_scores
    generar_datos_demo()
    recalcular_scores()
    flash("✅ Datos de demostración generados")
    return redirect("/limpieza")


@limpieza_bp.route("/limpieza/nuevo-checkout")
def formulario_checkout():
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, numero FROM habitaciones ORDER BY numero")
    habitaciones = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("limpieza_checkout.html", habitaciones=habitaciones)


@limpieza_bp.route("/limpieza/mapa")
def mapa():
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.id, h.numero, h.estado,
               l.urgency_score, l.nivel_urgencia, l.estado_limpieza, l.categoria_habitacion
        FROM habitaciones h
        LEFT JOIN limpieza_habitaciones l ON h.id = l.habitacion_id
              AND l.estado_limpieza != 'Completada'
        ORDER BY h.numero
    """)
    habitaciones = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()

    return render_template("limpieza_mapa.html", habitaciones=habitaciones)


@limpieza_bp.route("/limpieza/historial")
def historial():
    if "user" not in session:
        return redirect("/login")

    fecha_filtro = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, numero_habitacion, categoria, estado_ia,
               urgencia_inicial, empleado, fecha_checkout, fecha_completada, imagen_evidencia
        FROM historial_limpieza
        WHERE (fecha_completada AT TIME ZONE 'UTC' AT TIME ZONE 'America/Mexico_City')::DATE = %s::DATE
        ORDER BY fecha_completada DESC
    """, (fecha_filtro,))
    
    historial_completadas = cursor.fetchall()
    cursor.close()
    conn.close()

    total_limpias = sum(1 for c in historial_completadas if c[3] == "LIMPIA")
    total_sucias = sum(1 for c in historial_completadas if c[3] == "REQUIERE_LIMPIEZA")
    total_mantenimiento = sum(1 for c in historial_completadas if c[3] == "REQUIERE_MANTENIMIENTO")

    return render_template("limpieza_historial.html", 
                           limpiezas=historial_completadas, 
                           fecha_actual=fecha_filtro,
                           total_limpias=total_limpias,
                           total_sucias=total_sucias,
                           total_mantenimiento=total_mantenimiento)
