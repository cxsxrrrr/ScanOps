"""
HTTP method tampering detection (semi-active).

Tests whether restricted endpoints accept unexpected HTTP methods
(PUT, DELETE, PATCH, TRACE, OPTIONS) that may bypass access controls.
"""
import logging
import requests as req_lib

logger = logging.getLogger('scanner')

PROBE_TIMEOUT = 10
DANGEROUS_METHODS = ['PUT', 'DELETE', 'PATCH', 'TRACE']

PATHS_TO_PROBE = [
    '/', '/api', '/api/', '/api/v1', '/api/v1/',
    '/admin', '/admin/',
    '/login', '/login/',
    '/users', '/api/users',
    '/api/config', '/api/settings',
]


def check_http_methods(response, parsed_url, findings):
    """Detect HTTP methods that bypass access controls."""
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    original_path = parsed_url.path or '/'
    probe_paths = list(set([original_path] + PATHS_TO_PROBE))

    for path in probe_paths[:5]:
        url = f'{base_url}{path}'

        try:
            options_resp = session.options(
                url, timeout=PROBE_TIMEOUT,
                allow_redirects=True, verify=False,
            )
            allow_header = options_resp.headers.get('Allow', '')
            if allow_header:
                _check_allow_header(allow_header, url, findings)
        except req_lib.exceptions.RequestException:
            pass

        for method in DANGEROUS_METHODS:
            if method == 'DELETE' and path == '/':
                continue

            try:
                resp = session.request(
                    method, url,
                    timeout=PROBE_TIMEOUT,
                    allow_redirects=False,
                    verify=False,
                )
                _check_method_response(method, resp, url, findings)
            except req_lib.exceptions.RequestException:
                continue

    _check_trace_method(base_url, session, findings)


def _check_allow_header(allow_header, url, findings):
    """Check Allow header for dangerous methods."""
    methods = [m.strip().upper() for m in allow_header.split(',')]
    dangerous = [m for m in methods if m in ('PUT', 'DELETE', 'PATCH', 'TRACE', 'CONNECT')]

    if dangerous:
        findings.append({
            'title': f'Dangerous HTTP Methods Allowed ({", ".join(dangerous)})',
            'severity': 'MEDIUM',
            'category': 'http_methods',
            'description': (
                f'The server indicates it accepts {", ".join(dangerous)} methods '
                f'via the Allow header. These methods may allow unauthorized '
                f'modification or deletion of resources.'
            ),
            'recommendation': (
                'Disable unnecessary HTTP methods. In Apache: LimitExcept GET POST. '
                'In Nginx: limit_except GET POST { deny all; }. Only allow methods '
                'that are intentionally required.'
            ),
            'evidence': f'Allow: {allow_header} at {url}',
        })


def _check_method_response(method, resp, url, findings):
    """Check if a dangerous method returns a success response."""
    status = resp.status_code

    if status in (200, 201, 202, 204):
        body = resp.text[:200].replace('\n', ' ') if hasattr(resp, 'text') else ''
        findings.append({
            'title': f'{method} Method Accepted on {url}',
            'severity': 'HIGH',
            'category': 'http_methods',
            'description': (
                f'The endpoint {url} accepts {method} requests without '
                f'authentication apparent from the response. This may allow '
                f'unauthorized resource modification or deletion.'
            ),
            'recommendation': (
                f'Restrict {method} method to authenticated and authorized users. '
                f'Verify that proper access controls are in place for state-changing operations.'
            ),
            'evidence': f'{method} {url} returned {status} — {body[:100]}',
        })


def _check_trace_method(base_url, session, findings):
    """Check if TRACE method is enabled (enables XST attacks)."""
    try:
        resp = session.request(
            'TRACE', base_url,
            timeout=PROBE_TIMEOUT,
            allow_redirects=False,
            verify=False,
        )
        if resp.status_code == 200:
            body = resp.text[:200] if hasattr(resp, 'text') else ''
            test_header = 'X-Test-Trace'
            if test_header.lower() in body.lower() or resp.headers.get('Content-Type', '').startswith('message/'):
                findings.append({
                    'title': 'HTTP TRACE Method Enabled (XST Vulnerable)',
                    'severity': 'HIGH',
                    'category': 'http_methods',
                    'description': (
                        'The TRACE method is enabled and reflects the request '
                        'in the response. This enables Cross-Site Tracing (XST) '
                        'attacks to steal HttpOnly cookies.'
                    ),
                    'recommendation': 'Disable the TRACE method in server configuration.',
                    'evidence': f'TRACE returned 200 with body reflection',
                })
            else:
                findings.append({
                    'title': 'HTTP TRACE Method Enabled',
                    'severity': 'MEDIUM',
                    'category': 'http_methods',
                    'description': (
                        'The TRACE method is enabled. While it does not appear '
                        'to reflect request headers, it should still be disabled '
                        'as a defense-in-depth measure.'
                    ),
                    'recommendation': 'Disable the TRACE method in server configuration.',
                    'evidence': f'TRACE returned {resp.status_code}',
                })
    except req_lib.exceptions.RequestException:
        pass


HTTP_METHODS_CHECKS = [check_http_methods]