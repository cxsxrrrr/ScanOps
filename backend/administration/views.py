"""Admin panel views for system administration."""
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import User, Organization, PLAN_LIMITS
from accounts.serializers import OrganizationSerializer
from scanner.models import Scan, Finding
from notifications.models import EmailLog
from audit_log.models import APIRequestLog, AdminActionLog


class IsAdminUser(permissions.BasePermission):
    """Only allow admin users."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'admin'


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
    from accounts.clerk_api import backfill_real_emails, is_placeholder_email

    all_users = list(User.objects.select_related('organization').all())
    if any(is_placeholder_email(u.email) for u in all_users):
        backfill_real_emails(all_users)

    users = User.objects.select_related('organization').all().values(
        'id', 'email', 'first_name', 'last_name', 'role', 'is_active',
        'organization_id', 'organization__name', 'organization__plan',
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


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def organization_detail(request, pk):
    """Retrieve, update or delete an organization."""
    try:
        org = Organization.objects.get(pk=pk)
    except Organization.DoesNotExist:
        return Response({'detail': 'Organization not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(OrganizationSerializer(org).data)

    elif request.method == 'PUT':
        from .serializers import AdminOrgUpdateSerializer
        before_plan = org.plan
        serializer = AdminOrgUpdateSerializer(org, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if 'plan' in request.data and org.plan != before_plan:
                AdminActionLog.objects.create(
                    action='plan_change',
                    performed_by=request.user,
                    performed_by_email=request.user.email,
                    target_org_id=org.id,
                    target_org_name=org.name,
                    before_value=before_plan,
                    after_value=org.plan,
                )
            return Response(OrganizationSerializer(org).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        org.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def user_detail(request, pk):
    """Retrieve, update or delete a user."""
    from accounts.serializers import UserSerializer
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(UserSerializer(user).data)

    elif request.method == 'PUT':
        from .serializers import AdminUserUpdateSerializer
        if user.pk == request.user.pk and request.data.get('is_active') is False:
            return Response(
                {'detail': 'No puedes bloquear tu propia cuenta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        before_role = user.role
        before_org_id = user.organization_id
        before_org_name = str(user.organization) if user.organization else ''
        before_active = user.is_active
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if 'role' in request.data and user.role != before_role:
                AdminActionLog.objects.create(
                    action='role_change',
                    performed_by=request.user,
                    performed_by_email=request.user.email,
                    target_user_id=user.id,
                    target_user_email=user.email,
                    before_value=before_role,
                    after_value=user.role,
                )
            if 'organization' in request.data and user.organization_id != before_org_id:
                AdminActionLog.objects.create(
                    action='org_change',
                    performed_by=request.user,
                    performed_by_email=request.user.email,
                    target_user_id=user.id,
                    target_user_email=user.email,
                    before_value=before_org_name,
                    after_value=str(user.organization) if user.organization else '',
                )
            if 'is_active' in request.data and user.is_active != before_active:
                AdminActionLog.objects.create(
                    action='block_change',
                    performed_by=request.user,
                    performed_by_email=request.user.email,
                    target_user_id=user.id,
                    target_user_email=user.email,
                    before_value='active' if before_active else 'blocked',
                    after_value='active' if user.is_active else 'blocked',
                )
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def analytics_organizations(request):
    """Get global ranking and metrics for all organizations."""
    from django.db.models import Count, Q, Max, Sum
    
    orgs = Organization.objects.annotate(
        total_urls=Count('url_assets', distinct=True),
        total_users=Count('users', distinct=True),
        total_scans=Count('url_assets__scans', distinct=True),
        last_scan_date=Max('url_assets__scans__started_at'),
        critical_findings=Count('url_assets__scans__findings', filter=Q(url_assets__scans__findings__severity='CRITICAL'), distinct=True),
        high_findings=Count('url_assets__scans__findings', filter=Q(url_assets__scans__findings__severity='HIGH'), distinct=True),
        medium_findings=Count('url_assets__scans__findings', filter=Q(url_assets__scans__findings__severity='MEDIUM'), distinct=True),
    ).order_by('-critical_findings', '-high_findings')

    data = []
    for org in orgs:
        risk_score = org.critical_findings * 10 + org.high_findings * 5 + org.medium_findings * 2
        
        status = 'Sano'
        if risk_score > 50 or org.critical_findings > 0:
            status = 'Crítico'
        elif risk_score > 20 or org.high_findings > 0:
            status = 'Advertencia'

        data.append({
            'id': org.id,
            'name': org.name,
            'plan': org.plan,
            'total_urls': org.total_urls,
            'total_users': org.total_users,
            'total_scans': org.total_scans,
            'last_scan_date': org.last_scan_date,
            'critical_findings': org.critical_findings,
            'high_findings': org.high_findings,
            'medium_findings': org.medium_findings,
            'risk_score': risk_score,
            'status': status
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def analytics_organization_detail(request, pk):
    """Get detailed analytics for a specific organization."""
    try:
        org = Organization.objects.get(pk=pk)
    except Organization.DoesNotExist:
        return Response({'detail': 'Organization not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Users — backfill real Clerk emails in place of the placeholder
    # {clerk_id}@clerk.user before serializing (same as user_list).
    from accounts.clerk_api import backfill_real_emails, is_placeholder_email
    org_users = list(org.users.all())
    if any(is_placeholder_email(u.email) for u in org_users):
        backfill_real_emails(org_users)
    users_data = org.users.values('id', 'email', 'role', 'last_login')

    # URLs and their last scan status
    urls = org.url_assets.all()
    urls_data = []
    
    scan_history = []
    total_findings = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}

    for url in urls:
        last_scan = url.scans.order_by('-started_at').first()
        
        url_info = {
            'id': url.id,
            'url': url.url,
            'status': url.last_scan_status,
            'last_scan_status': last_scan.status if last_scan else None,
            'last_scan_date': last_scan.started_at if last_scan else None,
            'critical': last_scan.critical_count if last_scan else 0,
            'high': last_scan.high_count if last_scan else 0,
            'medium': last_scan.medium_count if last_scan else 0,
        }
        urls_data.append(url_info)
        
        # Accumulate finding totals from the LAST scan of each URL to avoid counting historical duplicates
        if last_scan:
            total_findings['CRITICAL'] += url_info['critical']
            total_findings['HIGH'] += url_info['high']
            total_findings['MEDIUM'] += url_info['medium']
            total_findings['LOW'] += last_scan.low_count
            
        # Collect recent scan history for charts (limit to last 10 per URL)
        for scan in url.scans.order_by('-started_at')[:10]:
            scan_history.append({
                'id': scan.id,
                'url': url.url,
                'started_at': scan.started_at,
                'status': scan.status,
                'findings_count': scan.findings_count
            })

    # Sort scan history chronologically for chart
    scan_history.sort(key=lambda x: x['started_at'])

    return Response({
        'organization': {
            'id': org.id,
            'name': org.name,
            'plan': org.plan,
        },
        'total_findings': total_findings,
        'users': list(users_data),
        'urls': urls_data,
        'recent_scans': scan_history[-50:], # limit global chart to 50
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def audit_log_list(request):
    """List API request audit logs (admin only) — evidence trail, paginated."""
    logs = APIRequestLog.objects.all()

    ip = request.query_params.get('ip')
    if ip:
        logs = logs.filter(ip_address__icontains=ip)

    method = request.query_params.get('method')
    if method:
        logs = logs.filter(method=method.upper())

    search = request.query_params.get('search')
    if search:
        logs = logs.filter(
            Q(path__icontains=search)
            | Q(user_email__icontains=search)
            | Q(organization_name__icontains=search)
        )

    try:
        page = max(int(request.query_params.get('page', 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max(int(request.query_params.get('page_size', 50)), 1), 200)
    except (TypeError, ValueError):
        page_size = 50

    total = logs.count()
    start = (page - 1) * page_size
    results = logs[start:start + page_size].values(
        'id', 'created_at', 'method', 'path', 'query_string', 'status_code',
        'ip_address', 'user_id', 'user_email', 'organization_id',
        'organization_name', 'user_agent', 'response_time_ms',
    )

    return Response({
        'count': total,
        'page': page,
        'page_size': page_size,
        'results': list(results),
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_action_log_list(request):
    """List admin action audit logs (who changed what) — paginated.

    Distinct from audit_log_list (raw HTTP request trail): this is the
    explicit before/after diff for sensitive actions — role changes,
    org moves, plan changes, block/unblock — so an admin can answer
    "who did this and what did it change" without querying the DB.
    """
    logs = AdminActionLog.objects.all()

    action = request.query_params.get('action')
    if action:
        logs = logs.filter(action=action)

    search = request.query_params.get('search')
    if search:
        logs = logs.filter(
            Q(performed_by_email__icontains=search)
            | Q(target_user_email__icontains=search)
            | Q(target_org_name__icontains=search)
        )

    try:
        page = max(int(request.query_params.get('page', 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max(int(request.query_params.get('page_size', 50)), 1), 200)
    except (TypeError, ValueError):
        page_size = 50

    total = logs.count()
    start = (page - 1) * page_size
    results = logs[start:start + page_size].values(
        'id', 'created_at', 'action', 'performed_by_email',
        'target_user_id', 'target_user_email', 'target_org_id',
        'target_org_name', 'before_value', 'after_value',
    )

    return Response({
        'count': total,
        'page': page,
        'page_size': page_size,
        'results': list(results),
    })
