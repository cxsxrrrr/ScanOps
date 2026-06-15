"""
Passive and semi-active 403 bypass detection.

Discovers paths from page content that look restricted, then probes
them with bypass techniques (header manipulation, path normalization)
to detect misconfigured access controls.
"""
import re
import logging
import requests as req_lib
from urllib.parse import urljoin

logger = logging.getLogger('scanner')

MAX_PROBED_PATHS = 15
PROBE_TIMEOUT = 10

BYPASS_HEADERS = [
    {'X-Forwarded-For': '127.0.0.1'},
    {'X-Original-URL': '/admin'},
    {'X-Rewrite-URL': '/admin'},
    {'X-Custom-IP-Authorization': '127.0.0.1'},
    {'X-Forwarded-Host': 'localhost'},
    {'X-Host': 'localhost'},
    {'X-Forwarded-For': '0.0.0.0'},
    {'X-Real-IP': '127.0.0.1'},
    {'X-Client-IP': '127.0.0.1'},
    {'X-Remote-IP': '127.0.0.1'},
    {'X-Remote-Addr': '127.0.0.1'},
    {'X-Originating-IP': '127.0.0.1'},
]

PATH_NORMALIZATIONS = [
    '{path}/',
    '{path}../',
    '{path}..;/',
    '{path}/.',
    '{path}//',
    '{path}%2F',
    '{path}%2e%2e%2f',
    '{path}/..%252f..%252f',
]

RESTRICTED_PATH_PATTERNS = [
    '/admin', '/administrator', '/manager', '/dashboard',
    '/console', '/cpanel', '/phpmyadmin', '/phpMyAdmin',
    '/wp-admin', '/wp-login.php',
    '/.env', '/.git', '/.svn', '/.hg',
    '/server-status', '/server-info',
    '/actuator', '/actuator/health', '/actuator/env',
    '/debug', '/_debug', '/__debug__',
    '/graphql', '/api/graphql',
    '/api/v1/admin', '/api/internal',
    '/backup', '/backups', '/db',
]

RESTRICTED_INDICATORS = re.compile(
    r'(?:'
    r'<title>[^<]*(?:403\s+Forbidden|Forbidden|Access\s+Denied|'
    r'Unauthorized|Not\s+Authorized|Privilege)[^<]*</title>'
    r'|status["\s:]+403'
    r'|HTTP/\d\.\d"\s*403'
    r')',
    re.IGNORECASE,
)

LINK_PATTERN = re.compile(
    r'<a\s[^>]*href\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def check_403_bypass(response, parsed_url, findings):
    """Detect potential 403 bypass vulnerabilities on restricted paths."""
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    restricted_paths = _discover_restricted_paths(response, base_url)

    if not restricted_paths:
        return

    bypasses_found = []

    for path in restricted_paths[:MAX_PROBED_PATHS]:
        url = f'{base_url}{path}'
        if not path.startswith('/'):
            url = f'{base_url}/{path}'

        try:
            original_resp = session.get(url, timeout=PROBE_TIMEOUT, allow_redirects=False, verify=False)
        except req_lib.exceptions.RequestException:
            continue

        original_status = original_resp.status_code

        if original_status not in (401, 403):
            continue

        path_bypasses = _probe_bypasses(session, url, path, original_status, base_url)
        bypasses_found.extend(path_bypasses)

    if bypasses_found:
        for bypass in bypasses_found[:10]:
            findings.append({
                'title': f"403 Bypass: {bypass['technique']}",
                'severity': bypass['severity'],
                'category': 'bypass_403',
                'description': bypass['description'],
                'recommendation': (
                    'Do not rely solely on IP-based or header-based access '
                    'control. Implement proper server-side authorization checks. '
                    'Block common bypass headers at the reverse proxy level.'
                ),
                'evidence': bypass['evidence'],
            })


def _discover_restricted_paths(response, base_url):
    """Find paths from page content that may be access-restricted."""
    paths = set()
    body = response.text[:200_000] if hasattr(response, 'text') else ''

    for pattern in RESTRICTED_PATH_PATTERNS:
        if pattern in body.lower() or pattern in body:
            paths.add(pattern)

    for match in LINK_PATTERN.findall(body):
        for pattern in RESTRICTED_PATH_PATTERNS:
            if pattern in match.lower():
                paths.add(pattern)
                break

    return sorted(paths)


def _probe_bypasses(session, url, path, original_status, base_url):
    """Try bypass techniques on a 401/403 URL."""
    bypasses = []

    for headers_dict in BYPASS_HEADERS:
        try:
            resp = session.get(
                url, timeout=PROBE_TIMEOUT,
                allow_redirects=False, verify=False,
                headers=headers_dict,
            )
            if resp.status_code != original_status and resp.status_code in (200, 201, 204, 301, 302):
                header_name = list(headers_dict.keys())[0]
                bypasses.append({
                    'technique': f"Header bypass ({header_name})",
                    'severity': 'HIGH',
                    'description': (
                        f'Access to {path} was blocked with {original_status}, but '
                        f'adding the {header_name} header returned {resp.status_code}. '
                        f'This indicates the server trusts this header for authorization.'
                    ),
                    'evidence': (
                        f'Path: {path}, Original: {original_status}, '
                        f'With {header_name}: {resp.status_code}'
                    ),
                })
                return bypasses
        except req_lib.exceptions.RequestException:
            continue

    for norm in PATH_NORMALIZATIONS:
        bypass_url = f'{base_url}{norm.format(path=path)}'
        try:
            resp = session.get(
                bypass_url, timeout=PROBE_TIMEOUT,
                allow_redirects=False, verify=False,
            )
            if resp.status_code != original_status and resp.status_code in (200, 201, 204):
                norm_desc = norm.replace('{path}', path)
                bypasses.append({
                    'technique': f"Path normalization bypass ({norm_desc})",
                    'severity': 'HIGH',
                    'description': (
                        f'Access to {path} was blocked with {original_status}, but '
                        f'accessing {norm_desc} returned {resp.status_code}. '
                        f'The server may not normalize paths before authorization.'
                    ),
                    'evidence': (
                        f'Original: {path} ({original_status}), '
                        f'Bypass: {norm_desc} ({resp.status_code})'
                    ),
                })
                return bypasses
        except req_lib.exceptions.RequestException:
            continue

    try:
        resp = session.options(
            url, timeout=PROBE_TIMEOUT,
            allow_redirects=False, verify=False,
        )
        if resp.status_code == 200 and original_status == 403:
            bypasses.append({
                'technique': f"HTTP method bypass (OPTIONS on {path})",
                'severity': 'MEDIUM',
                'description': (
                    f'Access to {path} returns 403 with GET, but OPTIONS '
                    f'returns 200. This may indicate inconsistent method-level '
                    f'access control.'
                ),
                'evidence': f'GET: {original_status}, OPTIONS: {resp.status_code}',
            })
    except req_lib.exceptions.RequestException:
        pass

    return bypasses


BYPASS_403_CHECKS = [check_403_bypass]