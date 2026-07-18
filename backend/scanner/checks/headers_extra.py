"""
Passive checks for modern browser-isolation headers, CSP/Referrer-Policy
quality (not just presence), missing Subresource Integrity, and unsafe
postMessage usage.

These complement the base header-presence check in engine.py, which only
flags a header as *missing* — these flag a header that's *present but
configured weakly enough to be useless*.
"""
import re
import logging

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 200_000

# Directives that make a CSP largely ineffective against XSS even though
# the header itself is present.
CSP_WEAK_PATTERNS = [
    (re.compile(r"unsafe-inline"), "'unsafe-inline' allows inline script/style execution"),
    (re.compile(r"unsafe-eval"), "'unsafe-eval' allows eval()-based script execution"),
    (re.compile(r"default-src\s+\*(?!\S)"), "default-src '*' allows loading from any origin"),
    (re.compile(r"script-src\s+\*(?!\S)"), "script-src '*' allows scripts from any origin"),
]

WEAK_REFERRER_VALUES = {'unsafe-url', 'no-referrer-when-downgrade'}

# <script>/<link> tags pulling from a third-party origin
SCRIPT_TAG_PATTERN = re.compile(
    r'<script[^>]+src\s*=\s*["\'](https?://[^"\']+)["\'][^>]*>',
    re.IGNORECASE,
)
INTEGRITY_ATTR_PATTERN = re.compile(r'integrity\s*=', re.IGNORECASE)

POSTMESSAGE_LISTENER_PATTERN = re.compile(
    r'addEventListener\(\s*["\']message["\']\s*,\s*(?:function\s*\(([^)]*)\)|(\([^)]*\)|\w+)\s*=>)',
    re.IGNORECASE,
)


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_coop_coep_corp(response, parsed_url, findings):
    """Detect missing Cross-Origin isolation headers (Spectre mitigations)."""
    headers = {k.lower(): v for k, v in response.headers.items()}

    checks = {
        'cross-origin-opener-policy': (
            'Cross-Origin-Opener-Policy',
            'Allows other origins to retain a window reference via window.opener, '
            'enabling some cross-origin leak and Spectre-class attacks.',
            'Add Cross-Origin-Opener-Policy: same-origin.',
        ),
        'cross-origin-resource-policy': (
            'Cross-Origin-Resource-Policy',
            'Resources can be loaded cross-origin by default, which can leak data '
            'to embedding sites (Spectre-class attacks).',
            'Add Cross-Origin-Resource-Policy: same-origin or same-site.',
        ),
    }

    for header_key, (name, desc, rec) in checks.items():
        if header_key not in headers:
            findings.append({
                'title': f'Missing {name} Header',
                'severity': 'LOW',
                'category': 'headers',
                'description': f'{name} header is missing. {desc}',
                'recommendation': rec,
                'evidence': f'Header not found on {parsed_url.geturl()}',
            })


def check_csp_quality(response, parsed_url, findings):
    """Flag a present-but-weak Content-Security-Policy."""
    csp = response.headers.get('Content-Security-Policy', '')
    if not csp:
        return  # absence is already flagged by the base header check

    issues = [reason for pattern, reason in CSP_WEAK_PATTERNS if pattern.search(csp)]
    if issues:
        findings.append({
            'title': 'Weak Content-Security-Policy Directives',
            'severity': 'MEDIUM',
            'category': 'headers',
            'description': (
                'A Content-Security-Policy header is present but contains '
                'directives that significantly weaken its protection: '
                + '; '.join(issues) + '.'
            ),
            'recommendation': (
                'Avoid unsafe-inline/unsafe-eval — use nonces or hashes for '
                'inline scripts. Scope default-src/script-src to specific '
                'trusted origins instead of wildcards.'
            ),
            'evidence': f'CSP: {csp[:300]}',
        })


def check_referrer_policy_quality(response, parsed_url, findings):
    """Flag a present-but-permissive Referrer-Policy."""
    policy = response.headers.get('Referrer-Policy', '').strip().lower()
    if not policy:
        return  # absence already flagged by the base header check

    if policy in WEAK_REFERRER_VALUES:
        findings.append({
            'title': 'Permissive Referrer-Policy',
            'severity': 'LOW',
            'category': 'headers',
            'description': (
                f'Referrer-Policy is set to "{policy}", which leaks the full '
                'URL (including query strings/paths) to third parties or '
                'over insecure connections.'
            ),
            'recommendation': (
                'Use a stricter policy such as strict-origin-when-cross-origin '
                'or no-referrer.'
            ),
            'evidence': f'Referrer-Policy: {policy}',
        })


def check_sri_missing(response, parsed_url, findings):
    """Detect third-party <script> tags without Subresource Integrity."""
    body = _get_body(response)
    if 'text/html' not in response.headers.get('Content-Type', ''):
        return

    own_host = parsed_url.netloc.lower()
    missing = []

    for match in SCRIPT_TAG_PATTERN.finditer(body):
        src = match.group(1)
        if own_host and own_host in src.lower():
            continue  # same-origin script, SRI less critical
        tag = match.group(0)
        if not INTEGRITY_ATTR_PATTERN.search(tag):
            missing.append(src)

    if missing:
        findings.append({
            'title': 'Missing Subresource Integrity (SRI)',
            'severity': 'MEDIUM',
            'category': 'sri',
            'description': (
                f'{len(missing)} third-party script(s) are loaded without an '
                'integrity attribute. If the third-party host is compromised '
                'or the CDN is poisoned, malicious code would run unmodified.'
            ),
            'recommendation': (
                'Add an integrity="sha384-..." attribute (with crossorigin) '
                'to every externally-hosted <script>/<link> tag.'
            ),
            'evidence': f'Scripts without SRI: {", ".join(missing[:5])}',
        })


def check_postmessage_origin(response, parsed_url, findings):
    """Detect window.postMessage listeners that don't validate event.origin."""
    body = _get_body(response)
    if 'text/html' not in response.headers.get('Content-Type', '') and '<script' not in body:
        return

    for match in POSTMESSAGE_LISTENER_PATTERN.finditer(body):
        # Look at a window of code right after the listener registration for
        # any origin check — good enough as a heuristic without a JS parser.
        window = body[match.end():match.end() + 300]
        if not re.search(r'\.origin\b', window):
            findings.append({
                'title': 'postMessage Listener Without Origin Validation',
                'severity': 'MEDIUM',
                'category': 'postmessage',
                'description': (
                    'A window.addEventListener("message", ...) handler was '
                    'found with no apparent check on event.origin nearby. '
                    'Any origin can send messages processed by this handler.'
                ),
                'recommendation': (
                    'Validate event.origin against an explicit allow-list '
                    'before trusting event.data.'
                ),
                'evidence': f'Handler near: {match.group(0)[:150]}',
            })
            break  # one finding is enough per page


HEADERS_EXTRA_CHECKS = [
    check_coop_coep_corp,
    check_csp_quality,
    check_referrer_policy_quality,
    check_sri_missing,
    check_postmessage_origin,
]
