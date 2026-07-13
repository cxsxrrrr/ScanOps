"""Middleware that records an APIRequestLog row for every /api/ request.

Placed last in MIDDLEWARE so get_response() has already run the view by the
time we read request.user — DRF authentication happens inside the view/
permission layer, not in Django middleware, and DRF's Request.user getter
writes back onto the underlying HttpRequest, so it's readable here.
"""
import logging
import time

logger = logging.getLogger(__name__)

# Never audit-log requests to the audit endpoint itself or infra noise.
EXCLUDED_PREFIXES = ('/api/schema', '/api/docs', '/api/redoc')


def _get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        # First entry is the original client; proxies append their own after it.
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or '0.0.0.0'


class APIRequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)

        if not request.path.startswith('/api/'):
            return response
        if request.path.startswith(EXCLUDED_PREFIXES):
            return response

        try:
            self._log(request, response, start)
        except Exception:
            # Auditing must never break the actual request/response cycle.
            logger.exception("Failed to write APIRequestLog")

        return response

    def _log(self, request, response, start):
        from .models import APIRequestLog

        user = getattr(request, 'user', None)
        is_authenticated = bool(user and getattr(user, 'is_authenticated', False))

        APIRequestLog.objects.create(
            ip_address=_get_client_ip(request),
            method=request.method,
            path=request.path[:500],
            query_string=request.META.get('QUERY_STRING', '')[:1000],
            status_code=getattr(response, 'status_code', None),
            user=user if is_authenticated else None,
            user_email=getattr(user, 'email', '') if is_authenticated else '',
            organization=getattr(user, 'organization', None) if is_authenticated else None,
            organization_name=(
                getattr(getattr(user, 'organization', None), 'name', '') if is_authenticated else ''
            ),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            response_time_ms=int((time.monotonic() - start) * 1000),
        )
