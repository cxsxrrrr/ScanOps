"""
Semi-active CORS origin reflection detection.

Detects misconfigured CORS that reflects arbitrary origins,
which is more dangerous than simple wildcard CORS.
"""
import logging
import requests as req_lib

logger = logging.getLogger('scanner')

PROBE_TIMEOUT = 10
TEST_ORIGINS = [
    'https://evil-test-12345.example.com',
    'https://sub.domain-not-exist.xyz',
]

NULL_ORIGIN = 'null'
SUBDOMAIN_ORIGIN_PREFIX = 'https://sub-evil-test-'


def check_cors_reflection(response, parsed_url, findings):
    """Detect CORS origin reflection by sending requests with custom Origin."""
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    acao = response.headers.get('Access-Control-Allow-Origin', '')
    acac = response.headers.get('Access-Control-Allow-Credentials', '').lower()

    if acao == '*' and acac == 'true':
        findings.append({
            'title': 'CORS Wildcard with Credentials (Critical)',
            'severity': 'CRITICAL',
            'category': 'cors',
            'description': (
                'The server returns Access-Control-Allow-Origin: * with '
                'Access-Control-Allow-Credentials: true. This combination '
                'allows any website to read authenticated responses from '
                'this origin — a severe misconfiguration.'
            ),
            'recommendation': (
                'Never combine Access-Control-Allow-Origin: * with '
                'Access-Control-Allow-Credentials: true. Specify explicit '
                'trusted origins instead.'
            ),
            'evidence': (
                f'Access-Control-Allow-Origin: {acao}, '
                f'Access-Control-Allow-Credentials: {acac}'
            ),
        })
        return

    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    origin_url = f'{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}'

    for test_origin in TEST_ORIGINS:
        try:
            resp = session.get(
                origin_url,
                timeout=PROBE_TIMEOUT,
                allow_redirects=True,
                verify=False,
                headers={'Origin': test_origin},
            )

            reflected_acao = resp.headers.get('Access-Control-Allow-Origin', '')
            reflected_acac = resp.headers.get('Access-Control-Allow-Credentials', '').lower()

            if reflected_acao == test_origin:
                severity = 'CRITICAL' if reflected_acac == 'true' else 'HIGH'
                desc_suffix = ''
                if reflected_acac == 'true':
                    desc_suffix = (
                        ' Combined with Allow-Credentials: true, this allows '
                        'any website to read authenticated responses.'
                    )

                findings.append({
                    'title': 'CORS Origin Reflection Detected',
                    'severity': severity,
                    'category': 'cors',
                    'description': (
                        'The server reflects the Origin header in '
                        'Access-Control-Allow-Origin, allowing any origin '
                        f'to make authenticated cross-origin requests.'
                        f'{desc_suffix}'
                    ),
                    'recommendation': (
                        'Never reflect the Origin header directly. Maintain '
                        'an explicit allowlist of trusted origins and only '
                        'echo those in Access-Control-Allow-Origin.'
                    ),
                    'evidence': (
                        f'Origin: {test_origin}, '
                        f'ACAO: {reflected_acao}, '
                        f'ACAC: {reflected_acac}'
                    ),
                })
                return

            if reflected_acao == '*' and reflected_acac != 'true':
                break

        except req_lib.exceptions.RequestException:
            continue

    _check_null_origin(session, origin_url, findings)
    _check_subdomain_reflection(session, origin_url, parsed_url, findings)


def _check_null_origin(session, origin_url, findings):
    """Check if the server allows the null origin (common in sandboxed iframes)."""
    try:
        resp = session.get(
            origin_url,
            timeout=PROBE_TIMEOUT,
            allow_redirects=True,
            verify=False,
            headers={'Origin': NULL_ORIGIN},
        )

        acao = resp.headers.get('Access-Control-Allow-Origin', '')
        acac = resp.headers.get('Access-Control-Allow-Credentials', '').lower()

        if acao == 'null':
            severity = 'HIGH' if acac == 'true' else 'MEDIUM'
            findings.append({
                'title': 'CORS Allows Null Origin',
                'severity': severity,
                'category': 'cors',
                'description': (
                    'The server responds with Access-Control-Allow-Origin: null '
                    'when the Origin header is "null". This occurs with sandboxed '
                    'iframes and local files, allowing cross-origin attacks from '
                    'these contexts.'
                    + (' Combined with Allow-Credentials: true, any sandboxed '
                       'iframe can read authenticated responses.' if acac == 'true' else '')
                ),
                'recommendation': (
                    'Do not allow "null" in Access-Control-Allow-Origin. '
                    'Reject requests with null Origin or handle them explicitly.'
                ),
                'evidence': f'Origin: null, ACAO: {acao}, ACAC: {acac}',
            })
    except req_lib.exceptions.RequestException:
        pass


def _check_subdomain_reflection(session, origin_url, parsed_url, findings):
    """Check if the server reflects arbitrary subdomains of the target domain."""
    if not parsed_url or not parsed_url.hostname:
        return

    hostname = parsed_url.hostname
    test_subdomain = f'https://evil-test-12345.{hostname}'

    try:
        resp = session.get(
            origin_url,
            timeout=PROBE_TIMEOUT,
            allow_redirects=True,
            verify=False,
            headers={'Origin': test_subdomain},
        )

        acao = resp.headers.get('Access-Control-Allow-Origin', '')
        acac = resp.headers.get('Access-Control-Allow-Credentials', '').lower()

        if acao == test_subdomain or acao == f'https://evil-test-12345.{hostname}':
            severity = 'CRITICAL' if acac == 'true' else 'HIGH'
            findings.append({
                'title': 'CORS Subdomain Reflection Detected',
                'severity': severity,
                'category': 'cors',
                'description': (
                    'The server reflects arbitrary subdomain origins in '
                    'Access-Control-Allow-Origin. An attacker who controls any '
                    'subdomain can read authenticated responses from this origin.'
                    + (' With Allow-Credentials: true, this is a critical '
                       'vulnerability.' if acac == 'true' else '')
                ),
                'recommendation': (
                    'Only allow specific, trusted subdomains in CORS '
                    'configuration. Do not use dynamic origin reflection '
                    'based on subdomain matching.'
                ),
                'evidence': f'Origin: {test_subdomain}, ACAO: {acao}, ACAC: {acac}',
            })
    except req_lib.exceptions.RequestException:
        pass


CORS_REFLECTION_CHECKS = [check_cors_reflection]