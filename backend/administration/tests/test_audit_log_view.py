"""Tests for GET /api/admin/audit-logs/ — the auditable API-request evidence trail."""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User, Organization
from audit_log.models import APIRequestLog


class AuditLogEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='Admin Org')
        self.admin = User.objects.create_user(
            username='admin_user', email='admin@test.com', password='x',
            organization=self.org, role='admin',
        )
        self.regular_user = User.objects.create_user(
            username='regular_user', email='user@test.com', password='x',
            organization=self.org, role='user',
        )
        # Note: setUp requests themselves also get audit-logged by the
        # middleware, so tests assert relative deltas, not absolute counts.

    def test_regular_user_denied(self):
        self.client.force_authenticate(user=self.regular_user)
        resp = self.client.get('/api/admin/audit-logs/')
        self.assertEqual(resp.status_code, 403)

    def test_unauthenticated_denied(self):
        resp = self.client.get('/api/admin/audit-logs/')
        self.assertIn(resp.status_code, [401, 403])

    def test_admin_lists_logs_paginated(self):
        APIRequestLog.objects.all().delete()
        for i in range(3):
            APIRequestLog.objects.create(
                ip_address='203.0.113.1', method='GET', path=f'/api/urls/?n={i}',
                status_code=200,
            )

        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/admin/audit-logs/?page_size=2')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['page_size'], 2)
        self.assertEqual(len(resp.data['results']), 2)
        # The current request's own log row is written by the middleware
        # *after* the view returns, so it isn't visible to this view's count().
        self.assertEqual(resp.data['count'], 3)

    def test_filters_by_ip(self):
        APIRequestLog.objects.all().delete()
        APIRequestLog.objects.create(ip_address='203.0.113.1', method='GET', path='/api/urls/', status_code=200)
        APIRequestLog.objects.create(ip_address='198.51.100.5', method='GET', path='/api/urls/', status_code=200)

        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/admin/audit-logs/?ip=203.0.113.1')
        self.assertEqual(resp.status_code, 200)
        ips = {row['ip_address'] for row in resp.data['results']}
        self.assertEqual(ips, {'203.0.113.1'})

    def test_filters_by_search_on_path(self):
        APIRequestLog.objects.all().delete()
        APIRequestLog.objects.create(ip_address='203.0.113.1', method='GET', path='/api/scans/1/', status_code=200)
        APIRequestLog.objects.create(ip_address='203.0.113.1', method='GET', path='/api/urls/', status_code=200)

        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/admin/audit-logs/?search=scans')
        self.assertEqual(resp.status_code, 200)
        paths = {row['path'] for row in resp.data['results']}
        self.assertTrue(all('scans' in p for p in paths))
