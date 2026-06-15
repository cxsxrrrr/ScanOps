"""
Cookie security analysis.

Checks for missing or weak cookie attributes: Secure, HttpOnly,
SameSite, and overly broad Path/Domain. Also detects session cookies
transmitted over HTTP.
"""
import re
import logging

logger = logging.getLogger('scanner')

AUTH_COOKIE_NAMES = re.compile(
    r'(session|sess|token|auth|sid|jsessionid|phpsessid|asp\.net_sessionid|laravel_session)',
    re.IGNORECASE,
)


def check_cookie_security(response, parsed_url, findings):
    """Analyze Set-Cookie headers for security attribute issues."""
    set_cookie_headers = response.headers.get_list('Set-Cookie') \
        if hasattr(response.headers, 'get_list') \
        else response.headers.get('Set-Cookie', '')

    headers = response.headers
    raw = headers.raw if hasattr(headers, 'raw') else {}

    cookie_lines = []
    if isinstance(set_cookie_headers, list):
        cookie_lines = set_cookie_headers
    elif set_cookie_headers:
        cookie_lines = [set_cookie_headers]

    for raw_header in raw:
        if raw_header.lower() == 'set-cookie':
            cookie_lines.append(raw[raw_header])

    if not cookie_lines:
        return

    for cookie_line in cookie_lines:
        _analyze_cookie(cookie_line, parsed_url, findings)


def _analyze_cookie(cookie_line, parsed_url, findings):
    """Check a single Set-Cookie header for security issues."""
    parts = cookie_line.split(';')
    name_value = parts[0].strip()
    if '=' not in name_value:
        return

    cookie_name = name_value.split('=', 1)[0].strip()
    cookie_value_lower = cookie_line.lower()
    is_auth_cookie = bool(AUTH_COOKIE_NAMES.search(cookie_name))

    attributes = {}
    for part in parts[1:]:
        part = part.strip()
        if '=' in part:
            key, val = part.split('=', 1)
            attributes[key.strip().lower()] = val.strip().lower()
        else:
            attributes[part.lower()] = True

    severity_base = 'HIGH' if is_auth_cookie else 'MEDIUM'

    _check_secure(cookie_line, cookie_value_lower, is_auth_cookie, severity_base, parsed_url, findings)
    _check_httponly(cookie_value_lower, is_auth_cookie, severity_base, findings)
    _check_samesite(cookie_value_lower, is_auth_cookie, severity_base, findings, attributes)
    _check_path(cookie_value_lower, findings, attributes)
    _check_domain(cookie_value_lower, findings, attributes)


def _check_secure(cookie_line, cookie_lower, is_auth, severity_base, parsed_url, findings):
    if 'secure' not in cookie_lower:
        if parsed_url.scheme == 'https':
            findings.append({
                'title': 'Cookie Missing Secure Flag',
                'severity': severity_base,
                'category': 'cookie_security',
                'description': (
                    f'The cookie is set without the Secure flag over HTTPS. '
                    f'Browsers will send this cookie over unencrypted HTTP '
                    f'connections, exposing it to man-in-the-middle attacks.'
                ),
                'recommendation': 'Add the Secure attribute to all cookies set over HTTPS.',
                'evidence': f'Cookie without Secure: {cookie_line[:150]}',
            })


def _check_httponly(cookie_lower, is_auth, severity_base, findings):
    if 'httponly' not in cookie_lower and is_auth:
        findings.append({
            'title': 'Session Cookie Missing HttpOnly Flag',
            'severity': severity_base,
            'category': 'cookie_security',
            'description': (
                'A session/authentication cookie does not have the HttpOnly flag. '
                'JavaScript can access this cookie, making it vulnerable to XSS theft.'
            ),
            'recommendation': 'Add the HttpOnly attribute to all session and authentication cookies.',
            'evidence': 'Session cookie without HttpOnly flag',
        })


def _check_samesite(cookie_lower, is_auth, severity_base, findings, attributes):
    if 'samesite' not in attributes:
        if is_auth:
            findings.append({
                'title': 'Session Cookie Missing SameSite Attribute',
                'severity': severity_base,
                'category': 'cookie_security',
                'description': (
                    'A session/authentication cookie is missing the SameSite attribute. '
                    'Without it, browsers may send the cookie with cross-site requests, '
                    'enabling CSRF attacks.'
                ),
                'recommendation': 'Set SameSite=Strict or SameSite=Lax on all session cookies.',
                'evidence': 'Session cookie without SameSite attribute',
            })
    else:
        samesite_val = attributes.get('samesite')
        if samesite_val in ('none', '') if isinstance(samesite_val, str) else False:
            findings.append({
                'title': 'Cookie SameSite=None',
                'severity': 'MEDIUM',
                'category': 'cookie_security',
                'description': (
                    'A cookie is explicitly set with SameSite=None. This allows '
                    'the cookie to be sent with cross-site requests, enabling CSRF.'
                ),
                'recommendation': (
                    'Use SameSite=Strict or SameSite=Lax unless cross-site access '
                    'is explicitly required. SameSite=None requires the Secure flag.'
                ),
                'evidence': f'SameSite=None on cookie',
            })


def _check_path(cookie_lower, findings, attributes):
    path_val = attributes.get('path', '/')
    if path_val == '/':
        cookie_name = 'cookie'
        findings.append({
            'title': 'Cookie with Overly Broad Path (/)',
            'severity': 'LOW',
            'category': 'cookie_security',
            'description': (
                'A cookie is set with Path=/. This means the browser sends '
                'the cookie with every request to the site, increasing exposure.'
            ),
            'recommendation': (
                'Set the Path attribute to the most specific path possible. '
                'E.g., Path=/api/auth instead of Path=/.'
            ),
            'evidence': 'Cookie with Path=/',
        })


def _check_domain(cookie_lower, findings, attributes):
    domain_val = attributes.get('domain', '')
    if domain_val and domain_val.startswith('.'):
        findings.append({
            'title': 'Cookie with Domain Attribute Including Subdomains',
            'severity': 'LOW',
            'category': 'cookie_security',
            'description': (
                f'A cookie is set with Domain={domain_val}, which includes all '
                f'subdomains. This increases the attack surface if any subdomain '
                f'is compromised.'
            ),
            'recommendation': (
                'Omit the Domain attribute to restrict the cookie to the exact '
                'host. Only set Domain when subdomain sharing is explicitly needed.'
            ),
            'evidence': f'Cookie Domain={domain_val}',
        })


COOKIE_SECURITY_CHECKS = [check_cookie_security]