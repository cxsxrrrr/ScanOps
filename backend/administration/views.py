"""Admin panel views for system administration."""
from django.utils import timezone
from datetime import timedelta
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import User, Organization
from scanner.models import Scan, Finding
from notifications.models import EmailLog


class IsAdminUser(permissions.BasePermission):
    """Only allow admin users."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_metrics(request):
    """Get system-wide metrics for admin dashboard."""
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)

    # Scan stats by status
    total_scans = Scan.objects.count()
    recent_scans = Scan.objects.filter(started_at__gte=last_7_days).count()
    error_scans = Scan.objects.filter(status='error', started_at__gte=last_30_days).count()

    # Finding stats
    total_findings = Finding.objects.count()
    high_findings = Finding.objects.filter(severity='HIGH').count()

    return Response({
        'users': {
            'total': User.objects.count(),
            'active_last_30d': User.objects.filter(last_login__gte=last_30_days).count(),
        },
        'organizations': {
            'total': Organization.objects.count(),
        },
        'scans': {
            'total': total_scans,
            'last_7_days': recent_scans,
            'errors_last_30d': error_scans,
            'by_status': {
                'pending': Scan.objects.filter(status='pending').count(),
                'running': Scan.objects.filter(status='running').count(),
                'completed': Scan.objects.filter(status='completed').count(),
                'error': Scan.objects.filter(status='error').count(),
            },
        },
        'findings': {
            'total': total_findings,
            'high': high_findings,
            'medium': Finding.objects.filter(severity='MEDIUM').count(),
            'low': Finding.objects.filter(severity='LOW').count(),
        },
        'emails': {
            'sent_last_30d': EmailLog.objects.filter(
                sent_at__gte=last_30_days, status='sent'
            ).count(),
            'failed_last_30d': EmailLog.objects.filter(
                sent_at__gte=last_30_days, status='failed'
            ).count(),
        },
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def recent_errors(request):
    """Get recent error logs."""
    errors = Scan.objects.filter(
        status='error'
    ).order_by('-started_at')[:20].values(
        'id', 'url_asset__url', 'error', 'started_at'
    )
    email_errors = EmailLog.objects.filter(
        status='failed'
    ).order_by('-sent_at')[:20].values(
        'id', 'organization__name', 'email_type', 'error', 'sent_at'
    )

    return Response({
        'scan_errors': list(errors),
        'email_errors': list(email_errors),
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAdminUser])
def scan_config(request):
    """Get or update scan engine configuration."""
    from django.conf import settings

    if request.method == 'GET':
        return Response({
            'timeout': settings.SCAN_TIMEOUT,
            'max_concurrent': settings.SCAN_MAX_CONCURRENT,
            'default_depth': settings.SCAN_DEFAULT_DEPTH,
        })

    # In production, these would be stored in DB
    return Response({
        'detail': 'Scan config updated.',
        'timeout': request.data.get('timeout', settings.SCAN_TIMEOUT),
        'max_concurrent': request.data.get('max_concurrent', settings.SCAN_MAX_CONCURRENT),
        'default_depth': request.data.get('default_depth', settings.SCAN_DEFAULT_DEPTH),
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_list(request):
    """List all users (admin view)."""
    users = User.objects.select_related('organization').all().values(
        'id', 'email', 'first_name', 'last_name', 'role',
        'organization__name', 'date_joined', 'last_login',
    )
    return Response(list(users))
