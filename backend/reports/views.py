"""Views for reports app."""
from io import BytesIO

from django.http import HttpResponse
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from openpyxl import Workbook

from scanner.models import Scan
from .models import ExecutiveSummary
from .serializers import ExecutiveSummarySerializer


def _build_pdf_with_reportlab(scan, findings, summary_content):
    """Build a styled PDF using ReportLab as a fallback for environments without WeasyPrint deps."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    def _clean(text):
        return (str(text or '')).replace('<', '&lt;').replace('>', '&gt;')

    def _severity_color(severity):
        mapping = {
            'CRITICAL': colors.HexColor('#7c3aed'),
            'HIGH': colors.HexColor('#dc2626'),
            'MEDIUM': colors.HexColor('#d97706'),
            'LOW': colors.HexColor('#2563eb'),
            'INFO': colors.HexColor('#475569'),
        }
        return mapping.get((severity or '').upper(), colors.HexColor('#334155'))

    stats = {
        'total': findings.count(),
        'critical': findings.filter(severity='CRITICAL').count(),
        'high': findings.filter(severity='HIGH').count(),
        'medium': findings.filter(severity='MEDIUM').count(),
        'low': findings.filter(severity='LOW').count(),
    }

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=f'Reporte Scan {scan.pk}',
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'VigiaTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.white,
        leading=24,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'VigiaSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#bfdbfe'),
        leading=12,
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'BodyCopy',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1f2937'),
    )

    story = []

    header_table = Table(
        [[
            Paragraph('Reporte de Auditoria Web', title_style),
            Paragraph('VIGIA', subtitle_style),
        ]],
        colWidths=[5.8 * inch, 1.0 * inch],
    )
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1d4ed8')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)

    metadata = [
        [Paragraph('<b>Scan ID</b>', body_style), Paragraph(_clean(scan.pk), body_style)],
        [Paragraph('<b>URL</b>', body_style), Paragraph(_clean(scan.url_asset.url), body_style)],
        [Paragraph('<b>Estado</b>', body_style), Paragraph(_clean(scan.status), body_style)],
        [
            Paragraph('<b>Fecha</b>', body_style),
            Paragraph(_clean(scan.started_at.strftime('%d/%m/%Y %H:%M') if scan.started_at else ''), body_style),
        ],
    ]
    meta_table = Table(metadata, colWidths=[1.0 * inch, 5.8 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph('Resumen de Hallazgos', section_title_style))
    stat_row = [
        [
            Paragraph('<b>Total</b><br/><font size="14">{}</font>'.format(stats['total']), body_style),
            Paragraph('<b>Critico</b><br/><font size="14">{}</font>'.format(stats['critical']), body_style),
            Paragraph('<b>Alto</b><br/><font size="14">{}</font>'.format(stats['high']), body_style),
            Paragraph('<b>Medio</b><br/><font size="14">{}</font>'.format(stats['medium']), body_style),
            Paragraph('<b>Bajo</b><br/><font size="14">{}</font>'.format(stats['low']), body_style),
        ]
    ]
    stats_table = Table(stat_row, colWidths=[1.35 * inch] * 5)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#ede9fe')),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#fee2e2')),
        ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#fef3c7')),
        ('BACKGROUND', (4, 0), (4, 0), colors.HexColor('#dbeafe')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 10))

    if summary_content:
        story.append(Paragraph('Resumen Ejecutivo', section_title_style))
        summary_text = _clean(summary_content)
        if len(summary_text) > 3500:
            summary_text = summary_text[:3500] + '...'

        # Use independent paragraphs so content can flow across pages.
        for part in summary_text.split('\n'):
            part = part.strip()
            if not part:
                continue
            story.append(Paragraph(part, body_style))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))

    story.append(Paragraph('Hallazgos Tecnicos', section_title_style))
    findings_data = [[
        Paragraph('<b>Severidad</b>', body_style),
        Paragraph('<b>Titulo</b>', body_style),
        Paragraph('<b>Categoria</b>', body_style),
        Paragraph('<b>Recomendacion</b>', body_style),
    ]]

    for finding in findings:
        findings_data.append([
            Paragraph(_clean(finding.severity), body_style),
            Paragraph(_clean(finding.title), body_style),
            Paragraph(_clean(finding.category), body_style),
            Paragraph(_clean(finding.recommendation), body_style),
        ])

    if len(findings_data) == 1:
        findings_data.append([
            Paragraph('INFO', body_style),
            Paragraph('Sin hallazgos detectados', body_style),
            Paragraph('-', body_style),
            Paragraph('Mantener monitoreo continuo', body_style),
        ])

    findings_table = Table(findings_data, colWidths=[1.0 * inch, 2.0 * inch, 1.2 * inch, 2.55 * inch], repeatRows=1)
    base_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    for row_idx, finding in enumerate(findings, start=1):
        stripe = colors.HexColor('#f8fafc') if row_idx % 2 else colors.HexColor('#ffffff')
        base_style.append(('BACKGROUND', (1, row_idx), (-1, row_idx), stripe))
        base_style.append(('BACKGROUND', (0, row_idx), (0, row_idx), _severity_color(finding.severity)))
        base_style.append(('TEXTCOLOR', (0, row_idx), (0, row_idx), colors.white))

    findings_table.setStyle(TableStyle(base_style))
    story.append(findings_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph('Generado por Vigia', ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        alignment=1,
        fontSize=8,
        textColor=colors.HexColor('#64748b'),
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
        summary_ws = workbook.active
        summary_ws.title = 'Resumen'
        summary_ws.append(['Campo', 'Valor'])
        summary_ws.append(['Scan ID', scan.pk])
        summary_ws.append(['URL', scan.url_asset.url])
        summary_ws.append(['Estado', scan.status])
        summary_ws.append(['Fecha inicio', scan.started_at.strftime('%d/%m/%Y %H:%M') if scan.started_at else ''])
        summary_ws.append(['Fecha fin', scan.finished_at.strftime('%d/%m/%Y %H:%M') if scan.finished_at else ''])
        summary_ws.append(['Total hallazgos', findings.count()])
        summary_ws.append(['Criticos', findings.filter(severity='CRITICAL').count()])
        summary_ws.append(['Altos', findings.filter(severity='HIGH').count()])
        summary_ws.append(['Medios', findings.filter(severity='MEDIUM').count()])
        summary_ws.append(['Bajos', findings.filter(severity='LOW').count()])
        summary_ws.append(['Info', findings.filter(severity='INFO').count()])

        findings_ws = workbook.create_sheet(title='Hallazgos')
        findings_ws.append([
            'ID', 'Titulo', 'Severidad', 'Categoria',
            'Descripcion', 'Recomendacion', 'Evidencia',
        ])
        for finding in findings:
            findings_ws.append([
                finding.pk,
                finding.title,
                finding.severity,
                finding.category,
                finding.description,
                finding.recommendation,
                finding.evidence,
            ])

        if summary_content:
            executive_ws = workbook.create_sheet(title='Resumen Ejecutivo')
            executive_ws.append(['Contenido'])
            executive_ws.append([summary_content])

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
        try:
            from weasyprint import HTML

            pdf = HTML(string=html_content).write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_scan_{scan.pk}.pdf"'
            return response
        except Exception as exc:
            try:
                pdf = _build_pdf_with_reportlab(scan, findings, summary_content)
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="reporte_scan_{scan.pk}.pdf"'
                return response
            except Exception as fallback_exc:
                return Response(
                    {
                        'detail': (
                            f'PDF generation not available. WeasyPrint error: {exc}. '
                            f'ReportLab fallback error: {fallback_exc}'
                        ),
                    },
                    status=status.HTTP_501_NOT_IMPLEMENTED,
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
