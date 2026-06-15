"""
Passive open redirect vulnerability checks.

Detects open redirect indicators by analyzing URL parameters,
meta refresh redirects, JavaScript redirect patterns, and
OAuth/callback URLs that may accept external destinations.
"""
import re
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 100_000

REDIRECT_PARAM_NAMES = {
    'url', 'uri', 'path', 'redirect', 'next', 'target', 'dest',
    'destination', 'return', 'returnto', 'return_url', 'returntourl',
    'continue', 'goto', 'link', 'src', 'source', 'fetch', 'proxy',
    'forward', 'return_path', 'redir', 'redirect_url', 'redirect_uri',
    'callback', 'callback_url', 'relay_url', 'redirect_to',
    'out', 'exit', 'jump', 'page', 'site', 'view',
}

META_REFRESH_PATTERN = re.compile(
    r'<meta[^>]*http-equiv\s*=\s*["\']?refresh["\']?[^>]*'
    r'content\s*=\s*["\']?\d+\s*;\s*url\s*=\s*([^"\']+)',
    re.IGNORECASE,
)

JS_REDIRECT_PATTERNS = [
    re.compile(r'window\.location\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'window\.location\.replace\s*\(\s*["\']([^"\']+)["\']\s*\)', re.IGNORECASE),
    re.compile(r'document\.location\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'location\.href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
]


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_open_redirect(response, parsed_url, findings):
    """Detect open redirect vulnerabilities in URL parameters and page content."""
    _check_redirect_params(response, parsed_url, findings)
    _check_meta_refresh(response, parsed_url, findings)
    _check_js_redirects(response, parsed_url, findings)


def _check_redirect_params(response, parsed_url, findings):
    """Detect redirect parameters in the URL that accept external URLs."""
    query_params = parse_qs(parsed_url.query)
    found_redirects = []

    for param_name, values in query_params.items():
        if param_name.lower() not in REDIRECT_PARAM_NAMES:
            continue
        for value in values:
            try:
                target = urlparse(value)
                if target.scheme in ('http', 'https') and target.netloc:
                    if target.netloc.lower() != parsed_url.netloc.lower():
                        found_redirects.append((param_name, value))
            except Exception:
                continue

    if found_redirects:
        param_names = list(set(p for p, _ in found_redirects))
        findings.append({
            'title': 'Open Redirect Parameter Detected',
            'severity': 'HIGH',
            'category': 'redirect',
            'description': (
                f'The URL contains redirect parameter(s) ({", ".join(param_names)}) '
                f'that point to an external domain. An attacker could manipulate '
                f'these parameters to redirect users to malicious sites.'
            ),
            'recommendation': (
                'Validate redirect destinations server-side against an '
                'allowlist of trusted domains. Use relative paths instead '
                'of absolute URLs for internal redirects.'
            ),
            'evidence': (
                f'Redirect params: {"; ".join(f"{p}={v[:100]}" for p, v in found_redirects[:5])}'
            ),
        })


def _check_meta_refresh(response, parsed_url, findings):
    """Detect meta refresh redirects pointing to external domains."""
    body = _get_body(response)

    external_redirects = []
    for match in META_REFRESH_PATTERN.findall(body):
        url = match.strip().strip("'\"")
        try:
            target = urlparse(url)
            if target.scheme in ('http', 'https') and target.netloc:
                if target.netloc.lower() != parsed_url.netloc.lower():
                    external_redirects.append(url)
        except Exception:
            continue

    if external_redirects:
        findings.append({
            'title': 'External Meta Refresh Redirect',
            'severity': 'MEDIUM',
            'category': 'redirect',
            'description': (
                'The page contains a meta refresh redirect pointing to an '
                'external domain. If the redirect URL is user-controllable, '
                'this enables open redirect attacks.'
            ),
            'recommendation': (
                'Avoid using meta refresh for redirects. Use server-side '
                'redirects (301/302) with validated destination URLs.'
            ),
            'evidence': f'External meta refresh targets: {", ".join(external_redirects[:3])}',
        })


def _check_js_redirects(response, parsed_url, findings):
    """Detect JavaScript redirect patterns that may be exploitable."""
    body = _get_body(response)

    js_redirects = []
    for pattern in JS_REDIRECT_PATTERNS:
        for match in pattern.findall(body):
            url = match.strip()
            try:
                target = urlparse(url)
                if target.scheme in ('http', 'https') and target.netloc:
                    if target.netloc.lower() != parsed_url.netloc.lower():
                        js_redirects.append(url)
            except Exception:
                continue

    if js_redirects:
        findings.append({
            'title': 'JavaScript External Redirect Detected',
            'severity': 'MEDIUM',
            'category': 'redirect',
            'description': (
                'The page contains JavaScript code that redirects to an '
                'external domain. If the target URL is derived from user '
                'input, this could enable open redirect or phishing attacks.'
            ),
            'recommendation': (
                'Never use user-supplied data directly in redirect targets. '
                'Validate and sanitize all redirect URLs against a domain allowlist.'
            ),
            'evidence': f'External JS redirect targets: {", ".join(js_redirects[:3])}',
        })

    redirect_param_refs = []
    for param in REDIRECT_PARAM_NAMES:
        if param in body.lower():
            redirect_param_refs.append(param)
            if len(redirect_param_refs) >= 5:
                break

    if redirect_param_refs and not js_redirects:
        findings.append({
            'title': 'Redirect Parameter References in JavaScript',
            'severity': 'LOW',
            'category': 'redirect',
            'description': (
                f'The page source references redirect parameter names '
                f'({", ".join(redirect_param_refs)}). If these are used '
                f'in redirect logic without validation, they may be '
                f'vulnerable to open redirect attacks.'
            ),
            'recommendation': (
                'Ensure all redirect logic validates destination URLs '
                'against a server-side allowlist of trusted domains.'
            ),
            'evidence': f'Redirect-related params referenced: {", ".join(redirect_param_refs)}',
        })


REDIRECT_CHECKS = [check_open_redirect]