"""
Local File Inclusion (LFI) path probing (semi-active).

Tests URL parameters with LFI payloads to detect path traversal
vulnerabilities. Only uses safe GET requests with probe payloads.
"""
import re
import logging
import requests as req_lib
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

logger = logging.getLogger('scanner')

PROBE_TIMEOUT = 10

LFI_PAYLOADS = [
    '../../../etc/passwd',
    '..%2f..%2f..%2fetc%2fpasswd',
    '..%252f..%252f..%252fetc%252fpasswd',
    '....//....//....//etc/passwd',
    '/etc/passwd',
    '..%2e%2e%2f..%2e%2e%2f..%2e%2e%2fetc%2fpasswd',
]

LFI_SUCCESS_PATTERNS = [
    re.compile(r'root:x:\d+:\d+:'),
    re.compile(r'root:\$6\$'),
    re.compile(r'nobody:x:'),
    re.compile(r'sbin:nologin'),
]

URL_PARAMS_TO_TEST = [
    'file', 'path', 'page', 'include', 'template', 'doc',
    'document', 'folder', 'content', 'view', 'show', 'dir',
    'action', 'load', 'img', 'image', 'src', 'source',
]


def check_lfi(response, parsed_url, findings):
    """Probe URL parameters for Local File Inclusion vulnerabilities."""
    query_string = parsed_url.query
    if not query_string:
        body = response.text[:100_000] if hasattr(response, 'text') else ''
        _check_body_lfi_refs(body, findings)
        return

    params = parse_qs(query_string, keep_blank_values=True)
    target_params = []

    for key in params:
        if any(t in key.lower() for t in URL_PARAMS_TO_TEST):
            target_params.append(key)

    if not target_params:
        for key in params:
            if _looks_like_path_param(params[key][0] if params[key] else ''):
                target_params.append(key)

    if not target_params:
        return

    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}'
    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    original_body = response.text[:5000] if hasattr(response, 'text') else ''

    for param in target_params[:3]:
        for payload in LFI_PAYLOADS[:3]:
            try:
                new_params = dict(params)
                new_params[param] = [payload]
                new_query = urlencode(new_params, doseq=True)
                test_url = f'{base_url}?{new_query}'

                resp = session.get(
                    test_url, timeout=PROBE_TIMEOUT,
                    allow_redirects=False, verify=False,
                )

                if resp.status_code in (200, 301, 302, 500):
                    body = resp.text[:5000] if hasattr(resp, 'text') else ''
                    if _is_lfi_successful(body, original_body):
                        findings.append({
                            'title': f'Local File Inclusion (LFI) in Parameter: {param}',
                            'severity': 'CRITICAL',
                            'category': 'injection',
                            'description': (
                                f'The parameter "{param}" appears vulnerable to Local '
                                f'File Inclusion. The server processed a path traversal '
                                f'payload and returned file system content, potentially '
                                f'exposing sensitive system files.'
                            ),
                            'recommendation': (
                                'Strictly validate and sanitize all file path inputs. '
                                'Use allowlists of permitted files. Never pass user input '
                                'directly to file system operations. Use basename() to strip '
                                'path components.'
                            ),
                            'evidence': f'LFI payload in {param} returned file content',
                        })
                        return

            except (req_lib.exceptions.RequestException, Exception):
                continue


def _is_lfi_successful(body, original_body):
    """Check if the response contains LFI success indicators."""
    for pattern in LFI_SUCCESS_PATTERNS:
        if pattern.search(body):
            return True
    return False


def _looks_like_path_param(value):
    """Check if a parameter value looks like a file path."""
    path_indicators = ['/', '\\', '.', '..', '%2f', '%5c', '.html', '.php', '.txt']
    value_lower = value.lower()
    return any(ind in value_lower for ind in path_indicators)


def _check_body_lfi_refs(body, findings):
    """Check page content for references to LFI-prone URL patterns."""
    lfi_refs = re.findall(
        r'(?:file|path|page|include|template|doc|view|load|img|src)=(?:["\']?)([^&"\']+)',
        body,
        re.IGNORECASE,
    )

    suspicious = []
    for ref in lfi_refs:
        if '..' in ref or ref.startswith('/') or ref.startswith('\\'):
            suspicious.append(ref[:100])

    if len(suspicious) >= 2:
        findings.append({
            'title': 'LFI-Susceptible URL Parameters Detected',
            'severity': 'MEDIUM',
            'category': 'injection',
            'description': (
                f'{len(suspicious)} URL parameter(s) appear to accept file paths. '
                f'This may indicate LFI vulnerability if the paths are not '
                f'properly validated.'
            ),
            'recommendation': (
                'Validate all file path parameters server-side. Use allowlists '
                'and never pass user input directly to file operations.'
            ),
            'evidence': f'Suspicious parameters: {"; ".join(suspicious[:3])}',
        })


LFI_CHECKS = [check_lfi]