"""Tests for the headers_extra passive check module."""
from unittest.mock import MagicMock
from urllib.parse import urlparse
from django.test import TestCase

from scanner.checks.headers_extra import (
    check_coop_coep_corp, check_csp_quality, check_referrer_policy_quality,
    check_sri_missing, check_postmessage_origin,
)


def _mock_response(body='', headers=None, url='https://example.com'):
    resp = MagicMock()
    resp.text = body
    resp.headers = headers or {}
    resp.url = url
    return resp


class CoopCoepCorpTest(TestCase):
    def test_missing_both_headers(self):
        resp = _mock_response(headers={})
        findings = []
        check_coop_coep_corp(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 2)
        titles = [f['title'] for f in findings]
        self.assertIn('Missing Cross-Origin-Opener-Policy Header', titles)
        self.assertIn('Missing Cross-Origin-Resource-Policy Header', titles)

    def test_both_present_no_findings(self):
        resp = _mock_response(headers={
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin',
        })
        findings = []
        check_coop_coep_corp(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 0)


class CspQualityTest(TestCase):
    def test_unsafe_inline_flagged(self):
        resp = _mock_response(headers={'Content-Security-Policy': "default-src 'self' 'unsafe-inline'"})
        findings = []
        check_csp_quality(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'MEDIUM')
        self.assertIn('unsafe-inline', findings[0]['description'])

    def test_strict_csp_no_finding(self):
        resp = _mock_response(headers={'Content-Security-Policy': "default-src 'self'"})
        findings = []
        check_csp_quality(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 0)

    def test_no_csp_header_no_finding(self):
        """Absence is the base header check's job, not this one's."""
        resp = _mock_response(headers={})
        findings = []
        check_csp_quality(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 0)


class ReferrerPolicyQualityTest(TestCase):
    def test_unsafe_url_flagged(self):
        resp = _mock_response(headers={'Referrer-Policy': 'unsafe-url'})
        findings = []
        check_referrer_policy_quality(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'LOW')

    def test_strict_policy_no_finding(self):
        resp = _mock_response(headers={'Referrer-Policy': 'strict-origin-when-cross-origin'})
        findings = []
        check_referrer_policy_quality(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 0)


class SriMissingTest(TestCase):
    def test_third_party_script_without_integrity(self):
        body = '<html><script src="https://cdn.example.net/lib.js"></script></html>'
        resp = _mock_response(body=body, headers={'Content-Type': 'text/html'})
        findings = []
        check_sri_missing(resp, urlparse('https://mysite.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'sri')

    def test_third_party_script_with_integrity_ok(self):
        body = (
            '<html><script src="https://cdn.example.net/lib.js" '
            'integrity="sha384-abc" crossorigin="anonymous"></script></html>'
        )
        resp = _mock_response(body=body, headers={'Content-Type': 'text/html'})
        findings = []
        check_sri_missing(resp, urlparse('https://mysite.com'), findings)
        self.assertEqual(len(findings), 0)

    def test_same_origin_script_ignored(self):
        body = '<html><script src="https://mysite.com/app.js"></script></html>'
        resp = _mock_response(body=body, headers={'Content-Type': 'text/html'})
        findings = []
        check_sri_missing(resp, urlparse('https://mysite.com'), findings)
        self.assertEqual(len(findings), 0)


class PostMessageOriginTest(TestCase):
    def test_missing_origin_check_flagged(self):
        body = '<script>window.addEventListener("message", function(e) { doStuff(e.data); });</script>'
        resp = _mock_response(body=body, headers={'Content-Type': 'text/html'})
        findings = []
        check_postmessage_origin(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'postmessage')

    def test_origin_check_present_no_finding(self):
        body = (
            '<script>window.addEventListener("message", function(e) { '
            'if (e.origin !== "https://trusted.com") return; doStuff(e.data); });</script>'
        )
        resp = _mock_response(body=body, headers={'Content-Type': 'text/html'})
        findings = []
        check_postmessage_origin(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 0)
