"""Views for urls_manager app."""
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import URLAsset
from .serializers import URLAssetSerializer


class URLAssetViewSet(viewsets.ModelViewSet):
    """CRUD operations for URL assets."""
    serializer_class = URLAssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter URLs by user's organization."""
        if not self.request.user.organization:
            return URLAsset.objects.none()
        return URLAsset.objects.filter(
            organization=self.request.user.organization
        )

    def perform_create(self, serializer):
        """Assign the URL to the user's organization."""
        if not self.request.user.organization:
            raise PermissionDenied(
                'You must belong to an organization to register URLs.'
            )
        serializer.save(organization=self.request.user.organization)
