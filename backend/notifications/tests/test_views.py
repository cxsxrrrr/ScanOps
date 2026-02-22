"""
Tests for notifications endpoints — Priority 6.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User, Organization
from notifications.models import NotificationConfig, EmailLog


class NotificationConfigViewTest(TestCase):
    """Tests for notification config API."""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='pass123',
            organization=self.org,
        )
        self.client.force_authenticate(user=self.user)

    def test_get_creates_default_config(self):
        """GET /api/notifications/config/ → auto-creates config."""
        response = self.client.get('/api/notifications/config/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['frequency'], 'weekly')
        self.assertTrue(response.data['enabled'])

    def test_update_config(self):
        """PUT /api/notifications/config/ → updates frequency."""
        self.client.get('/api/notifications/config/')  # create first
        response = self.client.put('/api/notifications/config/', {
            'frequency': 'daily',
            'enabled': False,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['frequency'], 'daily')
        self.assertFalse(response.data['enabled'])

    def test_email_logs_empty(self):
        """GET /api/notifications/logs/ → empty list."""
        response = self.client.get('/api/notifications/logs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_email_logs_with_data(self):
        """GET /api/notifications/logs/ → returns logs."""
        EmailLog.objects.create(
            organization=self.org,
            email_type='scheduled',
            status='sent',
        )
        EmailLog.objects.create(
            organization=self.org,
            email_type='alert',
            status='failed',
            error='SMTP error',
        )
        response = self.client.get('/api/notifications/logs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_user_without_org_gets_400(self):
        """User without org → 400."""
        user_no_org = User.objects.create_user(
            username='noorg', email='noorg@test.com',
        )
        self.client.force_authenticate(user=user_no_org)
        response = self.client.get('/api/notifications/config/')
        self.assertEqual(response.status_code, 400)
