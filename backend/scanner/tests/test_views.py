"""Tests for the scan trigger endpoint — Priority 2."""
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User, Organization
from urls_manager.models import URLAsset
from scanner.models import Scan


class TriggerScanTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='PYME Test')
        self.user = User.objects.create_user(
            username='tester', email='test@pyme.com', password='pass123',
            organization=self.org,
        )
        self.url_asset = URLAsset.objects.create(organization=self.org, url='https://example.com')
        self.client.force_authenticate(user=self.user)

    @patch('scanner.tasks.run_scan.s')
    @patch('scanner.tasks.process_scan_results.s')
    def test_trigger_creates_scan(self, mock_process, mock_run):
        response = self.client.post('/api/scans/trigger/', {'url_asset_id': self.url_asset.id})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(Scan.objects.filter(url_asset=self.url_asset).count(), 1)

    def test_rejects_while_scan_in_progress(self):
        Scan.objects.create(url_asset=self.url_asset, status='running')
        response = self.client.post('/api/scans/trigger/', {'url_asset_id': self.url_asset.id})
        self.assertEqual(response.status_code, 409)

    def test_rejects_within_cooldown_after_completed_scan(self):
        Scan.objects.create(url_asset=self.url_asset, status='completed')
        response = self.client.post('/api/scans/trigger/', {'url_asset_id': self.url_asset.id})
        self.assertEqual(response.status_code, 429)

    @patch('scanner.tasks.run_scan.s')
    @patch('scanner.tasks.process_scan_results.s')
    def test_allows_after_cooldown_expires(self, mock_process, mock_run):
        old_scan = Scan.objects.create(url_asset=self.url_asset, status='completed')
        Scan.objects.filter(pk=old_scan.pk).update(
            started_at=timezone.now() - timezone.timedelta(minutes=10)
        )
        response = self.client.post('/api/scans/trigger/', {'url_asset_id': self.url_asset.id})
        self.assertEqual(response.status_code, 202)

    def test_rejects_url_from_other_organization(self):
        other_org = Organization.objects.create(name='Other')
        other_url = URLAsset.objects.create(organization=other_org, url='https://other.com')
        response = self.client.post('/api/scans/trigger/', {'url_asset_id': other_url.id})
        self.assertEqual(response.status_code, 404)
