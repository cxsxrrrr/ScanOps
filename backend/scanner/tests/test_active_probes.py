"""Tests for the active_probes module (safe, read-only extra HTTP requests)."""
from unittest.mock import MagicMock
from django.test import TestCase

from scanner.checks.active_probes import (
    check_exposed_admin_panels, check_exposed_backup_files,
    check_actuator_exposure, check_wellknown_disclosures,
    check_directory_listing_generic, check_http_methods,
    check_open_redirect, check_reflected_xss,
    check_path_traversal_active, check_crlf_injection,
    XSS_CANARY, CANARY_HOST,
)


class FakeResponse:
    """Helper to build mock HTTP responses."""

    def __init__(self, text='', status_code=404, headers=None, content=b''):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content or text.encode()


NOT_FOUND = FakeResponse(text='Not Found', status_code=404)


class AdminPanelsTest(TestCase):
    def test_exposed_phpmyadmin_flagged(self):
        session = MagicMock()

        def mock_get(url, **kwargs):
            if 'phpmyadmin' in url.lower():
                return FakeResponse(text='phpMyAdmin', status_code=200)
            return NOT_FOUND

        session.get.side_effect = mock_get
        findings = []
        check_exposed_admin_panels(session, 'https://example.com', findings)
        self.assertTrue(any('phpMyAdmin' in f['title'] for f in findings))
        self.assertEqual(findings[0]['severity'], 'HIGH')

    def test_no_panels_exposed(self):
        session = MagicMock()
        session.get.return_value = NOT_FOUND
        findings = []
        check_exposed_admin_panels(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 0)


class BackupFilesTest(TestCase):
    def test_exposed_env_file_flagged(self):
        session = MagicMock()

        def mock_get(url, **kwargs):
            if url.endswith('/.env'):
                return FakeResponse(text='DB_PASSWORD=secret', status_code=200)
            return NOT_FOUND

        session.get.side_effect = mock_get
        findings = []
        check_exposed_backup_files(session, 'https://example.com', findings)
        self.assertTrue(any(f['severity'] == 'CRITICAL' for f in findings))

    def test_no_backups_exposed(self):
        session = MagicMock()
        session.get.return_value = NOT_FOUND
        findings = []
        check_exposed_backup_files(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 0)


class ActuatorTest(TestCase):
    def test_env_endpoint_exposed(self):
        session = MagicMock()

        def mock_get(url, **kwargs):
            if 'actuator/env' in url:
                return FakeResponse(text='{"activeProfiles":[]}', status_code=200)
            return NOT_FOUND

        session.get.side_effect = mock_get
        findings = []
        check_actuator_exposure(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'CRITICAL')

    def test_actuator_not_exposed(self):
        session = MagicMock()
        session.get.return_value = NOT_FOUND
        findings = []
        check_actuator_exposure(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 0)


class WellKnownTest(TestCase):
    def test_missing_security_txt_flagged(self):
        session = MagicMock()
        session.get.return_value = NOT_FOUND
        findings = []
        check_wellknown_disclosures(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'INFO')

    def test_present_security_txt_no_finding(self):
        session = MagicMock()

        def mock_get(url, **kwargs):
            if 'security.txt' in url:
                return FakeResponse(text='Contact: mailto:security@example.com', status_code=200)
            return NOT_FOUND

        session.get.side_effect = mock_get
        findings = []
        check_wellknown_disclosures(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 0)


class DirectoryListingGenericTest(TestCase):
    def test_listing_detected(self):
        session = MagicMock()

        def mock_get(url, **kwargs):
            if '/backup/' in url:
                return FakeResponse(text='<title>Index of /backup</title>', status_code=200)
            return NOT_FOUND

        session.get.side_effect = mock_get
        findings = []
        check_directory_listing_generic(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'path_traversal')

    def test_no_listing(self):
        session = MagicMock()
        session.get.return_value = NOT_FOUND
        findings = []
        check_directory_listing_generic(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 0)


class HttpMethodsTest(TestCase):
    def test_trace_enabled_flagged(self):
        session = MagicMock()
        session.options.return_value = FakeResponse(headers={'Allow': 'GET, POST'}, status_code=200)
        session.request.return_value = FakeResponse(text='TRACE / HTTP/1.1', status_code=200)
        findings = []
        check_http_methods(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 1)
        self.assertIn('TRACE', findings[0]['evidence'])

    def test_safe_methods_only(self):
        session = MagicMock()
        session.options.return_value = FakeResponse(headers={'Allow': 'GET, POST, HEAD'}, status_code=200)
        session.request.return_value = FakeResponse(status_code=405)
        findings = []
        check_http_methods(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 0)


class OpenRedirectTest(TestCase):
    def test_redirect_to_canary_flagged(self):
        session = MagicMock()
        session.get.return_value = FakeResponse(
            status_code=302, headers={'Location': f'https://{CANARY_HOST}/'},
        )
        findings = []
        check_open_redirect(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'redirect')

    def test_no_open_redirect(self):
        session = MagicMock()
        session.get.return_value = FakeResponse(status_code=200, headers={})
        findings = []
        check_open_redirect(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 0)


class ReflectedXssTest(TestCase):
    def test_unescaped_reflection_flagged(self):
        session = MagicMock()
        session.get.return_value = FakeResponse(
            text=f'<html>You searched: {XSS_CANARY}<script></html>', status_code=200,
        )
        findings = []
        check_reflected_xss(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'HIGH')

    def test_escaped_reflection_no_finding(self):
        session = MagicMock()
        session.get.return_value = FakeResponse(
            text=f'<html>You searched: {XSS_CANARY}&lt;script&gt;</html>', status_code=200,
        )
        findings = []
        check_reflected_xss(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 0)


class PathTraversalActiveTest(TestCase):
    def test_etc_passwd_leaked(self):
        session = MagicMock()

        def mock_get(url, **kwargs):
            if 'etc/passwd' in url or '..' in url:
                return FakeResponse(
                    text='root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1::/usr/sbin:/usr/sbin/nologin',
                    status_code=200,
                )
            return NOT_FOUND

        session.get.side_effect = mock_get
        findings = []
        check_path_traversal_active(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'CRITICAL')

    def test_no_traversal(self):
        session = MagicMock()
        session.get.return_value = NOT_FOUND
        findings = []
        check_path_traversal_active(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 0)


class CrlfInjectionTest(TestCase):
    def test_injected_header_detected(self):
        session = MagicMock()

        def mock_get(url, **kwargs):
            # Extract the marker the check generated from the request URL
            # so the fake server can "reflect" it back as a real header.
            import re
            m = re.search(r'X-Vigia-CRLF-(\w+)', url)
            marker = f'X-Vigia-CRLF-{m.group(1)}' if m else 'X-Vigia-CRLF-none'
            return FakeResponse(status_code=302, headers={marker: 'injected'})

        session.get.side_effect = mock_get
        findings = []
        check_crlf_injection(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'HIGH')

    def test_no_injection(self):
        session = MagicMock()
        session.get.return_value = FakeResponse(status_code=302, headers={'Location': '/foo'})
        findings = []
        check_crlf_injection(session, 'https://example.com', findings)
        self.assertEqual(len(findings), 0)
