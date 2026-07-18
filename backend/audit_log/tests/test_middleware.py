"""Tests for APIRequestLogMiddleware — the audit trail must record every /api/ call."""
from rest_framework.test import APIClient
from django.test import TestCase

from accounts.models import Organization, User
from audit_log.models import APIRequestLog


class APIRequestLogMiddlewareTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Audit Org')
        self.user = User.objects.create_user(
            username='auditee', email='auditee@example.com', password='x'
        )
        self.user.organization = self.org
        self.user.save()

    def test_logs_authenticated_request_with_user_and_org(self):
        client = APIClient()
        client.force_authenticate(self.user)

        resp = client.get('/api/urls/', REMOTE_ADDR='203.0.113.7')

        log = APIRequestLog.objects.latest('created_at')
        self.assertEqual(log.method, 'GET')
        self.assertEqual(log.path, '/api/urls/')
        self.assertEqual(log.status_code, resp.status_code)
        self.assertEqual(log.ip_address, '203.0.113.7')
        self.assertEqual(log.user_id, self.user.pk)
        self.assertEqual(log.user_email, 'auditee@example.com')
        self.assertEqual(log.organization_id, self.org.pk)
        self.assertEqual(log.organization_name, 'Audit Org')

    def test_logs_anonymous_request_without_user(self):
        client = APIClient()
        client.get('/api/urls/', REMOTE_ADDR='198.51.100.9')

        log = APIRequestLog.objects.latest('created_at')
        self.assertIsNone(log.user)
        self.assertEqual(log.user_email, '')
        self.assertIsNone(log.organization)
        self.assertEqual(log.ip_address, '198.51.100.9')
        self.assertEqual(log.status_code, 401)

    def test_prefers_x_forwarded_for_over_remote_addr(self):
        client = APIClient()
        client.get(
            '/api/urls/',
            REMOTE_ADDR='10.0.0.1',
            HTTP_X_FORWARDED_FOR='198.51.100.42, 10.0.0.1',
        )

        log = APIRequestLog.objects.latest('created_at')
        self.assertEqual(log.ip_address, '198.51.100.42')

    def test_does_not_log_non_api_paths(self):
        before = APIRequestLog.objects.count()
        client = APIClient()
        client.get('/admin/')

        self.assertEqual(APIRequestLog.objects.count(), before)

    def test_records_response_time_and_user_agent(self):
        client = APIClient()
        client.get('/api/urls/', HTTP_USER_AGENT='pytest-agent/1.0')

        log = APIRequestLog.objects.latest('created_at')
        self.assertEqual(log.user_agent, 'pytest-agent/1.0')
        self.assertIsNotNone(log.response_time_ms)
        self.assertGreaterEqual(log.response_time_ms, 0)

    def test_survives_deleted_user_via_set_null(self):
        client = APIClient()
        client.force_authenticate(self.user)
        client.get('/api/urls/')

        log = APIRequestLog.objects.latest('created_at')
        self.assertEqual(log.user_email, 'auditee@example.com')

        self.user.delete()
        log.refresh_from_db()
        self.assertIsNone(log.user)
        # Snapshot survives even though the FK was nulled out.
        self.assertEqual(log.user_email, 'auditee@example.com')
