"""
Tests for the technology fingerprinting module.

Tests detection rules, version extraction, and vulnerability checking
using mock HTTP responses.
"""
from unittest.mock import MagicMock
from django.test import TestCase

from scanner.checks.tech_fingerprint import (
    fingerprint_technologies,
    check_technologies,
    _is_version_below,
)


class FakeResponse:
    """Minimal mock response."""

    def __init__(self, text='', headers=None, cookies=None):
        self.text = text
        self.headers = headers or {}
        self.cookies = cookies or {}


class VersionComparisonTest(TestCase):
    """Tests for version comparison helper."""

    def test_below(self):
        self.assertTrue(_is_version_below('2.4.49', '2.4.58'))

    def test_equal(self):
        self.assertFalse(_is_version_below('2.4.58', '2.4.58'))

    def test_above(self):
        self.assertFalse(_is_version_below('2.4.60', '2.4.58'))

    def test_major_below(self):
        self.assertTrue(_is_version_below('1.22.0', '1.25.4'))

    def test_invalid(self):
        self.assertFalse(_is_version_below('abc', '1.0'))


class DetectionTest(TestCase):
    """Tests for technology detection from various sources."""

    def test_detect_apache(self):
        resp = FakeResponse(headers={'Server': 'Apache/2.4.41 (Ubuntu)'})
        techs = fingerprint_technologies(resp)
        names = {t['name'] for t in techs}
        self.assertIn('Apache', names)
        apache = next(t for t in techs if t['name'] == 'Apache')
        self.assertEqual(apache['version'], '2.4.41')

    def test_detect_nginx(self):
        resp = FakeResponse(headers={'Server': 'nginx/1.18.0'})
        techs = fingerprint_technologies(resp)
        names = {t['name'] for t in techs}
        self.assertIn('Nginx', names)

    def test_detect_php(self):
        resp = FakeResponse(headers={'X-Powered-By': 'PHP/8.1.2'})
        techs = fingerprint_technologies(resp)
        names = {t['name'] for t in techs}
        self.assertIn('PHP', names)
        php = next(t for t in techs if t['name'] == 'PHP')
        self.assertEqual(php['version'], '8.1.2')

    def test_detect_jquery(self):
        resp = FakeResponse(text='<script src="/js/jquery-3.3.1.min.js"></script>')
        techs = fingerprint_technologies(resp)
        names = {t['name'] for t in techs}
        self.assertIn('jQuery', names)
        jq = next(t for t in techs if t['name'] == 'jQuery')
        self.assertEqual(jq['version'], '3.3.1')

    def test_detect_bootstrap(self):
        resp = FakeResponse(
            text='<link href="/css/bootstrap-5.3.2.min.css" rel="stylesheet">'
        )
        techs = fingerprint_technologies(resp)
        names = {t['name'] for t in techs}
        self.assertIn('Bootstrap', names)

    def test_detect_react(self):
        resp = FakeResponse(text='<div data-reactroot></div>')
        techs = fingerprint_technologies(resp)
        names = {t['name'] for t in techs}
        self.assertIn('React', names)

    def test_detect_vue(self):
        resp = FakeResponse(text='<div data-v-abc123>Vue app</div>')
        techs = fingerprint_technologies(resp)
        names = {t['name'] for t in techs}
        self.assertIn('Vue.js', names)

    def test_detect_cloudflare(self):
        resp = FakeResponse(headers={'cf-ray': '12345abc', 'Server': 'cloudflare'})
        techs = fingerprint_technologies(resp)
        names = {t['name'] for t in techs}
        self.assertIn('Cloudflare', names)

    def test_detect_express(self):
        resp = FakeResponse(headers={'X-Powered-By': 'Express'})
        techs = fingerprint_technologies(resp)
        names = {t['name'] for t in techs}
        self.assertIn('Express', names)
        self.assertIn('Node.js', names)

    def test_no_tech(self):
        resp = FakeResponse(text='<html>plain page</html>', headers={})
        techs = fingerprint_technologies(resp)
        self.assertEqual(len(techs), 0)


class VulnerabilityCheckTest(TestCase):
    """Tests for vulnerability checking against known CVEs."""

    def test_vulnerable_jquery(self):
        """Old jQuery → vulnerability finding."""
        resp = FakeResponse(text='<script src="/jquery-1.11.3.min.js"></script>')
        findings = []
        check_technologies(resp, MagicMock(), findings)

        vuln_findings = [f for f in findings if 'Vulnerable' in f.get('title', '')]
        self.assertTrue(len(vuln_findings) > 0)
        self.assertIn('jQuery', vuln_findings[0]['title'])

    def test_safe_jquery(self):
        """Current jQuery → no vulnerability finding."""
        resp = FakeResponse(text='<script src="/jquery-3.7.1.min.js"></script>')
        findings = []
        check_technologies(resp, MagicMock(), findings)

        vuln_findings = [f for f in findings if 'Vulnerable' in f.get('title', '')]
        self.assertEqual(len(vuln_findings), 0)

    def test_vulnerable_apache(self):
        """Old Apache → vulnerability finding."""
        resp = FakeResponse(headers={'Server': 'Apache/2.4.29'})
        findings = []
        check_technologies(resp, MagicMock(), findings)

        vuln_findings = [f for f in findings if 'Vulnerable' in f.get('title', '')]
        self.assertTrue(len(vuln_findings) > 0)
        self.assertEqual(vuln_findings[0]['category'], 'technology')

    def test_technologies_summary(self):
        """Multiple techs → summary INFO finding."""
        resp = FakeResponse(
            text='<script src="/jquery-3.6.0.min.js"></script>',
            headers={'Server': 'nginx/1.24.0'},
        )
        findings = []
        check_technologies(resp, MagicMock(), findings)

        summary = [f for f in findings if 'Technologies Detected' in f.get('title', '')]
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]['severity'], 'INFO')

    def test_vulnerable_php(self):
        """Old PHP → CRITICAL finding."""
        resp = FakeResponse(headers={'X-Powered-By': 'PHP/7.2.5'})
        findings = []
        check_technologies(resp, MagicMock(), findings)

        vuln_findings = [f for f in findings if 'Vulnerable' in f.get('title', '')]
        self.assertTrue(len(vuln_findings) > 0)
        self.assertIn('CRITICAL', vuln_findings[0]['severity'])
