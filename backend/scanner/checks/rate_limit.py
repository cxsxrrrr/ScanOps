"""
Rate limiting verification (semi-active).

Sends multiple rapid requests to detect missing or ineffective
rate limiting on authentication and state-changing endpoints.
"""
import logging
import time
import requests as req_lib

logger = logging.getLogger('scanner')

PROBE_TIMEOUT = 10
RAPID_REQUESTS = 8
RAPID_INTERVAL = 0.1

RATE_LIMIT_HEADERS = [
    'X-RateLimit-Limit', 'X-Rate-Limit-Limit',
    'RateLimit-Limit', 'X-RateLimit-Remaining',
    'X-Rate-Limit-Remaining', 'RateLimit-Remaining',
    'Retry-After',
]

AUTH_ENDPOINTS = [
    '/login', '/api/login', '/api/auth/login',
    '/signin', '/api/signin', '/auth/login',
    '/api/auth', '/api/token', '/oauth/token',
]


def check_rate_limit(response, parsed_url, findings):
    """Test for missing rate limiting on authentication endpoints."""
    base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
    session = req_lib.Session()
    session.headers.update({'User-Agent': 'AuditoriaWeb-Scanner/1.0'})

    has_rate_limit_headers = any(
        h in response.headers for h in RATE_LIMIT_HEADERS
    )

    for endpoint in AUTH_ENDPOINTS:
        url = f'{base_url}{endpoint}'
        try:
            resp = session.get(
                url, timeout=PROBE_TIMEOUT,
                allow_redirects=True, verify=False,
            )
        except req_lib.exceptions.RequestException:
            continue

        endpoint_has_rate_limit = any(
            h in resp.headers for h in RATE_LIMIT_HEADERS
        )

        if endpoint_has_rate_limit:
            continue

        status_codes = []
        start_time = time.time()

        for i in range(RAPID_REQUESTS):
            try:
                fast_resp = session.get(
                    url, timeout=PROBE_TIMEOUT,
                    allow_redirects=True, verify=False,
                )
                status_codes.append(fast_resp.status_code)
            except req_lib.exceptions.RequestException:
                status_codes.append(0)
            time.sleep(RAPID_INTERVAL)

        elapsed = time.time() - start_time

        _analyze_rate_limit(
            endpoint, status_codes, elapsed,
            has_rate_limit_headers, findings,
        )
        break


def _analyze_rate_limit(endpoint, status_codes, elapsed, has_headers, findings):
    """Analyze rate limiting based on response codes and timing."""
    successful = sum(1 for c in status_codes if 200 <= c < 300)
    total = len(status_codes)

    if total == 0:
        return

    rate_limited = sum(1 for c in status_codes if c in (429, 503))

    if successful >= 6 and rate_limited == 0:
        requests_per_second = total / max(elapsed, 0.01)

        findings.append({
            'title': f'Missing Rate Limiting on {endpoint}',
            'severity': 'MEDIUM',
            'category': 'rate_limit',
            'description': (
                f'Sent {total} requests to {endpoint} in {elapsed:.1f}s '
                f'({requests_per_second:.1f} req/s) without rate limiting. '
                f'{successful} of {total} requests succeeded with no throttling. '
                f'This allows brute-force and credential stuffing attacks.'
            ),
            'recommendation': (
                'Implement rate limiting on all authentication endpoints. '
                'Use progressive delays, CAPTCHA challenges, or temporary '
                'account lockout after repeated failures. Set rate limit '
                'headers (X-RateLimit-Limit, Retry-After).'
            ),
            'evidence': (
                f'{successful}/{total} requests succeeded in {elapsed:.1f}s '
                f'at ~{requests_per_second:.1f} req/s'
            ),
        })

    elif successful > 0 and rate_limited > 0:
        findings.append({
            'title': f'Weak Rate Limiting on {endpoint}',
            'severity': 'LOW',
            'category': 'rate_limit',
            'description': (
                f'Rate limiting was triggered after {rate_limited} requests, '
                f'but {successful} requests succeeded before throttling. '
                f'An attacker can still make {successful} attempts before lockout.'
            ),
            'recommendation': (
                'Reduce the rate limit threshold. Consider stricter limits '
                '(e.g., 3-5 attempts per minute) for authentication endpoints. '
                'Implement CAPTCHA after threshold is reached.'
            ),
            'evidence': (
                f'{successful} successful, {rate_limited} rate-limited '
                f'out of {total} requests'
            ),
        })


RATE_LIMIT_CHECKS = [check_rate_limit]