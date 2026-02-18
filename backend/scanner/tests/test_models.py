"""
Tests for Scan/Finding models — Priority 3.
"""
from django.test import TestCase
from accounts.models import User, Organization
from urls_manager.models import URLAsset
from scanner.models import Scan, Finding


class ScanModelTest(TestCase):
    """Tests for the Scan model."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org')
        self.url_asset = URLAsset.objects.create(
            organization=self.org, url='https://example.com'
        )
        self.scan = Scan.objects.create(url_asset=self.url_asset)

    def test_default_status_pending(self):
        """New scan has status 'pending'."""
        self.assertEqual(self.scan.status, 'pending')

    def test_str_representation(self):
        """__str__ includes scan ID, URL, and status."""
        result = str(self.scan)
        self.assertIn('example.com', result)
        self.assertIn('pending', result)

    def test_findings_count_property(self):
        """findings_count returns total number of findings."""
        Finding.objects.create(
            scan=self.scan, title='Test', severity='HIGH',
            description='desc',
        )
        Finding.objects.create(
            scan=self.scan, title='Test 2', severity='LOW',
            description='desc',
        )
        self.assertEqual(self.scan.findings_count, 2)

    def test_severity_count_properties(self):
        """high_count, medium_count, low_count return correct counts."""
        Finding.objects.create(
            scan=self.scan, title='H1', severity='HIGH', description='d'
        )
        Finding.objects.create(
            scan=self.scan, title='H2', severity='HIGH', description='d'
        )
        Finding.objects.create(
            scan=self.scan, title='M1', severity='MEDIUM', description='d'
        )
        Finding.objects.create(
            scan=self.scan, title='L1', severity='LOW', description='d'
        )
        self.assertEqual(self.scan.high_count, 2)
        self.assertEqual(self.scan.medium_count, 1)
        self.assertEqual(self.scan.low_count, 1)

    def test_ordering_newest_first(self):
        """Scans are ordered newest first (-started_at)."""
        from django.utils import timezone
        from datetime import timedelta
        old_time = timezone.now() - timedelta(hours=1)
        # Force the first scan to have an older timestamp
        Scan.objects.filter(pk=self.scan.pk).update(started_at=old_time)
        scan2 = Scan.objects.create(url_asset=self.url_asset)
        scans = list(Scan.objects.all())
        self.assertEqual(scans[0].pk, scan2.pk)


class FindingModelTest(TestCase):
    """Tests for the Finding model."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org')
        self.url_asset = URLAsset.objects.create(
            organization=self.org, url='https://example.com'
        )
        self.scan = Scan.objects.create(url_asset=self.url_asset)

    def test_str_representation(self):
        """__str__ shows severity and title."""
        finding = Finding.objects.create(
            scan=self.scan, title='Missing HSTS',
            severity='HIGH', description='desc',
        )
        self.assertEqual(str(finding), '[HIGH] Missing HSTS')

    def test_ordering_by_severity(self):
        """Findings ordered: HIGH → MEDIUM → LOW → INFO."""
        Finding.objects.create(
            scan=self.scan, title='Low', severity='LOW', description='d'
        )
        Finding.objects.create(
            scan=self.scan, title='High', severity='HIGH', description='d'
        )
        Finding.objects.create(
            scan=self.scan, title='Medium', severity='MEDIUM', description='d'
        )
        findings = list(self.scan.findings.values_list('severity', flat=True))
        self.assertEqual(findings, ['HIGH', 'MEDIUM', 'LOW'])

    def test_default_category_is_other(self):
        """Default category is 'other'."""
        finding = Finding.objects.create(
            scan=self.scan, title='Test', severity='LOW', description='d'
        )
        self.assertEqual(finding.category, 'other')
