"""Views for accounts app."""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import User, Organization
from .serializers import UserSerializer, ProfileSerializer, OrganizationSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """
    Verify Clerk token and return user data.
    The ClerkJWTAuthentication backend auto-creates users,
    so if we reach here, the user is already authenticated.
    """
    serializer = ProfileSerializer(request.user)
    return Response({
        'user': serializer.data,
        'is_new': request.user.organization is None,
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get or update user profile."""
    if request.method == 'GET':
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    serializer = UserSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(ProfileSerializer(request.user).data)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def organization_detail(request):
    """Get or update user's organization."""
    if not request.user.organization:
        if request.method == 'GET':
            return Response({'detail': 'No organization set.'}, status=404)
        # Create org on PATCH if none exists
        name = request.data.get('name')
        if not name:
            return Response(
                {'name': ['Organization name is required.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        org = Organization.objects.create(name=name, plan='free', url_limit=1)
        request.user.organization = org
        request.user.save()
        return Response(OrganizationSerializer(org).data, status=status.HTTP_201_CREATED)

    if request.method == 'GET':
        serializer = OrganizationSerializer(request.user.organization)
        return Response(serializer.data)

    serializer = OrganizationSerializer(
        request.user.organization, data=request.data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_terms(request):
    """Record that the user has accepted the terms and conditions."""
    user = request.user
    if user.has_accepted_terms:
        return Response({
            'detail': 'Terms already accepted.',
            'accepted_terms_at': user.accepted_terms_at,
        })

    user.accept_terms()
    return Response({
        'detail': 'Terms accepted successfully.',
        'accepted_terms_at': user.accepted_terms_at,
    }, status=status.HTTP_200_OK)
