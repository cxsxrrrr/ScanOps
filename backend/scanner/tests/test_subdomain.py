"""
Tests for the subdomain enumeration module.

Tests crt.sh parsing, DNS wordlist resolution, and the combined
discover_subdomains function using mocks to avoid real network calls.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase

from scanner.checks.subdomain_enum import (
    enumerate_subdomains_crtsh,
    enumerate_subdomains_wordlist,
    discover_subdomains,
    _extract_root_domain,
    _resolve_subdomain,
)


class ExtractRootDomainTest(TestCase):
    """Tests for the _extract_root_domain helper."""

    def test_simple_domain(self):
        self.assertEqual(_extract_root_domain('example.com'), 'example.com')

    def test_subdomain(self):
        self.assertEqual(_extract_root_domain('www.example.com'), 'example.com')

    def test_deep_subdomain(self):
        self.assertEqual(_extract_root_domain('a.b.example.com'), 'example.com')


class CrtshEnumerationTest(TestCase):
    """Tests for Certificate Transparency enumeration via crt.sh."""

    @patch('scanner.checks.subdomain_enum.requests.get')
    def test_parses_crtsh_response(self, mock_get):
        """Valid crt.sh JSON → extracts unique subdomains."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {'name_value': 'www.example.com'},
            {'name_value': 'api.example.com\nmail.example.com'},
            {'name_value': '*.example.com'},  # wildcard — should be skipped
            {'name_value': 'api.example.com'},  # duplicate — should be deduped
        ]
        mock_get.return_value = mock_resp

        result = enumerate_subdomains_crtsh('example.com')

        self.assertIn('www.example.com', result)
        self.assertIn('api.example.com', result)
        self.assertIn('mail.example.com', result)
        self.assertNotIn('*.example.com', result)
        self.assertEqual(len(result), 3)

    @patch('scanner.checks.subdomain_enum.requests.get')
    def test_handles_crtsh_error(self, mock_get):
        """Network error → returns empty set."""
        import requests as real_requests
        mock_get.side_effect = real_requests.exceptions.Timeout()

        result = enumerate_subdomains_crtsh('example.com')

        self.assertEqual(len(result), 0)

    @patch('scanner.checks.subdomain_enum.requests.get')
    def test_handles_non_200_status(self, mock_get):
        """Non-200 status → returns empty set."""
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp

        result = enumerate_subdomains_crtsh('example.com')

        self.assertEqual(len(result), 0)


class DnsWordlistTest(TestCase):
    """Tests for DNS wordlist enumeration."""

    @patch('scanner.checks.subdomain_enum._resolve_subdomain')
    def test_finds_alive_subdomains(self, mock_resolve):
        """Resolvable subdomains are returned."""
        def side_effect(subdomain):
            if subdomain in ('www.example.com', 'api.example.com'):
                return (subdomain, '1.2.3.4')
            return None

        mock_resolve.side_effect = side_effect

        result = enumerate_subdomains_wordlist('example.com')

        subs = {r[0] for r in result}
        self.assertIn('www.example.com', subs)
        self.assertIn('api.example.com', subs)

    @patch('scanner.checks.subdomain_enum._resolve_subdomain')
    def test_no_alive_subdomains(self, mock_resolve):
        """No resolvable subdomains → empty set."""
        mock_resolve.return_value = None

        result = enumerate_subdomains_wordlist('example.com')

        self.assertEqual(len(result), 0)


class DiscoverSubdomainsTest(TestCase):
    """Tests for the combined discover_subdomains function."""

    @patch('scanner.checks.subdomain_enum.enumerate_subdomains_wordlist')
    @patch('scanner.checks.subdomain_enum.enumerate_subdomains_crtsh')
    @patch('scanner.checks.subdomain_enum._resolve_subdomain')
    def test_combines_both_sources(self, mock_resolve, mock_crtsh, mock_wordlist):
        """Results from crt.sh and DNS wordlist are combined."""
        mock_crtsh.return_value = {'api.example.com', 'dev.example.com'}
        mock_resolve.side_effect = lambda sub: (sub, '1.2.3.4')
        mock_wordlist.return_value = {('mail.example.com', '5.6.7.8')}

        result = discover_subdomains('www.example.com')

        subs = {r['subdomain'] for r in result}
        self.assertIn('api.example.com', subs)
        self.assertIn('dev.example.com', subs)
        self.assertIn('mail.example.com', subs)

    @patch('scanner.checks.subdomain_enum.enumerate_subdomains_wordlist')
    @patch('scanner.checks.subdomain_enum.enumerate_subdomains_crtsh')
    @patch('scanner.checks.subdomain_enum._resolve_subdomain')
    def test_excludes_main_hostname(self, mock_resolve, mock_crtsh, mock_wordlist):
        """The main domain itself is excluded from results."""
        mock_crtsh.return_value = {'example.com', 'api.example.com'}
        mock_resolve.side_effect = lambda sub: (sub, '1.2.3.4')
        mock_wordlist.return_value = set()

        result = discover_subdomains('example.com')

        subs = {r['subdomain'] for r in result}
        self.assertNotIn('example.com', subs)
        self.assertIn('api.example.com', subs)

    @patch('scanner.checks.subdomain_enum.enumerate_subdomains_wordlist')
    @patch('scanner.checks.subdomain_enum.enumerate_subdomains_crtsh')
    @patch('scanner.checks.subdomain_enum._resolve_subdomain')
    def test_empty_when_no_subdomains(self, mock_resolve, mock_crtsh, mock_wordlist):
        """No subdomains found → returns empty list."""
        mock_crtsh.return_value = set()
        mock_resolve.return_value = None
        mock_wordlist.return_value = set()

        result = discover_subdomains('isolated.test')

        self.assertEqual(len(result), 0)
