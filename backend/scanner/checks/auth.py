"""
Passive authentication vulnerability checks.

Detects issues related to authentication mechanisms, JWT tokens,
OAuth flows, and WebSocket security by analyzing HTTP responses
and headers.
"""
import re
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 100_000

# JWT regex: three base64url-encoded segments separated by dots
JWT_PATTERN = re.compile(
    r'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+'
)


def _get_body(response):
    """Return the response body truncated to MAX_BODY_SIZE."""
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_auth(response, parsed_url, findings):
    """Detect weak authentication indicators."""
    headers = response.headers
    body = _get_body(response)

    # Login form over HTTP (not HTTPS)
    is_login_page = bool(re.search(
        r'<input[^>]*type\s*=\s*["\']password["\'][^>]*>',
        body,
        re.IGNORECASE,
    ))

    if is_login_page and parsed_url.scheme != 'https':
        findings.append({
            'title': 'Login Form Over Unencrypted HTTP',
            'severity': 'CRITICAL',
            'category': 'auth',
            'description': (
                'A password input field was found on a page served over HTTP. '
                'Credentials will be transmitted in plaintext.'
            ),
            'recommendation': (
                'Serve all login pages and forms exclusively over HTTPS. '
                'Redirect all HTTP traffic to HTTPS.'
            ),
            'evidence': f'Password field detected on {parsed_url.geturl()}',
        })

    # Login page without autocomplete=off on password fields
    if is_login_page:
        password_fields = re.findall(
            r'<input[^>]*type\s*=\s*["\']password["\'][^>]*>',
            body,
            re.IGNORECASE,
        )
        for field in password_fields:
            if 'autocomplete' not in field.lower():
                findings.append({
                    'title': 'Password Field Allows Autocomplete',
                    'severity': 'LOW',
                    'category': 'auth',
                    'description': (
                        'A password field does not set autocomplete="off". '
                        'Browsers may store the password.'
                    ),
                    'recommendation': (
                        'Add autocomplete="off" or autocomplete="new-password" '
                        'to password input fields.'
                    ),
                    'evidence': 'Password field without autocomplete attribute.',
                })
                break

    # Missing rate-limiting headers
    rate_limit_headers = [
        'X-RateLimit-Limit', 'X-Rate-Limit-Limit',
        'RateLimit-Limit', 'Retry-After',
    ]
    has_rate_limit = any(h in headers for h in rate_limit_headers)

    if is_login_page and not has_rate_limit:
        findings.append({
            'title': 'No Rate Limiting Detected on Login',
            'severity': 'MEDIUM',
            'category': 'auth',
            'description': (
                'The login page response does not include rate-limiting '
                'headers, which may allow brute-force attacks.'
            ),
            'recommendation': (
                'Implement rate limiting on authentication endpoints. '
                'Use progressive delays or account lockout mechanisms.'
            ),
            'evidence': 'No rate-limiting headers found in response.',
        })


def check_jwt(response, parsed_url, findings):
    """Detect JWT vulnerabilities: tokens in URLs, weak algorithms."""
    body = _get_body(response)
    query_string = parsed_url.query

    # JWT in URL parameters (tokens should be in headers/cookies only)
    if JWT_PATTERN.search(query_string):
        findings.append({
            'title': 'JWT Token Exposed in URL',
            'severity': 'HIGH',
            'category': 'jwt',
            'description': (
                'A JWT token was found in the URL query string. Tokens in '
                'URLs can be leaked via browser history, server logs, Referer '
                'headers, and proxy logs.'
            ),
            'recommendation': (
                'Send JWT tokens in the Authorization header or secure '
                'HTTP-only cookies. Never include tokens in URLs.'
            ),
            'evidence': 'JWT token found in URL query string.',
        })

    # JWKS endpoint exposure (informational)
    jwks_patterns = [
        '/.well-known/jwks.json',
        '/jwks',
        '/.well-known/openid-configuration',
    ]
    for pattern in jwks_patterns:
        if pattern in body:
            findings.append({
                'title': 'JWKS Endpoint Reference Discovered',
                'severity': 'INFO',
                'category': 'jwt',
                'description': (
                    f'A reference to a JSON Web Key Set endpoint ({pattern}) '
                    f'was found. While this is often intentional, ensure the '
                    f'endpoint does not expose sensitive key material.'
                ),
                'recommendation': (
                    'Verify that the JWKS endpoint only exposes public keys. '
                    'Ensure private keys are not accessible.'
                ),
                'evidence': f'JWKS reference found: {pattern}',
            })
            break


def check_oauth(response, parsed_url, findings):
    """Detect OAuth security issues."""
    body = _get_body(response)

    # Open redirect in OAuth callback URLs
    oauth_patterns = re.findall(
        r'(?:redirect_uri|callback_url)\s*=\s*["\']?([^"\'&\s]+)',
        body,
        re.IGNORECASE,
    )

    for redirect_uri in oauth_patterns:
        if redirect_uri.startswith('http://'):
            findings.append({
                'title': 'OAuth Redirect URI Uses HTTP',
                'severity': 'HIGH',
                'category': 'oauth',
                'description': (
                    'An OAuth redirect URI uses unencrypted HTTP. '
                    'Authorization codes or tokens could be intercepted.'
                ),
                'recommendation': (
                    'Always use HTTPS for OAuth redirect URIs. '
                    'Register only HTTPS callbacks with the OAuth provider.'
                ),
                'evidence': f'Redirect URI: {redirect_uri[:200]}',
            })
            break

    # Token in URL fragment (informational)
    if re.search(r'[?&](?:access_token|token)=', body, re.IGNORECASE):
        findings.append({
            'title': 'Access Token Found in URL/Page Content',
            'severity': 'MEDIUM',
            'category': 'oauth',
            'description': (
                'An access token reference was found in the page content. '
                'Tokens in URLs or embedded in pages may be leaked.'
            ),
            'recommendation': (
                'Use the Authorization Code flow with PKCE instead of '
                'the Implicit flow. Avoid embedding tokens in HTML.'
            ),
            'evidence': 'Token parameter reference found in page content.',
        })


def check_websockets(response, parsed_url, findings):
    """Detect insecure WebSocket usage."""
    body = _get_body(response)

    # Insecure ws:// connections
    ws_matches = re.findall(r'ws://[^\s"\'<>]+', body, re.IGNORECASE)
    if ws_matches:
        findings.append({
            'title': 'Insecure WebSocket Connection (ws://)',
            'severity': 'MEDIUM',
            'category': 'websockets',
            'description': (
                'The page references unencrypted WebSocket connections. '
                'Data transmitted over ws:// can be intercepted.'
            ),
            'recommendation': (
                'Use wss:// (WebSocket Secure) instead of ws://. '
                'Validate the Origin header on the server side.'
            ),
            'evidence': f'Insecure WebSocket URLs: {", ".join(ws_matches[:3])}',
        })

    # WebSocket without origin validation is hard to detect passively,
    # but we flag ws usage as informational
    wss_matches = re.findall(r'wss?://[^\s"\'<>]+', body, re.IGNORECASE)
    if wss_matches and not ws_matches:
        findings.append({
            'title': 'WebSocket Endpoints Detected',
            'severity': 'INFO',
            'category': 'websockets',
            'description': (
                'The page uses WebSocket connections. Ensure proper '
                'origin validation and authentication on the server.'
            ),
            'recommendation': (
                'Validate the Origin header for WebSocket connections. '
                'Implement authentication for WebSocket handshakes.'
            ),
            'evidence': f'WebSocket endpoints: {", ".join(wss_matches[:3])}',
        })


# Export list of all authentication check functions
AUTH_CHECKS = [
    check_auth,
    check_jwt,
    check_oauth,
    check_websockets,
]
