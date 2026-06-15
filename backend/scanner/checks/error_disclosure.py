"""
Error page information disclosure detection.

Detects stack traces, internal paths, SQL errors, framework debug
pages, and other information leakage in error responses.
"""
import re
import logging

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 100_000

STACK_TRACE_PATTERNS = [
    re.compile(r'at\s+[\w.$]+\([\w./]+:\d+(?::\d+)?\)', re.IGNORECASE),
    re.compile(r'Traceback\s*\(most recent call last\)', re.IGNORECASE),
    re.compile(r'File\s+"[^"]+",\s*line\s+\d+', re.IGNORECASE),
    re.compile(r'Exception\s+in\s+thread\s+"[^"]*"', re.IGNORECASE),
    re.compile(r'java\.lang\.\w+Exception', re.IGNORECASE),
    re.compile(r'System\.\w+Exception', re.IGNORECASE),
    re.compile(r'\bat\s+\w+(?:\.\w+)*\s*\(', re.IGNORECASE),
    re.compile(r'PHP\s+(?:Fatal|Warning|Notice):\s+', re.IGNORECASE),
    re.compile(r'ASP\.NET\s+version:\s*[\d.]+', re.IGNORECASE),
    re.compile(r'Server\s+Error\s+in\s+Application\s+\'[^\']+\'', re.IGNORECASE),
    re.compile(r'UnhandledExceptionHandler', re.IGNORECASE),
]

INTERNAL_PATH_PATTERNS = [
    re.compile(r'(?:C:\\|/home/|/var/|/usr/|/opt/|/etc/|/tmp/|/app/|/src/|/root/)\S+', re.IGNORECASE),
    re.compile(r'[A-Z]:\\(?:Users|Windows|Program Files|inetpub|wwwroot)\\', re.IGNORECASE),
]

SQL_ERROR_PATTERNS = [
    re.compile(r'SQL(?:STATE)?_\w*error', re.IGNORECASE),
    re.compile(r'(?:mysql|postgresql|oracle|sqlserver|sqlite|mysqli|pdo)_error', re.IGNORECASE),
    re.compile(r'ODBC\s+SQL\s+Server\s+Driver', re.IGNORECASE),
    re.compile(r'SQL\s+syntax.*?(?:MySQL|PostgreSQL|SQL Server|SQLite)', re.IGNORECASE),
    re.compile(r'(?:unknown column|table.*?doesn\'t exist|invalid column)', re.IGNORECASE),
]

DEBUG_INDICATORS = [
    re.compile(r'DEBUG\s*=\s*True', re.IGNORECASE),
    re.compile(r'DJANGO_SETTINGS_MODULE', re.IGNORECASE),
    re.compile(r'APP_DEBUG\s*=\s*true', re.IGNORECASE),
    re.compile(r'RAILS_ENV\s*=\s*["\']development["\']', re.IGNORECASE),
    re.compile(r'config\.debug\s*=\s*true', re.IGNORECASE),
    re.compile(r'<title>(?:Whitelabel Error|Error\s+\d{3})</title>', re.IGNORECASE),
    re.compile(r'laravel\s+debugbar', re.IGNORECASE),
    re.compile(r'ASP\.NET\s+customErrors\s*=\s*["\']Off["\']', re.IGNORECASE),
    re.compile(r'mode\s*=\s*["\']Off["\'].*?customErrors', re.IGNORECASE),
]

VERSION_DISCLOSURE_PATTERNS = [
    re.compile(r'Server:\s*(?:Apache|nginx|IIS|LiteSpeed|Caddy)[/\s]', re.IGNORECASE),
    re.compile(r'X-Powered-By:\s*[^\s]+', re.IGNORECASE),
    re.compile(r'X-AspNet-Version:\s*[\d.]+', re.IGNORECASE),
    re.compile(r'PHP/\d+\.\d+', re.IGNORECASE),
]


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_error_disclosure(response, parsed_url, findings):
    """Detect information leakage in error pages and responses."""
    body = _get_body(response)
    status_code = getattr(response, 'status_code', 200)

    if status_code < 400 and not _has_debug_indicators(body):
        return

    _check_stack_traces(body, status_code, findings)
    _check_internal_paths(body, status_code, findings)
    _check_sql_errors(body, status_code, findings)
    _check_debug_mode(body, status_code, findings)
    _check_version_disclosure(response, body, findings)


def _has_debug_indicators(body):
    for pattern in DEBUG_INDICATORS:
        if pattern.search(body):
            return True
    return False


def _check_stack_traces(body, status_code, findings):
    found_patterns = []
    for pattern in STACK_TRACE_PATTERNS:
        matches = pattern.findall(body)
        if matches:
            found_patterns.extend(matches[:3])

    if found_patterns:
        severity = 'HIGH' if status_code >= 400 else 'MEDIUM'
        findings.append({
            'title': 'Stack Trace Exposed in Response',
            'severity': severity,
            'category': 'info_disclosure',
            'description': (
                f'{len(found_patterns)} stack trace pattern(s) detected in the '
                f'response. Stack traces reveal internal application structure, '
                f'file paths, and library versions that aid attackers in '
                f'crafting targeted exploits.'
            ),
            'recommendation': (
                'Configure custom error pages for all status codes. Never display '
                'stack traces in production. Set debug=False in all frameworks.'
            ),
            'evidence': f'Stack trace patterns: {"; ".join(str(m)[:100] for m in found_patterns[:3])}',
        })


def _check_internal_paths(body, status_code, findings):
    found_paths = set()
    for pattern in INTERNAL_PATH_PATTERNS:
        matches = pattern.findall(body)
        for m in matches:
            found_paths.add(m[:80])

    if found_paths:
        severity = 'MEDIUM' if status_code >= 400 else 'LOW'
        findings.append({
            'title': f'Internal File Paths Exposed ({len(found_paths)})',
            'severity': severity,
            'category': 'info_disclosure',
            'description': (
                f'{len(found_paths)} internal file path(s) detected in the response. '
                f'Exposed paths reveal server directory structure and help attackers '
                f'plan further attacks like path traversal.'
            ),
            'recommendation': (
                'Sanitize error messages to remove file paths. Use custom error '
                'pages that do not include stack traces or server paths.'
            ),
            'evidence': f'Paths: {"; ".join(list(found_paths)[:3])}',
        })


def _check_sql_errors(body, status_code, findings):
    found = []
    for pattern in SQL_ERROR_PATTERNS:
        matches = pattern.findall(body)
        if matches:
            found.extend(matches[:3])

    if found:
        findings.append({
            'title': 'SQL Error Message Exposed',
            'severity': 'HIGH',
            'category': 'info_disclosure',
            'description': (
                'SQL error messages are exposed in the response. These errors '
                'reveal database type, table names, and column names that help '
                'attackers craft SQL injection attacks.'
            ),
            'recommendation': (
                'Use generic error messages in production. Catch all database '
                'exceptions and log them server-side, never exposing them to users.'
            ),
            'evidence': f'SQL errors: {"; ".join(str(m)[:100] for m in found[:3])}',
        })


def _check_debug_mode(body, status_code, findings):
    found_indicators = []
    for pattern in DEBUG_INDICATORS:
        matches = pattern.findall(body)
        if matches:
            found_indicators.extend(matches[:2])

    if found_indicators:
        findings.append({
            'title': 'Application Running in Debug Mode',
            'severity': 'CRITICAL',
            'category': 'info_disclosure',
            'description': (
                'The application appears to be running in debug mode. Debug mode '
                'exposes detailed error information, stack traces, and environment '
                'variables, providing attackers with a roadmap for exploitation.'
            ),
            'recommendation': (
                'Disable debug mode in production. Set DEBUG=False (Django), '
                'APP_DEBUG=false (Laravel), and ensure custom error pages are active.'
            ),
            'evidence': f'Debug indicators: {"; ".join(str(i)[:100] for i in found_indicators[:3])}',
        })


def _check_version_disclosure(response, body, findings):
    version_headers = []
    server = response.headers.get('Server', '')
    x_powered = response.headers.get('X-Powered-By', '')
    x_aspnet = response.headers.get('X-AspNet-Version', '')

    if server and re.match(r'(?:Apache|nginx|IIS|LiteSpeed|Caddy)[/\s]', server, re.IGNORECASE):
        version_headers.append(f'Server: {server[:60]}')
    if x_powered:
        version_headers.append(f'X-Powered-By: {x_powered[:60]}')
    if x_aspnet:
        version_headers.append(f'X-AspNet-Version: {x_aspnet}')

    if version_headers:
        findings.append({
            'title': f'Server Version Disclosure ({len(version_headers)})',
            'severity': 'LOW',
            'category': 'info_disclosure',
            'description': (
                f'The server reveals version information via HTTP headers: '
                f'{"; ".join(version_headers)}. Attackers use version numbers '
                f'to identify known vulnerabilities for that specific version.'
            ),
            'recommendation': (
                'Remove or obfuscate server version headers. In Apache: '
                'ServerTokens Prod. In Nginx: server_tokens off. Remove '
                'X-Powered-By and X-AspNet-Version headers.'
            ),
            'evidence': '; '.join(version_headers),
        })


ERROR_DISCLOSURE_CHECKS = [check_error_disclosure]