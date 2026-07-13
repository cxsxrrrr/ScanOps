"""Tests for organization-level date-range reports."""
from datetime import date, timedelta
from io import BytesIO

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Organization, User
from scanner.models import Scan, Finding
from urls_manager.models import URLAsset


class OrgReportTest(TestCase):
    """Tests for GET /api/reports/org/ endpoint."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org')
        self.other_org = Organization.objects.create(name='Other Org')
        self.user = User.objects.create_user(
            username='tester', email='t@example.com', password='x'
        )
        self.user.organization = self.org
        self.user.save()

        self.url_asset = URLAsset.objects.create(
            organization=self.org, url='https://example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _create_scan_with_findings(self, url_asset, days_ago, findings_specs):
        """Create a scan with a given started_at and findings."""
        scan = Scan.objects.create(url_asset=url_asset, status='completed')
        target = timezone.now() - timedelta(days=days_ago)
        Scan.objects.filter(pk=scan.pk).update(started_at=target, finished_at=target)
        for sev, title in findings_specs:
            Finding.objects.create(
                scan=scan, severity=sev, title=title,
                description='d', category='other',
            )
        scan.refresh_from_db()
        return scan

    def test_401_sin_auth(self):
        """Unauthenticated request returns 401."""
        anon = APIClient()
        resp = anon.get('/api/reports/org/?start=2026-01-01&end=2026-01-31')
        self.assertEqual(resp.status_code, 401)

    def test_400_usuario_sin_org(self):
        """User without organization gets 400."""
        no_org_user = User.objects.create_user(
            username='noorg', email='no@example.com', password='x'
        )
        c = APIClient()
        c.force_authenticate(no_org_user)
        resp = c.get('/api/reports/org/?start=2026-01-01&end=2026-01-31')
        self.assertEqual(resp.status_code, 400)

    def test_422_rango_start_mayor_end(self):
        """Start date after end date returns 422."""
        resp = self.client.get('/api/reports/org/?start=2026-02-01&end=2026-01-01')
        self.assertEqual(resp.status_code, 422)
        self.assertIn('detail', resp.data)

    def test_422_sin_scans_en_rango(self):
        """No scans in range returns 422 with concrete message."""
        resp = self.client.get(
            '/api/reports/org/?start=2025-01-01&end=2025-01-31'
        )
        self.assertEqual(resp.status_code, 422)
        self.assertIn('detail', resp.data)
        self.assertIn('Sin', str(resp.data['detail']))

    def test_200_pdf_default(self):
        """Default format is PDF, returns application/pdf."""
        self._create_scan_with_findings(
            self.url_asset, days_ago=5, findings_specs=[('HIGH', 'h1')]
        )
        resp = self.client.get(
            '/api/reports/org/?start=2026-01-01&end=2026-12-31'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertGreater(len(resp.content), 100)

    def test_200_excel(self):
        """Excel format returns correct content type."""
        self._create_scan_with_findings(
            self.url_asset, days_ago=5, findings_specs=[('MEDIUM', 'm1')]
        )
        resp = self.client.get(
            '/api/reports/org/?start=2026-01-01&end=2026-12-31&format=excel'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            'spreadsheetml.sheet', resp['Content-Type']
        )
        self.assertGreater(len(resp.content), 100)

    def test_no_incluye_scans_de_otras_fechas(self):
        """Scans outside the date range are excluded."""
        self._create_scan_with_findings(
            self.url_asset, days_ago=200, findings_specs=[('HIGH', 'old')]
        )
        self._create_scan_with_findings(
            self.url_asset, days_ago=5, findings_specs=[('HIGH', 'recent')]
        )
        end = (timezone.now() + timedelta(days=1)).date().isoformat()
        start = (timezone.now() - timedelta(days=30)).date().isoformat()
        resp = self.client.get(f'/api/reports/org/?start={start}&end={end}')
        self.assertEqual(resp.status_code, 200)

    def test_filtra_solo_scans_de_su_org(self):
        """Scans from another organization are not included."""
        other_asset = URLAsset.objects.create(
            organization=self.other_org, url='https://other.com'
        )
        self._create_scan_with_findings(
            other_asset, days_ago=5, findings_specs=[('HIGH', 'other org')]
        )
        today = timezone.now().date().isoformat()
        start = (timezone.now() - timedelta(days=30)).date().isoformat()
        resp = self.client.get(f'/api/reports/org/?start={start}&end={today}')
        self.assertEqual(resp.status_code, 422)
        self.assertIn('Sin', str(resp.data['detail']))

    def test_agrega_multiple_scans_findings(self):
        """Multiple scans with multiple findings are aggregated correctly."""
        scan1 = self._create_scan_with_findings(
            self.url_asset, days_ago=5,
            findings_specs=[('HIGH', 'h1'), ('MEDIUM', 'm1'), ('LOW', 'l1')]
        )
        scan2 = self._create_scan_with_findings(
            self.url_asset, days_ago=10,
            findings_specs=[('CRITICAL', 'c1'), ('HIGH', 'h2')]
        )
        end = (timezone.now() + timedelta(days=1)).date().isoformat()
        start = (timezone.now() - timedelta(days=30)).date().isoformat()
        resp = self.client.get(f'/api/reports/org/?start={start}&end={end}')
        self.assertEqual(resp.status_code, 200)

    def test_400_formato_invalido(self):
        """Invalid format returns 400."""
        self._create_scan_with_findings(
            self.url_asset, days_ago=5, findings_specs=[('HIGH', 'h1')]
        )
        resp = self.client.get(
            '/api/reports/org/?start=2026-01-01&end=2026-12-31&format=docx'
        )
        self.assertEqual(resp.status_code, 400)

    def test_400_falta_parametro_start(self):
        """Missing start param returns 400."""
        resp = self.client.get('/api/reports/org/?end=2026-12-31')
        self.assertEqual(resp.status_code, 400)

    def test_400_falta_parametro_end(self):
        """Missing end param returns 400."""
        resp = self.client.get('/api/reports/org/?start=2026-01-01')
        self.assertEqual(resp.status_code, 400)