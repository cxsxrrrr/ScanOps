"""Views for reports app."""
import json
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

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
    """Download report as HTML."""
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
        .stat.high {{ background: #e74c3c; }}
        .stat.medium {{ background: #f39c12; }}
        .stat.low {{ background: #3498db; }}
        .finding {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; border-left: 4px solid; }}
        .finding.HIGH {{ border-left-color: #e74c3c; }}
        .finding.MEDIUM {{ border-left-color: #f39c12; }}
        .finding.LOW {{ border-left-color: #3498db; }}
        .finding.INFO {{ border-left-color: #95a5a6; }}
        .severity {{ display: inline-block; padding: 2px 8px; border-radius: 4px; color: white; font-size: 12px; }}
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

    fmt = request.query_params.get('format', 'html')

    if fmt == 'html':
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="reporte_scan_{scan_id}.html"'
        return response

    # For PDF, we'd use WeasyPrint (optional; requires system deps)
    try:
        from weasyprint import HTML
        pdf = HTML(string=html_content).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_scan_{scan_id}.pdf"'
        return response
    except ImportError:
        return Response(
            {'detail': 'PDF generation not available. Download HTML instead.'},
            status=501
        )
