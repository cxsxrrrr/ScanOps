"""
Reflected XSS detection (semi-active).

Injects probe payloads into URL parameters and form fields to detect
reflected input that is not properly sanitized. Only uses safe probes
that do not execute JavaScript.
"""
import re
import logging
import requests as req_lib
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

logger = logging.getLogger('scanner')

PROBE_TIMEOUT = 10

XSS_PROBES = [
    ('XSS_CANARY_9x7z', 'unique_marker'),
    ('"><svg/onload=XSS_CANARY_9x7z>', 'event_handler_breakout'),
    ("'><img/src=x onerror=XSS_CANARY_9x7z>", 'event_handler_single_quote'),
    ('<script>XSS_CANARY_9x7z</script>', 'script_tag'),
    ('javascript:XSS_CANARY_9x7z', 'javascript_uri'),
    ('"><a/href="javascript:XSS_CANARY_9x7z">click</a>', 'anchor_js'),
]

CANARY = 'XSS_CANARY_9x7z'

URL_PARAMS_TO_INJECT = [
    'q', 'query', 'search', 's', 'keyword', 'term', 'find',
    'name', 'user', 'username', 'email', 'id', 'page',
    'category', 'tag', 'sort', 'filter', 'action',
]


def check_reflected_xss(response, parsed_url, findings):
    """Inject XSS probes into URL parameters to detect reflected input."""
    body = response.text[:150_000] if hasattr(response, 'text') else ''
    url_str = parsed_url.geturl()

    _check_existing_reflection(body, findings)

    params = parse_qs(parsed_url.query, keep_blank_values=True) if parsed_url.query else {}

    inject_params = []
    for key in params:
        if any(t in key.lower() for t in URL_PARAMS_TO_INJECT):
            inject_params.append(key)

    if not inject_params and not params:
        inject_params = ['q']

    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}'
    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    for param in inject_params[:3]:
        for probe_value, probe_type in XSS_PROBES[:4]:
            try:
                new_params = dict(params) if params else {}
                new_params[param] = [probe_value]
                new_query = urlencode(new_params, doseq=True)
                test_url = f'{base_url}?{new_query}'

                resp = session.get(
                    test_url, timeout=PROBE_TIMEOUT,
                    allow_redirects=True, verify=False,
                )

                if resp.status_code == 200:
                    resp_body = resp.text[:150_000] if hasattr(resp, 'text') else ''

                    if CANARY not in resp_body:
                        continue

                    severity, desc = _assess_reflection(
                        probe_value, probe_type, resp_body
                    )

                    findings.append({
                        'title': f'Reflected XSS in Parameter: {param}',
                        'severity': severity,
                        'category': 'xss',
                        'description': desc,
                        'recommendation': (
                            'Sanitize and encode all user input before rendering '
                            'in HTML. Use context-appropriate output encoding: '
                            'HTML entity encoding for body content, JavaScript '
                            'encoding for script contexts, URL encoding for URL '
                            'contexts. Implement Content-Security-Policy headers.'
                        ),
                        'evidence': (
                            f'Input in param "{param}" reflected with '
                            f'{probe_type} pattern'
                        ),
                    })
                    return

            except (req_lib.exceptions.RequestException, Exception):
                continue


def _check_existing_reflection(body, findings):
    """Check if the page already reflects URL parameters without sanitization."""
    dangerous_patterns = [
        (r'<script[^>]*>[\s\S]*?document\.write\s*\(', 'document.write with script'),
        (r'<script[^>]*>[\s\S]*?\.innerHTML\s*=', 'innerHTML assignment in script'),
        (r'<script[^>]*>[\s\S]*?eval\s*\(', 'eval() in script'),
    ]

    for pattern, desc in dangerous_patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        if matches and len(matches) > 3:
            findings.append({
                'title': f'Potentially Dangerous JS Pattern: {desc}',
                'severity': 'LOW',
                'category': 'xss',
                'description': (
                    f'Multiple instances of {desc} found in the page source. '
                    f'These DOM sinks can be exploited if they process '
                    f'unsanitized user input.'
                ),
                'recommendation': (
                    'Use textContent instead of innerHTML. Avoid eval() and '
                    'document.write(). Use DOMPurify for any HTML rendering.'
                ),
                'evidence': f'{len(matches)} instances of {desc}',
            })
            break


def _assess_reflection(probe_value, probe_type, resp_body):
    """Assess the severity and description of a reflected XSS finding."""
    if probe_type == 'script_tag':
        if f'<script>{CANARY}</script>' in resp_body.lower():
            return 'CRITICAL', (
                'User input is reflected inside a <script> tag without '
                'sanitization. This allows direct JavaScript execution.'
            )
        return 'HIGH', 'User input is reflected with script tag patterns.'

    if probe_type in ('event_handler_breakout', 'event_handler_single_quote'):
        if CANARY in resp_body:
            tag_context = _find_reflection_context(CANARY, resp_body)
            if tag_context and '<' in tag_context:
                return 'HIGH', (
                    f'User input breaks out of an HTML attribute and creates '
                    f'an event handler. Reflected context: {tag_context[:100]}'
                )
            return 'MEDIUM', 'User input is reflected in an HTML attribute context.'

    if probe_type == 'javascript_uri':
        if CANARY in resp_body:
            return 'HIGH', (
                'User input is reflected in a javascript: URI context, '
                'enabling script execution via link clicks.'
            )

    return 'MEDIUM', 'User input is reflected in the page without proper encoding.'


def _find_reflection_context(canary, body):
    """Find the HTML context around the reflected canary."""
    idx = body.find(canary)
    if idx == -1:
        return None

    start = max(0, idx - 50)
    end = min(len(body), idx + len(canary) + 50)
    return body[start:end]


REFLECTED_XSS_CHECKS = [check_reflected_xss]