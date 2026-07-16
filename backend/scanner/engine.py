"""
Core scan engine for passive security analysis.

Performs non-intrusive checks: HTTP headers, SSL/TLS, cookies,
information disclosure, DNS configuration, and extended vulnerability
detection modules covering OWASP Top 10 and beyond.

The engine crawls same-origin pages (up to MAX_PAGES) to discover
login forms, signup pages, and other interesting endpoints that
surface additional vulnerabilities.
"""
import re
import logging
import socket
import ssl
import requests
from datetime import datetime
from urllib.parse import urlparse, urljoin

from scanner.checks import ALL_CHECKS
from scanner.checks.subdomain_enum import discover_subdomains
from scanner.checks.wordpress import check_wordpress
from scanner.checks.tech_fingerprint import check_technologies
from scanner.checks.active_probes import run_active_probes

logger = logging.getLogger('scanner')

# Maximum number of same-origin pages to crawl
MAX_PAGES = 10

# Maximum subdomains to scan
MAX_SUBDOMAIN_SCANS = 15

# Paths commonly associated with authentication / sensitive functionality
INTERESTING_PATH_KEYWORDS = [
    'login', 'signin', 'sign-in', 'signup', 'sign-up', 'register',
    'newaccount', 'account', 'auth', 'admin', 'dashboard', 'profile',
    'upload', 'api', 'graphql', 'reset', 'password', 'forgot',
]

# Regex to extract same-origin links from HTML
HREF_PATTERN = re.compile(
    r'<a\s[^>]*href\s*=\s*["\']([^"\'#]+)["\']',
    re.IGNORECASE,
)

# Cipher suite names considered weak/broken (matched against ssock.cipher()[0])
WEAK_CIPHER_PATTERN = re.compile(
    r'RC4|DES|3DES|MD5|NULL|EXPORT|_CBC3_',
    re.IGNORECASE,
)

# Common DKIM selectors to probe when no explicit selector is known
DKIM_COMMON_SELECTORS = ['default', 'google', 'selector1', 'selector2', 'k1', 'mail', 'dkim']


class ScanEngine:
    """Passive security scanner for web URLs."""

    def __init__(self, url, timeout=30):
        self.url = url
        self.timeout = timeout
        self.findings = []
        self.parsed_url = urlparse(url)
        self._session = requests.Session()
        self._session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    def run(self):
        """Execute all scan checks and return findings."""
        logger.info(f"Starting scan for: {self.url}")

        try:
            response = self._session.get(
                self.url,
                timeout=self.timeout,
                allow_redirects=True,
                verify=True,
            )

            # Core passive checks (run only on the main page)
            self._check_security_headers(response)
            self._check_cookie_security(response)
            self._check_info_disclosure(response)
            self._check_mixed_content(response)

            # Technology fingerprinting & vulnerability check
            check_technologies(response, self.parsed_url, self.findings)

            if self.parsed_url.scheme == 'https':
                self._check_ssl(self.parsed_url.hostname)

            self._check_dns_records(self.parsed_url.hostname)
            self._check_zone_transfer(self.parsed_url.hostname)

            # Extended checks on the main page
            self._run_extended_checks(response, self.parsed_url)

            # WordPress-specific checks
            base_url = f'{self.parsed_url.scheme}://{self.parsed_url.netloc}'
            check_wordpress(response, self._session, base_url, self.findings)

            # Active probes: extra safe, read-only requests against
            # well-known paths (admin panels, backups, actuator, etc.)
            # and canary payloads (open redirect, reflected XSS, path
            # traversal, CRLF injection).
            run_active_probes(self._session, base_url, self.findings)

            # Crawl same-origin pages and run extended checks on each
            self._crawl_and_check(response)

            # Discover and scan subdomains
            self._discover_and_scan_subdomains()

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
        self._deduplicate()
        logger.info(f"After deduplication: {len(self.findings)} unique findings")
        return self.findings

    # ------------------------------------------------------------------
    # Extended checks & crawling
    # ------------------------------------------------------------------

    def _deduplicate(self):
        """Remove duplicate findings, keeping the highest-severity instance."""
        severity_rank = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        seen = {}

        for f in self.findings:
            key = (f.get('title', ''), f.get('category', ''))
            rank = severity_rank.get(f.get('severity', 'INFO'), 5)
            if key not in seen or rank < seen[key][1]:
                seen[key] = (f, rank)

        self.findings = [entry[0] for entry in seen.values()]

    def _run_extended_checks(self, response, parsed_url):
        """Run all extended vulnerability check modules on a response."""
        for check_fn in ALL_CHECKS:
            try:
                check_fn(response, parsed_url, self.findings)
            except Exception as exc:
                logger.warning(
                    f"Check {check_fn.__name__} failed for {parsed_url.geturl()}: {exc}"
                )

    def _crawl_and_check(self, main_response):
        """Discover same-origin pages and run extended checks on each."""
        visited = {self.url.rstrip('/')}
        to_visit = []

        # Extract links from the main page
        discovered = self._extract_links(main_response)

        # Prioritize interesting paths (login, signup, admin, etc.)
        prioritized = sorted(
            discovered,
            key=lambda u: any(kw in u.lower() for kw in INTERESTING_PATH_KEYWORDS),
            reverse=True,
        )

        for link in prioritized:
            normalized = link.rstrip('/')
            if normalized not in visited:
                to_visit.append(link)
                visited.add(normalized)
            if len(to_visit) >= MAX_PAGES - 1:  # -1 because main page already scanned
                break

        logger.info(f"Crawling {len(to_visit)} additional pages for {self.url}")

        for page_url in to_visit:
            try:
                resp = self._session.get(
                    page_url,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=True,
                )
                page_parsed = urlparse(page_url)
                self._run_extended_checks(resp, page_parsed)
                # Also check cookies on sub-pages
                self._check_cookie_security(resp)
            except requests.exceptions.RequestException as exc:
                logger.warning(f"Failed to crawl {page_url}: {exc}")

    def _extract_links(self, response):
        """Extract same-origin links from HTML response body."""
        links = set()
        body = response.text[:200_000]

        base_scheme = self.parsed_url.scheme
        base_netloc = self.parsed_url.netloc

        for href in HREF_PATTERN.findall(body):
            absolute = urljoin(self.url, href)
            parsed = urlparse(absolute)

            # Only follow same-origin HTTP(S) links
            if parsed.netloc == base_netloc and parsed.scheme in ('http', 'https'):
                # Skip static assets
                path_lower = parsed.path.lower()
                if any(path_lower.endswith(ext) for ext in (
                    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg',
                    '.ico', '.woff', '.woff2', '.ttf', '.eot', '.map',
                )):
                    continue
                links.add(f'{parsed.scheme}://{parsed.netloc}{parsed.path}')

        return links

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

                    # Check negotiated cipher suite strength
                    cipher = ssock.cipher()
                    if cipher:
                        cipher_name = cipher[0]
                        if WEAK_CIPHER_PATTERN.search(cipher_name):
                            self.findings.append({
                                'title': 'Weak TLS Cipher Suite',
                                'severity': 'HIGH',
                                'category': 'ssl',
                                'description': (
                                    f'Server negotiated a weak cipher suite: {cipher_name}. '
                                    'This cipher is considered cryptographically broken '
                                    'or too weak for modern use.'
                                ),
                                'recommendation': (
                                    'Disable RC4, DES/3DES, MD5, NULL, and export-grade '
                                    'ciphers. Use only modern AEAD ciphers (AES-GCM, '
                                    'ChaCha20-Poly1305).'
                                ),
                                'evidence': f'Negotiated cipher: {cipher_name}',
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

    def _nslookup(self, record_type, name):
        """Run nslookup for a record type/name, returning stdout (or '' on failure)."""
        import subprocess
        try:
            result = subprocess.run(
                ['nslookup', f'-type={record_type}', name],
                capture_output=True, text=True, timeout=10,
            )
            return result.stdout
        except Exception as e:
            logger.warning(f"nslookup {record_type} {name} failed: {e}")
            return ''

    def _check_dns_records(self, hostname):
        """Check DNS security records: SPF, DMARC, CAA, DKIM, DNSSEC, MTA-STS, TLS-RPT."""
        if not hostname:
            return

        if 'v=spf1' not in self._nslookup('txt', hostname):
            self.findings.append({
                'title': 'Missing SPF Record',
                'severity': 'MEDIUM',
                'category': 'dns',
                'description': 'No SPF record found. Email spoofing may be possible.',
                'recommendation': 'Add an SPF TXT record to the DNS configuration.',
                'evidence': 'No v=spf1 record found.',
            })

        if 'v=DMARC1' not in self._nslookup('txt', f'_dmarc.{hostname}'):
            self.findings.append({
                'title': 'Missing DMARC Record',
                'severity': 'MEDIUM',
                'category': 'dns',
                'description': 'No DMARC record found. Email authentication is not enforced.',
                'recommendation': 'Add a DMARC TXT record to the DNS configuration.',
                'evidence': f'No DMARC record for _dmarc.{hostname}',
            })

        caa_output = self._nslookup('caa', hostname).upper()
        # nslookup doesn't always print a friendly "CAA" label — it may show
        # the raw type-257 rdata line instead, so match on either.
        if not any(marker in caa_output for marker in ('CAA', 'RDATA_257', 'ISSUE')):
            self.findings.append({
                'title': 'Missing CAA Record',
                'severity': 'LOW',
                'category': 'dns',
                'description': (
                    'No CAA (Certification Authority Authorization) record found. '
                    'Any public CA can issue certificates for this domain.'
                ),
                'recommendation': (
                    'Add a CAA record restricting certificate issuance to your '
                    'chosen certificate authority.'
                ),
                'evidence': 'No CAA record found.',
            })

        dkim_found = any(
            'v=DKIM1' in self._nslookup('txt', f'{selector}._domainkey.{hostname}')
            for selector in DKIM_COMMON_SELECTORS
        )
        if not dkim_found:
            self.findings.append({
                'title': 'No DKIM Record Found (Common Selectors)',
                'severity': 'LOW',
                'category': 'dns',
                'description': (
                    'No DKIM record was found under common selector names '
                    f'({", ".join(DKIM_COMMON_SELECTORS)}). The actual selector '
                    'may differ, so this is informational — verify manually if '
                    'a custom selector is used.'
                ),
                'recommendation': (
                    'Configure DKIM signing for outbound mail and publish the '
                    'public key as a DNS TXT record.'
                ),
                'evidence': f'No DKIM TXT record at common selectors for {hostname}',
            })

        dnskey_output = self._nslookup('dnskey', hostname).upper()
        # Same rdata-line caveat as CAA above (type 48 = DNSKEY).
        if not any(marker in dnskey_output for marker in ('DNSKEY', 'RDATA_48')):
            self.findings.append({
                'title': 'DNSSEC Not Enabled',
                'severity': 'LOW',
                'category': 'dns',
                'description': (
                    'No DNSKEY record found — the domain does not appear to '
                    'use DNSSEC, leaving DNS responses unsigned and vulnerable '
                    'to cache poisoning/spoofing.'
                ),
                'recommendation': 'Enable DNSSEC signing at your DNS provider/registrar.',
                'evidence': 'No DNSKEY record found.',
            })

        mta_sts_txt = self._nslookup('txt', f'_mta-sts.{hostname}')
        if 'v=STSv1' not in mta_sts_txt:
            self.findings.append({
                'title': 'Missing MTA-STS Record',
                'severity': 'LOW',
                'category': 'dns',
                'description': (
                    'No MTA-STS (_mta-sts TXT) record found. Without it, '
                    'inbound mail delivery can be downgraded to unencrypted '
                    'SMTP via an active network attacker.'
                ),
                'recommendation': (
                    'Publish an MTA-STS policy and the corresponding '
                    '_mta-sts TXT record to enforce TLS for inbound mail.'
                ),
                'evidence': 'No v=STSv1 record found.',
            })

        if 'v=TLSRPTv1' not in self._nslookup('txt', f'_smtp._tls.{hostname}'):
            self.findings.append({
                'title': 'Missing TLS-RPT Record',
                'severity': 'INFO',
                'category': 'dns',
                'description': (
                    'No TLS-RPT (_smtp._tls TXT) record found. Without it, '
                    'you won\'t receive reports about SMTP TLS delivery failures.'
                ),
                'recommendation': (
                    'Add a _smtp._tls TXT record (v=TLSRPTv1; rua=mailto:...) '
                    'to receive TLS failure reports.'
                ),
                'evidence': 'No v=TLSRPTv1 record found.',
            })

    def _check_zone_transfer(self, hostname):
        """Attempt an AXFR zone transfer against each authoritative nameserver.

        A misconfigured nameserver that permits AXFR from anyone leaks the
        domain's entire DNS zone (every subdomain, internal hostnames, etc.)
        to an unauthenticated requester.
        """
        import subprocess

        ns_output = self._nslookup('ns', hostname)
        nameservers = re.findall(r'nameserver\s*=\s*([\w.-]+)', ns_output, re.IGNORECASE)
        if not nameservers:
            return

        for ns in nameservers[:5]:
            ns = ns.rstrip('.')
            try:
                result = subprocess.run(
                    ['nslookup', f'-type=axfr', hostname, ns],
                    capture_output=True, text=True, timeout=10,
                )
                output = result.stdout
                # A refused/failed transfer explicitly says so; a successful
                # one dumps many resource records instead.
                if (
                    'Transfer failed' not in output
                    and 'refused' not in output.lower()
                    and output.count('\n') > 10
                ):
                    self.findings.append({
                        'title': 'DNS Zone Transfer (AXFR) Allowed',
                        'severity': 'HIGH',
                        'category': 'dns',
                        'description': (
                            f'Nameserver {ns} allows unauthenticated AXFR zone '
                            'transfers, leaking the complete DNS zone (every '
                            'subdomain and internal hostname) for the domain.'
                        ),
                        'recommendation': (
                            'Restrict AXFR to authorized secondary nameservers '
                            'only (allow-transfer in BIND, or the equivalent on '
                            'your DNS provider).'
                        ),
                        'evidence': f'AXFR from {ns} returned {output.count(chr(10))} lines of records.',
                    })
            except Exception as e:
                logger.warning(f"Zone transfer check failed for {ns}: {e}")

    # ------------------------------------------------------------------
    # Subdomain discovery & scanning
    # ------------------------------------------------------------------

    def _discover_and_scan_subdomains(self):
        """Discover subdomains and run lightweight scans on each."""
        hostname = self.parsed_url.hostname
        if not hostname:
            return

        try:
            subdomains = discover_subdomains(hostname)
        except Exception as exc:
            logger.warning(f"Subdomain discovery failed for {hostname}: {exc}")
            return

        if not subdomains:
            logger.info(f"No subdomains found for {hostname}")
            return

        # Report discovered subdomains as an informational finding
        sub_list = ', '.join(s['subdomain'] for s in subdomains[:MAX_SUBDOMAIN_SCANS])
        self.findings.append({
            'title': 'Subdomains Discovered',
            'severity': 'INFO',
            'category': 'subdomain',
            'description': (
                f'{len(subdomains)} subdomain(s) discovered via passive enumeration '
                f'(Certificate Transparency and DNS resolution).'
            ),
            'recommendation': (
                'Review all discovered subdomains. Remove DNS records for '
                'decommissioned services. Ensure all subdomains follow '
                'security best practices.'
            ),
            'evidence': f'Subdomains found: {sub_list}',
        })

        # Lightweight scan on each subdomain
        for sub_info in subdomains[:MAX_SUBDOMAIN_SCANS]:
            sub_host = sub_info['subdomain']
            self._scan_subdomain(sub_host)

    def _scan_subdomain(self, subdomain):
        """Run a lightweight security scan on a discovered subdomain."""
        prefix = f'[{subdomain}]'
        scheme = 'https'
        url = f'{scheme}://{subdomain}'

        try:
            resp = self._session.get(
                url, timeout=self.timeout,
                allow_redirects=True, verify=True,
            )
        except requests.exceptions.SSLError:
            # Try HTTP fallback
            try:
                scheme = 'http'
                url = f'{scheme}://{subdomain}'
                resp = self._session.get(
                    url, timeout=self.timeout,
                    allow_redirects=True, verify=False,
                )
                self.findings.append({
                    'title': f'{prefix} No Valid SSL Certificate',
                    'severity': 'HIGH',
                    'category': 'subdomain',
                    'description': (
                        f'Subdomain {subdomain} does not have a valid SSL/TLS '
                        f'certificate. Connection fell back to HTTP.'
                    ),
                    'recommendation': (
                        'Install a valid SSL certificate. Use services like '
                        "Let's Encrypt for free certificates."
                    ),
                    'evidence': f'SSL connection failed for {subdomain}',
                })
            except requests.exceptions.RequestException:
                logger.warning(f"Cannot reach subdomain {subdomain} over HTTP or HTTPS")
                return
        except requests.exceptions.RequestException as exc:
            logger.warning(f"Cannot reach subdomain {subdomain}: {exc}")
            return

        headers = resp.headers

        # Check HSTS
        if 'Strict-Transport-Security' not in headers:
            self.findings.append({
                'title': f'{prefix} Missing HSTS Header',
                'severity': 'MEDIUM',
                'category': 'subdomain',
                'description': f'Subdomain {subdomain} is missing the HSTS header.',
                'recommendation': 'Add Strict-Transport-Security header.',
                'evidence': f'No HSTS header on {url}',
            })

        # Check CSP
        if 'Content-Security-Policy' not in headers:
            self.findings.append({
                'title': f'{prefix} Missing CSP Header',
                'severity': 'LOW',
                'category': 'subdomain',
                'description': f'Subdomain {subdomain} is missing the CSP header.',
                'recommendation': 'Add Content-Security-Policy header.',
                'evidence': f'No CSP header on {url}',
            })

        # Check for exposed sensitive information
        server = headers.get('Server', '')
        powered_by = headers.get('X-Powered-By', '')
        if server or powered_by:
            tech = server or powered_by
            self.findings.append({
                'title': f'{prefix} Technology Disclosure',
                'severity': 'LOW',
                'category': 'subdomain',
                'description': f'Subdomain {subdomain} reveals technology: {tech}',
                'recommendation': 'Remove Server and X-Powered-By headers.',
                'evidence': f'Technology header: {tech}',
            })

        # Check SSL certificate expiry (if HTTPS)
        if scheme == 'https':
            self._check_subdomain_ssl(subdomain, prefix)

    def _check_subdomain_ssl(self, subdomain, prefix):
        """Check SSL certificate expiry for a subdomain."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((subdomain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=subdomain) as ssock:
                    cert = ssock.getpeercert()
                    not_after = ssl.cert_time_to_seconds(cert['notAfter'])
                    days_left = (not_after - datetime.now().timestamp()) / 86400

                    if days_left < 30:
                        self.findings.append({
                            'title': f'{prefix} SSL Certificate Expiring Soon',
                            'severity': 'HIGH' if days_left < 7 else 'MEDIUM',
                            'category': 'subdomain',
                            'description': (
                                f'SSL certificate for {subdomain} expires in '
                                f'{int(days_left)} days.'
                            ),
                            'recommendation': 'Renew the SSL certificate.',
                            'evidence': f"Expires: {cert['notAfter']}",
                        })
        except Exception as exc:
            logger.warning(f"SSL check failed for subdomain {subdomain}: {exc}")
