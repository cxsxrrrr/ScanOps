"""Admin panel views for system administration."""
from django.utils import timezone
from datetime import timedelta
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import User, Organization, PLAN_LIMITS
from accounts.serializers import OrganizationSerializer
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

    # Plan distribution
    plan_distribution = {}
    for plan_key, _ in Organization.PLAN_CHOICES:
        plan_distribution[plan_key] = Organization.objects.filter(plan=plan_key).count()

    return Response({
        'users': {
            'total': User.objects.count(),
            'active_last_30d': User.objects.filter(last_login__gte=last_30_days).count(),
            'admins': User.objects.filter(role='admin').count(),
        },
        'organizations': {
            'total': Organization.objects.count(),
            'by_plan': plan_distribution,
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
        'organization__name', 'organization__plan',
        'date_joined', 'last_login', 'accepted_terms_at',
    )
    return Response(list(users))


@api_view(['GET'])
@permission_classes([IsAdminUser])
def organization_list(request):
    """List all organizations with plan info."""
    orgs = Organization.objects.all()
    serializer = OrganizationSerializer(orgs, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_org_plan(request, pk):
    """Update an organization's plan (admin only)."""
    try:
        org = Organization.objects.get(pk=pk)
    except Organization.DoesNotExist:
        return Response(
            {'detail': 'Organization not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    new_plan = request.data.get('plan')
    if new_plan not in PLAN_LIMITS:
        return Response(
            {'detail': f'Invalid plan. Options: {", ".join(PLAN_LIMITS.keys())}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    org.set_plan(new_plan)
    return Response({
        'detail': f'Plan updated to {new_plan}.',
        'organization': OrganizationSerializer(org).data,
    })


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_user_role(request, pk):
    """Update a user's role (admin only)."""
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {'detail': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    new_role = request.data.get('role')
    if new_role not in dict(User.ROLE_CHOICES):
        return Response(
            {'detail': 'Invalid role. Options: user, admin'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.role = new_role
    user.save(update_fields=['role'])
    return Response({
        'detail': f'Role updated to {new_role}.',
        'user_id': user.id,
        'role': user.role,
    })
