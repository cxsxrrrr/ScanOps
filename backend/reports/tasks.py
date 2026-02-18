"""Celery tasks for reports app."""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_ai_summary(self, scan_id):
    """Generate AI executive summary for a completed scan."""
    from scanner.models import Scan
    from .models import ExecutiveSummary
    from .ai_service import generate_executive_summary

    try:
        scan = Scan.objects.select_related('url_asset').get(pk=scan_id)
    except Scan.DoesNotExist:
        logger.error(f"Scan {scan_id} not found for AI summary.")
        return

    if scan.status != 'completed':
        logger.warning(f"Scan {scan_id} not completed, skipping AI summary.")
        return

    # Skip if summary already exists
    if hasattr(scan, 'executive_summary'):
        logger.info(f"Summary already exists for scan {scan_id}.")
        return

    # Gather findings data
    findings = scan.findings.all().values(
        'title', 'severity', 'description', 'recommendation'
    )
    findings_list = list(findings)

    if not findings_list:
        # Create a simple summary for clean scans
        ExecutiveSummary.objects.create(
            scan=scan,
            ai_provider='gemini',
            content='## ✅ Escaneo Limpio\n\nNo se encontraron vulnerabilidades en esta auditoría. El sitio presenta una buena postura de seguridad.',
            token_usage=0,
        )
        return

    # Generate AI summary
    result = generate_executive_summary(findings_list, scan.url_asset.url)

    ExecutiveSummary.objects.create(
        scan=scan,
        ai_provider='gemini',
        content=result['content'],
        token_usage=result['token_usage'],
    )

    logger.info(f"AI summary generated for scan {scan_id} ({result['token_usage']} tokens)")
