"""Celery tasks for notifications."""
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_scheduled_reports():
    """Check and send scheduled email reports."""
    from .models import NotificationConfig, EmailLog
    from accounts.models import Organization

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
                _send_report_email(config.organization)
                config.last_sent_at = now
                config.save(update_fields=['last_sent_at'])

                EmailLog.objects.create(
                    organization=config.organization,
                    email_type='scheduled',
                    status='sent',
                )
                logger.info(f"Scheduled report sent for {config.organization.name}")
            except Exception as e:
                EmailLog.objects.create(
                    organization=config.organization,
                    email_type='scheduled',
                    status='failed',
                    error=str(e),
                )
                logger.exception(f"Failed to send report for {config.organization.name}: {e}")


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
    high_findings = scan.findings.filter(severity='HIGH')

    if not high_findings.exists():
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


def _send_report_email(organization):
    """Send a scheduled report email via SendGrid."""
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    users = organization.users.values_list('email', flat=True)
    if not users:
        return

    # Build email content
    from urls_manager.models import URLAsset
    urls = URLAsset.objects.filter(organization=organization)

    content = f"""
    <h2>Reporte de Auditoría - {organization.name}</h2>
    <p>Resumen del estado de sus URLs:</p>
    <ul>
    {"".join([f"<li>{u.url} - Estado: {u.last_scan_status}</li>" for u in urls])}
    </ul>
    <p>Ingrese a la plataforma para ver los reportes detallados.</p>
    """

    message = Mail(
        from_email=settings.SENDGRID_FROM_EMAIL,
        to_emails=list(users),
        subject=f'Reporte de Auditoría - {organization.name}',
        html_content=content,
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(message)


def _send_alert_email(organization, scan, high_findings):
    """Send high-severity alert email via SendGrid."""
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    users = organization.users.values_list('email', flat=True)
    if not users:
        return

    findings_html = "".join([
        f"<li><strong>[{f.severity}]</strong> {f.title}: {f.description}</li>"
        for f in high_findings
    ])

    content = f"""
    <h2>⚠️ Alerta de Seguridad - {scan.url_asset.url}</h2>
    <p>Se detectaron <strong>{high_findings.count()}</strong> vulnerabilidades de severidad ALTA:</p>
    <ul>{findings_html}</ul>
    <p>Ingrese a la plataforma para revisar los detalles y recomendaciones.</p>
    """

    message = Mail(
        from_email=settings.SENDGRID_FROM_EMAIL,
        to_emails=list(users),
        subject=f'⚠️ Alerta: Vulnerabilidades Altas en {scan.url_asset.url}',
        html_content=content,
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(message)
