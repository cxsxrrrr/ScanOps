"""
Tests for the ScanEngine — Priority 1 (Critical).

Tests passive scan checks: security headers, cookies, SSL/TLS,
information disclosure, mixed content, DNS, and error handling.
"""
from unittest.mock import patch, MagicMock, PropertyMock
from django.test import TestCase
from scanner.engine import ScanEngine


class FakeResponse:
    """Helper to build mock HTTP responses."""

    def __init__(self, headers=None, cookies=None, text='', status_code=200, url='http://example.com'):
        self.headers = headers or {}
        self.cookies = cookies or []
        self.text = text
        self.status_code = status_code
        self.url = url


class FakeCookie:
    """Helper to simulate a cookie."""

    def __init__(self, name, secure=True, httponly=True, samesite=True):
        self.name = name
        self.secure = secure
        self._httponly = httponly
        self._samesite = samesite
        self.path = '/'

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


def _patch_engine_session(engine, fake_response):
    """Patch the Session.get on a ScanEngine instance."""
    engine._session.get = MagicMock(return_value=fake_response)


class ScanEngineSecurityHeadersTest(TestCase):
    """Tests for HTTP security header checks."""

    def test_missing_all_security_headers(self):
        """All headers missing → should produce 7 core header findings."""
        engine = ScanEngine('http://example.com')
        _patch_engine_session(engine, FakeResponse(headers={}, cookies=[]))

        with patch.object(engine, '_check_dns_records'):
            with patch.object(engine, '_run_extended_checks'):
                with patch.object(engine, '_crawl_and_check'):
                    with patch.object(engine, '_discover_and_scan_subdomains'):
                        with patch.object(engine, '_check_cookie_security'):
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

    def test_all_security_headers_present(self):
        """All headers present → 0 core header findings."""
        headers = {
            'Strict-Transport-Security': 'max-age=31536000',
            'Content-Security-Policy': "default-src 'self'",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'camera=()',
        }
        engine = ScanEngine('http://example.com')
        _patch_engine_session(engine, FakeResponse(headers=headers, cookies=[]))

        with patch.object(engine, '_check_dns_records'):
            with patch.object(engine, '_run_extended_checks'):
                with patch.object(engine, '_crawl_and_check'):
                    with patch.object(engine, '_discover_and_scan_subdomains'):
                        with patch.object(engine, '_check_cookie_security'):
                            findings = engine.run()

        header_findings = [f for f in findings if f['category'] == 'headers']
        self.assertEqual(len(header_findings), 0)

    def test_hsts_missing_is_high_severity(self):
        """Missing HSTS should be HIGH severity."""
        engine = ScanEngine('http://example.com')
        _patch_engine_session(engine, FakeResponse(headers={}, cookies=[]))

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        hsts = next(f for f in findings if 'Strict-Transport-Security' in f['title'])
        self.assertEqual(hsts['severity'], 'HIGH')

    def test_csp_missing_is_medium_severity(self):
        """Missing CSP should be MEDIUM severity."""
        engine = ScanEngine('http://example.com')
        _patch_engine_session(engine, FakeResponse(headers={}, cookies=[]))

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        csp = next(f for f in findings if 'Content-Security-Policy' in f['title'])
        self.assertEqual(csp['severity'], 'MEDIUM')


class ScanEngineCookieTest(TestCase):
    """Tests for cookie security checks."""

    def test_insecure_cookie_detected(self):
        """Cookie without Secure flag → finding."""
        cookie = FakeCookie('session_id', secure=False, httponly=False, samesite=False)
        engine = ScanEngine('http://example.com')
        _patch_engine_session(engine, FakeResponse(headers={}, cookies=[cookie]))

        with patch.object(engine, '_check_dns_records'):
            with patch.object(engine, '_run_extended_checks'):
                with patch.object(engine, '_crawl_and_check'):
                    with patch.object(engine, '_discover_and_scan_subdomains'):
                        with patch.object(engine, '_check_security_headers'):
                            with patch.object(engine, '_check_info_disclosure'):
                                with patch.object(engine, '_check_mixed_content'):
                                    findings = engine.run()

        cookie_findings = [f for f in findings if f['category'] == 'cookies']
        self.assertTrue(len(cookie_findings) >= 1)
        self.assertIn('session_id', cookie_findings[0]['title'])

    def test_secure_cookie_no_finding(self):
        """Fully secure cookie → no cookie findings."""
        cookie = FakeCookie('my_cookie', secure=True, httponly=True, samesite=True)
        engine = ScanEngine('http://example.com')
        _patch_engine_session(engine, FakeResponse(headers={}, cookies=[cookie]))

        with patch.object(engine, '_check_dns_records'):
            with patch.object(engine, '_run_extended_checks'):
                with patch.object(engine, '_crawl_and_check'):
                    with patch.object(engine, '_discover_and_scan_subdomains'):
                        with patch.object(engine, '_check_security_headers'):
                            with patch.object(engine, '_check_info_disclosure'):
                                with patch.object(engine, '_check_mixed_content'):
                                    findings = engine.run()

        cookie_findings = [f for f in findings if f['category'] == 'cookies']
        self.assertEqual(len(cookie_findings), 0)


class ScanEngineInfoDisclosureTest(TestCase):
    """Tests for information disclosure checks."""

    def test_server_version_disclosure(self):
        """Server header with version → LOW finding."""
        engine = ScanEngine('http://example.com')
        _patch_engine_session(engine, FakeResponse(
            headers={'Server': 'Apache/2.4.41 (Ubuntu)'},
            cookies=[],
        ))

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        info_findings = [f for f in findings if f['category'] == 'info_disclosure']
        self.assertTrue(any('Server Version' in f['title'] for f in info_findings))

    def test_powered_by_disclosure(self):
        """X-Powered-By header → LOW finding."""
        engine = ScanEngine('http://example.com')
        _patch_engine_session(engine, FakeResponse(
            headers={'X-Powered-By': 'PHP/7.4'},
            cookies=[],
        ))

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        info_findings = [f for f in findings if f['category'] == 'info_disclosure']
        self.assertTrue(any('Technology Stack' in f['title'] for f in info_findings))


class ScanEngineMixedContentTest(TestCase):
    """Tests for mixed content detection."""

    def test_mixed_content_detected(self):
        """HTTPS page with HTTP references → MEDIUM finding."""
        engine = ScanEngine('https://example.com')
        _patch_engine_session(engine, FakeResponse(
            headers={},
            cookies=[],
            text='<img src="http://insecure.com/image.png">',
        ))

        with patch.object(engine, '_check_ssl'):
            with patch.object(engine, '_check_dns_records'):
                findings = engine.run()

        mixed = [f for f in findings if f['category'] == 'mixed_content']
        self.assertEqual(len(mixed), 1)
        self.assertEqual(mixed[0]['severity'], 'MEDIUM')

    def test_no_mixed_content_on_http(self):
        """HTTP page → no mixed content check."""
        engine = ScanEngine('http://example.com')
        _patch_engine_session(engine, FakeResponse(
            headers={},
            cookies=[],
            text='<img src="http://example.com/image.png">',
        ))

        with patch.object(engine, '_check_dns_records'):
            findings = engine.run()

        mixed = [f for f in findings if f['category'] == 'mixed_content']
        self.assertEqual(len(mixed), 0)


class ScanEngineErrorHandlingTest(TestCase):
    """Tests for network error handling."""

    def test_connection_timeout(self):
        """Timeout → MEDIUM finding."""
        import requests as real_requests
        engine = ScanEngine('http://example.com')
        engine._session.get = MagicMock(side_effect=real_requests.exceptions.Timeout())
        findings = engine.run()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'MEDIUM')
        self.assertIn('Timeout', findings[0]['title'])

    def test_connection_error(self):
        """Connection error → HIGH finding."""
        import requests as real_requests
        engine = ScanEngine('http://unreachable.test')
        engine._session.get = MagicMock(
            side_effect=real_requests.exceptions.ConnectionError('refused')
        )
        findings = engine.run()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'HIGH')
        self.assertIn('Connection Error', findings[0]['title'])

    def test_ssl_error(self):
        """SSL error → HIGH finding."""
        import requests as real_requests
        engine = ScanEngine('https://bad-ssl.test')
        engine._session.get = MagicMock(
            side_effect=real_requests.exceptions.SSLError('cert invalid')
        )
        findings = engine.run()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'HIGH')
        self.assertIn('SSL', findings[0]['title'])
