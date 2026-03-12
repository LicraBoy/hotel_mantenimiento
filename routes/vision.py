import os, json
from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.utils import secure_filename

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.db import conectar

vision_bp = Blueprint("vision", __name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


@vision_bp.route("/vision")
def panel():
    if "user" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.id, h.numero 
        FROM habitaciones h
        JOIN limpieza_habitaciones l ON h.id = l.habitacion_id
        WHERE l.estado_limpieza != 'Completada'
        GROUP BY h.id, h.numero
        ORDER BY h.numero
    """)
    habitaciones = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("vision.html", habitaciones=habitaciones, resultado=None)


@vision_bp.route("/vision/analizar", methods=["POST"])
def analizar():
    if "user" not in session:
        return redirect("/login")

    habitacion_id = request.form.get("habitacion_id")
    archivo = request.files.get("imagen")

    if not archivo or not _allowed(archivo.filename):
        flash("⚠️ Sube una imagen válida (JPG, PNG, WEBP)")
        return redirect("/vision")

    if not habitacion_id:
        flash("⚠️ Selecciona una habitación")
        return redirect("/vision")

    from datetime import datetime
    import os
    from werkzeug.utils import secure_filename
    from ai.detector import analizar_imagen
    
    nombre_base = secure_filename(archivo.filename).rsplit('.', 1)[0]
    nombre = f"hab{habitacion_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{nombre_base}.webp"
    ruta = os.path.join(UPLOAD_DIR, nombre)
    
    from PIL import Image
    try:
        img = Image.open(archivo)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # Redimensionar para no exceder 1080px
        max_size = 1080
        if max(img.width, img.height) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
        img.save(ruta, "WEBP", quality=80)
    except Exception as e:
        flash(f"⚠️ Error procesando la imagen a WebP: {str(e)}")
        return redirect("/vision")

    try:
        resultado = analizar_imagen(ruta, int(habitacion_id), session.get("user", "Sistema"))
        if "error" in resultado:
            flash(f"⚠️ Error en análisis: {resultado['error']}")
            return redirect("/vision")
    except Exception as e:
        flash(f"⚠️ Error fatal en análisis: {str(e)}")
        return redirect("/vision")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.id, h.numero 
        FROM habitaciones h
        JOIN limpieza_habitaciones l ON h.id = l.habitacion_id
        WHERE l.estado_limpieza != 'Completada'
        GROUP BY h.id, h.numero
        ORDER BY h.numero
    """)
    habitaciones = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("vision.html", habitaciones=habitaciones, resultado=resultado, imagen_original=f"/static/uploads/{nombre}")



