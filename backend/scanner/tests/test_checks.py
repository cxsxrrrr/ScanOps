"""
Unit tests for the new vulnerability check modules.

Tests representative checks from each module (injection, access_control,
auth, app_security) using mocked HTTP responses.
"""
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse
from django.test import TestCase

from scanner.checks.injection import (
    check_sqli, check_xss, check_nosql_injection,
    check_cmd_injection, check_xxe, check_ssti,
)
from scanner.checks.access_control import (
    check_csrf, check_clickjacking, check_cors,
    check_ssrf, check_path_traversal, check_access_control,
    check_host_header,
)
from scanner.checks.auth import (
    check_auth, check_jwt, check_oauth, check_websockets,
)
from scanner.checks.app_security import (
    check_http_smuggling, check_cache_poisoning, check_deserialization,
    check_file_upload, check_graphql, check_api_security,
    check_cache_deception, check_llm,
)


def _mock_response(body='', headers=None, url='https://example.com'):
    """Build a mock requests.Response with given body and headers."""
    resp = MagicMock()
    resp.text = body
    resp.headers = headers or {}
    resp.url = url
    return resp


class InjectionChecksTest(TestCase):
    """Tests for injection-related passive checks."""

    def test_sqli_detects_mysql_error(self):
        body = '<html>You have an error in your SQL syntax near something</html>'
        resp = _mock_response(body=body)
        findings = []
        check_sqli(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'sqli')
        self.assertEqual(findings[0]['severity'], 'HIGH')

    def test_sqli_clean_page(self):
        resp = _mock_response(body='<html>Normal page</html>')
        findings = []
        check_sqli(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 0)

    def test_xss_dom_sinks(self):
        body = '<script>document.getElementById("x").innerHTML = data;</script>'
        resp = _mock_response(body=body, headers={'Content-Type': 'text/html; charset=utf-8'})
        findings = []
        check_xss(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'xss')

    def test_xss_missing_charset(self):
        resp = _mock_response(body='<html></html>', headers={'Content-Type': 'text/html'})
        findings = []
        check_xss(resp, urlparse('https://example.com'), findings)
        self.assertTrue(any(f['title'] == 'Missing Charset in Content-Type' for f in findings))

    def test_nosql_detects_mongo_error(self):
        body = '<html>MongoError: connection refused</html>'
        resp = _mock_response(body=body)
        findings = []
        check_nosql_injection(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'nosqli')

    def test_cmd_injection_cgi_bin(self):
        body = '<a href="/cgi-bin/test.cgi">link</a>'
        resp = _mock_response(body=body)
        findings = []
        check_cmd_injection(resp, urlparse('https://example.com'), findings)
        self.assertTrue(any(f['category'] == 'cmd_injection' for f in findings))

    def test_xxe_xml_content_type(self):
        resp = _mock_response(body='<root/>', headers={'Content-Type': 'application/xml'})
        findings = []
        check_xxe(resp, urlparse('https://example.com'), findings)
        self.assertTrue(any(f['category'] == 'xxe' for f in findings))

    def test_ssti_detects_jinja2(self):
        body = '<html>jinja2.exceptions.UndefinedError: x is undefined</html>'
        resp = _mock_response(body=body)
        findings = []
        check_ssti(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'ssti')


class AccessControlChecksTest(TestCase):
    """Tests for access control passive checks."""

    def test_csrf_missing_token(self):
        body = '<form method="post"><input type="text" name="q"><button>Submit</button></form>'
        resp = _mock_response(body=body, headers={'Content-Type': 'text/html; charset=utf-8'})
        findings = []
        check_csrf(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'csrf')

    def test_csrf_with_token(self):
        body = '<form method="post"><input type="hidden" name="csrfmiddlewaretoken" value="abc"></form>'
        resp = _mock_response(body=body, headers={'Content-Type': 'text/html; charset=utf-8'})
        findings = []
        check_csrf(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 0)

    def test_clickjacking_no_protection(self):
        resp = _mock_response(headers={'Content-Type': 'text/html'})
        findings = []
        check_clickjacking(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'clickjacking')

    def test_clickjacking_with_xfo(self):
        resp = _mock_response(headers={'X-Frame-Options': 'DENY'})
        findings = []
        check_clickjacking(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 0)

    def test_cors_wildcard(self):
        resp = _mock_response(headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': 'true',
        })
        findings = []
        check_cors(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'HIGH')

    def test_cors_null_origin(self):
        resp = _mock_response(headers={'Access-Control-Allow-Origin': 'null'})
        findings = []
        check_cors(resp, urlparse('https://example.com'), findings)
        self.assertTrue(any(f['category'] == 'cors' for f in findings))

    def test_ssrf_internal_ip(self):
        findings = []
        parsed = urlparse('https://example.com/api?url=http://192.168.1.1/admin')
        check_ssrf(_mock_response(), parsed, findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'ssrf')

    def test_path_traversal_dir_listing(self):
        body = '<html><title>Index of /var/www</title></html>'
        resp = _mock_response(body=body)
        findings = []
        check_path_traversal(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'path_traversal')

    def test_access_control_debug_mode(self):
        body = '<html>Traceback (most recent call last):\n  File "app.py"</html>'
        resp = _mock_response(body=body)
        findings = []
        check_access_control(resp, urlparse('https://example.com'), findings)
        self.assertTrue(any(f['title'] == 'Debug Information Exposed' for f in findings))


class AuthChecksTest(TestCase):
    """Tests for authentication passive checks."""

    def test_login_over_http(self):
        body = '<form><input type="password" name="pwd"></form>'
        resp = _mock_response(body=body, headers={'Content-Type': 'text/html'})
        findings = []
        check_auth(resp, urlparse('http://example.com/login'), findings)
        self.assertTrue(any(f['severity'] == 'CRITICAL' for f in findings))

    def test_jwt_in_url(self):
        findings = []
        parsed = urlparse(
            'https://example.com/api?token=eyJhbGciOiJIUzI1NiJ9.'
            'eyJzdWIiOiIxMjM0NTY3ODkwIn0.'
            'dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U'
        )
        check_jwt(_mock_response(), parsed, findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'jwt')

    def test_oauth_http_redirect(self):
        body = 'redirect_uri=http://example.com/callback'
        resp = _mock_response(body=body)
        findings = []
        check_oauth(resp, urlparse('https://example.com'), findings)
        self.assertTrue(any(f['category'] == 'oauth' for f in findings))

    def test_insecure_websocket(self):
        body = '<script>var ws = new WebSocket("ws://example.com/ws");</script>'
        resp = _mock_response(body=body)
        findings = []
        check_websockets(resp, urlparse('https://example.com'), findings)
        self.assertTrue(any(f['category'] == 'websockets' for f in findings))


class AppSecurityChecksTest(TestCase):
    """Tests for application-level security checks."""

    def test_http_smuggling_dual_headers(self):
        resp = _mock_response(headers={
            'Content-Length': '100',
            'Transfer-Encoding': 'chunked',
        })
        findings = []
        check_http_smuggling(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'http_smuggling')

    def test_cache_poisoning_no_vary(self):
        resp = _mock_response(headers={'X-Cache': 'HIT'})
        findings = []
        check_cache_poisoning(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'cache_poisoning')

    def test_deserialization_java(self):
        body = 'data=rO0ABXNyABlqYXZhLnV0aWwuSGFzaE1hcA'
        resp = _mock_response(body=body)
        findings = []
        check_deserialization(resp, urlparse('https://example.com'), findings)
        self.assertTrue(any(f['category'] == 'deserialization' for f in findings))

    def test_file_upload_no_accept(self):
        body = '<form><input type="file" name="doc"></form>'
        resp = _mock_response(body=body)
        findings = []
        check_file_upload(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'file_upload')

    def test_graphql_introspection(self):
        body = '{"data":{"__schema":{"types":[]}}}'
        resp = _mock_response(body=body)
        findings = []
        check_graphql(resp, urlparse('https://example.com'), findings)
        self.assertTrue(any(f['category'] == 'graphql' for f in findings))

    def test_api_swagger_exposed(self):
        body = '<html><div id="swagger-ui"></div></html>'
        resp = _mock_response(body=body)
        findings = []
        check_api_security(resp, urlparse('https://example.com'), findings)
        self.assertTrue(any(f['category'] == 'api' for f in findings))

    def test_cache_deception_public_auth(self):
        resp = _mock_response(headers={
            'Set-Cookie': 'session=abc',
            'Cache-Control': 'public, max-age=3600',
        })
        findings = []
        check_cache_deception(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['category'], 'cache_deception')

    def test_llm_api_key_exposed(self):
        body = 'const KEY = "sk-abcdefghijklmnopqrstuvwxyz1234567890"'
        resp = _mock_response(body=body)
        findings = []
        check_llm(resp, urlparse('https://example.com'), findings)
        self.assertTrue(any(f['severity'] == 'CRITICAL' for f in findings))

    def test_llm_clean_page(self):
        body = '<html>Normal business page</html>'
        resp = _mock_response(body=body)
        findings = []
        check_llm(resp, urlparse('https://example.com'), findings)
        self.assertEqual(len(findings), 0)
