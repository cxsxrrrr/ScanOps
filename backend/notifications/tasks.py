"""Celery tasks for notifications."""
import logging
from html import escape as _esc
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

VIGIA_BRANDING = {
    'primary_color': '#2a88ff',
    'primary_dark': '#1366f5',
    'accent_color': '#8b5cf6',
    'bg_color': '#0f172a',
    'card_bg': '#1e293b',
    'text_color': '#e2e8f0',
    'text_muted': '#94a3b8',
    'border_color': '#334155',
    'success_color': '#22c55e',
    'warning_color': '#f59e0b',
    'danger_color': '#ef4444',
    'logo_url': 'https://vigia.website/logo.png',
    'dashboard_url': 'https://vigia.website/dashboard',
}


def _build_email_wrapper(subject, body_html):
    """Wrap body HTML in a branded Vigia email template."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="color-scheme" content="dark light" />
<title>{subject}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 0; background-color: {VIGIA_BRANDING['bg_color']}; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; width: 100%; }}
  .container {{ max-width: 600px; width: 100%; margin: 0 auto; padding: 32px 24px; }}
  .card {{ background-color: {VIGIA_BRANDING['card_bg']}; border: 1px solid {VIGIA_BRANDING['border_color']}; border-radius: 16px; padding: 32px; overflow: hidden; }}
  .header {{ text-align: center; margin-bottom: 32px; }}
  .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; color: #ffffff; }}
  .header .logo {{ width: 40px; height: 40px; margin-bottom: 12px; }}
  /* Solid colors, not background-clip:text gradients or gradient-only backgrounds —
     most email clients (Gmail Android app included) don't render those and leave
     text/buttons invisible. Solid color is the reliable choice for email HTML. */
  .btn {{ display: inline-block; background-color: {VIGIA_BRANDING['primary_color']}; color: #ffffff !important; text-decoration: none; padding: 12px 32px; border-radius: 12px; font-weight: 600; font-size: 14px; max-width: 100%; }}
  .footer {{ text-align: center; margin-top: 32px; color: {VIGIA_BRANDING['text_muted']}; font-size: 12px; padding: 0 16px; }}
  .footer a {{ color: {VIGIA_BRANDING['primary_color']}; text-decoration: none; }}
  table {{ width: 100%; max-width: 100%; border-collapse: collapse; margin: 20px 0; table-layout: fixed; }}
  /* Give the 3rd column (description/findings — the long one) most of the
     width instead of table-layout:fixed's default equal thirds. */
  th:nth-child(1), td:nth-child(1) {{ width: 18%; }}
  th:nth-child(2), td:nth-child(2) {{ width: 27%; }}
  th:nth-child(3), td:nth-child(3) {{ width: 55%; }}
  th {{ background-color: rgba(42, 136, 255, 0.1); color: {VIGIA_BRANDING['primary_color']}; padding: 10px 12px; text-align: left; font-size: 13px; border-bottom: 1px solid {VIGIA_BRANDING['border_color']}; word-break: break-word; }}
  td {{ padding: 10px 12px; font-size: 14px; color: {VIGIA_BRANDING['text_color']}; border-bottom: 1px solid rgba(51, 65, 85, 0.5); word-break: break-word; overflow-wrap: break-word; }}
  tr:last-child td {{ border-bottom: none; }}
  .severity-badge {{ display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 700; white-space: nowrap; }}
  .severity-high {{ background-color: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
  .severity-medium {{ background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
  .severity-low {{ background-color: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
  .status-ok {{ color: {VIGIA_BRANDING['success_color']}; }}
  .status-warning {{ color: {VIGIA_BRANDING['warning_color']}; }}
  .status-error {{ color: {VIGIA_BRANDING['danger_color']}; }}
  p {{ color: {VIGIA_BRANDING['text_color']}; font-size: 14px; line-height: 1.6; word-break: break-word; overflow-wrap: break-word; }}
  .muted {{ color: {VIGIA_BRANDING['text_muted']}; }}
  a {{ word-break: break-word; overflow-wrap: break-word; }}
  @media only screen and (max-width: 480px) {{
    .container {{ padding: 16px 8px; }}
    .card {{ padding: 20px 16px; border-radius: 12px; }}
    .header h1 {{ font-size: 20px; }}
    table, thead, tbody, th, td, tr {{ display: block; width: 100%; }}
    thead {{ display: none; }}
    table {{ margin: 16px 0; }}
    tr {{ border-bottom: 1px solid {VIGIA_BRANDING['border_color']}; padding: 10px 0; }}
    tr:last-child {{ border-bottom: none; }}
    td {{ border-bottom: none; padding: 4px 0; }}
    td:before {{ content: attr(data-label); display: block; font-size: 11px; font-weight: 700; color: {VIGIA_BRANDING['primary_color']}; margin-bottom: 2px; }}
    .btn {{ display: block; width: 100%; padding: 14px 16px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="card">
    <div class="header">
      <h1>Vigia</h1>
    </div>
    {body_html}
    <div style="text-align: center; margin-top: 28px;">
      <a href="{VIGIA_BRANDING['dashboard_url']}" class="btn">Ver en Vigia</a>
    </div>
  </div>
  <div class="footer">
    <p>Vigia &mdash; Auditoría Web Automatizada para PYMES</p>
    <p><a href="{VIGIA_BRANDING['dashboard_url']}/settings">Configurar notificaciones</a> &bull; <a href="{VIGIA_BRANDING['dashboard_url']}/settings">Desuscribirse</a></p>
  </div>
</div>
</body>
</html>"""


def _send_with_resend(to_emails, subject, html_content):
    """Send an email using the Resend API."""
    import resend

    resend.api_key = settings.RESEND_API_KEY

    params = {
        'from': settings.RESEND_FROM_EMAIL,
        'to': to_emails,
        'subject': subject,
        'html': html_content,
    }

    resend.Emails.send(params)


def _get_org_data(organization):
    """Get organization URLs and latest scan summary."""
    from urls_manager.models import URLAsset
    from scanner.models import Scan

    urls = URLAsset.objects.filter(organization=organization)
    url_data = []
    for u in urls:
        latest_scan = Scan.objects.filter(url_asset=u).order_by('-started_at').first()
        url_data.append({
            'url': u.url,
            'status': u.last_scan_status or 'Pendiente',
            'high_count': latest_scan.high_count if latest_scan else 0,
            'medium_count': latest_scan.medium_count if latest_scan else 0,
            'total_findings': latest_scan.findings_count if latest_scan else 0,
        })

    return url_data


@shared_task
def send_scheduled_reports():
    """Trigger scheduled scans and send email reports when finished."""
    from .models import NotificationConfig
    from accounts.models import Organization
    from urls_manager.models import URLAsset
    from scanner.models import Scan
    from scanner.tasks import run_scan, process_scan_results
    from celery import chord, chain

    configs = NotificationConfig.objects.filter(enabled=True).select_related('organization')

    for config in configs:
        should_send = False
        now = timezone.now()

        if not config.last_sent_at:
            should_send = True
        elif config.frequency == 'daily':
            should_send = (now - config.last_sent_at).days >= 1
        elif config.frequency == 'weekly':
            should_send = (now - config.last_sent_at).days >= 7
        elif config.frequency == 'monthly':
            should_send = (now - config.last_sent_at).days >= 30

        if should_send:
            try:
                org = config.organization
                urls = URLAsset.objects.filter(organization=org)
                
                if not urls.exists():
                    # Nothing to scan, just update timestamp
                    config.last_sent_at = now
                    config.save(update_fields=['last_sent_at'])
                    continue

                # Create scans for all URLs
                scan_ids = []
                for u in urls:
                    scan = Scan.objects.create(url_asset=u) # System scheduled scan
                    scan_ids.append(scan.id)

                # Orchestrate execution:
                # 1. Run scans and process results for each URL in parallel
                # 2. When ALL are done, trigger the report callback
                header = [
                    chain(run_scan.s(sid), process_scan_results.s()) 
                    for sid in scan_ids
                ]
                
                callback = send_report_email_callback.si(org.id, config.id)
                chord(header)(callback)

                # We consider it "sent" from a scheduling perspective once triggered
                config.last_sent_at = now
                config.save(update_fields=['last_sent_at'])
                logger.info(f"Scheduled scans triggered for {org.name} ({len(scan_ids)} URLs)")
                
            except Exception as e:
                logger.exception(f"Failed to trigger scheduled scans for {config.organization.name}: {e}")


@shared_task
def send_report_email_callback(org_id, config_id):
    """Callback triggered after all scheduled scans finish for an organization."""
    from accounts.models import Organization
    from .models import NotificationConfig, EmailLog
    
    try:
        org = Organization.objects.get(pk=org_id)
    except Organization.DoesNotExist:
        return
        
    try:
        _send_report_email(org)
        
        EmailLog.objects.create(
            organization=org,
            email_type='scheduled',
            status='sent',
        )
        logger.info(f"Scheduled report sent successfully for {org.name}")
    except Exception as e:
        EmailLog.objects.create(
            organization=org,
            email_type='scheduled',
            status='failed',
            error=str(e),
        )
        logger.exception(f"Failed to send scheduled report for {org.name}: {e}")


@shared_task
def send_high_severity_alert(scan_id):
    """Send alert email when high-severity findings are detected."""
    from scanner.models import Scan
    from .models import EmailLog

    try:
        scan = Scan.objects.select_related('url_asset__organization').get(pk=scan_id)
    except Scan.DoesNotExist:
        return

    org = scan.url_asset.organization
    high_findings = list(scan.findings.filter(severity='HIGH'))

    if not high_findings:
        return

    try:
        _send_alert_email(org, scan, high_findings)
        EmailLog.objects.create(
            organization=org,
            email_type='alert',
            status='sent',
        )
    except Exception as e:
        EmailLog.objects.create(
            organization=org,
            email_type='alert',
            status='failed',
            error=str(e),
        )
        logger.exception(f"Failed to send alert for scan {scan_id}: {e}")


@shared_task
def send_manual_report(org_id):
    """Manually send a report email to all organization members."""
    from .models import EmailLog
    from accounts.models import Organization

    try:
        org = Organization.objects.get(pk=org_id)
    except Organization.DoesNotExist:
        logger.error(f"Organization {org_id} not found for manual report")
        return

    try:
        _send_report_email(org)
        EmailLog.objects.create(
            organization=org,
            email_type='manual',
            status='sent',
        )
        logger.info(f"Manual report sent for {org.name}")
    except Exception as e:
        EmailLog.objects.create(
            organization=org,
            email_type='manual',
            status='failed',
            error=str(e),
        )
        logger.exception(f"Failed to send manual report for {org.name}: {e}")


def _send_report_email(organization):
    """Send a scheduled report email via Resend with branded template."""
    users = [e for e in organization.users.values_list('email', flat=True) if e and not e.endswith('@clerk.user')]
    if not users:
        return

    url_data = _get_org_data(organization)

    status_class_map = {
        'completed': 'status-ok',
        'ok': 'status-ok',
        'warning': 'status-warning',
        'error': 'status-error',
    }

    rows_html = ""
    for ud in url_data:
        status_class = status_class_map.get(ud['status'], 'status-warning')
        findings_text = f"{ud['total_findings']} hallazgos" if ud['total_findings'] > 0 else "Sin hallazgos"
        rows_html += f"""
        <tr>
          <td data-label="URL">{_esc(ud['url'])}</td>
          <td data-label="Estado"><span class="{status_class}">{_esc(ud['status'])}</span></td>
          <td data-label="Hallazgos">{_esc(findings_text)}</td>
        </tr>"""

    body = f"""
    <h2 style="color: {VIGIA_BRANDING['text_color']}; margin-top: 0;">Reporte de Auditoría Web</h2>
    <p>Aquí tienes un resumen del estado de seguridad de tus URLs:</p>
    <table>
      <thead>
        <tr>
          <th>URL</th>
          <th>Estado</th>
          <th>Hallazgos</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
    <p class="muted">Ingresa a la plataforma para ver los reportes detallados y las recomendaciones de seguridad.</p>
    """

    html_content = _build_email_wrapper(
        subject='Reporte de Auditoría Web',
        body_html=body,
    )

    _send_with_resend(
        to_emails=users,
        subject='Reporte de Auditoría Web',
        html_content=html_content,
    )


def _send_alert_email(organization, scan, high_findings):
    """Send high-severity alert email via Resend with branded template."""
    users = [e for e in organization.users.values_list('email', flat=True) if e and not e.endswith('@clerk.user')]
    if not users:
        return

    findings_html = ""
    for f in high_findings[:10]:
        severity_class = "severity-high" if f.severity == 'HIGH' else "severity-medium"
        desc = f.description[:120] + ('...' if len(f.description) > 120 else '')
        findings_html += f"""
        <tr>
          <td data-label="Severidad"><span class="severity-badge {severity_class}">{_esc(f.severity)}</span></td>
          <td data-label="Título">{_esc(f.title)}</td>
          <td data-label="Descripción" class="muted" style="font-size: 13px;">{_esc(desc)}</td>
        </tr>"""

    remaining = len(high_findings) - 10 if len(high_findings) > 10 else 0

    body = f"""
    <h2 style="color: {VIGIA_BRANDING['danger_color']}; margin-top: 0;">⚠️ Alerta de Seguridad</h2>
    <p>Se detectaron <strong>{len(high_findings)}</strong> vulnerabilidades de severidad alta en <strong>{_esc(scan.url_asset.url)}</strong>.</p>
    <table>
      <thead>
        <tr>
          <th>Severidad</th>
          <th>Título</th>
          <th>Descripción</th>
        </tr>
      </thead>
      <tbody>
        {findings_html}
      </tbody>
    </table>
    {"<p class='muted'>... y " + str(remaining) + " hallazgos más.</p>" if remaining > 0 else ""}
    <p>Ingresa a la plataforma para revisar los detalles completos y las recomendaciones de seguridad.</p>
    """

    html_content = _build_email_wrapper(
        subject=f'⚠️ Alerta: Vulnerabilidades Altas en {scan.url_asset.url}',
        body_html=body,
    )

    _send_with_resend(
        to_emails=users,
        subject=f'⚠️ Alerta: Vulnerabilidades Altas en {scan.url_asset.url}',
        html_content=html_content,
    )