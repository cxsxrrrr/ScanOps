"""Views for scanner app."""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Scan, Finding
from .serializers import (
    ScanListSerializer, ScanDetailSerializer,
    FindingSerializer, TriggerScanSerializer,
)
from .tasks import run_scan


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trigger_scan(request):
    """Trigger a new scan for a URL asset."""
    serializer = TriggerScanSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    url_asset_id = serializer.validated_data['url_asset_id']

    # Verify URL belongs to user's organization
    from urls_manager.models import URLAsset
    try:
        url_asset = URLAsset.objects.get(
            pk=url_asset_id,
            organization=request.user.organization,
        )
    except URLAsset.DoesNotExist:
        return Response(
            {'detail': 'URL not found or not in your organization.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Check for running scans
    if Scan.objects.filter(url_asset=url_asset, status__in=['pending', 'running']).exists():
        return Response(
            {'detail': 'A scan is already in progress for this URL.'},
            status=status.HTTP_409_CONFLICT,
        )

    # Create scan record and dispatch task
    scan = Scan.objects.create(
        url_asset=url_asset,
        created_by=request.user,
    )
    
    from celery import chain
    from .tasks import process_scan_results
    chain(run_scan.s(scan.pk), process_scan_results.s()).delay()

    return Response(
        ScanListSerializer(scan).data,
        status=status.HTTP_202_ACCEPTED,
    )


class ScanViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for scans."""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['url_asset', 'status']

    def get_queryset(self):
        if not self.request.user.organization:
            return Scan.objects.none()
        return Scan.objects.filter(
            url_asset__organization=self.request.user.organization
        ).select_related('url_asset')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ScanDetailSerializer
        return ScanListSerializer

    @action(detail=True, methods=['get'])
    def findings(self, request, pk=None):
        """Get findings for a specific scan."""
        scan = self.get_object()
        severity = request.query_params.get('severity')
        findings = scan.findings.all()
        if severity:
            findings = findings.filter(severity=severity.upper())
        serializer = FindingSerializer(findings, many=True)
        return Response(serializer.data)
