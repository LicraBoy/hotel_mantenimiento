from flask import Blueprint, render_template, request, redirect, session
from flask import send_file
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from database.db import conectar

reportes_bp = Blueprint("reportes", __name__)


# ===============================
# Formulario de fechas
# ===============================
@reportes_bp.route("/reporte")
def formulario():
    if "user" not in session:
        return redirect("/login")
    return render_template("reporte_form.html")


# ===============================
# Generar PDF profesional
# ===============================
@reportes_bp.route("/reporte/pdf")
def generar_pdf():
    if "user" not in session:
        return redirect("/login")

    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, HRFlowable
    import os, tempfile, datetime

    fecha_inicio = request.args.get("fecha_inicio", "2000-01-01")
    fecha_fin = request.args.get("fecha_fin", "2099-12-31")

    conn = conectar()
    cursor = conn.cursor()

    # KPIs generales
    cursor.execute("SELECT COUNT(*) FROM habitaciones")
    total_habitaciones = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM habitaciones WHERE estado='Disponible'")
    hab_disponibles = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM habitaciones WHERE estado!='Disponible'")
    hab_mantenimiento = cursor.fetchone()[0]

    # Mantenimientos en el rango
    cursor.execute("""
        SELECT h.numero, m.fecha, m.tipo, m.elemento, m.descripcion,
               m.tecnico, m.estado, m.costo, m.prioridad
        FROM mantenimiento m
        JOIN habitaciones h ON m.habitacion_id = h.id
        WHERE m.fecha BETWEEN %s AND %s
        ORDER BY m.fecha DESC
    """, (fecha_inicio, fecha_fin))
    mantenimientos_periodo = cursor.fetchall()

    # Totales del período
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(costo),0), COALESCE(AVG(costo),0)
        FROM mantenimiento WHERE fecha BETWEEN %s AND %s
    """, (fecha_inicio, fecha_fin))
    periodo_stats = cursor.fetchone()
    total_mant_periodo = periodo_stats[0]
    costo_total_periodo = periodo_stats[1]
    costo_promedio_periodo = round(float(periodo_stats[2]), 2)

    # Top 5 más costosas
    cursor.execute("""
        SELECT h.numero, COUNT(m.id) as fallas, COALESCE(SUM(m.costo),0) as total_costo
        FROM mantenimiento m
        JOIN habitaciones h ON m.habitacion_id = h.id
        WHERE m.fecha BETWEEN %s AND %s
        GROUP BY m.habitacion_id, h.numero
        ORDER BY total_costo DESC LIMIT 5
    """, (fecha_inicio, fecha_fin))
    top_costosas = cursor.fetchall()

    # Inspecciones en el período
    cursor.execute("""
        SELECT h.numero, i.empleado, i.fecha, i.observaciones,
               CASE WHEN i.genera_mantenimiento = 1 THEN 'Si' ELSE 'No' END as genero
        FROM inspecciones i
        JOIN habitaciones h ON i.habitacion_id = h.id
        WHERE i.fecha BETWEEN %s AND %s
        ORDER BY i.fecha DESC
    """, (fecha_inicio, fecha_fin))
    inspecciones_periodo = cursor.fetchall()

    # Fallas por tipo de elemento
    cursor.execute("""
        SELECT elemento, COUNT(*) as veces, COALESCE(SUM(costo),0) as costo_total
        FROM mantenimiento
        WHERE fecha BETWEEN %s AND %s
          AND elemento IS NOT NULL AND elemento != ''
        GROUP BY elemento ORDER BY veces DESC LIMIT 10
    """, (fecha_inicio, fecha_fin))
    fallas_por_elemento = cursor.fetchall()

    cursor.close()
    conn.close()

    # ════════════════════════════════════════
    # GENERAR PDF
    # ════════════════════════════════════════
    pdf_path = os.path.join(tempfile.gettempdir(), "reporte_hotel.pdf")

    doc = SimpleDocTemplate(
        pdf_path, pagesize=letter,
        topMargin=40, bottomMargin=40, leftMargin=50, rightMargin=50
    )

    styles = getSampleStyleSheet()

    # Colores corporativos
    azul_acento = colors.HexColor("#6c5ce7")
    rojo = colors.HexColor("#ff6b6b")
    gris_claro = colors.HexColor("#f5f6fa")
    gris_borde = colors.HexColor("#dcdde1")

    contenido = []

    # ── ENCABEZADO ──
    header_data = [[
        Paragraph('<font size="18" color="#6c5ce7"><b>REPORTE DE MANTENIMIENTO</b></font>', styles["Normal"]),
        Paragraph(
            f'<font size="9" color="#636e72"><b>Hotel Mantenimiento</b><br/>'
            f'Período: {fecha_inicio} al {fecha_fin}<br/>'
            f'Generado: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</font>',
            styles["Normal"]
        )
    ]]
    header_table = Table(header_data, colWidths=[320, 190])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    contenido.append(header_table)
    contenido.append(Spacer(1, 6))
    contenido.append(HRFlowable(width="100%", thickness=2, color=azul_acento))
    contenido.append(Spacer(1, 18))

    # ── RESUMEN EJECUTIVO ──
    contenido.append(Paragraph('<font size="12" color="#6c5ce7"><b>RESUMEN EJECUTIVO</b></font>', styles["Normal"]))
    contenido.append(Spacer(1, 10))

    kpi_data = [
        [
            Paragraph('<font size="8" color="#636e72">TOTAL HABITACIONES</font>', styles["Normal"]),
            Paragraph('<font size="8" color="#636e72">DISPONIBLES</font>', styles["Normal"]),
            Paragraph('<font size="8" color="#636e72">EN MANTENIMIENTO</font>', styles["Normal"]),
            Paragraph('<font size="8" color="#636e72">MANTENIMIENTOS (PERÍODO)</font>', styles["Normal"]),
        ],
        [
            Paragraph(f'<font size="16" color="#2d3436"><b>{total_habitaciones}</b></font>', styles["Normal"]),
            Paragraph(f'<font size="16" color="#00d68f"><b>{hab_disponibles}</b></font>', styles["Normal"]),
            Paragraph(f'<font size="16" color="#ff6b6b"><b>{hab_mantenimiento}</b></font>', styles["Normal"]),
            Paragraph(f'<font size="16" color="#6c5ce7"><b>{total_mant_periodo}</b></font>', styles["Normal"]),
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[125, 125, 125, 135])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), gris_claro),
        ('BOX', (0, 0), (-1, -1), 1, gris_borde),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, gris_borde),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    contenido.append(kpi_table)
    contenido.append(Spacer(1, 8))

    # KPI financieros
    kpi_fin_data = [
        [
            Paragraph('<font size="8" color="#636e72">COSTO TOTAL DEL PERÍODO</font>', styles["Normal"]),
            Paragraph('<font size="8" color="#636e72">COSTO PROMEDIO POR MANTENIMIENTO</font>', styles["Normal"]),
            Paragraph('<font size="8" color="#636e72">INSPECCIONES REALIZADAS</font>', styles["Normal"]),
        ],
        [
            Paragraph(f'<font size="16" color="#e17055"><b>${float(costo_total_periodo):,.2f}</b></font>', styles["Normal"]),
            Paragraph(f'<font size="16" color="#fdcb6e"><b>${costo_promedio_periodo:,.2f}</b></font>', styles["Normal"]),
            Paragraph(f'<font size="16" color="#00cec9"><b>{len(inspecciones_periodo)}</b></font>', styles["Normal"]),
        ]
    ]
    kpi_fin_table = Table(kpi_fin_data, colWidths=[170, 170, 170])
    kpi_fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), gris_claro),
        ('BOX', (0, 0), (-1, -1), 1, gris_borde),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, gris_borde),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    contenido.append(kpi_fin_table)
    contenido.append(Spacer(1, 22))

    # ── TABLA DE MANTENIMIENTOS ──
    contenido.append(Paragraph('<font size="12" color="#6c5ce7"><b>DETALLE DE MANTENIMIENTOS</b></font>', styles["Normal"]))
    contenido.append(Spacer(1, 4))
    contenido.append(Paragraph(f'<font size="8" color="#636e72">{total_mant_periodo} registros encontrados en el período</font>', styles["Normal"]))
    contenido.append(Spacer(1, 10))

    if mantenimientos_periodo:
        mant_header = ['Hab.', 'Fecha', 'Elemento', 'Descripción', 'Técnico', 'Prioridad', 'Costo']
        mant_rows = [mant_header]
        for m in mantenimientos_periodo:
            desc = (m[4] or '')[:30] + ('...' if m[4] and len(m[4]) > 30 else '')
            mant_rows.append([
                f'#{m[0]}', m[1] or '-', (m[3] or '-')[:18], desc or '-',
                (m[5] or '-')[:12], m[8] or 'Media',
                f'${float(m[7]):,.2f}' if m[7] else '$0.00'
            ])

        mant_table = Table(mant_rows, colWidths=[40, 65, 72, 110, 62, 55, 55], repeatRows=1)
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), azul_acento),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7.5),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BOX', (0, 0), (-1, -1), 1, gris_borde),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, gris_borde),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, gris_claro]),
        ]
        for i, m in enumerate(mantenimientos_periodo, start=1):
            pri = (m[8] or '').lower()
            if 'crítica' in pri or 'critica' in pri:
                table_style.append(('TEXTCOLOR', (5, i), (5, i), rojo))
            elif 'alta' in pri:
                table_style.append(('TEXTCOLOR', (5, i), (5, i), colors.HexColor("#e17055")))
        mant_table.setStyle(TableStyle(table_style))
        contenido.append(mant_table)
    else:
        contenido.append(Paragraph('<font size="9" color="#636e72"><i>No se encontraron mantenimientos en este período.</i></font>', styles["Normal"]))

    contenido.append(Spacer(1, 22))

    # ── TOP 5 MÁS COSTOSAS ──
    if top_costosas:
        contenido.append(Paragraph('<font size="12" color="#6c5ce7"><b>TOP 5 HABITACIONES MÁS COSTOSAS</b></font>', styles["Normal"]))
        contenido.append(Spacer(1, 10))
        cost_rows = [['#', 'Habitación', 'Cantidad de Fallas', 'Costo Total']]
        for idx, c in enumerate(top_costosas, start=1):
            cost_rows.append([str(idx), f'Hab. #{c[0]}', str(c[1]), f'${float(c[2]):,.2f}'])
        cost_table = Table(cost_rows, colWidths=[30, 150, 120, 120])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e17055")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('BOX', (0, 0), (-1, -1), 1, gris_borde),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, gris_borde),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, gris_claro]),
        ]))
        contenido.append(cost_table)
        contenido.append(Spacer(1, 22))

    # ── FALLAS POR ELEMENTO ──
    if fallas_por_elemento:
        contenido.append(Paragraph('<font size="12" color="#6c5ce7"><b>ANÁLISIS POR TIPO DE FALLA</b></font>', styles["Normal"]))
        contenido.append(Spacer(1, 10))
        elem_rows = [['Elemento', 'Ocurrencias', 'Costo Total']]
        for fe in fallas_por_elemento:
            elem_rows.append([fe[0], str(fe[1]), f'${float(fe[2]):,.2f}'])
        elem_table = Table(elem_rows, colWidths=[200, 100, 120])
        elem_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00cec9")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, gris_borde),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, gris_borde),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, gris_claro]),
        ]))
        contenido.append(elem_table)
        contenido.append(Spacer(1, 22))

    # ── INSPECCIONES ──
    contenido.append(Paragraph('<font size="12" color="#6c5ce7"><b>INSPECCIONES REALIZADAS</b></font>', styles["Normal"]))
    contenido.append(Spacer(1, 4))
    contenido.append(Paragraph(f'<font size="8" color="#636e72">{len(inspecciones_periodo)} inspecciones en el período</font>', styles["Normal"]))
    contenido.append(Spacer(1, 10))

    if inspecciones_periodo:
        insp_rows = [['Habitación', 'Empleado', 'Fecha', 'Observaciones', 'Generó Mant.']]
        for insp in inspecciones_periodo:
            obs = (insp[3] or '')[:35] + ('...' if insp[3] and len(insp[3]) > 35 else '')
            insp_rows.append([
                f'#{insp[0]}', insp[1] or '-',
                str(insp[2]) if insp[2] else '-', obs or '-', insp[4]
            ])
        insp_table = Table(insp_rows, colWidths=[60, 80, 70, 180, 70])
        insp_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00b894")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7.5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, gris_borde),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, gris_borde),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, gris_claro]),
        ]
        for i, insp in enumerate(inspecciones_periodo, start=1):
            if insp[4] == 'Si':
                insp_style.append(('TEXTCOLOR', (4, i), (4, i), rojo))
                insp_style.append(('FONTNAME', (4, i), (4, i), 'Helvetica-Bold'))
        insp_table.setStyle(TableStyle(insp_style))
        contenido.append(insp_table)
    else:
        contenido.append(Paragraph('<font size="9" color="#636e72"><i>No se encontraron inspecciones en este período.</i></font>', styles["Normal"]))

    contenido.append(Spacer(1, 30))

    # ── PIE DE PÁGINA ──
    contenido.append(HRFlowable(width="100%", thickness=1, color=gris_borde))
    contenido.append(Spacer(1, 8))
    contenido.append(Paragraph(
        f'<font size="7" color="#b2bec3">'
        f'Este reporte fue generado automáticamente por el Sistema de Mantenimiento Hotelero. '
        f'Período: {fecha_inicio} al {fecha_fin}. '
        f'Documento confidencial para uso interno.</font>',
        styles["Normal"]
    ))

    doc.build(contenido)

    nombre_archivo = f"Reporte_Hotel_{fecha_inicio}_a_{fecha_fin}.pdf"
    return send_file(pdf_path, as_attachment=True, download_name=nombre_archivo)
