"""
Tests for administration endpoints — Priority 6.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User, Organization


class AdminDashboardTest(TestCase):
    """Tests for admin-only endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='Admin Org')
        self.admin = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='admin123',
            organization=self.org,
            role='admin',
        )
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='user@test.com',
            password='user123',
            organization=self.org,
            role='user',
        )

    def test_admin_can_access_metrics(self):
        """Admin user → 200 on /api/admin/metrics/."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/metrics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('users', response.data)
        self.assertIn('scans', response.data)
        self.assertIn('findings', response.data)

    def test_regular_user_denied_metrics(self):
        """Non-admin user → 403 on /api/admin/metrics/."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/admin/metrics/')
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_denied_metrics(self):
        """Unauthenticated → 401/403."""
        response = self.client.get('/api/admin/metrics/')
        self.assertIn(response.status_code, [401, 403])

    def test_admin_can_access_errors(self):
        """Admin → 200 on /api/admin/errors/."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/errors/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('scan_errors', response.data)
        self.assertIn('email_errors', response.data)

    def test_admin_can_view_users(self):
        """Admin → 200 on /api/admin/users/."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/users/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)  # admin + regular


class AdminActionLogTest(TestCase):
    """Tests for the admin action log (who-changed-what) endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='Admin Org')
        self.admin = User.objects.create_user(
            username='admin_user', email='admin@test.com', password='admin123',
            organization=self.org, role='admin',
        )
        self.regular_user = User.objects.create_user(
            username='regular_user', email='user@test.com', password='user123',
            organization=self.org, role='user',
        )

    def test_regular_user_denied(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/admin/audit-logs/actions/')
        self.assertEqual(response.status_code, 403)

    def test_admin_sees_logged_role_change(self):
        from audit_log.models import AdminActionLog
        AdminActionLog.objects.create(
            action='role_change',
            performed_by=self.admin,
            performed_by_email=self.admin.email,
            target_user_id=self.regular_user.id,
            target_user_email=self.regular_user.email,
            before_value='user',
            after_value='org_admin',
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/audit-logs/actions/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        entry = response.data['results'][0]
        self.assertEqual(entry['action'], 'role_change')
        self.assertEqual(entry['before_value'], 'user')
        self.assertEqual(entry['after_value'], 'org_admin')
        self.assertEqual(entry['performed_by_email'], self.admin.email)

    def test_filter_by_action(self):
        from audit_log.models import AdminActionLog
        AdminActionLog.objects.create(action='role_change', performed_by=self.admin, performed_by_email=self.admin.email)
        AdminActionLog.objects.create(action='block_change', performed_by=self.admin, performed_by_email=self.admin.email)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/audit-logs/actions/?action=block_change')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['action'], 'block_change')

    def test_search_by_target_email(self):
        from audit_log.models import AdminActionLog
        AdminActionLog.objects.create(
            action='role_change', performed_by=self.admin, performed_by_email=self.admin.email,
            target_user_email='someone@else.com',
        )
        AdminActionLog.objects.create(
            action='role_change', performed_by=self.admin, performed_by_email=self.admin.email,
            target_user_email=self.regular_user.email,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f'/api/admin/audit-logs/actions/?search={self.regular_user.email}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
