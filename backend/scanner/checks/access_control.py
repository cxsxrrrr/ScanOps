"""
Passive access control vulnerability checks.

Detects CSRF, clickjacking, CORS misconfiguration, SSRF indicators,
path traversal, broken access control, 403 bypass, and host header issues
by analyzing HTTP responses and headers.
"""
import re
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 100_000

# Common admin/debug paths that should not be publicly accessible
SENSITIVE_PATHS = [
    '/admin', '/admin/', '/wp-admin/', '/wp-login.php',
    '/phpmyadmin/', '/phpMyAdmin/', '/adminer/',
    '/debug/', '/_debug/', '/__debug__/',
    '/server-status', '/server-info',
    '/elmah.axd', '/trace.axd',
    '/.env', '/.git/', '/.git/config',
    '/actuator/', '/actuator/health',
    '/console/', '/manager/html',
]

# Internal IP ranges for SSRF detection
INTERNAL_IP_PATTERN = re.compile(
    r'(?:'
    r'(?:10|127)\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    r'|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}'
    r'|192\.168\.\d{1,3}\.\d{1,3}'
    r'|0\.0\.0\.0'
    r'|localhost'
    r'|::1'
    r')',
)


def _get_body(response):
    """Return the response body truncated to MAX_BODY_SIZE."""
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_csrf(response, parsed_url, findings):
    """Detect missing CSRF protection and insecure form methods."""
    body = _get_body(response)
    content_type = response.headers.get('Content-Type', '')

    if 'text/html' not in content_type:
        return

    # Find ALL forms in the page
    all_forms = re.findall(
        r'<form[^>]*>(.*?)</form>',
        body,
        re.IGNORECASE | re.DOTALL,
    )

    for form_match in re.finditer(
        r'<form([^>]*)>(.*?)</form>',
        body,
        re.IGNORECASE | re.DOTALL,
    ):
        form_attrs = form_match.group(1)
        form_content = form_match.group(2)

        has_password = bool(re.search(
            r'<input[^>]*type\s*=\s*["\']?password',
            form_content,
            re.IGNORECASE,
        ))

        method_match = re.search(
            r'method\s*=\s*["\']?(\w+)',
            form_attrs,
            re.IGNORECASE,
        )
        method = (method_match.group(1).upper() if method_match else 'GET')

        # Login/signup form using GET — credentials will be in URL
        if has_password and method == 'GET':
            findings.append({
                'title': 'Login Form Uses GET Method',
                'severity': 'CRITICAL',
                'category': 'csrf',
                'description': (
                    'A form with a password field uses the GET method. '
                    'Credentials will be sent in the URL query string, '
                    'visible in browser history, server logs, and Referer headers.'
                ),
                'recommendation': (
                    'Always use method="POST" for forms that handle '
                    'passwords or sensitive data. Add CSRF tokens.'
                ),
                'evidence': f'Login form with method=GET on {parsed_url.geturl()}',
            })
            return  # One finding per page

        # POST form without CSRF token
        if method == 'POST':
            has_csrf = bool(re.search(
                r'(?:csrf|_token|authenticity_token|__RequestVerificationToken)',
                form_content,
                re.IGNORECASE,
            ))
            if not has_csrf:
                severity = 'CRITICAL' if has_password else 'HIGH'
                findings.append({
                    'title': 'Form Missing CSRF Token',
                    'severity': severity,
                    'category': 'csrf',
                    'description': (
                        'A POST form was found without a visible CSRF token. '
                        'This may allow cross-site request forgery attacks.'
                        + (' This form handles passwords, making the risk critical.'
                           if has_password else '')
                    ),
                    'recommendation': (
                        'Include a CSRF token in all state-changing forms. '
                        'Use framework-provided CSRF protection mechanisms.'
                    ),
                    'evidence': f'Form without CSRF token found on {parsed_url.geturl()}',
                })
                return  # One finding per page


def check_clickjacking(response, parsed_url, findings):
    """Detect clickjacking vulnerability via missing frame protections."""
    headers = response.headers
    has_xfo = 'X-Frame-Options' in headers
    csp = headers.get('Content-Security-Policy', '')
    has_frame_ancestors = 'frame-ancestors' in csp.lower()

    if not has_xfo and not has_frame_ancestors:
        findings.append({
            'title': 'Clickjacking: No Frame Protection',
            'severity': 'MEDIUM',
            'category': 'clickjacking',
            'description': (
                'Neither X-Frame-Options nor CSP frame-ancestors is set. '
                'An attacker could embed this page in an iframe to trick '
                'users into unintended actions.'
            ),
            'recommendation': (
                'Set X-Frame-Options: DENY (or SAMEORIGIN) and add '
                'frame-ancestors directive to your Content-Security-Policy.'
            ),
            'evidence': 'No X-Frame-Options or CSP frame-ancestors header found.',
        })


def check_cors(response, parsed_url, findings):
    """Detect CORS misconfigurations."""
    headers = response.headers
    acao = headers.get('Access-Control-Allow-Origin', '')
    acac = headers.get('Access-Control-Allow-Credentials', '').lower()

    if acao == '*':
        severity = 'HIGH' if acac == 'true' else 'MEDIUM'
        findings.append({
            'title': 'Permissive CORS Policy',
            'severity': severity,
            'category': 'cors',
            'description': (
                'Access-Control-Allow-Origin is set to wildcard (*). '
                'Any website can make cross-origin requests to this endpoint.'
                + (' Combined with Allow-Credentials, this exposes '
                   'authenticated data to any origin.' if acac == 'true' else '')
            ),
            'recommendation': (
                'Restrict CORS to specific trusted origins. '
                'Never combine wildcard origin with Allow-Credentials.'
            ),
            'evidence': (
                f'Access-Control-Allow-Origin: {acao}'
                + (f', Access-Control-Allow-Credentials: {acac}' if acac else '')
            ),
        })

    # Null origin can be exploited via sandboxed iframes
    if acao.lower() == 'null':
        findings.append({
            'title': 'CORS Allows Null Origin',
            'severity': 'HIGH',
            'category': 'cors',
            'description': (
                'Access-Control-Allow-Origin is set to "null". '
                'Attackers can send requests from sandboxed iframes '
                'that carry a null origin.'
            ),
            'recommendation': (
                'Never allow the null origin. Whitelist specific '
                'trusted domains instead.'
            ),
            'evidence': f'Access-Control-Allow-Origin: {acao}',
        })


def check_ssrf(response, parsed_url, findings):
    """Detect SSRF indicators in URL parameters."""
    query_params = parse_qs(parsed_url.query)
    url_param_names = ['url', 'uri', 'path', 'redirect', 'next', 'target',
                       'dest', 'link', 'src', 'source', 'fetch', 'proxy']

    for param_name, values in query_params.items():
        if param_name.lower() in url_param_names:
            for value in values:
                if INTERNAL_IP_PATTERN.search(value):
                    findings.append({
                        'title': 'Potential SSRF: Internal IP in URL Parameter',
                        'severity': 'HIGH',
                        'category': 'ssrf',
                        'description': (
                            f'The URL parameter "{param_name}" contains an '
                            f'internal IP address, which may indicate an SSRF '
                            f'vulnerability or internal network exposure.'
                        ),
                        'recommendation': (
                            'Validate and sanitize URL parameters server-side. '
                            'Block requests to internal IP ranges and localhost.'
                        ),
                        'evidence': f'{param_name}={value}',
                    })
                    return


def check_path_traversal(response, parsed_url, findings):
    """Detect directory listing and path traversal indicators."""
    body = _get_body(response)

    # Directory listing indicators
    dir_listing_patterns = [
        r'<title>\s*Index of\s*/.*?</title>',
        r'<title>\s*Directory listing for\s*/.*?</title>',
        r'Parent Directory</a>',
    ]

    for pattern in dir_listing_patterns:
        if re.search(pattern, body, re.IGNORECASE):
            findings.append({
                'title': 'Directory Listing Enabled',
                'severity': 'MEDIUM',
                'category': 'path_traversal',
                'description': (
                    'The server exposes directory contents. This reveals '
                    'the file structure and may expose sensitive files.'
                ),
                'recommendation': (
                    'Disable directory listing in the web server configuration. '
                    'For Apache, use "Options -Indexes". For Nginx, remove '
                    '"autoindex on".'
                ),
                'evidence': f'Directory listing detected on {parsed_url.geturl()}',
            })
            break


def check_access_control(response, parsed_url, findings):
    """Detect exposed admin panels and debug endpoints."""
    body = _get_body(response)

    # Check for exposed sensitive paths referenced in the page
    found_paths = []
    for path in SENSITIVE_PATHS:
        if path in body:
            found_paths.append(path)

    if found_paths:
        findings.append({
            'title': 'Sensitive Paths Referenced in Page',
            'severity': 'MEDIUM',
            'category': 'access_control',
            'description': (
                'The response references sensitive administrative or debug '
                'paths that should not be publicly accessible.'
            ),
            'recommendation': (
                'Restrict access to administrative endpoints via IP '
                'allowlisting or authentication. Remove debug endpoints '
                'in production.'
            ),
            'evidence': f'Sensitive paths found: {", ".join(found_paths[:10])}',
        })

    # Check for debug mode indicators
    debug_indicators = [
        'Traceback (most recent call last)',
        'DJANGO_SETTINGS_MODULE',
        'PHP Fatal error',
        'Stack Trace:',
        'WEB-INF/',
        'DEBUG = True',
    ]

    for indicator in debug_indicators:
        if indicator in body:
            findings.append({
                'title': 'Debug Information Exposed',
                'severity': 'HIGH',
                'category': 'access_control',
                'description': (
                    'Debug or stack trace information is visible in the response. '
                    'This exposes internal application details to attackers.'
                ),
                'recommendation': (
                    'Disable debug mode in production. Configure a custom error '
                    'page and centralized logging instead of displaying errors.'
                ),
                'evidence': f'Debug indicator found: {indicator}',
            })
            break


def check_host_header(response, parsed_url, findings):
    """Detect potential host header injection indicators."""
    body = _get_body(response)

    # Check for password reset or redirect URLs that include the host
    if re.search(
        r'(?:action|href|src)\s*=\s*["\']https?://[^/]*\{',
        body,
        re.IGNORECASE,
    ):
        findings.append({
            'title': 'Potential Host Header Injection',
            'severity': 'MEDIUM',
            'category': 'host_header',
            'description': (
                'The response appears to dynamically construct URLs using '
                'the Host header, which could enable host header injection '
                'attacks in password resets or redirects.'
            ),
            'recommendation': (
                'Use a hardcoded or configuration-based server URL instead of '
                'relying on the Host header. Validate the Host header against '
                'an allowlist (e.g., Django ALLOWED_HOSTS).'
            ),
            'evidence': 'Dynamic URL construction detected in response.',
        })


# Export list of all access control check functions
ACCESS_CONTROL_CHECKS = [
    check_csrf,
    check_clickjacking,
    check_cors,
    check_ssrf,
    check_path_traversal,
    check_access_control,
    check_host_header,
]
