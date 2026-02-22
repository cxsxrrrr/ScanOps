"""
Tests for URLAsset API endpoints — Priority 4.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User, Organization
from urls_manager.models import URLAsset


class URLAssetViewSetTest(TestCase):
    """Tests for URLAsset CRUD API."""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='Test Org', url_limit=3)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='pass123',
            organization=self.org,
        )
        self.client.force_authenticate(user=self.user)

    def test_list_urls_empty(self):
        """GET /api/urls/ → empty list when no URLs registered."""
        response = self.client.get('/api/urls/')
        self.assertEqual(response.status_code, 200)

    def test_create_url(self):
        """POST /api/urls/ → creates URL asset."""
        response = self.client.post('/api/urls/', {'url': 'https://example.com'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(URLAsset.objects.count(), 1)
        self.assertEqual(URLAsset.objects.first().organization, self.org)

    def test_list_urls_shows_own_org_only(self):
        """User can only see URLs from their organization."""
        URLAsset.objects.create(organization=self.org, url='https://mine.com')
        other_org = Organization.objects.create(name='Other Org')
        URLAsset.objects.create(organization=other_org, url='https://theirs.com')

        response = self.client.get('/api/urls/')
        urls = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]['url'], 'https://mine.com')

    def test_delete_url(self):
        """DELETE /api/urls/{id}/ → removes URL asset."""
        url_asset = URLAsset.objects.create(
            organization=self.org, url='https://delete-me.com'
        )
        response = self.client.delete(f'/api/urls/{url_asset.pk}/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(URLAsset.objects.count(), 0)

    def test_cannot_delete_other_org_url(self):
        """User cannot delete URLs from another org."""
        other_org = Organization.objects.create(name='Other')
        url_asset = URLAsset.objects.create(
            organization=other_org, url='https://not-mine.com'
        )
        response = self.client.delete(f'/api/urls/{url_asset.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_url_limit_enforced(self):
        """Creating URLs beyond limit → 400."""
        for i in range(3):
            URLAsset.objects.create(
                organization=self.org, url=f'https://site{i}.com'
            )
        response = self.client.post('/api/urls/', {'url': 'https://overflow.com'})
        self.assertEqual(response.status_code, 400)

    def test_invalid_url_rejected(self):
        """URL without valid domain → 400."""
        response = self.client.post('/api/urls/', {'url': 'not-a-url'})
        self.assertEqual(response.status_code, 400)

    def test_ftp_url_rejected(self):
        """FTP protocol → 400."""
        response = self.client.post('/api/urls/', {'url': 'ftp://files.com/data'})
        self.assertEqual(response.status_code, 400)

    def test_user_without_org_gets_empty(self):
        """User without org → empty queryset."""
        user_no_org = User.objects.create_user(
            username='noorg', email='noorg@test.com'
        )
        self.client.force_authenticate(user=user_no_org)
        response = self.client.get('/api/urls/')
        urls = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(urls), 0)

    def test_unauthenticated_access_denied(self):
        """Unauthenticated → 401/403."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/urls/')
        self.assertIn(response.status_code, [401, 403])
