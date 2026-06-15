"""
Passive race condition vulnerability detection.

Detects indicators of race condition vulnerabilities by analyzing
forms and API endpoints for missing idempotency tokens, financial/
state-changing operations without debouncing, and concurrent request risks.
"""
import re
import logging

logger = logging.getLogger('scanner')

MAX_BODY_SIZE = 100_000

FINANCIAL_KEYWORDS = [
    'buy', 'purchase', 'checkout', 'payment', 'pay', 'transfer',
    'withdraw', 'deposit', 'submit-order', 'place-order', 'order',
    'charge', 'refund', 'subscribe', 'subscription', 'donate',
    'cart', 'checkout', 'stripe', 'paypal', 'braintree',
]

IDEMPOTENCY_TOKEN_NAMES = {
    'csrfmiddlewaretoken', 'csrf_token', '_token',
    'authenticity_token', '__requestverificationtoken',
    'idempotency_key', 'idempotency-key', 'x-idempotency-key',
    'nonce', 'transaction_id', 'request_id',
}


def _get_body(response):
    return response.text[:MAX_BODY_SIZE] if hasattr(response, 'text') else ''


def check_race_condition(response, parsed_url, findings):
    """Detect potential race condition vulnerabilities in forms and APIs."""
    body = _get_body(response)
    content_type = response.headers.get('Content-Type', '')

    _check_forms_without_debounce(body, parsed_url, findings)
    _check_financial_forms_without_idempotency(body, parsed_url, findings)
    _check_api_endpoints_without_rate_limit(response, parsed_url, findings)


def _check_forms_without_debounce(body, parsed_url, findings):
    """Detect forms that perform state-changing operations without debouncing."""
    form_matches = list(re.finditer(
        r'<form[^>]*>(.*?)</form>',
        body,
        re.IGNORECASE | re.DOTALL,
    ))

    for form in form_matches:
        form_attrs = form.group(1) if form.lastindex else ''
        form_content = form.group(2) if form.lastindex else ''

        method_match = re.search(r'method\s*=\s*["\']?(\w+)', form_attrs, re.IGNORECASE)
        action_match = re.search(r'action\s*=\s*["\']([^"\']+)', form_attrs, re.IGNORECASE)
        method = (method_match.group(1).upper() if method_match else 'GET')
        action = action_match.group(1) if action_match else parsed_url.path

        if method != 'POST':
            continue

        has_double_submit = bool(re.search(
            r'onclick\s*=\s*["\'].*?disable|preventdouble|submitting',
            form_content,
            re.IGNORECASE,
        ))

        has_debounce = bool(re.search(
            r'(?:disabled|submitting|loading|processing).*?(?:button|submit|input)',
            form_content,
            re.IGNORECASE,
        )) or bool(re.search(
            r'onsubmit\s*=\s*["\'].*?return\s+false.*?if\s+submitted',
            form_content,
            re.IGNORECASE,
        ))

        if has_double_submit or has_debounce:
            continue

        has_financial = any(kw in action.lower() for kw in FINANCIAL_KEYWORDS)
        has_financial |= any(kw in form_content.lower() for kw in FINANCIAL_KEYWORDS[:8])

        if has_financial:
            findings.append({
                'title': 'Financial Form Without Idempotency Protection',
                'severity': 'HIGH',
                'category': 'race_condition',
                'description': (
                    f'A form submitting to "{action[:100]}" appears to be a '
                    f'financial or state-changing operation but lacks visible '
                    f'idempotency tokens or double-submit protection. This could '
                    f'allow duplicate transactions via race conditions.'
                ),
                'recommendation': (
                    'Add idempotency keys to all financial transactions. '
                    'Implement double-submit prevention on the client side. '
                    'Use database-level constraints to prevent duplicate operations.'
                ),
                'evidence': f'Financial form without debounce on {parsed_url.geturl()}',
            })
            return


def _check_financial_forms_without_idempotency(body, parsed_url, findings):
    """Check for API endpoints related to transactions without idempotency."""
    api_patterns = re.findall(
        r'(?:fetch|axios|XMLHttpRequest|\.post|\.put|\.patch)\s*\(\s*["\']'
        r'(/api/[^"\']*(?:pay|order|transact|buy|checkout|withdraw|deposit)[^"\']*)',
        body,
        re.IGNORECASE,
    )

    for endpoint in api_patterns:
        context_start = max(0, body.lower().find(endpoint) - 200)
        context = body[context_start:context_start + 400]

        has_idempotency = any(tok in context.lower() for tok in IDEMPOTENCY_TOKEN_NAMES)

        if not has_idempotency:
            findings.append({
                'title': 'Financial API Endpoint Without Idempotency',
                'severity': 'MEDIUM',
                'category': 'race_condition',
                'description': (
                    f'An API endpoint ({endpoint[:80]}) appears to handle '
                    f'financial or state-changing operations but does not '
                    f'include idempotency key protection in the request.'
                ),
                'recommendation': (
                    'Add idempotency keys (X-Idempotency-Key header) to all '
                    'financial API calls. Implement server-side deduplication.'
                ),
                'evidence': f'Endpoint: {endpoint[:100]}',
            })
            return


def _check_api_endpoints_without_rate_limit(response, parsed_url, findings):
    """Check state-changing endpoints for missing rate limiting."""
    path = parsed_url.path.lower()
    state_changing_paths = [
        '/api/login', '/api/auth', '/api/register', '/api/signup',
        '/api/password', '/api/reset', '/api/verify',
        '/api/payment', '/api/transfer', '/api/order',
    ]

    if not any(p in path for p in state_changing_paths):
        return

    headers = response.headers
    rate_limit_headers = [
        'X-RateLimit-Limit', 'X-Rate-Limit-Limit',
        'RateLimit-Limit', 'Retry-After',
    ]
    has_rate_limit = any(h in headers for h in rate_limit_headers)

    if not has_rate_limit:
        findings.append({
            'title': 'State-Changing Endpoint Without Rate Limiting',
            'severity': 'MEDIUM',
            'category': 'race_condition',
            'description': (
                f'The endpoint {parsed_url.geturl()} appears to handle '
                f'state-changing operations but does not include rate-limiting '
                f'headers, making it susceptible to race condition attacks.'
            ),
            'recommendation': (
                'Implement rate limiting on all state-changing endpoints. '
                'Use progressive delays or token buckets for login, '
                'payment, and transaction APIs.'
            ),
            'evidence': f'No rate-limit headers on {path}',
        })


RACE_CONDITION_CHECKS = [check_race_condition]