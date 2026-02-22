"""Views for notifications app."""
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import NotificationConfig, EmailLog
from .serializers import NotificationConfigSerializer, EmailLogSerializer


@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def notification_config(request):
    """Get or update notification configuration."""
    if not request.user.organization:
        return Response({'detail': 'No organization.'}, status=400)

    config, created = NotificationConfig.objects.get_or_create(
        organization=request.user.organization,
    )

    if request.method == 'GET':
        serializer = NotificationConfigSerializer(config)
        return Response(serializer.data)

    serializer = NotificationConfigSerializer(config, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def email_logs(request):
    """Get email log history."""
    if not request.user.organization:
        return Response({'detail': 'No organization.'}, status=400)

    logs = EmailLog.objects.filter(organization=request.user.organization)[:50]
    serializer = EmailLogSerializer(logs, many=True)
    return Response(serializer.data)
