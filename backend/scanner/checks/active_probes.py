"""
Active vulnerability probes.

Unlike the passive checks in this package (which only look at a single
already-fetched response), these functions issue their own extra HTTP
requests against the target — safe, read-only probes (GET/OPTIONS against
well-known paths, harmless canary payloads in query params). No requests
that create/modify/delete data or attempt authentication are performed.

Mirrors the (session, base_url, findings) calling convention already used
by checks/wordpress.py, and is invoked the same way (directly from
ScanEngine, not through the passive ALL_CHECKS list).
"""
import logging
import re
import uuid

import requests as req_lib

logger = logging.getLogger('scanner')

REQUEST_TIMEOUT = 10

# Generic admin/DB-management panels not specific to any one CMS (WordPress
# has its own dedicated, more thorough module).
ADMIN_PANEL_PATHS = {
    '/phpmyadmin/': 'phpMyAdmin',
    '/phpMyAdmin/': 'phpMyAdmin',
    '/adminer.php': 'Adminer',
    '/pgadmin4/': 'pgAdmin',
    '/manager/html': 'Tomcat Manager',
    '/console/': 'Application console',
    '/_profiler/phpinfo': 'Symfony profiler',
}

# Backup/config files that commonly get left behind by editors, deploy
# scripts, or manual backups — none of these should ever be reachable.
BACKUP_FILE_PATHS = [
    '/.env', '/.env.bak', '/.env.local',
    '/.git/config', '/.git/HEAD',
    '/config.php.bak', '/config.php~', '/config.php.old',
    '/backup.sql', '/db.sql', '/dump.sql', '/database.sql',
    '/site.zip', '/backup.zip', '/www.zip',
    '/docker-compose.yml', '/docker-compose.yaml',
    '/web.config.bak', '/.DS_Store',
]

# Spring Boot Actuator endpoints — /health alone is often intentionally
# public, but env/heapdump/beans/configprops leak real secrets.
ACTUATOR_SENSITIVE_ENDPOINTS = [
    '/actuator/env', '/actuator/heapdump', '/actuator/beans',
    '/actuator/configprops', '/actuator/mappings', '/actuator/trace',
]

WELLKNOWN_PATHS = {
    '/.well-known/security.txt': 'security.txt',
    '/security.txt': 'security.txt (legacy location)',
}

GENERIC_LISTING_DIRS = ['/backup/', '/uploads/', '/logs/', '/includes/', '/tmp/', '/files/']

DIR_LISTING_PATTERNS = [
    re.compile(r'<title>\s*Index of\s*/', re.IGNORECASE),
    re.compile(r'Parent Directory</a>', re.IGNORECASE),
]

OPEN_REDIRECT_PARAMS = ['next', 'url', 'redirect', 'return', 'redirect_uri', 'continue', 'dest']
CANARY_HOST = 'evil-canary-vigia-scan.example.com'

XSS_CANARY = f'vigiaXSS{uuid.uuid4().hex[:8]}'
TRAVERSAL_PAYLOADS = [
    '/../../../../../../etc/passwd',
    '/static/../../../../etc/passwd',
]
TRAVERSAL_SIGNATURE = re.compile(r'root:.*:0:0:')


def _safe_get(session, url, **kwargs):
    kwargs.setdefault('timeout', REQUEST_TIMEOUT)
    kwargs.setdefault('verify', False)
    try:
        return session.get(url, **kwargs)
    except req_lib.exceptions.RequestException as exc:
        logger.warning(f"Active probe request failed for {url}: {exc}")
        return None


def check_exposed_admin_panels(session, base_url, findings):
    """Probe for generic (non-WordPress) admin/DB-management panels."""
    for path, name in ADMIN_PANEL_PATHS.items():
        resp = _safe_get(session, f'{base_url}{path}')
        if resp is not None and resp.status_code == 200:
            findings.append({
                'title': f'{name} Panel Exposed',
                'severity': 'HIGH',
                'category': 'access_control',
                'description': (
                    f'{name} is publicly reachable at {path}. Database/admin '
                    'management panels should never be exposed to the internet.'
                ),
                'recommendation': (
                    'Restrict access via IP allowlisting, VPN, or remove the '
                    'panel from the production server entirely.'
                ),
                'evidence': f'HTTP 200 at {base_url}{path}',
            })


def check_exposed_backup_files(session, base_url, findings):
    """Probe for common backup/config files left on the server."""
    for path in BACKUP_FILE_PATHS:
        resp = _safe_get(session, f'{base_url}{path}')
        if resp is not None and resp.status_code == 200 and len(resp.content) > 0:
            findings.append({
                'title': 'Exposed Backup/Configuration File',
                'severity': 'CRITICAL',
                'category': 'info_disclosure',
                'description': (
                    f'A backup or configuration file is publicly accessible at '
                    f'{path}. These files often contain credentials, API keys, '
                    'or source code.'
                ),
                'recommendation': (
                    'Remove the file from the web root immediately and rotate '
                    'any credentials it may have contained.'
                ),
                'evidence': f'HTTP 200 at {base_url}{path}',
            })


def check_actuator_exposure(session, base_url, findings):
    """Probe for sensitive Spring Boot Actuator endpoints."""
    for path in ACTUATOR_SENSITIVE_ENDPOINTS:
        resp = _safe_get(session, f'{base_url}{path}')
        if resp is not None and resp.status_code == 200:
            findings.append({
                'title': 'Spring Boot Actuator Endpoint Exposed',
                'severity': 'CRITICAL',
                'category': 'info_disclosure',
                'description': (
                    f'The Actuator management endpoint {path} is publicly '
                    'reachable and can leak environment variables, memory '
                    'dumps, or internal application configuration.'
                ),
                'recommendation': (
                    'Disable or restrict Actuator endpoints in production '
                    '(management.endpoints.web.exposure.include) to '
                    'authenticated internal access only.'
                ),
                'evidence': f'HTTP 200 at {base_url}{path}',
            })


def check_wellknown_disclosures(session, base_url, findings):
    """Check for the presence (or absence) of security.txt (RFC 9116)."""
    for path, name in WELLKNOWN_PATHS.items():
        resp = _safe_get(session, f'{base_url}{path}')
        if resp is not None and resp.status_code == 200:
            return  # found — nothing to flag, no need to check the fallback path

    findings.append({
        'title': 'Missing security.txt',
        'severity': 'INFO',
        'category': 'info_disclosure',
        'description': (
            'No /.well-known/security.txt file was found. This file (RFC 9116) '
            'gives security researchers a clear channel to report '
            'vulnerabilities responsibly.'
        ),
        'recommendation': (
            'Publish a security.txt at /.well-known/security.txt with a '
            'contact address and disclosure policy.'
        ),
        'evidence': f'No security.txt at {base_url}',
    })


def check_directory_listing_generic(session, base_url, findings):
    """Probe common non-CMS-specific directories for autoindex listing."""
    for path in GENERIC_LISTING_DIRS:
        resp = _safe_get(session, f'{base_url}{path}')
        if resp is None or resp.status_code != 200:
            continue
        body = resp.text[:20_000]
        if any(pattern.search(body) for pattern in DIR_LISTING_PATTERNS):
            findings.append({
                'title': 'Directory Listing Enabled',
                'severity': 'MEDIUM',
                'category': 'path_traversal',
                'description': (
                    f'Directory listing is enabled at {path}, exposing the '
                    'contents of a server directory that is often used for '
                    'backups, logs, or uploads.'
                ),
                'recommendation': (
                    'Disable directory listing (Apache: "Options -Indexes", '
                    'Nginx: remove "autoindex on") or restrict access to the path.'
                ),
                'evidence': f'Index listing at {base_url}{path}',
            })


def check_http_methods(session, base_url, findings):
    """Check which HTTP methods the server allows via OPTIONS/TRACE."""
    try:
        resp = session.options(base_url, timeout=REQUEST_TIMEOUT, verify=False)
    except req_lib.exceptions.RequestException as exc:
        logger.warning(f"OPTIONS probe failed for {base_url}: {exc}")
        resp = None

    risky_methods = set()
    if resp is not None:
        allow = resp.headers.get('Allow', '')
        risky_methods = {m.strip().upper() for m in allow.split(',')} & {'PUT', 'DELETE', 'TRACE', 'CONNECT'}

    try:
        trace_resp = session.request('TRACE', base_url, timeout=REQUEST_TIMEOUT, verify=False)
        if trace_resp.status_code == 200:
            risky_methods.add('TRACE')
    except req_lib.exceptions.RequestException:
        pass

    if risky_methods:
        findings.append({
            'title': 'Dangerous HTTP Methods Enabled',
            'severity': 'MEDIUM',
            'category': 'http_methods',
            'description': (
                f'The server accepts the following potentially dangerous HTTP '
                f'methods: {", ".join(sorted(risky_methods))}. TRACE can enable '
                'Cross-Site Tracing (XST); PUT/DELETE without proper '
                'authorization can allow arbitrary file upload/deletion.'
            ),
            'recommendation': (
                'Disable TRACE, and restrict PUT/DELETE/CONNECT to authenticated, '
                'authorized requests only.'
            ),
            'evidence': f'Methods allowed: {", ".join(sorted(risky_methods))}',
        })


def check_open_redirect(session, base_url, findings):
    """Test common redirect params for unvalidated open-redirect behavior."""
    for param in OPEN_REDIRECT_PARAMS:
        target = f'https://{CANARY_HOST}/'
        url = f'{base_url}/?{param}={target}'
        try:
            resp = session.get(
                url, timeout=REQUEST_TIMEOUT, verify=False, allow_redirects=False,
            )
        except req_lib.exceptions.RequestException:
            continue

        location = resp.headers.get('Location', '')
        if CANARY_HOST in location:
            findings.append({
                'title': 'Open Redirect',
                'severity': 'MEDIUM',
                'category': 'redirect',
                'description': (
                    f'The "{param}" parameter redirects to an arbitrary '
                    'attacker-controlled URL without validation, which can be '
                    'abused for phishing (the link appears to point at the '
                    'trusted domain).'
                ),
                'recommendation': (
                    'Validate redirect targets against an allow-list of known '
                    'internal paths, or require a signed/relative-only value.'
                ),
                'evidence': f'{param}={target} -> Location: {location}',
            })
            return  # one confirmed instance is enough


def check_reflected_xss(session, base_url, findings):
    """Inject a non-executing canary string and check for unescaped reflection."""
    url = f'{base_url}/?q={XSS_CANARY}<script>'
    resp = _safe_get(session, url)
    if resp is None:
        return

    if f'{XSS_CANARY}<script>' in resp.text:
        findings.append({
            'title': 'Reflected Cross-Site Scripting (XSS)',
            'severity': 'HIGH',
            'category': 'xss',
            'description': (
                'A query parameter value is reflected in the response body '
                'without HTML-encoding. An attacker-controlled <script> tag '
                'survives unescaped, indicating exploitable reflected XSS.'
            ),
            'recommendation': (
                'HTML-encode all user-controlled output before rendering it. '
                'Use your framework\'s auto-escaping templates and add a CSP '
                'as defense in depth.'
            ),
            'evidence': f'Canary {XSS_CANARY}<script> reflected unescaped at {url}',
        })


def check_path_traversal_active(session, base_url, findings):
    """Actively probe common path-traversal payloads for /etc/passwd leakage."""
    for payload in TRAVERSAL_PAYLOADS:
        resp = _safe_get(session, f'{base_url}{payload}')
        if resp is not None and resp.status_code == 200 and TRAVERSAL_SIGNATURE.search(resp.text):
            findings.append({
                'title': 'Path Traversal',
                'severity': 'CRITICAL',
                'category': 'path_traversal',
                'description': (
                    f'Requesting {payload} returned the contents of /etc/passwd, '
                    'confirming an exploitable path traversal vulnerability.'
                ),
                'recommendation': (
                    'Never build file paths directly from user input. Resolve '
                    'and validate the final path stays within an allowed base '
                    'directory before opening any file.'
                ),
                'evidence': f'Traversal payload at {base_url}{payload} leaked /etc/passwd',
            })
            return


def check_crlf_injection(session, base_url, findings):
    """Test whether a CRLF sequence in a query param injects a response header."""
    marker = f'X-Vigia-CRLF-{uuid.uuid4().hex[:6]}'
    payload = f'%0d%0a{marker}: injected'
    url = f'{base_url}/?next=/foo{payload}'
    resp = _safe_get(session, url, allow_redirects=False)
    if resp is not None and marker.lower() in {k.lower() for k in resp.headers.keys()}:
        findings.append({
            'title': 'CRLF / HTTP Response Header Injection',
            'severity': 'HIGH',
            'category': 'crlf_injection',
            'description': (
                'A CRLF sequence in a query parameter was reflected into the '
                'raw HTTP response headers, allowing an attacker to inject '
                'arbitrary headers (and potentially split the response, '
                'enabling response splitting / cache poisoning / session '
                'fixation).'
            ),
            'recommendation': (
                'Strip or encode CR/LF characters from any user input before '
                'using it to build a header or redirect Location value.'
            ),
            'evidence': f'Injected header "{marker}" appeared in response at {url}',
        })


def run_active_probes(session, base_url, findings):
    """Run every active probe, isolating failures so one bad probe can't
    prevent the rest of the scan from completing."""
    probes = [
        check_exposed_admin_panels,
        check_exposed_backup_files,
        check_actuator_exposure,
        check_wellknown_disclosures,
        check_directory_listing_generic,
        check_http_methods,
        check_open_redirect,
        check_reflected_xss,
        check_path_traversal_active,
        check_crlf_injection,
    ]
    for probe in probes:
        try:
            probe(session, base_url, findings)
        except Exception as exc:
            logger.warning(f"Active probe {probe.__name__} failed for {base_url}: {exc}")
