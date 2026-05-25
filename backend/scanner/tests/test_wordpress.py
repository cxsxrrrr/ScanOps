"""
Tests for the WordPress scanner module.

Tests detection, version extraction, enumeration, and
misconfiguration checks using mocked HTTP responses.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase

from scanner.checks.wordpress import (
    detect_wordpress,
    extract_wp_version,
    enumerate_themes,
    enumerate_plugins,
    check_wordpress,
)


class FakeResponse:
    """Helper to build mock HTTP responses."""

    def __init__(self, text='', status_code=200, headers=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}


class DetectWordPressTest(TestCase):
    """Tests for WordPress detection."""

    def test_detects_wp_content(self):
        resp = FakeResponse(text='<link rel="stylesheet" href="/wp-content/themes/mytheme/style.css">')
        self.assertTrue(detect_wordpress(resp))

    def test_detects_generator_meta(self):
        resp = FakeResponse(text='<meta name="generator" content="WordPress 6.4.2">')
        self.assertTrue(detect_wordpress(resp))

    def test_no_wordpress(self):
        resp = FakeResponse(text='<html><body>Hello World</body></html>')
        self.assertFalse(detect_wordpress(resp))

    def test_detects_wp_json(self):
        resp = FakeResponse(text='<link rel="alternate" href="/wp-json/">')
        self.assertTrue(detect_wordpress(resp))

    def test_detects_x_powered_by(self):
        resp = FakeResponse(text='<html></html>', headers={'X-Powered-By': 'WordPress'})
        self.assertTrue(detect_wordpress(resp))


class ExtractVersionTest(TestCase):
    """Tests for WordPress version extraction."""

    def test_extracts_from_meta(self):
        resp = FakeResponse(text='<meta name="generator" content="WordPress 6.4.2">')
        session = MagicMock()
        version = extract_wp_version(resp, session, 'https://example.com')
        self.assertEqual(version, '6.4.2')

    def test_returns_none_for_no_version(self):
        resp = FakeResponse(text='<html>No WordPress here</html>')
        session = MagicMock()
        import requests as real_requests
        session.get.side_effect = real_requests.exceptions.ConnectionError()
        version = extract_wp_version(resp, session, 'https://example.com')
        self.assertIsNone(version)


class EnumerationTest(TestCase):
    """Tests for theme and plugin enumeration."""

    def test_enumerate_themes(self):
        body = (
            '<link rel="stylesheet" href="/wp-content/themes/twentytwenty/style.css">'
            '<link rel="stylesheet" href="/wp-content/themes/astra/style.css">'
        )
        themes = enumerate_themes(body)
        self.assertEqual(themes, {'twentytwenty', 'astra'})

    def test_enumerate_plugins(self):
        body = (
            '<script src="/wp-content/plugins/akismet/script.js"></script>'
            '<script src="/wp-content/plugins/contact-form-7/js/main.js"></script>'
        )
        plugins = enumerate_plugins(body)
        self.assertEqual(plugins, {'akismet', 'contact-form-7'})

    def test_no_themes(self):
        self.assertEqual(enumerate_themes('<html>No WP</html>'), set())

    def test_no_plugins(self):
        self.assertEqual(enumerate_plugins('<html>No WP</html>'), set())


class CheckWordPressTest(TestCase):
    """Integration tests for the main check_wordpress function."""

    def test_skips_non_wordpress(self):
        """Non-WordPress site → no findings."""
        resp = FakeResponse(text='<html>Regular site</html>')
        session = MagicMock()
        findings = []
        check_wordpress(resp, session, 'https://example.com', findings)
        self.assertEqual(len(findings), 0)

    def test_detects_wordpress_with_version(self):
        """WordPress with version → detection + version findings."""
        resp = FakeResponse(
            text=(
                '<meta name="generator" content="WordPress 5.9.1">'
                '<link href="/wp-content/themes/mytheme/style.css">'
            ),
        )
        session = MagicMock()
        # Make all probe requests return 404
        probe_resp = FakeResponse(text='Not Found', status_code=404)
        session.get.return_value = probe_resp
        session.post.return_value = probe_resp

        findings = []
        check_wordpress(resp, session, 'https://example.com', findings)

        titles = [f['title'] for f in findings]
        self.assertIn('WordPress Installation Detected', titles)
        self.assertTrue(any('5.9.1' in t for t in titles))
        self.assertTrue(any('Outdated' in t for t in titles))

    def test_detects_dangerous_plugin(self):
        """Known dangerous plugin → HIGH finding."""
        resp = FakeResponse(
            text=(
                '<meta name="generator" content="WordPress 6.4">'
                '<script src="/wp-content/plugins/wp-file-manager/js/main.js"></script>'
            ),
        )
        session = MagicMock()
        probe_resp = FakeResponse(text='Not Found', status_code=404)
        session.get.return_value = probe_resp
        session.post.return_value = probe_resp

        findings = []
        check_wordpress(resp, session, 'https://example.com', findings)

        plugin_findings = [f for f in findings if 'High-Risk Plugin' in f['title']]
        self.assertEqual(len(plugin_findings), 1)
        self.assertEqual(plugin_findings[0]['severity'], 'HIGH')

    def test_detects_debug_log(self):
        """Exposed debug.log → CRITICAL finding."""
        resp = FakeResponse(
            text='<meta name="generator" content="WordPress 6.4">',
        )
        session = MagicMock()

        def mock_get(url, **kwargs):
            if 'debug.log' in url:
                return FakeResponse(
                    text='[25-Feb-2026] PHP Warning: something in /var/www/...',
                    status_code=200,
                )
            return FakeResponse(text='Not Found', status_code=404)

        session.get.side_effect = mock_get
        session.post.return_value = FakeResponse(text='', status_code=404)

        findings = []
        check_wordpress(resp, session, 'https://example.com', findings)

        debug_findings = [f for f in findings if 'Debug Log' in f['title']]
        self.assertEqual(len(debug_findings), 1)
        self.assertEqual(debug_findings[0]['severity'], 'CRITICAL')

    def test_detects_xmlrpc(self):
        """XML-RPC enabled → MEDIUM finding."""
        resp = FakeResponse(
            text='<meta name="generator" content="WordPress 6.4">',
        )
        session = MagicMock()

        session.get.return_value = FakeResponse(text='Not Found', status_code=404)
        session.post.return_value = FakeResponse(
            text='<?xml version="1.0"?><methodResponse><params></params></methodResponse>',
            status_code=200,
        )

        findings = []
        check_wordpress(resp, session, 'https://example.com', findings)

        xmlrpc_findings = [f for f in findings if 'XML-RPC' in f['title']]
        self.assertEqual(len(xmlrpc_findings), 1)
        self.assertEqual(xmlrpc_findings[0]['severity'], 'MEDIUM')

    def test_detects_user_enumeration(self):
        """REST API users endpoint open → user enumeration finding."""
        resp = FakeResponse(
            text='<meta name="generator" content="WordPress 6.4">',
        )
        session = MagicMock()

        def mock_get(url, **kwargs):
            if '/wp-json/wp/v2/users' in url:
                r = FakeResponse(text='', status_code=200)
                r.json = lambda: [{'name': 'admin', 'slug': 'admin'}]
                return r
            return FakeResponse(text='Not Found', status_code=404)

        session.get.side_effect = mock_get
        session.post.return_value = FakeResponse(text='', status_code=404)

        findings = []
        check_wordpress(resp, session, 'https://example.com', findings)

        user_findings = [f for f in findings if 'User Enumeration' in f['title']]
        self.assertEqual(len(user_findings), 1)
        self.assertEqual(user_findings[0]['severity'], 'HIGH')  # admin user found
