"""
Tests for Celery scan task — Priority 5.

Note: ScanEngine is lazily imported inside run_scan(), so we
patch 'scanner.engine.ScanEngine' instead of 'scanner.tasks.ScanEngine'.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone

from accounts.models import Organization
from urls_manager.models import URLAsset
from scanner.models import Scan, Finding


class RunScanTaskTest(TestCase):
    """Tests for the run_scan Celery task."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org')
        self.url_asset = URLAsset.objects.create(
            organization=self.org, url='https://example.com'
        )
        self.scan = Scan.objects.create(url_asset=self.url_asset)

    @patch('reports.tasks.generate_ai_summary')
    @patch('scanner.engine.ScanEngine')
    def test_successful_scan(self, MockEngine, mock_ai):
        """Successful scan → status completed, findings saved."""
        mock_instance = MockEngine.return_value
        mock_instance.run.return_value = [
            {
                'title': 'Missing HSTS',
                'severity': 'HIGH',
                'category': 'headers',
                'description': 'HSTS is missing',
                'recommendation': 'Add HSTS',
                'evidence': 'no header',
            },
        ]
        mock_ai.delay = MagicMock()

        from scanner.tasks import run_scan
        with patch('notifications.tasks.send_high_severity_alert') as mock_alert:
            mock_alert.delay = MagicMock()
            run_scan(self.scan.pk)

        self.scan.refresh_from_db()
        self.assertEqual(self.scan.status, 'completed')
        self.assertIsNotNone(self.scan.finished_at)
        self.assertEqual(Finding.objects.filter(scan=self.scan).count(), 1)

    @patch('reports.tasks.generate_ai_summary')
    @patch('scanner.engine.ScanEngine')
    def test_scan_updates_url_asset_status(self, MockEngine, mock_ai):
        """After scan with HIGH findings → url_asset status = 'warning'."""
        mock_instance = MockEngine.return_value
        mock_instance.run.return_value = [
            {
                'title': 'Critical Issue',
                'severity': 'HIGH',
                'description': 'bad',
            },
        ]
        mock_ai.delay = MagicMock()

        from scanner.tasks import run_scan
        with patch('notifications.tasks.send_high_severity_alert') as mock_alert:
            mock_alert.delay = MagicMock()
            run_scan(self.scan.pk)

        self.url_asset.refresh_from_db()
        self.assertEqual(self.url_asset.last_scan_status, 'warning')

    @patch('reports.tasks.generate_ai_summary')
    @patch('scanner.engine.ScanEngine')
    def test_scan_no_high_findings_status_ok(self, MockEngine, mock_ai):
        """No HIGH findings → url_asset status = 'ok'."""
        mock_instance = MockEngine.return_value
        mock_instance.run.return_value = [
            {'title': 'Low Issue', 'severity': 'LOW', 'description': 'd'},
        ]
        mock_ai.delay = MagicMock()

        from scanner.tasks import run_scan
        run_scan(self.scan.pk)

        self.url_asset.refresh_from_db()
        self.assertEqual(self.url_asset.last_scan_status, 'ok')

    @patch('scanner.engine.ScanEngine')
    def test_scan_error_sets_error_status(self, MockEngine):
        """Engine exception → scan status = 'error'."""
        mock_instance = MockEngine.return_value
        mock_instance.run.side_effect = Exception('Network failure')

        from scanner.tasks import run_scan
        try:
            run_scan(self.scan.pk)
        except Exception:
            pass

        self.scan.refresh_from_db()
        self.assertEqual(self.scan.status, 'error')
        self.assertIn('Network failure', self.scan.error)

    def test_scan_not_found(self):
        """Non-existent scan ID → task exits silently."""
        from scanner.tasks import run_scan
        run_scan(99999)
