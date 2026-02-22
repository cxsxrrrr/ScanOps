"""
Tests for URLAsset model — Priority 3.
"""
from django.test import TestCase
from django.db import IntegrityError
from accounts.models import User, Organization
from urls_manager.models import URLAsset


class URLAssetModelTest(TestCase):
    """Tests for the URLAsset model."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org')
        self.url_asset = URLAsset.objects.create(
            organization=self.org,
            url='https://example.com',
        )

    def test_str_representation(self):
        """__str__ returns the URL."""
        self.assertEqual(str(self.url_asset), 'https://example.com')

    def test_default_status_is_pending(self):
        """Default scan status is 'pending'."""
        self.assertEqual(self.url_asset.last_scan_status, 'pending')

    def test_last_scan_at_default_none(self):
        """last_scan_at is None initially."""
        self.assertIsNone(self.url_asset.last_scan_at)

    def test_unique_together_org_url(self):
        """Same URL + same org → IntegrityError."""
        with self.assertRaises(IntegrityError):
            URLAsset.objects.create(
                organization=self.org,
                url='https://example.com',
            )

    def test_same_url_different_org_allowed(self):
        """Same URL + different org → OK."""
        other_org = Organization.objects.create(name='Other Org')
        url2 = URLAsset.objects.create(
            organization=other_org,
            url='https://example.com',
        )
        self.assertIsNotNone(url2.pk)

    def test_ordering_by_created_at_desc(self):
        """URLs ordered by most recent first."""
        url2 = URLAsset.objects.create(
            organization=self.org,
            url='https://second.com',
        )
        urls = list(URLAsset.objects.filter(organization=self.org))
        self.assertEqual(urls[0], url2)
