"""Views for reports app."""
from io import BytesIO

from django.http import HttpResponse
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# ReportLab is optional — only needed for PDF generation
try:
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from scanner.models import Scan
from .models import ExecutiveSummary
from .serializers import ExecutiveSummarySerializer


def _build_pdf_with_reportlab(scan, findings, summary_content):
    """Build a styled PDF using ReportLab (cross-platform, always available)."""
    def _clean(text):
        return (str(text or '')).replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')

    def _severity_color(severity):
        mapping = {
            'CRITICAL': rl_colors.HexColor('#7c3aed'),
            'HIGH': rl_colors.HexColor('#dc2626'),
            'MEDIUM': rl_colors.HexColor('#d97706'),
            'LOW': rl_colors.HexColor('#2563eb'),
            'INFO': rl_colors.HexColor('#475569'),
        }
        return mapping.get((severity or '').upper(), rl_colors.HexColor('#334155'))

    findings_list = list(findings)

    stats = {
        'total': len(findings_list),
        'critical': sum(1 for f in findings_list if f.severity == 'CRITICAL'),
        'high': sum(1 for f in findings_list if f.severity == 'HIGH'),
        'medium': sum(1 for f in findings_list if f.severity == 'MEDIUM'),
        'low': sum(1 for f in findings_list if f.severity == 'LOW'),
    }

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title=f'Reporte Scan {scan.pk}',
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'VigiaTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=rl_colors.white,
        leading=24,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'VigiaSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=rl_colors.HexColor('#bfdbfe'),
        leading=12,
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=rl_colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'BodyCopy',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=rl_colors.HexColor('#1f2937'),
    )
    header_finding_style = ParagraphStyle(
        'FindingHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=rl_colors.white,
        leading=11,
    )
    thin_border = rl_colors.HexColor('#cbd5e1')

    story = []

    header_table = Table(
        [[
            Paragraph('Reporte de Auditoria Web', title_style),
            Paragraph('VIGIA', subtitle_style),
        ]],
        colWidths=[5.6 * inch, 1.0 * inch],
    )
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), rl_colors.HexColor('#1d4ed8')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(header_table)

    scan_date = scan.started_at.strftime('%d/%m/%Y %H:%M') if scan.started_at else '-'
    metadata = [
        [Paragraph('<b>Scan ID</b>', body_style), Paragraph(_clean(scan.pk), body_style)],
        [Paragraph('<b>URL</b>', body_style), Paragraph(_clean(scan.url_asset.url if scan.url_asset else '-'), body_style)],
        [Paragraph('<b>Estado</b>', body_style), Paragraph(_clean(scan.status), body_style)],
        [Paragraph('<b>Fecha</b>', body_style), Paragraph(scan_date, body_style)],
    ]
    meta_table = Table(metadata, colWidths=[1.0 * inch, 5.6 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), rl_colors.HexColor('#eff6ff')),
        ('GRID', (0, 0), (-1, -1), 0.4, rl_colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph('Resumen de Hallazgos', section_title_style))
    stat_row = [[
        Paragraph('<b>Total</b><br/><font size="14">{}</font>'.format(stats['total']), body_style),
        Paragraph('<b>Critico</b><br/><font size="14">{}</font>'.format(stats['critical']), body_style),
        Paragraph('<b>Alto</b><br/><font size="14">{}</font>'.format(stats['high']), body_style),
        Paragraph('<b>Medio</b><br/><font size="14">{}</font>'.format(stats['medium']), body_style),
        Paragraph('<b>Bajo</b><br/><font size="14">{}</font>'.format(stats['low']), body_style),
    ]]
    stats_table = Table(stat_row, colWidths=[1.3 * inch] * 5)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), rl_colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (1, 0), (1, 0), rl_colors.HexColor('#ede9fe')),
        ('BACKGROUND', (2, 0), (2, 0), rl_colors.HexColor('#fee2e2')),
        ('BACKGROUND', (3, 0), (3, 0), rl_colors.HexColor('#fef3c7')),
        ('BACKGROUND', (4, 0), (4, 0), rl_colors.HexColor('#dbeafe')),
        ('BOX', (0, 0), (-1, -1), 0.5, rl_colors.HexColor('#94a3b8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, rl_colors.HexColor('#cbd5e1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 12))

    if summary_content:
        story.append(Paragraph('Resumen Ejecutivo', section_title_style))
        summary_text = _clean(summary_content)
        if len(summary_text) > 4000:
            summary_text = summary_text[:4000] + '...'
        for part in summary_text.split('\n'):
            part = part.strip()
            if not part:
                continue
            story.append(Paragraph(part, body_style))
            story.append(Spacer(1, 3))
        story.append(Spacer(1, 8))

    story.append(Paragraph('Hallazgos Tecnicos', section_title_style))
    # Table: Severity | Title | Category | Description | Recommendation | Evidence
    findings_header = [
        Paragraph('<b>Sev.</b>', header_finding_style),
        Paragraph('<b>Titulo</b>', header_finding_style),
        Paragraph('<b>Categoria</b>', header_finding_style),
        Paragraph('<b>Descripcion</b>', header_finding_style),
        Paragraph('<b>Recomendacion</b>', header_finding_style),
        Paragraph('<b>Evidencia</b>', header_finding_style),
    ]
    findings_data = [findings_header]

    for finding in findings_list:
        findings_data.append([
            Paragraph(_clean(finding.severity or '-'), body_style),
            Paragraph(_clean(finding.title or '-'), body_style),
            Paragraph(_clean(finding.category or '-'), body_style),
            Paragraph(_clean(finding.description or '-'), body_style),
            Paragraph(_clean(finding.recommendation or '-'), body_style),
            Paragraph(_clean(finding.evidence or '-'), body_style),
        ])

    if len(findings_data) == 1:
        findings_data.append([
            Paragraph('INFO', body_style),
            Paragraph('Sin hallazgos detectados', body_style),
            Paragraph('-', body_style),
            Paragraph('No se encontraron vulnerabilidades en este escaneo.', body_style),
            Paragraph('Mantener monitoreo continuo.', body_style),
            Paragraph('-', body_style),
        ])

    col_widths = [0.55 * inch, 1.4 * inch, 0.8 * inch, 1.4 * inch, 1.4 * inch, 1.1 * inch]
    findings_table = Table(findings_data, colWidths=col_widths, repeatRows=1)
    table_style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
        ('GRID', (0, 0), (-1, -1), 0.3, thin_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    for row_idx, finding in enumerate(findings_list, start=1):
        stripe = rl_colors.HexColor('#f8fafc') if row_idx % 2 else rl_colors.white
        table_style_cmds.append(('BACKGROUND', (1, row_idx), (-1, row_idx), stripe))
        table_style_cmds.append(('BACKGROUND', (0, row_idx), (0, row_idx), _severity_color(finding.severity)))
        table_style_cmds.append(('TEXTCOLOR', (0, row_idx), (0, row_idx), rl_colors.white))

    findings_table.setStyle(TableStyle(table_style_cmds))
    story.append(findings_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph('Generado por Vigia', ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        alignment=1,
        fontSize=8,
        textColor=rl_colors.HexColor('#64748b'),
    )))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _build_report_file_response(scan, fmt):
    """Return a file response for report download in requested format."""
    findings = scan.findings.all()

    summary_content = ''
    try:
        summary_content = scan.executive_summary.content
    except ExecutiveSummary.DoesNotExist:
        pass

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte de Auditoría - {scan.url_asset.url}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #1a1a2e; }}
        h1 {{ color: #16213e; border-bottom: 3px solid #0f3460; padding-bottom: 10px; }}
        h2 {{ color: #0f3460; margin-top: 30px; }}
        .meta {{ background: #f0f4f8; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ padding: 15px 25px; border-radius: 8px; text-align: center; color: white; }}
        .stat.critical {{ background: #8b5cf6; }}
        .stat.high {{ background: #e74c3c; }}
        .stat.medium {{ background: #f39c12; }}
        .stat.low {{ background: #3498db; }}
        .finding {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; border-left: 4px solid; }}
        .finding.CRITICAL {{ border-left-color: #8b5cf6; }}
        .finding.HIGH {{ border-left-color: #e74c3c; }}
        .finding.MEDIUM {{ border-left-color: #f39c12; }}
        .finding.LOW {{ border-left-color: #3498db; }}
        .finding.INFO {{ border-left-color: #95a5a6; }}
        .severity {{ display: inline-block; padding: 2px 8px; border-radius: 4px; color: white; font-size: 12px; }}
        .severity.CRITICAL {{ background: #8b5cf6; }}
        .severity.HIGH {{ background: #e74c3c; }}
        .severity.MEDIUM {{ background: #f39c12; }}
        .severity.LOW {{ background: #3498db; }}
        .severity.INFO {{ background: #95a5a6; }}
        .executive {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #0f3460; }}
        @media print {{ body {{ margin: 20px; }} }}
    </style>
</head>
<body>
    <h1>🔒 Reporte de Auditoría Web</h1>
    <div class="meta">
        <strong>URL:</strong> {scan.url_asset.url}<br>
        <strong>Fecha:</strong> {scan.started_at.strftime('%d/%m/%Y %H:%M')}<br>
        <strong>Estado:</strong> {scan.status}
    </div>

    <h2>📊 Resumen de Hallazgos</h2>
    <div class="stats">
        <div class="stat critical">Crítico: {findings.filter(severity='CRITICAL').count()}</div>
        <div class="stat high">Alto: {findings.filter(severity='HIGH').count()}</div>
        <div class="stat medium">Medio: {findings.filter(severity='MEDIUM').count()}</div>
        <div class="stat low">Bajo: {findings.filter(severity='LOW').count()}</div>
    </div>

    {"<h2>📋 Resumen Ejecutivo</h2><div class='executive'>" + summary_content + "</div>" if summary_content else ""}

    <h2>🔍 Hallazgos Técnicos</h2>
    {"".join([f'''
    <div class="finding {f.severity}">
        <h3><span class="severity {f.severity}">{f.severity}</span> {f.title}</h3>
        <p><strong>Categoría:</strong> {f.category}</p>
        <p>{f.description}</p>
        <p><strong>Recomendación:</strong> {f.recommendation}</p>
        {"<p><strong>Evidencia:</strong> " + f.evidence + "</p>" if f.evidence else ""}
    </div>''' for f in findings])}

    <hr>
    <p style="text-align:center; color:#999;">Generado por Auditoría Web Automatizada para PYMES</p>
</body>
</html>"""

    if fmt in ('excel', 'xlsx'):
        workbook = Workbook()

        # --- Styles ---
        header_font = Font(bold=True, size=11, color='FFFFFF')
        header_fill = PatternFill(start_color='1E293B', end_color='1E293B', fill_type='solid')
        header_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell_align = Alignment(vertical='top', wrap_text=True)
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1'),
        )
        url_font = Font(color='2563EB', underline='single')

        def style_header(ws, row_num, col_count):
            for col in range(1, col_count + 1):
                cell = ws.cell(row=row_num, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_align
                cell.border = thin_border

        def style_data_cell(cell):
            cell.alignment = cell_align
            cell.border = thin_border

        def auto_width(ws, min_width=10, max_width=55):
            for col_cells in ws.columns:
                col_letter = get_column_letter(col_cells[0].column)
                max_len = 0
                for cell in col_cells:
                    val = str(cell.value or '')
                    max_len = max(max_len, min(len(val), max_width))
                ws.column_dimensions[col_letter].width = max(max_len + 2, min_width)

        # --- Hoja 1: Resumen ---
        summary_ws = workbook.active
        summary_ws.title = 'Resumen'
        summary_ws.append(['Campo', 'Valor'])
        style_header(summary_ws, 1, 2)

        scan_date_str = scan.started_at.strftime('%d/%m/%Y %H:%M') if scan.started_at else '-'
        scan_url = scan.url_asset.url if scan.url_asset else '-'
        summary_rows = [
            ['Scan ID', scan.pk],
            ['URL', scan_url],
            ['Estado', scan.status],
            ['Fecha inicio', scan_date_str],
            ['Fecha fin', scan.finished_at.strftime('%d/%m/%Y %H:%M') if scan.finished_at else '-'],
            ['Total hallazgos', findings.count()],
            ['Criticos', findings.filter(severity='CRITICAL').count()],
            ['Altos', findings.filter(severity='HIGH').count()],
            ['Medios', findings.filter(severity='MEDIUM').count()],
            ['Bajos', findings.filter(severity='LOW').count()],
            ['Info', findings.filter(severity='INFO').count()],
        ]
        for row in summary_rows:
            summary_ws.append(row)
            current_row = summary_ws.max_row
            for cell in summary_ws[current_row]:
                style_data_cell(cell)
            if row[0] == 'URL':
                summary_ws.cell(row=current_row, column=2).font = url_font
        auto_width(summary_ws)

        # --- Hoja 2: Hallazgos (con detalle completo) ---
        findings_ws = workbook.create_sheet(title='Hallazgos')
        findings_headers = [
            'ID', 'URL', 'Fecha Escaneo', 'Titulo', 'Severidad',
            'Categoria', 'Descripcion', 'Recomendacion', 'Evidencia',
        ]
        findings_ws.append(findings_headers)
        style_header(findings_ws, 1, len(findings_headers))

        for finding in findings:
            row_data = [
                finding.pk,
                scan_url,
                scan_date_str,
                finding.title or '',
                finding.severity or '',
                finding.category or '',
                finding.description or '',
                finding.recommendation or '',
                finding.evidence or '',
            ]
            findings_ws.append(row_data)
            for cell in findings_ws[findings_ws.max_row]:
                style_data_cell(cell)

        auto_width(findings_ws)

        # --- Hoja 3: Resumen Ejecutivo (si existe) ---
        if summary_content:
            executive_ws = workbook.create_sheet(title='Resumen Ejecutivo')
            executive_ws.append(['Contenido del Resumen Ejecutivo'])
            executive_ws.merge_cells('A1:B1')
            style_header(executive_ws, 1, 1)
            executive_ws.append([summary_content])
            executive_ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=2)
            cell = executive_ws.cell(row=2, column=1)
            cell.alignment = Alignment(vertical='top', wrap_text=True)
            executive_ws.column_dimensions['A'].width = 80

        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="reporte_scan_{scan.pk}.xlsx"'
        return response

    if fmt == 'pdf':
        # Try WeasyPrint first (produces nicer PDF with CSS), fall back to ReportLab
        weasyprint_error = None
        try:
            from weasyprint import HTML

            pdf = HTML(string=html_content).write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_scan_{scan.pk}.pdf"'
            return response
        except Exception as exc:
            weasyprint_error = str(exc)

        if REPORTLAB_AVAILABLE:
            try:
                pdf = _build_pdf_with_reportlab(scan, findings, summary_content)
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="reporte_scan_{scan.pk}.pdf"'
                return response
            except Exception as fallback_exc:
                return Response(
                    {
                        'detail': f'No se pudo generar el PDF. WeasyPrint: {weasyprint_error}. ReportLab: {fallback_exc}',
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            return Response(
                {
                    'detail': (
                        'No se pudo generar el PDF. Instala WeasyPrint o ReportLab en el servidor. '
                        f'WeasyPrint error: {weasyprint_error}. ReportLab no esta instalado.'
                    ),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return Response(
        {'detail': 'Formato no soportado. Usa format=excel o format=pdf.'},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def report_detail(request, scan_id):
    """Get full report (technical + executive) for a scan."""
    access_filter = Q(url_asset__organization_id=request.user.organization_id)
    access_filter |= Q(created_by=request.user)

    try:
        scan = Scan.objects.select_related(
            'url_asset', 'url_asset__organization'
        ).prefetch_related('findings').filter(
            access_filter,
        ).get(
            pk=scan_id,
        )
    except Scan.DoesNotExist:
        if Scan.objects.filter(pk=scan_id).exists():
            return Response(
                {'detail': 'No tienes permiso para ver este reporte.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response({'detail': 'Scan not found.'}, status=404)

    # Get executive summary if available
    summary = None
    try:
        summary = ExecutiveSummarySerializer(scan.executive_summary).data
    except ExecutiveSummary.DoesNotExist:
        pass

    findings = scan.findings.all()

    download_flag = (request.query_params.get('download') or '').lower()
    fmt = (request.query_params.get('format') or '').lower()
    if download_flag in {'1', 'true', 'yes'} and fmt:
        return _build_report_file_response(scan, fmt)

    report_data = {
        'scan_id': scan.pk,
        'url': scan.url_asset.url,
        'scan_status': scan.status,
        'scan_date': scan.started_at,
        'finished_at': scan.finished_at,
        'findings': [
            {
                'id': f.pk,
                'title': f.title,
                'severity': f.severity,
                'category': f.category,
                'description': f.description,
                'recommendation': f.recommendation,
                'evidence': f.evidence,
            }
            for f in findings
        ],
        'executive_summary': summary,
        'stats': {
            'total': findings.count(),
            'critical': findings.filter(severity='CRITICAL').count(),
            'high': findings.filter(severity='HIGH').count(),
            'medium': findings.filter(severity='MEDIUM').count(),
            'low': findings.filter(severity='LOW').count(),
            'info': findings.filter(severity='INFO').count(),
        },
    }

    return Response(report_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_report(request, scan_id):
    """Download report as Excel (.xlsx) or PDF."""
    access_filter = Q(url_asset__organization_id=request.user.organization_id)
    access_filter |= Q(created_by=request.user)

    try:
        scan = Scan.objects.select_related(
            'url_asset', 'url_asset__organization'
        ).prefetch_related('findings').filter(
            access_filter,
        ).get(
            pk=scan_id,
        )
    except Scan.DoesNotExist:
        if Scan.objects.filter(pk=scan_id).exists():
            return Response(
                {'detail': 'No tienes permiso para descargar este reporte.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response({'detail': 'Scan not found.'}, status=404)

    fmt = (request.query_params.get('format', 'excel') or 'excel').lower()
    return _build_report_file_response(scan, fmt)
