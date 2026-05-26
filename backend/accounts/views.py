"""Views for accounts app."""
import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import User, Organization, Invitation, PLAN_MEMBER_LIMITS
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def team_list(request):
    """List team members in the user's organization."""
    org = request.user.organization
    if not org:
        return Response([], status=200)
    members = org.users.select_related('organization').values(
        'id', 'email', 'first_name', 'last_name', 'role'
    )
    return Response(list(members))


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def invitation_list(request):
    """List or create invitations for the user's organization."""
    org = request.user.organization
    if not org:
        return Response({'detail': 'No organization.'}, status=400)

    if request.method == 'GET':
        invitations = Invitation.objects.filter(
            organization=org, accepted_by__isnull=True
        ).select_related('created_by').values(
            'id', 'token', 'created_at', 'created_by__email'
        )
        result = []
        for inv in invitations:
            result.append({
                'id': inv['id'],
                'token': str(inv['token']),
                'created_at': inv['created_at'],
                'created_by__email': inv['created_by__email'],
                'uses': 0,
                'max_uses': 1,
                'is_valid': True,
            })
        return Response(result)

    # POST: create invitation
    member_count = org.users.count()
    member_limit = PLAN_MEMBER_LIMITS.get(org.plan, 1)
    if member_count >= member_limit:
        return Response(
            {'detail': f'Limite de miembros alcanzado ({member_limit}). Mejora tu plan.'},
            status=400,
        )

    invitation = Invitation.objects.create(
        organization=org, created_by=request.user
    )
    return Response({
        'id': invitation.id,
        'token': str(invitation.token),
        'created_at': invitation.created_at,
        'uses': 0,
        'max_uses': 1,
        'is_valid': True,
    }, status=201)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def revoke_invitation(request, invitation_id):
    """Revoke a pending invitation."""
    org = request.user.organization
    try:
        invitation = Invitation.objects.get(
            id=invitation_id, organization=org, accepted_by__isnull=True
        )
        invitation.delete()
        return Response({'detail': 'Invitacion revocada.'})
    except Invitation.DoesNotExist:
        return Response({'detail': 'Invitacion no encontrada.'}, status=404)


@api_view(['GET'])
@permission_classes([AllowAny])
def invitation_info(request, token):
    """Get invitation info by token (public, no auth needed)."""
    try:
        invitation = Invitation.objects.select_related('organization', 'created_by').get(
            token=token, accepted_by__isnull=True
        )
        org = invitation.organization
        member_limit = PLAN_MEMBER_LIMITS.get(org.plan, 1)
        return Response({
            'id': invitation.id,
            'token': str(invitation.token),
            'organization_name': org.name,
            'organization_plan': org.plan,
            'member_count': org.users.count(),
            'member_limit': member_limit,
            'created_by_email': invitation.created_by.email,
            'created_at': invitation.created_at,
        })
    except Invitation.DoesNotExist:
        return Response(
            {'detail': 'Invitacion invalida o ya aceptada.'}, status=404
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_invitation(request, token):
    """Accept an invitation and join the organization."""
    try:
        invitation = Invitation.objects.select_related('organization').get(
            token=token, accepted_by__isnull=True
        )
    except Invitation.DoesNotExist:
        return Response(
            {'detail': 'Invitacion invalida o ya aceptada.'}, status=404
        )

    org = invitation.organization
    member_count = org.users.count()
    member_limit = PLAN_MEMBER_LIMITS.get(org.plan, 1)
    if member_count >= member_limit:
        return Response(
            {'detail': f'Limite de miembros alcanzado en esta organizacion ({member_limit}).'},
            status=400,
        )

    if request.user.organization and request.user.organization != org:
        return Response(
            {'detail': 'Ya perteneces a otra organizacion. Sal de ella primero.'},
            status=400,
        )

    request.user.organization = org
    if request.data.get('first_name'):
        request.user.first_name = request.data['first_name']
    if request.data.get('last_name'):
        request.user.last_name = request.data['last_name']
    request.user.save(update_fields=['organization', 'first_name', 'last_name'])

    invitation.accepted_by = request.user
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=['accepted_by', 'accepted_at'])

    return Response({
        'detail': f'Te has unido a {org.name}.',
        'organization': OrganizationSerializer(org).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_organization(request):
    """Leave the current organization."""
    user = request.user
    if not user.organization:
        return Response({'detail': 'No perteneces a ninguna organizacion.'}, status=400)

    user.organization = None
    user.save(update_fields=['organization'])
    return Response({'detail': 'Has salido de la organizacion.'})
