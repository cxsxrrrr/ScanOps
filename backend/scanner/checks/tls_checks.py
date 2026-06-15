"""
TLS/SSL security checks.

Checks for missing HTTPS, weak TLS configuration, certificate issues,
and mixed content on HTTPS pages.
"""
import ssl
import socket
import logging
from urllib.parse import urlparse

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 100_000

MIXED_CONTENT_PATTERNS = [
    r'<(?:img|script|link|iframe|video|audio|source|embed|object)\s[^>]*(?:src|href)\s*=\s*["\']http://',
    r'<form\s[^>]*action\s*=\s*["\']http://',
]

INSECURE_TLS_VERSIONS = {
    'TLSv1': 'TLS 1.0',
    'TLSv1.1': 'TLS 1.1',
    'SSLv3': 'SSL 3.0',
    'SSLv2': 'SSL 2.0',
    'SSLv23': 'SSL 2.3',
}

WEAK_CIPHERS = [
    'RC4', 'DES', '3DES', 'MD5', 'NULL', 'EXPORT', 'anon',
    'RC2', 'NULL',
]


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_tls_security(response, parsed_url, findings):
    """Check TLS configuration, certificate validity, and mixed content."""
    if parsed_url.scheme == 'https':
        _check_certificate(parsed_url.netloc, findings)
        _check_hsts_presence(response, findings)
    else:
        findings.append({
            'title': 'Site Not Serving Over HTTPS',
            'severity': 'CRITICAL',
            'category': 'tls',
            'description': (
                'The site is accessible over unencrypted HTTP. All traffic '
                'should be served over HTTPS to protect data in transit.'
            ),
            'recommendation': (
                'Enable HTTPS for all pages. Obtain a TLS certificate from '
                'a trusted CA, configure the server for HTTPS, and redirect '
                'all HTTP traffic to HTTPS.'
            ),
            'evidence': f'Site accessible at {parsed_url.scheme}://{parsed_url.netloc}',
        })

    _check_mixed_content(response, parsed_url, findings)


def _check_certificate(hostname, findings):
    """Check TLS certificate validity, expiration, and basic properties."""
    port = 443
    if ':' in hostname:
        hostname, port_str = hostname.rsplit(':', 1)
        try:
            port = int(port_str)
        except ValueError:
            port = 443

    try:
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                protocol = ssock.version()
                cipher = ssock.cipher()

                _check_cert_expiry(cert, findings)
                _check_cert_hostname(cert, hostname, findings)
                _check_tls_version(protocol, findings)
                _check_cipher_suite(cipher, findings)

    except ssl.SSLCertVerificationError as e:
        findings.append({
            'title': 'TLS Certificate Verification Failed',
            'severity': 'CRITICAL',
            'category': 'tls',
            'description': (
                f'The TLS certificate verification failed: {str(e)[:200].rstrip()}. '
                f'This may indicate an expired, self-signed, or misconfigured certificate.'
            ),
            'recommendation': (
                'Ensure the TLS certificate is valid, not expired, and '
                'issued by a trusted Certificate Authority. Check hostname '
                'matching and certificate chain completeness.'
            ),
            'evidence': f'Certificate error: {str(e)[:150]}',
        })
    except ssl.SSLError as e:
        findings.append({
            'title': 'TLS/SSL Error',
            'severity': 'HIGH',
            'category': 'tls',
            'description': (
                f'A TLS/SSL error occurred: {str(e)[:200]}. '
                f'The server may have weak or broken TLS configuration.'
            ),
            'recommendation': 'Review TLS configuration and ensure only TLS 1.2+ is supported.',
            'evidence': f'SSL error: {str(e)[:150]}',
        })
    except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError):
        logger.debug(f'Could not connect to {hostname}:{port} for TLS check')


def _check_cert_expiry(cert, findings):
    """Check if certificate is expired or expiring soon."""
    import datetime
    not_after = cert.get('notAfter', '')
    if not not_after:
        return

    try:
        expiry_date = datetime.datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
    except (ValueError, TypeError):
        try:
            expiry_date = datetime.datetime.strptime(not_after, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return

    now = datetime.datetime.now(expiry_date.tzinfo)
    days_until_expiry = (expiry_date - now).days

    if days_until_expiry < 0:
        findings.append({
            'title': f'TLS Certificate Expired ({abs(days_until_expiry)} days ago)',
            'severity': 'CRITICAL',
            'category': 'tls',
            'description': (
                f'The TLS certificate expired {abs(days_until_expiry)} days ago. '
                f'Users will see security warnings and connections may be blocked.'
            ),
            'recommendation': 'Renew the TLS certificate immediately.',
            'evidence': f'Certificate expired on {not_after}',
        })
    elif days_until_expiry <= 30:
        findings.append({
            'title': f'TLS Certificate Expiring Soon ({days_until_expiry} days)',
            'severity': 'HIGH',
            'category': 'tls',
            'description': (
                f'The TLS certificate expires in {days_until_expiry} days. '
                f'If not renewed, users will encounter security warnings.'
            ),
            'recommendation': 'Renew the TLS certificate before it expires.',
            'evidence': f'Certificate expires on {not_after}',
        })
    elif days_until_expiry <= 90:
        findings.append({
            'title': f'TLS Certificate Expiring in {days_until_expiry} days',
            'severity': 'LOW',
            'category': 'tls',
            'description': (
                f'The TLS certificate expires in {days_until_expiry} days. '
                f'Plan renewal to avoid service interruption.'
            ),
            'recommendation': 'Schedule certificate renewal.',
            'evidence': f'Certificate expires on {not_after}',
        })


def _check_cert_hostname(cert, hostname, findings):
    """Check if certificate matches the hostname."""
    san_list = cert.get('subjectAltName', ())
    cn_list = [v for k, v in cert.get('subject', ()) if k == 'commonName']

    if not san_list and not cn_list:
        findings.append({
            'title': 'TLS Certificate Missing Subject Alternative Name',
            'severity': 'HIGH',
            'category': 'tls',
            'description': (
                'The TLS certificate does not include Subject Alternative Names '
                '(SANs). Modern browsers require SANs and may reject this certificate.'
            ),
            'recommendation': 'Re-issue the certificate with appropriate SAN entries.',
            'evidence': 'No SAN entries in certificate',
        })


def _check_tls_version(protocol, findings):
    """Check for insecure TLS versions."""
    if protocol in INSECURE_TLS_VERSIONS:
        findings.append({
            'title': f'Insecure TLS Version: {INSECURE_TLS_VERSIONS[protocol]}',
            'severity': 'HIGH',
            'category': 'tls',
            'description': (
                f'The server negotiates {INSECURE_TLS_VERSIONS[protocol]}, '
                f'which has known vulnerabilities and is deprecated. '
                f'This enables BEAST, POODLE, and other attacks.'
            ),
            'recommendation': (
                'Disable TLS 1.0, 1.1, and all SSL versions. '
                'Enable only TLS 1.2 and TLS 1.3.'
            ),
            'evidence': f'Negotiated protocol: {protocol}',
        })


def _check_cipher_suite(cipher, findings):
    """Check for weak cipher suites."""
    if not cipher:
        return

    cipher_name = cipher[0].upper() if cipher else ''

    for weak in WEAK_CIPHERS:
        if weak in cipher_name:
            findings.append({
                'title': f'Weak Cipher Suite: {cipher[0]}',
                'severity': 'MEDIUM',
                'category': 'tls',
                'description': (
                    f'The server negotiated a cipher suite that uses {weak}, '
                    f'which is considered weak. This may allow attackers to '
                    f'decrypt or tamper with traffic.'
                ),
                'recommendation': (
                    'Configure the server to prefer strong cipher suites: '
                    'AES-GCM, ChaCha20-Poly1305 with ECDHE key exchange.'
                ),
                'evidence': f'Cipher: {cipher[0]}, protocol: {cipher[1]}, bits: {cipher[2]}',
            })
            break


def _check_hsts_presence(response, findings):
    """Check for HSTS header on HTTPS pages."""
    hsts = response.headers.get('Strict-Transport-Security', '')
    if not hsts:
        findings.append({
            'title': 'Missing HSTS Header on HTTPS Site',
            'severity': 'MEDIUM',
            'category': 'tls',
            'description': (
                'The site is served over HTTPS but does not include the '
                'Strict-Transport-Security header. Browsers can still access '
                'the site over HTTP, allowing SSL stripping attacks.'
            ),
            'recommendation': (
                'Add the Strict-Transport-Security header with a long max-age, '
                'includeSubDomains, and preload directives. '
                'E.g., Strict-Transport-Security: max-age=63072000; includeSubDomains; preload'
            ),
            'evidence': 'Strict-Transport-Security header not present',
        })


def _check_mixed_content(response, parsed_url, findings):
    """Detect mixed content (HTTP resources on HTTPS pages)."""
    if parsed_url.scheme != 'https':
        return

    body = _get_body(response)
    import re

    mixed_items = []
    for pattern in MIXED_CONTENT_PATTERNS:
        matches = re.findall(pattern, body, re.IGNORECASE)
        mixed_items.extend(matches[:5])

    if mixed_items:
        findings.append({
            'title': f'Mixed Content Detected ({len(mixed_items)} resources)',
            'severity': 'MEDIUM',
            'category': 'tls',
            'description': (
                f'{len(mixed_items)} HTTP resource(s) are loaded on an HTTPS page. '
                f'Mixed content weakens HTTPS protection and allows attackers to '
                f'intercept or modify these resources.'
            ),
            'recommendation': (
                'Replace all HTTP URLs with HTTPS. Use protocol-relative URLs '
                '(//) or enforce HTTPS in the Content-Security-Policy.'
            ),
            'evidence': f'{len(mixed_items)} mixed content resources detected',
        })


TLS_CHECKS = [check_tls_security]