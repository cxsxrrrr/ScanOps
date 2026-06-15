"""
Data exposure detection.

Detects exposed emails, phone numbers, API keys, and other
personally identifiable information (PII) in page source.
"""
import re
import logging

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 200_000

EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
)

PHONE_PATTERN = re.compile(
    r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
)

API_KEY_PATTERNS = [
    (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI API Key', 'CRITICAL'),
    (r'AIzaSy[a-zA-Z0-9_-]{33}', 'Google API Key', 'HIGH'),
    (r'aws[_-]?access[_-]?key[_-]?id\s*[=:]\s*[\'"]?(AKIA[A-Z0-9]{16})', 'AWS Access Key', 'CRITICAL'),
    (r'aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*[\'"]?([A-Za-z0-9/+=]{40})', 'AWS Secret Key', 'CRITICAL'),
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Access Token', 'CRITICAL'),
    (r'gho_[a-zA-Z0-9]{36}', 'GitHub OAuth Token', 'CRITICAL'),
    (r'glpat-[a-zA-Z0-9\-]{20,}', 'GitLab Personal Access Token', 'CRITICAL'),
    (r'slack[_-]?xox[bpras]-[a-zA-Z0-9-]{10,}', 'Slack Token', 'CRITICAL'),
    (r'xox[bpras]-[a-zA-Z0-9-]{10,}', 'Slack Token', 'CRITICAL'),
    (r'hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[a-zA-Z0-9]{24}', 'Slack Webhook', 'HIGH'),
    (r'key=[\'"]?[a-f0-9]{32}[\'"]?', 'Possible API Key (32-char hex)', 'HIGH'),
    (r'sendgrid[_-]?api[_-]?key\s*[=:]\s*[\'"]?(SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43})', 'SendGrid API Key', 'CRITICAL'),
    (r'stripe[_-]?(?:live|test)?[_-]?key\s*[=:]\s*[\'"]?(sk_(?:live|test)_[a-zA-Z0-9]{24,})', 'Stripe Secret Key', 'CRITICAL'),
    (r'rk_live_[a-zA-Z0-9]{24,}', 'Stripe Restricted Key', 'CRITICAL'),
    (r'PRIVATE[_-]?KEY', 'Private Key Reference', 'HIGH'),
]


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_data_exposure(response, parsed_url, findings):
    """Detect exposed emails, phone numbers, and API keys in page source."""
    body = _get_body(response)

    _check_email_exposure(body, parsed_url, findings)
    _check_api_key_exposure(body, parsed_url, findings)
    _check_internal_ip_exposure(body, parsed_url, findings)


def _check_email_exposure(body, parsed_url, findings):
    """Detect email addresses exposed in page source."""
    domain = parsed_url.hostname or ''

    internal_emails = []
    external_emails = []

    for email in set(EMAIL_PATTERN.findall(body)):
        email_domain = email.split('@')[-1].lower()
        if email_domain == domain.lower():
            internal_emails.append(email)
        elif email_domain not in (
            'example.com', 'test.com', 'localhost',
            'email.com', 'domain.com', 'yourdomain.com',
            'yoursite.com', 'company.com', 'user.com',
        ):
            external_emails.append(email)

    if internal_emails:
        findings.append({
            'title': f'Internal Email Addresses Exposed ({len(internal_emails)})',
            'severity': 'MEDIUM',
            'category': 'info_disclosure',
            'description': (
                f'{len(internal_emails)} internal email address(es) found '
                f'in the page source. Exposed emails can be harvested for '
                f'phishing attacks and spam.'
            ),
            'recommendation': (
                'Remove email addresses from publicly accessible pages. '
                'Use contact forms instead of mailto: links. Obfuscate '
                'email addresses in HTML with JavaScript or encoding.'
            ),
            'evidence': f'Internal emails: {", ".join(internal_emails[:5])}',
        })

    mailto_links = re.findall(r'mailto:([^"\'\s<>]+)', body, re.IGNORECASE)
    if mailto_links:
        findings.append({
            'title': f'mailto: Links Detected ({len(mailto_links)})',
            'severity': 'LOW',
            'category': 'info_disclosure',
            'description': (
                f'{len(mailto_links)} mailto: link(s) found. Email '
                f'addresses in mailto: links are easily harvested by bots.'
            ),
            'recommendation': (
                'Replace mailto: links with contact forms. If mailto: is '
                'needed, obfuscate the email address with JavaScript.'
            ),
            'evidence': f'mailto: links: {", ".join(mailto_links[:5])}',
        })


def _check_api_key_exposure(body, parsed_url, findings):
    """Detect exposed API keys and secrets in page source."""
    found_keys = []

    for pattern, name, severity in API_KEY_PATTERNS:
        matches = re.findall(pattern, body, re.IGNORECASE)
        if matches:
            found_keys.append({
                'name': name,
                'severity': severity,
                'count': len(matches),
                'redacted': matches[0][:8] + '...' if isinstance(matches[0], str) else 'found',
            })

    for key_info in found_keys:
        findings.append({
            'title': f"Exposed {key_info['name']}",
            'severity': key_info['severity'],
            'category': 'info_disclosure',
            'description': (
                f"A {key_info['name']} was found in the page source. "
                f"Exposed API keys allow attackers to abuse services, "
                f"incur costs, or access sensitive data."
            ),
            'recommendation': (
                'Remove API keys from client-side code immediately. '
                'Proxy all API requests through your backend server. '
                'Rotate compromised keys and use environment variables.'
            ),
            'evidence': f"{key_info['name']} detected (redacted): {key_info['redacted']}",
        })


def _check_internal_ip_exposure(body, parsed_url, findings):
    """Detect internal IP addresses exposed in page source."""
    internal_ips = set(re.findall(
        r'\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
        r'172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|'
        r'192\.168\.\d{1,3}\.\d{1,3})\b',
        body,
    ))

    localhost_refs = set(re.findall(
        r'(?:localhost|127\.0\.0\.1|0\.0\.0\.0)(?::\d+)?',
        body,
        re.IGNORECASE,
    ))

    all_internal = internal_ips | localhost_refs

    if len(all_internal) >= 3:
        findings.append({
            'title': f'Internal IP Addresses Exposed ({len(all_internal)})',
            'severity': 'MEDIUM',
            'category': 'info_disclosure',
            'description': (
                f'{len(all_internal)} internal/private IP addresses found '
                f'in the page source. This reveals the internal network '
                f'topology and aids SSRF and internal network attacks.'
            ),
            'recommendation': (
                'Remove internal IP addresses from client-side code. '
                'Use hostnames or relative URLs instead of IP addresses.'
            ),
            'evidence': f'Internal IPs: {", ".join(list(all_internal)[:5])}',
        })


DATA_EXPOSURE_CHECKS = [check_data_exposure]