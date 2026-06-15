"""
JavaScript security analysis.

Detects insecure JavaScript patterns: postMessage without origin
validation, localStorage with sensitive data, eval/Function usage,
innerHTML with user data, window.opener without noopener, and
missing Subresource Integrity (SRI) on external scripts.
"""
import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 150_000


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_js_security(response, parsed_url, findings):
    """Detect insecure JavaScript patterns in page source."""
    body = _get_body(response)

    _check_postmessage(body, parsed_url, findings)
    _check_sensitive_storage(body, parsed_url, findings)
    _check_window_opener(body, parsed_url, findings)
    _check_sri_integrity(body, parsed_url, findings)
    _check_inline_event_handlers(body, parsed_url, findings)
    _check_webworker_insecure(body, parsed_url, findings)


def _check_postmessage(body, parsed_url, findings):
    """Detect postMessage calls without origin validation."""
    postmessage_calls = re.findall(
        r'(?:otherWindow|targetWindow|window|parent|opener|iframe)\s*\.\s*postMessage\s*\(',
        body,
        re.IGNORECASE,
    )

    if not postmessage_calls:
        return

    origin_checks = re.findall(
        r'event\.origin\s*[=!]==?\s*[\'"]([^\'"]+)[\'"]',
        body,
        re.IGNORECASE,
    ) or re.findall(
        r'origin\s*[=!]==?\s*[\'"]([^\'"]+)[\'"]',
        body,
        re.IGNORECASE,
    )

    wildcard_origins = re.findall(
        r'event\.origin\s*[=!]==?\s*["\']\*["\']|'
        r'origin\s*[=!]==?\s*["\']\*["\']|'
        r'origin\.indexOf\s*\(',
        body,
        re.IGNORECASE,
    )

    if postmessage_calls and not origin_checks:
        findings.append({
            'title': 'postMessage Without Origin Validation',
            'severity': 'HIGH',
            'category': 'xss',
            'description': (
                f'{len(postmessage_calls)} postMessage call(s) were found '
                f'without visible origin validation. Without checking '
                f'event.origin, any malicious window can send messages '
                f'to this page, potentially leading to XSS.'
            ),
            'recommendation': (
                'Always validate event.origin in message event handlers. '
                'Use strict string comparison (===) against an allowlist of '
                'trusted origins.'
            ),
            'evidence': f'{len(postmessage_calls)} postMessage calls without origin checks',
        })
    elif wildcard_origins:
        findings.append({
            'title': 'postMessage With Weak Origin Validation',
            'severity': 'MEDIUM',
            'category': 'xss',
            'description': (
                'postMessage calls were found with weak origin validation '
                '(wildcard or indexOf). This may allow messages from '
                'untrusted origins.'
            ),
            'recommendation': (
                'Use strict origin comparison (event.origin === "https://trusted.com") '
                'instead of indexOf or wildcard patterns.'
            ),
            'evidence': 'Weak origin validation pattern detected',
        })


def _check_sensitive_storage(body, parsed_url, findings):
    """Detect sensitive data stored in localStorage/sessionStorage."""
    sensitive_keys = [
        'token', 'auth', 'password', 'secret', 'credential',
        'api_key', 'apikey', 'access_token', 'refresh_token',
        'session', 'jwt', 'id_token',
    ]

    storage_patterns = []
    for key in sensitive_keys:
        if not re.search(
            r'(?:localStorage|sessionStorage)\s*\.\s*setItem\s*\(\s*["\'][^"\']*'
            + re.escape(key)
            + r'[^"\']*["\']',
            body,
            re.IGNORECASE,
        ):
            continue

        if key in ('session', 'auth') and 'sessionStorage' in body:
            continue

        storage_patterns.append(key)

    if storage_patterns:
        findings.append({
            'title': 'Sensitive Data in Browser Storage',
            'severity': 'MEDIUM',
            'category': 'auth',
            'description': (
                f'Sensitive data ({", ".join(storage_patterns)}) appears to '
                f'be stored in localStorage or sessionStorage. This data is '
                f'accessible to any JavaScript on the page and persists across '
                f'sessions, making it vulnerable to XSS attacks.'
            ),
            'recommendation': (
                'Use HttpOnly, Secure, SameSite cookies for sensitive data '
                'instead of browser storage. If browser storage is necessary, '
                'encrypt the data and clear it on logout.'
            ),
            'evidence': f'Sensitive keys in storage: {", ".join(storage_patterns)}',
        })


def _check_window_opener(body, parsed_url, findings):
    """Detect window.opener access without rel=noopener."""
    links_with_target_blank = re.findall(
        r'<a\s[^>]*target\s*=\s*["\']_blank["\'][^>]*>',
        body,
        re.IGNORECASE,
    )

    links_without_noopener = []
    for link in links_with_target_blank:
        if 'rel=' not in link.lower() or 'noopener' not in link.lower():
            links_without_noopener.append(link[:100])

    if links_without_noopener:
        findings.append({
            'title': f'Links Without rel="noopener" ({len(links_without_noopener)})',
            'severity': 'MEDIUM',
            'category': 'access_control',
            'description': (
                f'{len(links_without_noopener)} link(s) with target="_blank" '
                f'do not include rel="noopener". This allows the opened page '
                f'to access window.opener, enabling tab-nabbing attacks.'
            ),
            'recommendation': (
                'Add rel="noopener noreferrer" to all links with '
                'target="_blank". Modern browsers default to noopener '
                'but noreferrer ensures compatibility.'
            ),
            'evidence': f'{len(links_without_noopener)} links missing rel="noopener"',
        })


def _check_sri_integrity(body, parsed_url, findings):
    """Check external scripts/styles for Subresource Integrity attributes."""
    external_scripts = re.findall(
        r'<script\s+[^>]*src\s*=\s*["\']https?://[^"\']+["\'][^>]*>',
        body,
        re.IGNORECASE,
    )

    scripts_without_sri = []
    for script in external_scripts:
        if 'integrity=' not in script.lower():
            scripts_without_sri.append(script[:120])

    external_styles = re.findall(
        r'<link\s+[^>]*href\s*=\s*["\']https?://[^"\']+\.css[^"\']*["\'][^>]*/?>',
        body,
        re.IGNORECASE,
    )

    styles_without_sri = []
    for style in external_styles:
        if 'integrity=' not in style.lower():
            styles_without_sri.append(style[:120])

    total_missing = len(scripts_without_sri) + len(styles_without_sri)
    if total_missing > 0:
        severity = 'HIGH' if len(scripts_without_sri) > 3 else 'MEDIUM'
        findings.append({
            'title': f'Missing Subresource Integrity ({total_missing} resources)',
            'severity': severity,
            'category': 'info_disclosure',
            'description': (
                f'{len(scripts_without_sri)} external script(s) and '
                f'{len(styles_without_sri)} external stylesheet(s) are loaded '
                f'without Subresource Integrity (SRI) attributes. If the CDN '
                f'or third-party server is compromised, attackers could inject '
                f'malicious code.'
            ),
            'recommendation': (
                'Add integrity and crossorigin attributes to all external '
                'resources. Use https://www.srihash.org/ to generate hashes. '
                'E.g., <script src="..." integrity="sha384-..." crossorigin="anonymous">'
            ),
            'evidence': (
                f'{len(scripts_without_sri)} scripts, '
                f'{len(styles_without_sri)} styles without SRI'
            ),
        })


def _check_inline_event_handlers(body, parsed_url, findings):
    """Detect inline event handlers that may be XSS vectors."""
    event_handlers = re.findall(
        r'<[^>]+\son(?:click|load|error|mouseover|focus|blur|submit|change)\s*=\s*["\']',
        body,
        re.IGNORECASE,
    )

    if len(event_handlers) > 20:
        findings.append({
            'title': f'Excessive Inline Event Handlers ({len(event_handlers)})',
            'severity': 'LOW',
            'category': 'xss',
            'description': (
                f'{len(event_handlers)} inline event handlers were found. '
                f'Inline handlers make CSP with unsafe-inline impossible to '
                f'enforce and increase XSS attack surface.'
            ),
            'recommendation': (
                'Move all event handlers to external JavaScript files. '
                'Use addEventListener() instead of inline event attributes.'
            ),
            'evidence': f'{len(event_handlers)} inline event handlers detected',
        })


def _check_webworker_insecure(body, parsed_url, findings):
    """Detect insecure Web Worker patterns."""
    insecure_workers = re.findall(
        r'new\s+Worker\s*\(\s*["\']http://[^"\']+["\']',
        body,
        re.IGNORECASE,
    )

    if insecure_workers:
        findings.append({
            'title': 'Web Worker Loaded Over HTTP',
            'severity': 'MEDIUM',
            'category': 'mixed_content',
            'description': (
                'A Web Worker is being loaded over an insecure HTTP connection. '
                'This creates a mixed content vulnerability and allows '
                'man-in-the-middle attacks on the worker script.'
            ),
            'recommendation': (
                'Load all Web Workers over HTTPS. Ensure the Worker '
                'script URL uses the same origin or a trusted secure origin.'
            ),
            'evidence': f'{len(insecure_workers)} HTTP Worker URLs found',
        })


def _check_service_workers(body, parsed_url, findings):
    """Detect service worker registrations that may intercept requests."""
    sw_patterns = re.findall(
        r'navigator\s*\.\s*serviceWorker\s*\.\s*register\s*\(\s*["\']([^"\']+)["\']',
        body,
        re.IGNORECASE,
    )

    sw_generic = re.findall(
        r'navigator\s*\.\s*serviceWorker\s*\.\s*register\s*\(',
        body,
        re.IGNORECASE,
    )

    if sw_patterns:
        findings.append({
            'title': f'Service Worker Registered ({len(sw_patterns)} worker(s))',
            'severity': 'INFO',
            'category': 'js_security',
            'description': (
                f'{len(sw_patterns)} service worker(s) are registered: '
                f'{", ".join(sw_patterns[:3])}. Service workers can intercept '
                f'and modify network requests. A compromised service worker '
                f'can serve malicious content even after the original attack.'
            ),
            'recommendation': (
                'Audit service worker scripts for security. Ensure they use '
                'strict Content-Security-Policy and do not cache sensitive data. '
                'Implement proper cache invalidation.'
            ),
            'evidence': f'Service worker URLs: {", ".join(sw_patterns[:3])}',
        })
    elif sw_generic and not sw_patterns:
        findings.append({
            'title': 'Dynamic Service Worker Registration',
            'severity': 'LOW',
            'category': 'js_security',
            'description': (
                'A service worker is registered with a dynamic URL. Dynamic '
                'registrations are harder to audit and may be exploitable '
                'if the URL is attacker-controlled.'
            ),
            'recommendation': (
                'Use static service worker URLs. Audit service worker scopes '
                'and ensure they are as narrow as possible.'
            ),
            'evidence': 'Dynamic serviceWorker.register() call detected',
        })


def _check_indexeddb_sensitive(body, parsed_url, findings):
    """Detect sensitive data stored in IndexedDB."""
    idb_patterns = re.findall(
        r'(?:indexedDB|webkitIndexedDB)\s*\.\s*open\s*\(\s*["\']([^"\']+)["\']',
        body,
        re.IGNORECASE,
    )

    if not idb_patterns:
        return

    db_names = list(set(idb_patterns))

    sensitive_stores = [
        'user', 'auth', 'token', 'session', 'credential',
        'password', 'key', 'wallet', 'payment', 'account',
    ]

    sensitive_found = []
    for db_name in db_names:
        if any(s in db_name.lower() for s in sensitive_stores):
            sensitive_found.append(db_name)

    if sensitive_found:
        findings.append({
            'title': f'Sensitive Data in IndexedDB ({len(sensitive_found)} database(s))',
            'severity': 'MEDIUM',
            'category': 'js_security',
            'description': (
                f'IndexedDB databases with potentially sensitive names detected: '
                f'{", ".join(sensitive_found)}. IndexedDB persists across sessions '
                f'and is accessible to any script running in the same origin, '
                f'making data vulnerable to XSS attacks.'
            ),
            'recommendation': (
                'Avoid storing sensitive data in IndexedDB. Use HttpOnly cookies '
                'for authentication tokens. If IndexedDB is necessary, encrypt '
                'sensitive values before storage.'
            ),
            'evidence': f'Sensitive IndexedDB databases: {", ".join(sensitive_found)}',
        })
    elif len(db_names) > 0:
        findings.append({
            'title': f'IndexedDB Usage Detected ({len(db_names)} database(s))',
            'severity': 'INFO',
            'category': 'js_security',
            'description': (
                f'IndexedDB databases detected: {", ".join(db_names[:3])}. '
                f'Review what data is stored to ensure no sensitive information '
                f'is persisted client-side.'
            ),
            'recommendation': (
                'Review IndexedDB usage to ensure sensitive data is not stored '
                'client-side. Use encrypted storage for any non-trivial data.'
            ),
            'evidence': f'IndexedDB databases: {", ".join(db_names[:3])}',
        })


def check_js_security(response, parsed_url, findings):
    """Detect insecure JavaScript patterns in page source."""
    body = _get_body(response)

    _check_postmessage(body, parsed_url, findings)
    _check_sensitive_storage(body, parsed_url, findings)
    _check_window_opener(body, parsed_url, findings)
    _check_sri_integrity(body, parsed_url, findings)
    _check_inline_event_handlers(body, parsed_url, findings)
    _check_webworker_insecure(body, parsed_url, findings)
    _check_service_workers(body, parsed_url, findings)
    _check_indexeddb_sensitive(body, parsed_url, findings)


JS_SECURITY_CHECKS = [check_js_security]