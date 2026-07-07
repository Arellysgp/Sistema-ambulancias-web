# backend/routes/reportes.py
# Generación de PDF — Sistema SAMU

from flask import Blueprint, jsonify, request, make_response, session
from datetime import datetime, timedelta
import io

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle,
        Paragraph, Spacer, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.graphics.charts.lineplots import LinePlot
    from reportlab.graphics.charts.textlabels import Label
    from reportlab.graphics.widgets.markers import makeMarker
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

# ── Imports del proyecto ─────────────────────────────────────
from database.models.emergencia import Emergencia
from database.models.user import User

reportes_bp = Blueprint('reportes', __name__)

# ── Paleta SAMU ──────────────────────────────────────────────
ROJO     = colors.HexColor('#D0342C')  if REPORTLAB_OK else None
ROJO_OSC = colors.HexColor('#A0251F')  if REPORTLAB_OK else None
OSCURO   = colors.HexColor('#1A1410')  if REPORTLAB_OK else None
CREMA    = colors.HexColor('#FAF8F5')  if REPORTLAB_OK else None
GRIS_BRD = colors.HexColor('#E8E4E0')  if REPORTLAB_OK else None
BLANCO   = colors.white                if REPORTLAB_OK else None
VERDE    = colors.HexColor('#27AE60')  if REPORTLAB_OK else None
AMARILLO = colors.HexColor('#F39C12')  if REPORTLAB_OK else None
AZUL     = colors.HexColor('#3498DB')  if REPORTLAB_OK else None


# ── Auth helpers ─────────────────────────────────────────────
def _get_user_id():
    return (session.get('user_id') 
            or request.headers.get('X-User-Id')
            or request.args.get('user_id'))

def _require_auth():
    if not _get_user_id():
        return jsonify({'error': 'No autorizado'}), 401
    return None


# ── Estilos PDF ──────────────────────────────────────────────
def _estilos():
    return {
        'h_inst': ParagraphStyle('hi', fontSize=11, fontName='Helvetica-Bold',
                                  textColor=BLANCO),
        'h_date': ParagraphStyle('hd', fontSize=8, fontName='Helvetica',
                                  textColor=BLANCO, alignment=TA_RIGHT),
        'titulo': ParagraphStyle('tr', fontSize=16, fontName='Helvetica-Bold',
                                  textColor=OSCURO, alignment=TA_CENTER, spaceAfter=4),
        'subtit': ParagraphStyle('sr', fontSize=10, fontName='Helvetica',
                                  textColor=colors.HexColor('#6B6560'),
                                  alignment=TA_CENTER, spaceAfter=4),
        'seccion':ParagraphStyle('sec', fontSize=11, fontName='Helvetica-Bold',
                                  textColor=ROJO, spaceBefore=10, spaceAfter=4),
        'pie':    ParagraphStyle('pie', fontSize=7, fontName='Helvetica',
                                  textColor=colors.HexColor('#6B6560'),
                                  alignment=TA_CENTER),
    }

def _header(elements, estilos, titulo, subtitulo=''):
    data = [[
        Paragraph('<font color="#FFFFFF"><b>SAMU - SISTEMA DE AMBULANCIAS</b></font>', estilos['h_inst']),
        Paragraph(f'<font color="#FFFFFF">{datetime.now().strftime("%d/%m/%Y  %H:%M")}</font>', estilos['h_date']),
    ]]
    t = Table(data, colWidths=[13*cm, 5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor('#2C3E50')), # Elegante gris azulado oscuro
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('RIGHTPADDING',  (0,0), (-1,-1), 12),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS',[3, 3, 3, 3]), # Si lo soporta, aunque reportlab Table no soporta esto directamente sin canvas. Lo omitimos.
    ]))
    elements.append(t)
    elements.append(Spacer(1, .6*cm))
    elements.append(Paragraph(f'<font color="#2C3E50">{titulo}</font>', estilos['titulo']))
    if subtitulo:
        elements.append(Paragraph(f'<font color="#7F8C8D">{subtitulo}</font>', estilos['subtit']))
    elements.append(Spacer(1, .2*cm))
    elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#ECF0F1')))
    elements.append(Spacer(1, .6*cm))

def _tabla_style():
    return TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#F8F9FA')),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.HexColor('#2C3E50')),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,0), 8),
        ('ALIGN',         (0,0), (-1,0), 'LEFT'),
        ('TOPPADDING',    (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('LINEBELOW',     (0,0), (-1,0), 1.5, colors.HexColor('#BDC3C7')), # Línea más fuerte bajo el header
        ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,1), (-1,-1), 8),
        ('TEXTCOLOR',     (0,1), (-1,-1), colors.HexColor('#34495E')),
        ('ALIGN',         (0,1), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,1), (-1,-1), 8),
        ('BOTTOMPADDING', (0,1), (-1,-1), 8),
        ('LINEBELOW',     (0,1), (-1,-1), 0.5, colors.HexColor('#ECF0F1')), # Solo líneas horizontales sutiles
    ])

def _pie_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.HexColor('#6B6560'))
    canvas.drawCentredString(
        A4[0]/2, 1.5*cm,
        f'SAMU - Sistema de Ambulancias  |  '
        f'Generado el {datetime.now().strftime("%d/%m/%Y a las %H:%M")}  |  Pagina {doc.page}'
    )
    canvas.setStrokeColor(GRIS_BRD)
    canvas.setLineWidth(.5)
    canvas.line(2*cm, 1.8*cm, A4[0]-2*cm, 1.8*cm)
    canvas.restoreState()

def _color_estado(estado):
    return {
        'atendida':  colors.HexColor('#EAFAF1'),
        'pendiente': colors.HexColor('#FEF9E7'),
        'en_camino': colors.HexColor('#EAF4FE'),
        'cancelado': colors.HexColor('#FDECEA'),
        'cancelada': colors.HexColor('#FDECEA'),
    }.get(estado)



#  RUTA 1 — PDF de emergencias (reporte general)

@reportes_bp.route('/api/reportes/servicios/pdf', methods=['GET'])
def reporte_servicios_pdf():
    err = _require_auth()
    if err: return err
    if not REPORTLAB_OK:
        return jsonify({'error': 'Instala reportlab: pip install reportlab'}), 500

    query = Emergencia.query.order_by(Emergencia.fecha_registro.desc())

    estado    = request.args.get('estado')
    prioridad = request.args.get('prioridad')
    fecha_ini = request.args.get('fecha_ini')
    fecha_fin = request.args.get('fecha_fin')

    if estado:    query = query.filter(Emergencia.estado == estado)
    if prioridad: query = query.filter(Emergencia.prioridad == int(prioridad))
    if fecha_ini:
        query = query.filter(Emergencia.fecha_registro >= datetime.fromisoformat(fecha_ini))
    if fecha_fin:
        # Extender fecha_fin hasta el final del dia
        fecha_fin_dt = datetime.fromisoformat(fecha_fin).replace(hour=23, minute=59, second=59)
        query = query.filter(Emergencia.fecha_registro <= fecha_fin_dt)

    emergencias = query.limit(300).all()
    total      = len(emergencias)
    atendidas  = sum(1 for e in emergencias if e.estado == 'atendida')
    pendientes = sum(1 for e in emergencias if e.estado == 'pendiente')
    canceladas = sum(1 for e in emergencias if e.estado in ('cancelado', 'cancelada'))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm,  bottomMargin=2.5*cm)
    estilos = _estilos()
    elems   = []

    _header(elems, estilos, 'REPORTE DE EMERGENCIAS',
            f'Total: {total}  |  Atendidas: {atendidas}  |  '
            f'Pendientes: {pendientes}  |  Canceladas: {canceladas}')

    PRIO = {1: 'P1 - Vital', 2: 'P2 - Urgente', 3: 'P3 - Normal'}
    EST  = {'atendida': 'Atendida', 'pendiente': 'Pendiente',
            'en_camino': 'En camino', 'cancelado': 'Cancelado', 'cancelada': 'Cancelada'}

    cols = ['#', 'Fecha', 'Paciente', 'Edad', 'Direccion', 'Prioridad', 'Estado', 'Descripcion']
    cw   = [.8*cm, 3*cm, 3.5*cm, 1.5*cm, 5*cm, 3*cm, 2.5*cm, 4.7*cm]

    filas = [cols]
    for i, e in enumerate(emergencias, 1):
        filas.append([
            str(i),
            e.fecha_registro.strftime('%d/%m/%Y\n%H:%M') if e.fecha_registro else '-',
            e.nombre_paciente or '-',
            str(e.edad) if e.edad else '-',
            (e.direccion or '-')[:45],
            PRIO.get(e.prioridad, str(e.prioridad or '-')),
            EST.get(e.estado, e.estado or '-'),
            (e.descripcion or '-')[:50],
        ])

    tabla = Table(filas, colWidths=cw, repeatRows=1)
    ts = _tabla_style()
    for idx, e in enumerate(emergencias, 1):
        c = _color_estado(e.estado)
        if c: ts.add('BACKGROUND', (6, idx), (6, idx), c)
    tabla.setStyle(ts)
    elems.append(tabla)
    elems.append(Spacer(1, .5*cm))
    elems.append(Paragraph(
        f'* Reporte generado el {datetime.now().strftime("%d/%m/%Y a las %H:%M")}',
        estilos['pie']))

    doc.build(elems, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers['Content-Type']        = 'application/pdf'
    resp.headers['Content-Disposition'] = \
        f'attachment; filename=reporte_emergencias_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    return resp


#  RUTA 2 — PDF individual por conductor

@reportes_bp.route('/api/reportes/conductor/<int:conductor_id>/pdf', methods=['GET'])
def reporte_conductor_pdf(conductor_id):
    err = _require_auth()
    if err: return err
    if not REPORTLAB_OK:
        return jsonify({'error': 'Instala reportlab: pip install reportlab'}), 500

    conductor   = User.query.get_or_404(conductor_id)
    emergencias = (Emergencia.query
                   .filter_by(conductor_id=conductor_id)
                   .order_by(Emergencia.fecha_registro.desc())
                   .all())

    total     = len(emergencias)
    atendidas = sum(1 for e in emergencias if e.estado == 'atendida')
    pct       = round(atendidas / total * 100, 1) if total else 0

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm,  bottomMargin=2.5*cm)
    estilos = _estilos()
    elems   = []

    _header(elems, estilos,
            'REPORTE DEL CONDUCTOR',
            f'{conductor.nombre}  -  {conductor.email}')

    # ── Ficha ────────────────────────────────────────────────
    from reportlab.platypus import TableStyle as TS
    from reportlab.lib.colors import HexColor

    elems.append(Paragraph('DATOS DEL CONDUCTOR', estilos['seccion']))
    info = [
        ['Nombre completo', conductor.nombre or '-', 'Email',  conductor.email or '-'],
        ['Rol',    (conductor.rol or '-').capitalize(), 'Estado', 'Activo' if conductor.activo else 'Inactivo'],
    ]
    t_info = Table(info, colWidths=[4*cm, 4.5*cm, 4*cm, 4.5*cm])
    t_info.setStyle(TS([
        ('FONTNAME',      (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME',      (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',      (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('TEXTCOLOR',     (0,0), (-1,-1), HexColor('#333333')),
        ('BACKGROUND',    (0,0), (-1,-1), BLANCO),
        ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('GRID',          (0,0), (-1,-1), 0.5, HexColor('#E0E0E0')),
        ('BOX',           (0,0), (-1,-1), 1, HexColor('#BDBDBD')),
    ]))
    elems.append(t_info)
    elems.append(Spacer(1, 0.6*cm))

    # ── KPIs ─────────────────────────────────────────────────
    elems.append(Paragraph('ESTADÍSTICAS DE RENDIMIENTO', estilos['seccion']))
    kpis = [[
        Paragraph(f'<font size="24" color="#1A1410"><b>{total}</b></font><br/>'
                  f'<font size="8" color="#666666">Emergencias totales</font>', estilos['pie']),
        Paragraph(f'<font size="24" color="#1A1410"><b>{atendidas}</b></font><br/>'
                  f'<font size="8" color="#666666">Atendidas</font>', estilos['pie']),
        Paragraph(f'<font size="24" color="#1A1410"><b>{total - atendidas}</b></font><br/>'
                  f'<font size="8" color="#666666">Pendientes / Canceladas</font>', estilos['pie']),
        Paragraph(f'<font size="24" color="#1A1410"><b>{pct}%</b></font><br/>'
                  f'<font size="8" color="#666666">Tasa de atención</font>', estilos['pie']),
    ]]
    t_kpi = Table(kpis, colWidths=[4.25*cm]*4)
    t_kpi.setStyle(TS([
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 15),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('BACKGROUND',    (0,0), (-1,-1), BLANCO),
        ('BOX',           (0,0), (0,0), 1, HexColor('#E0E0E0')),
        ('BOX',           (1,0), (1,0), 1, HexColor('#E0E0E0')),
        ('BOX',           (2,0), (2,0), 1, HexColor('#E0E0E0')),
        ('BOX',           (3,0), (3,0), 1, HexColor('#E0E0E0')),
    ]))
    elems.append(t_kpi)
    elems.append(Spacer(1, 0.6*cm))



    # ── Historial ────────────────────────────────────────────
    elems.append(Paragraph('HISTORIAL DE EMERGENCIAS', estilos['seccion']))
    if not emergencias:
        empty = [[Paragraph('<font size="12" color="#999999">No se encontraron registros de emergencias</font><br/><font size="8" color="#BBBBBB">No hay datos para mostrar en este historial.</font>', estilos['pie'])]]
        t_empty = Table(empty, colWidths=[17*cm], rowHeights=[3*cm])
        t_empty.setStyle(TS([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (0,0), (-1,-1), 1, HexColor('#E0E0E0')),
            ('BACKGROUND', (0,0), (-1,-1), HexColor('#F9F9F9')),
        ]))
        elems.append(t_empty)
    else:
        PRIO  = {1: 'P1 - Vital', 2: 'P2 - Urgente', 3: 'P3 - Normal'}
        EST   = {'atendida': 'Atendida', 'pendiente': 'Pendiente',
                 'en_camino': 'En camino', 'cancelado': 'Cancelado'}
        cols2 = ['#', 'Fecha', 'Paciente', 'Edad', 'Dirección', 'Prioridad', 'Estado']
        cw2   = [.8*cm, 3*cm, 3.5*cm, 1.5*cm, 5*cm, 2.5*cm, 2.5*cm]
        filas2 = [cols2]
        for i, e in enumerate(emergencias, 1):
            filas2.append([
                str(i),
                e.fecha_registro.strftime('%d/%m/%Y\n%H:%M') if e.fecha_registro else '-',
                e.nombre_paciente or '-',
                str(e.edad) if e.edad else '-',
                (e.direccion or '-')[:45],
                PRIO.get(e.prioridad, str(e.prioridad or '-')),
                EST.get(e.estado, e.estado or '-'),
            ])
        tabla2 = Table(filas2, colWidths=cw2, repeatRows=1)
        ts2 = _tabla_style()
        for idx, e in enumerate(emergencias, 1):
            c = _color_estado(e.estado)
            if c: ts2.add('BACKGROUND', (6, idx), (6, idx), c)
        tabla2.setStyle(ts2)
        elems.append(tabla2)
        
    elems.append(Spacer(1, 1.5*cm))

    # ── FOOTER ───────────────────────────────────────────────
    footer_data = [[
        Paragraph(f'<font size="7" color="#999999">Reporte generado el<br/><b>{datetime.now().strftime("%d/%m/%Y a las %H:%M")}</b></font>', estilos['pie']),
        Paragraph('<font size="7" color="#999999">Este documento es confidencial y de<br/>uso exclusivo del Sistema SAMU.</font>', estilos['pie'])
    ]]
    t_footer = Table(footer_data, colWidths=[8.5*cm, 8.5*cm])
    t_footer.setStyle(TS([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elems.append(t_footer)

    doc.build(elems)
    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers['Content-Type']        = 'application/pdf'
    resp.headers['Content-Disposition'] = \
        f'attachment; filename=reporte_conductor_{conductor_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
    return resp