"""
Detector Visual — Análisis de fotos de habitaciones
Usa YOLOv8 si está disponible, sino un clasificador basado en OpenCV
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import cv2
import numpy as np
from datetime import datetime

from database.db import conectar

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Clases de detección
CLASES = ["suciedad_general", "pared_sucia", "basura_tirada", "daño_mueble", "fuga_agua", "mancha", "desorden_leve"]

# Intentar cargar YOLOv8
_yolo_model = None
_use_yolo = False

def _init_yolo():
    global _yolo_model, _use_yolo
    try:
        from ultralytics import YOLO
        model_path = os.path.join(os.path.dirname(__file__), "models", "yolov8n.pt")
        if not os.path.exists(model_path):
            # Descargar modelo base
            _yolo_model = YOLO("yolov8n.pt")
        else:
            _yolo_model = YOLO(model_path)
        _use_yolo = True
        print("✅ YOLOv8 cargado correctamente")
    except Exception as e:
        print(f"⚠️  YOLOv8 no disponible ({e}). Usando análisis OpenCV básico.")
        _use_yolo = False


def analizar_imagen(ruta_imagen, habitacion_id, empleado="Sistema"):
    """
    Analiza una imagen de habitación.
    Retorna: score_estado, detecciones, ruta_imagen_anotada
    """
    if _yolo_model is None:
        _init_yolo()

    img = cv2.imread(ruta_imagen)
    if img is None:
        return {"error": "No se pudo leer la imagen"}

    detecciones = []
    img_anotada = img.copy()

    # Análisis básico con OpenCV (Detección de textura, color para paredes y suelo)
    detecciones_cv = _analisis_opencv(img, img_anotada)
    detecciones.extend(detecciones_cv)

    if _use_yolo:
        # Análisis adicional con YOLOv8 (Objetos)
        results = _yolo_model(img, verbose=False)

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = r.names.get(cls_id, "desconocido")

                # Mapear clases COCO a nuestras clases de hotel
                hotel_cls = _mapear_clase(cls_name)

                detecciones.append({
                    "clase": hotel_cls,
                    "clase_original": cls_name,
                    "confianza": round(conf, 4),
                    "bbox": [x1, y1, x2, y2]
                })

                # Dibujar bounding box (YOLO)
                color = _color_por_clase(hotel_cls)
                cv2.rectangle(img_anotada, (x1, y1), (x2, y2), color, 2)
                label = f"{hotel_cls} {conf:.0%}"
                cv2.putText(img_anotada, label, (x1, y1 - 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Calcular score
    score_estado = _calcular_score(detecciones)

    # Guardar imagen anotada
    nombre_anotada = f"anotada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webp"
    ruta_anotada = os.path.join(UPLOAD_DIR, nombre_anotada)
    cv2.imwrite(ruta_anotada, img_anotada, [cv2.IMWRITE_WEBP_QUALITY, 80])

    # Confianza promedio (convertir a float nativo)
    conf_prom = float(np.mean([d["confianza"] for d in detecciones])) if detecciones else 0.0

    # Asegurar que todas las detecciones usen tipos nativos de Python
    for d in detecciones:
        d["confianza"] = float(d["confianza"])
        d["bbox"] = [int(v) for v in d["bbox"]]

    # Guardar en BD
    conn = conectar()
    cursor = conn.cursor()
    
    # Obtener el ciclo activo de limpieza
    cursor.execute("SELECT id FROM limpieza_habitaciones WHERE habitacion_id=%s AND estado_limpieza != 'Completada' ORDER BY id DESC LIMIT 1", (habitacion_id,))
    limp_row = cursor.fetchone()
    limpieza_id = limp_row[0] if limp_row else None
    
    cursor.execute("""
        INSERT INTO detecciones_visuales
        (habitacion_id, limpieza_id, imagen_original, imagen_anotada, score_estado,
         detecciones_json, confianza_promedio, empleado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (habitacion_id, limpieza_id, f"/static/uploads/{os.path.basename(ruta_imagen)}", f"/static/uploads/{nombre_anotada}", score_estado,
          json.dumps(detecciones), round(conf_prom, 4), empleado))
    det_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return {
        "id": det_id,
        "score_estado": score_estado,
        "detecciones": detecciones,
        "total_detecciones": len(detecciones),
        "confianza_promedio": round(conf_prom, 4),
        "imagen_anotada": f"/static/uploads/{nombre_anotada}",
    }


def _analisis_opencv(img, img_anotada):
    """Análisis avanzado con OpenCV para suciedad, paredes sucias y basura."""
    detecciones = []
    h, w = img.shape[:2]

    # Convertir a HSV y LAB para distintas detecciones
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

    # 1. Detectar suciedad general oscura en el piso (mitad inferior)
    _, dark_mask = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
    # Enfocarse en la mitad inferior de la imagen (piso)
    dark_mask[:int(h*0.5), :] = 0 
    contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > (h * w * 0.008):  # > 0.8% del área total
            x, y, bw, bh = cv2.boundingRect(cnt)
            conf = float(min(area / (h * w) * 1.5, 0.95))
            detecciones.append({
                "clase": "suciedad_general",
                "clase_original": "dark_area_floor",
                "confianza": round(float(conf), 4),
                "bbox": [int(x), int(y), int(x + bw), int(y + bh)]
            })
            cv2.rectangle(img_anotada, (x, y), (x + bw, y + bh), (0, 0, 255), 2)
            cv2.putText(img_anotada, f"suciedad {conf:.0%}", (x, y - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # 2. Detectar paredes sucias / manchas amplias (mitad superior, variaciones en canal B de LAB)
    # Zonas amarillentas o manchadas
    l_channel, a_channel, b_channel = cv2.split(lab)
    _, stain_mask = cv2.threshold(b_channel, 160, 255, cv2.THRESH_BINARY)
    # Enfocarse en la mitad superior de la imagen (paredes)
    stain_mask[int(h*0.7):, :] = 0
    contours, _ = cv2.findContours(stain_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > (h * w * 0.01): # > 1%
            x, y, bw, bh = cv2.boundingRect(cnt)
            conf = float(min(area / (h * w) * 2, 0.90))
            detecciones.append({
                "clase": "pared_sucia",
                "clase_original": "wall_stain",
                "confianza": round(float(conf), 4),
                "bbox": [int(x), int(y), int(x + bw), int(y + bh)]
            })
            cv2.rectangle(img_anotada, (x, y), (x + bw, y + bh), (0, 100, 255), 2)
            cv2.putText(img_anotada, f"pared sucia {conf:.0%}", (x, y - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 100, 255), 2)

    # 3. Detectar bordes fuertes densos (posibles daños o mucha basura tirada)
    edges = cv2.Canny(gray, 100, 200)
    edge_density = float(np.sum(edges > 0) / (h * w))

    if edge_density > 0.12:
        detecciones.append({
            "clase": "basura_tirada",
            "clase_original": "high_edge_density_clutter",
            "confianza": round(float(min(edge_density * 2, 0.85)), 4),
            "bbox": [0, 0, int(w), int(h)]
        })
        cv2.putText(img_anotada, f"desorden/basura {edge_density:.0%}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    return detecciones


def _mapear_clase(coco_cls):
    """Mapea clases COCO a clases de hotel."""
    mapping = {
        "person": "desorden_leve",
        "cup": "desorden_leve",
        "bottle": "basura_tirada",
        "chair": "desorden_leve",
        "suitcase": "desorden_leve",
        "backpack": "desorden_leve",
        "handbag": "desorden_leve",
        "cell phone": "desorden_leve",
        "book": "desorden_leve",
        "laptop": "desorden_leve",
    }
    return mapping.get(coco_cls, "desorden_leve")


def _color_por_clase(cls):
    colores = {
        "suciedad_general": (0, 0, 255),
        "pared_sucia": (0, 69, 255),
        "daño_mueble": (0, 140, 255),
        "mancha": (0, 165, 255),
        "basura_tirada": (255, 165, 0),
        "fuga_agua": (255, 0, 0),
        "desorden_leve": (255, 255, 0),
    }
    return colores.get(cls, (128, 128, 128))


def _calcular_score(detecciones):
    """Determina el estado general de la habitación."""
    if not detecciones:
        return "LIMPIA"

    clases_graves = {"fuga_agua", "daño_mueble"}
    clases_limpieza = {"suciedad_general", "pared_sucia", "basura_tirada", "mancha"}
    # desorden_leve es ignorado a propósito

    tiene_graves = any(d["clase"] in clases_graves for d in detecciones)
    tiene_limpieza = any(d["clase"] in clases_limpieza for d in detecciones)
    
    # Solo consideramos la confianza máxima de las alertas reales (ignoramos el desorden leve para el cálculo crítico)
    alertas_reales = [d["confianza"] for d in detecciones if d["clase"] != "desorden_leve"]
    conf_max = max(alertas_reales) if alertas_reales else 0.0

    if tiene_graves and conf_max > 0.5:
        return "REQUIERE_MANTENIMIENTO"
    elif tiene_limpieza and conf_max > 0.4:
        return "REQUIERE_LIMPIEZA"
    elif tiene_limpieza or len(alertas_reales) > 2:
        return "REQUIERE_LIMPIEZA"
    else:
        # Pude que la habitación tenga muchas de maletas detectadas pero ninguna de basura o daños
        return "LIMPIA"
