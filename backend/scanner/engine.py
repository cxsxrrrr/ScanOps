"""
Core scan engine for passive security analysis.

Performs non-intrusive checks: HTTP headers, SSL/TLS, cookies,
information disclosure, and DNS configuration.
"""
import logging
import socket
import ssl
import requests
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger('scanner')


class ScanEngine:
    """Passive security scanner for web URLs."""

    def __init__(self, url, timeout=30):
        self.url = url
        self.timeout = timeout
        self.findings = []
        self.parsed_url = urlparse(url)

    def run(self):
        """Execute all scan checks and return findings."""
        logger.info(f"Starting scan for: {self.url}")

        try:
            response = requests.get(
                self.url,
                timeout=self.timeout,
                allow_redirects=True,
                headers={'User-Agent': 'AuditoriaWeb-Scanner/1.0'},
                verify=True,
            )

            self._check_security_headers(response)
            self._check_cookie_security(response)
            self._check_info_disclosure(response)
            self._check_mixed_content(response)

            if self.parsed_url.scheme == 'https':
                self._check_ssl(self.parsed_url.hostname)

            self._check_dns_records(self.parsed_url.hostname)

        except requests.exceptions.SSLError as e:
            self.findings.append({
                'title': 'SSL/TLS Connection Error',
                'severity': 'HIGH',
                'category': 'ssl',
                'description': f'Failed to establish secure connection: {str(e)}',
                'recommendation': 'Ensure the SSL/TLS certificate is valid and properly configured.',
                'evidence': str(e),
            })
        except requests.exceptions.ConnectionError as e:
            self.findings.append({
                'title': 'Connection Error',
                'severity': 'HIGH',
                'category': 'other',
                'description': f'Could not connect to the target: {str(e)}',
                'recommendation': 'Verify the URL is accessible and the server is running.',
                'evidence': str(e),
            })
        except requests.exceptions.Timeout:
            self.findings.append({
                'title': 'Connection Timeout',
                'severity': 'MEDIUM',
                'category': 'other',
                'description': f'Connection timed out after {self.timeout} seconds.',
                'recommendation': 'Check server performance or increase timeout.',
                'evidence': f'Timeout: {self.timeout}s',
            })

        logger.info(f"Scan complete for {self.url}: {len(self.findings)} findings")
        return self.findings

    def _check_security_headers(self, response):
        """Check for missing or misconfigured security headers."""
        headers = response.headers

        security_headers = {
            'Strict-Transport-Security': {
                'severity': 'HIGH',
                'description': 'HSTS header is missing. The site does not enforce HTTPS connections.',
                'recommendation': 'Add Strict-Transport-Security header with max-age of at least 31536000.',
            },
            'Content-Security-Policy': {
                'severity': 'MEDIUM',
                'description': 'CSP header is missing. The site is vulnerable to XSS attacks.',
                'recommendation': 'Implement a Content-Security-Policy header to restrict resource loading.',
            },
            'X-Content-Type-Options': {
                'severity': 'MEDIUM',
                'description': 'X-Content-Type-Options header is missing. Browser may MIME-sniff responses.',
                'recommendation': 'Add X-Content-Type-Options: nosniff header.',
            },
            'X-Frame-Options': {
                'severity': 'MEDIUM',
                'description': 'X-Frame-Options header is missing. Site may be vulnerable to clickjacking.',
                'recommendation': 'Add X-Frame-Options: DENY or SAMEORIGIN header.',
            },
            'X-XSS-Protection': {
                'severity': 'LOW',
                'description': 'X-XSS-Protection header is missing.',
                'recommendation': 'Add X-XSS-Protection: 1; mode=block header.',
            },
            'Referrer-Policy': {
                'severity': 'LOW',
                'description': 'Referrer-Policy header is missing. Referrer information may leak.',
                'recommendation': 'Add Referrer-Policy: strict-origin-when-cross-origin header.',
            },
            'Permissions-Policy': {
                'severity': 'LOW',
                'description': 'Permissions-Policy header is missing.',
                'recommendation': 'Add Permissions-Policy header to restrict browser features.',
            },
        }

        for header_name, info in security_headers.items():
            if header_name.lower() not in {k.lower() for k in headers.keys()}:
                self.findings.append({
                    'title': f'Missing {header_name} Header',
                    'severity': info['severity'],
                    'category': 'headers',
                    'description': info['description'],
                    'recommendation': info['recommendation'],
                    'evidence': f'Header not found in response from {self.url}',
                })

    def _check_cookie_security(self, response):
        """Check cookie security flags."""
        for cookie in response.cookies:
            issues = []

            if not cookie.secure:
                issues.append('Secure flag missing')
            if not cookie.has_nonstandard_attr('HttpOnly') and 'httponly' not in str(cookie).lower():
                issues.append('HttpOnly flag missing')
            if 'samesite' not in str(cookie).lower():
                issues.append('SameSite attribute missing')

            if issues:
                self.findings.append({
                    'title': f'Insecure Cookie: {cookie.name}',
                    'severity': 'MEDIUM',
                    'category': 'cookies',
                    'description': f'Cookie "{cookie.name}" has security issues: {", ".join(issues)}.',
                    'recommendation': 'Set Secure, HttpOnly, and SameSite flags on all cookies.',
                    'evidence': f'Cookie: {cookie.name}, Issues: {", ".join(issues)}',
                })

    def _check_info_disclosure(self, response):
        """Check for information disclosure in headers."""
        headers = response.headers

        # Server header
        server = headers.get('Server', '')
        if server and any(v in server.lower() for v in ['apache/', 'nginx/', 'iis/', 'openresty/']):
            self.findings.append({
                'title': 'Server Version Disclosure',
                'severity': 'LOW',
                'category': 'info_disclosure',
                'description': f'Server header reveals software version: {server}',
                'recommendation': 'Remove or obfuscate the Server header.',
                'evidence': f'Server: {server}',
            })

        # X-Powered-By header
        powered_by = headers.get('X-Powered-By', '')
        if powered_by:
            self.findings.append({
                'title': 'Technology Stack Disclosure',
                'severity': 'LOW',
                'category': 'info_disclosure',
                'description': f'X-Powered-By header reveals technology: {powered_by}',
                'recommendation': 'Remove the X-Powered-By header.',
                'evidence': f'X-Powered-By: {powered_by}',
            })

    def _check_ssl(self, hostname):
        """Check SSL/TLS certificate details."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    protocol = ssock.version()

                    # Check expiry
                    not_after = ssl.cert_time_to_seconds(cert['notAfter'])
                    days_until_expiry = (not_after - datetime.now().timestamp()) / 86400

                    if days_until_expiry < 30:
                        self.findings.append({
                            'title': 'SSL Certificate Expiring Soon',
                            'severity': 'HIGH' if days_until_expiry < 7 else 'MEDIUM',
                            'category': 'ssl',
                            'description': f'SSL certificate expires in {int(days_until_expiry)} days.',
                            'recommendation': 'Renew the SSL certificate before expiration.',
                            'evidence': f'Expires: {cert["notAfter"]}',
                        })

                    # Check protocol version
                    if protocol in ('TLSv1', 'TLSv1.1'):
                        self.findings.append({
                            'title': 'Outdated TLS Version',
                            'severity': 'HIGH',
                            'category': 'ssl',
                            'description': f'Server supports outdated {protocol}.',
                            'recommendation': 'Disable TLS 1.0 and 1.1. Use TLS 1.2 or 1.3.',
                            'evidence': f'Protocol: {protocol}',
                        })

        except Exception as e:
            logger.warning(f"SSL check error for {hostname}: {e}")

    def _check_mixed_content(self, response):
        """Basic mixed content check."""
        if self.parsed_url.scheme == 'https' and 'http://' in response.text[:50000]:
            self.findings.append({
                'title': 'Potential Mixed Content',
                'severity': 'MEDIUM',
                'category': 'mixed_content',
                'description': 'Page loaded over HTTPS may reference HTTP resources.',
                'recommendation': 'Ensure all resources use HTTPS.',
                'evidence': 'HTTP references found in page source.',
            })

    def _check_dns_records(self, hostname):
        """Check DNS security records (SPF, DMARC)."""
        import subprocess

        try:
            # Check SPF
            result = subprocess.run(
                ['nslookup', '-type=txt', hostname],
                capture_output=True, text=True, timeout=10
            )
            if 'v=spf1' not in result.stdout:
                self.findings.append({
                    'title': 'Missing SPF Record',
                    'severity': 'MEDIUM',
                    'category': 'dns',
                    'description': 'No SPF record found. Email spoofing may be possible.',
                    'recommendation': 'Add an SPF TXT record to the DNS configuration.',
                    'evidence': 'No v=spf1 record found.',
                })

            # Check DMARC
            result = subprocess.run(
                ['nslookup', '-type=txt', f'_dmarc.{hostname}'],
                capture_output=True, text=True, timeout=10
            )
            if 'v=DMARC1' not in result.stdout:
                self.findings.append({
                    'title': 'Missing DMARC Record',
                    'severity': 'MEDIUM',
                    'category': 'dns',
                    'description': 'No DMARC record found. Email authentication is not enforced.',
                    'recommendation': 'Add a DMARC TXT record to the DNS configuration.',
                    'evidence': f'No DMARC record for _dmarc.{hostname}',
                })

        except Exception as e:
            logger.warning(f"DNS check error for {hostname}: {e}")
