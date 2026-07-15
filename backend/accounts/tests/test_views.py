"""
Tests for accounts views — Priority 2.

Tests verify token, profile, and organization endpoints.
"""
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User, Organization


class AccountsViewsTest(TestCase):
    """Tests for auth/profile/organization endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='PYME Test')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@pyme.com',
            password='testpass123',
            organization=self.org,
            clerk_user_id='clerk_test_123',
        )
        self.client.force_authenticate(user=self.user)

    def test_verify_token_returns_user_data(self):
        """POST /api/auth/verify/ → 200 with user info."""
        response = self.client.post('/api/auth/verify/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@pyme.com')

    def test_verify_token_unauthenticated(self):
        """Unauthenticated verify → 401."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/auth/verify/')
        self.assertIn(response.status_code, [401, 403])

    def test_get_profile(self):
        """GET /api/auth/profile/ → current user data."""
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'test@pyme.com')

    def test_update_profile(self):
        """PATCH /api/auth/profile/ → updates name."""
        response = self.client.patch('/api/auth/profile/', {
            'first_name': 'Samuel',
            'last_name': 'Rodríguez',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Samuel')

    def test_get_organization(self):
        """GET /api/auth/organization/ → org data."""
        response = self.client.get('/api/auth/organization/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'PYME Test')

    def test_update_organization(self):
        """PATCH /api/auth/organization/ → updates name."""
        response = self.client.patch('/api/auth/organization/', {
            'name': 'Updated PYME',
        })
        self.assertEqual(response.status_code, 200)
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, 'Updated PYME')

    def test_create_organization_for_user_without_one(self):
        """PATCH /api/auth/organization/ without org → creates one."""
        user_no_org = User.objects.create_user(
            username='no_org_user',
            email='noorg@test.com',
            password='pass123',
        )
        self.client.force_authenticate(user=user_no_org)
        response = self.client.patch('/api/auth/organization/', {
            'name': 'New Org',
        })
        self.assertEqual(response.status_code, 201)
        user_no_org.refresh_from_db()
        self.assertIsNotNone(user_no_org.organization)
        self.assertEqual(user_no_org.organization.name, 'New Org')

    def test_organization_auto_created_without_name(self):
        """PATCH /api/auth/organization/ without name still auto-creates one
        (fallback name from the user's email) — intentional lazy-creation
        design so checkout/URL registration never 404s on a brand-new user.
        """
        user_no_org = User.objects.create_user(
            username='noorg2',
            email='noorg2@test.com',
        )
        self.client.force_authenticate(user=user_no_org)
        response = self.client.patch('/api/auth/organization/', {})
        self.assertEqual(response.status_code, 201)
        user_no_org.refresh_from_db()
        self.assertIsNotNone(user_no_org.organization)
        # Founding member of a brand-new org is auto-promoted to org_admin.
        self.assertEqual(user_no_org.role, 'org_admin')
