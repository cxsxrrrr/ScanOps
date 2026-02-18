"""
Tests for the ScanEngine — Priority 1 (Critical).

Tests passive scan checks: security headers, cookies, SSL/TLS,
information disclosure, mixed content, DNS, and error handling.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from scanner.engine import ScanEngine


class FakeResponse:
    """Helper to build mock HTTP responses."""

    def __init__(self, headers=None, cookies=None, text='', status_code=200):
        self.headers = headers or {}
        self.cookies = cookies or []
        self.text = text
        self.status_code = status_code


class FakeCookie:
    """Helper to simulate a cookie."""

    def __init__(self, name, secure=True, httponly=True, samesite=True):
        self.name = name
        self.secure = secure
        self._httponly = httponly
        self._samesite = samesite

    def has_nonstandard_attr(self, attr):
        if attr == 'HttpOnly':
            return self._httponly
        return False

    def __str__(self):
        parts = [f'{self.name}=value']
        if self._httponly:
            parts.append('HttpOnly')
        if self._samesite:
            parts.append('SameSite=Lax')
        return '; '.join(parts)


class ScanEngineSecurityHeadersTest(TestCase):
    """Tests for HTTP security header checks."""

    @patch('scanner.engine.requests.get')
    def test_missing_all_security_headers(self, mock_get):
        """All headers missing → should produce 7 findings."""
        mock_get.return_value = FakeResponse(headers={}, cookies=[])
        engine = ScanEngine('http://example.com')

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        header_findings = [f for f in findings if f['category'] == 'headers']
        self.assertEqual(len(header_findings), 7)
        titles = [f['title'] for f in header_findings]
        self.assertIn('Missing Strict-Transport-Security Header', titles)
        self.assertIn('Missing Content-Security-Policy Header', titles)
        self.assertIn('Missing X-Content-Type-Options Header', titles)
        self.assertIn('Missing X-Frame-Options Header', titles)
        self.assertIn('Missing X-XSS-Protection Header', titles)
        self.assertIn('Missing Referrer-Policy Header', titles)
        self.assertIn('Missing Permissions-Policy Header', titles)

    @patch('scanner.engine.requests.get')
    def test_all_security_headers_present(self, mock_get):
        """All headers present → 0 header findings."""
        headers = {
            'Strict-Transport-Security': 'max-age=31536000',
            'Content-Security-Policy': "default-src 'self'",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'camera=()',
        }
        mock_get.return_value = FakeResponse(headers=headers, cookies=[])
        engine = ScanEngine('http://example.com')

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        header_findings = [f for f in findings if f['category'] == 'headers']
        self.assertEqual(len(header_findings), 0)

    @patch('scanner.engine.requests.get')
    def test_hsts_missing_is_high_severity(self, mock_get):
        """Missing HSTS should be HIGH severity."""
        mock_get.return_value = FakeResponse(headers={}, cookies=[])
        engine = ScanEngine('http://example.com')

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        hsts = next(f for f in findings if 'Strict-Transport-Security' in f['title'])
        self.assertEqual(hsts['severity'], 'HIGH')

    @patch('scanner.engine.requests.get')
    def test_csp_missing_is_medium_severity(self, mock_get):
        """Missing CSP should be MEDIUM severity."""
        mock_get.return_value = FakeResponse(headers={}, cookies=[])
        engine = ScanEngine('http://example.com')

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        csp = next(f for f in findings if 'Content-Security-Policy' in f['title'])
        self.assertEqual(csp['severity'], 'MEDIUM')


class ScanEngineCookieTest(TestCase):
    """Tests for cookie security checks."""

    @patch('scanner.engine.requests.get')
    def test_insecure_cookie_detected(self, mock_get):
        """Cookie without Secure flag → finding."""
        cookie = FakeCookie('session_id', secure=False, httponly=False, samesite=False)
        mock_get.return_value = FakeResponse(headers={}, cookies=[cookie])
        engine = ScanEngine('http://example.com')

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        cookie_findings = [f for f in findings if f['category'] == 'cookies']
        self.assertEqual(len(cookie_findings), 1)
        self.assertEqual(cookie_findings[0]['severity'], 'MEDIUM')
        self.assertIn('session_id', cookie_findings[0]['title'])

    @patch('scanner.engine.requests.get')
    def test_secure_cookie_no_finding(self, mock_get):
        """Fully secure cookie → no cookie findings."""
        cookie = FakeCookie('session_id', secure=True, httponly=True, samesite=True)
        mock_get.return_value = FakeResponse(headers={}, cookies=[cookie])
        engine = ScanEngine('http://example.com')

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        cookie_findings = [f for f in findings if f['category'] == 'cookies']
        self.assertEqual(len(cookie_findings), 0)


class ScanEngineInfoDisclosureTest(TestCase):
    """Tests for information disclosure checks."""

    @patch('scanner.engine.requests.get')
    def test_server_version_disclosure(self, mock_get):
        """Server header with version → LOW finding."""
        mock_get.return_value = FakeResponse(
            headers={'Server': 'Apache/2.4.41 (Ubuntu)'},
            cookies=[],
        )
        engine = ScanEngine('http://example.com')

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        info_findings = [f for f in findings if f['category'] == 'info_disclosure']
        self.assertTrue(any('Server Version' in f['title'] for f in info_findings))

    @patch('scanner.engine.requests.get')
    def test_powered_by_disclosure(self, mock_get):
        """X-Powered-By header → LOW finding."""
        mock_get.return_value = FakeResponse(
            headers={'X-Powered-By': 'PHP/7.4'},
            cookies=[],
        )
        engine = ScanEngine('http://example.com')

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        info_findings = [f for f in findings if f['category'] == 'info_disclosure']
        self.assertTrue(any('Technology Stack' in f['title'] for f in info_findings))


class ScanEngineMixedContentTest(TestCase):
    """Tests for mixed content detection."""

    @patch('scanner.engine.requests.get')
    def test_mixed_content_detected(self, mock_get):
        """HTTPS page with HTTP references → MEDIUM finding."""
        mock_get.return_value = FakeResponse(
            headers={},
            cookies=[],
            text='<img src="http://insecure.com/image.png">',
        )
        engine = ScanEngine('https://example.com')

        with patch.object(engine, '_check_ssl'):
            with patch.object(engine, '_check_dns_records'):
                findings = engine.run()

        mixed = [f for f in findings if f['category'] == 'mixed_content']
        self.assertEqual(len(mixed), 1)
        self.assertEqual(mixed[0]['severity'], 'MEDIUM')

    @patch('scanner.engine.requests.get')
    def test_no_mixed_content_on_http(self, mock_get):
        """HTTP page → no mixed content check."""
        mock_get.return_value = FakeResponse(
            headers={},
            cookies=[],
            text='<img src="http://example.com/image.png">',
        )
        engine = ScanEngine('http://example.com')

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        mixed = [f for f in findings if f['category'] == 'mixed_content']
        self.assertEqual(len(mixed), 0)


class ScanEngineErrorHandlingTest(TestCase):
    """Tests for network error handling."""

    @patch('scanner.engine.requests.get')
    def test_connection_timeout(self, mock_get):
        """Timeout → MEDIUM finding."""
        import requests as real_requests
        mock_get.side_effect = real_requests.exceptions.Timeout()
        engine = ScanEngine('http://example.com')
        findings = engine.run()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'MEDIUM')
        self.assertIn('Timeout', findings[0]['title'])

    @patch('scanner.engine.requests.get')
    def test_connection_error(self, mock_get):
        """Connection error → HIGH finding."""
        import requests as real_requests
        mock_get.side_effect = real_requests.exceptions.ConnectionError('refused')
        engine = ScanEngine('http://unreachable.test')
        findings = engine.run()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'HIGH')
        self.assertIn('Connection Error', findings[0]['title'])

    @patch('scanner.engine.requests.get')
    def test_ssl_error(self, mock_get):
        """SSL error → HIGH finding."""
        import requests as real_requests
        mock_get.side_effect = real_requests.exceptions.SSLError('cert invalid')
        engine = ScanEngine('https://bad-ssl.test')
        findings = engine.run()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'HIGH')
        self.assertIn('SSL', findings[0]['title'])
