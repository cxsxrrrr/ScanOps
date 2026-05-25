"""Celery tasks for the scanner app."""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('scanner')


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def run_scan(self, scan_id):
    """Execute a security scan asynchronously."""
    from .models import Scan, Finding
    from .engine import ScanEngine

    try:
        scan = Scan.objects.select_related('url_asset').get(pk=scan_id)
    except Scan.DoesNotExist:
        logger.error(f"Scan {scan_id} not found.")
        return

    scan.status = 'running'
    scan.save(update_fields=['status'])
    logger.info(f"Starting scan #{scan_id} for {scan.url_asset.url}")

    try:
        engine = ScanEngine(scan.url_asset.url)
        findings_data = engine.run()

        # Save findings to database
        findings = [
            Finding(
                scan=scan,
                title=f['title'],
                severity=f['severity'],
                category=f.get('category', 'other'),
                description=f['description'],
                recommendation=f.get('recommendation', ''),
                evidence=f.get('evidence', ''),
            )
            for f in findings_data
        ]
        Finding.objects.bulk_create(findings)

        # Update scan status
        scan.status = 'completed'
        scan.finished_at = timezone.now()
        scan.save(update_fields=['status', 'finished_at'])

        # Update URL asset status
        url_asset = scan.url_asset
        critical_count = scan.findings.filter(severity='CRITICAL').count()
        high_count = scan.findings.filter(severity='HIGH').count()
        if critical_count > 0 or high_count > 0:
            url_asset.last_scan_status = 'warning'
        else:
            url_asset.last_scan_status = 'ok'
        url_asset.last_scan_at = timezone.now()
        url_asset.save(update_fields=['last_scan_status', 'last_scan_at'])

        logger.info(f"Scan #{scan_id} completed: {len(findings)} findings")

        # Trigger report generation
        from reports.tasks import generate_ai_summary
        generate_ai_summary.delay(scan_id)

        # Check for high-severity alerts
        if critical_count > 0 or high_count > 0:
            from notifications.tasks import send_high_severity_alert
            send_high_severity_alert.delay(scan_id)

    except Exception as e:
        logger.exception(f"Scan #{scan_id} failed: {e}")
        scan.status = 'error'
        scan.error = str(e)
        scan.finished_at = timezone.now()
        scan.save(update_fields=['status', 'error', 'finished_at'])

        # Update URL asset status
        scan.url_asset.last_scan_status = 'error'
        scan.url_asset.save(update_fields=['last_scan_status'])

        raise self.retry(exc=e)
