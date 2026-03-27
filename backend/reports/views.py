"""Views for reports app."""
from io import BytesIO

from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from openpyxl import Workbook

from scanner.models import Scan
from .models import ExecutiveSummary
from .serializers import ExecutiveSummarySerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def report_detail(request, scan_id):
    """Get full report (technical + executive) for a scan."""
    try:
        scan = Scan.objects.select_related(
            'url_asset', 'url_asset__organization'
        ).prefetch_related('findings').get(
            pk=scan_id,
            url_asset__organization=request.user.organization,
        )
    except Scan.DoesNotExist:
        return Response({'detail': 'Scan not found.'}, status=404)

    # Get executive summary if available
    summary = None
    try:
        summary = ExecutiveSummarySerializer(scan.executive_summary).data
    except ExecutiveSummary.DoesNotExist:
        pass

    findings = scan.findings.all()

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
    try:
        scan = Scan.objects.select_related(
            'url_asset'
        ).prefetch_related('findings').get(
            pk=scan_id,
            url_asset__organization=request.user.organization,
        )
    except Scan.DoesNotExist:
        return Response({'detail': 'Scan not found.'}, status=404)

    findings = scan.findings.all()

    # Get executive summary
    summary_content = ''
    try:
        summary_content = scan.executive_summary.content
    except ExecutiveSummary.DoesNotExist:
        pass

    # Build HTML report
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

    fmt = (request.query_params.get('format', 'excel') or 'excel').lower()

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
        response['Content-Disposition'] = f'attachment; filename="reporte_scan_{scan_id}.xlsx"'
        return response

    if fmt == 'pdf':
        try:
            from weasyprint import HTML

            pdf = HTML(string=html_content).write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_scan_{scan_id}.pdf"'
            return response
        except Exception as exc:
            return Response(
                {'detail': f'PDF generation not available: {exc}'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

    return Response(
        {'detail': 'Formato no soportado. Usa format=excel o format=pdf.'},
        status=status.HTTP_400_BAD_REQUEST,
    )
