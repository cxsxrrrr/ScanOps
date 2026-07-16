"""Views for the support app.

Organization members manage their own tickets; the platform admin
(role == 'admin') sees and responds to every organization's tickets
through the same endpoints — filtered by role instead of duplicating
list/detail views for the admin panel.
"""
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import SupportTicket, TicketMessage
from .serializers import (
    SupportTicketListSerializer,
    SupportTicketDetailSerializer,
    SupportTicketCreateSerializer,
    TicketMessageSerializer,
)


def _is_platform_admin(user):
    return user.role == 'admin'


def _get_ticket_for_user(user, pk):
    """Fetch a ticket the user is allowed to see, or None."""
    try:
        ticket = SupportTicket.objects.get(pk=pk)
    except SupportTicket.DoesNotExist:
        return None
    if _is_platform_admin(user) or ticket.organization_id == user.organization_id:
        return ticket
    return None


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def ticket_list_create(request):
    if request.method == 'GET':
        if _is_platform_admin(request.user):
            tickets = SupportTicket.objects.all()
        else:
            if not request.user.organization_id:
                return Response({'detail': 'No organization.'}, status=400)
            tickets = SupportTicket.objects.filter(organization_id=request.user.organization_id)

        status_filter = request.query_params.get('status')
        if status_filter:
            tickets = tickets.filter(status=status_filter)

        return Response(SupportTicketListSerializer(tickets, many=True).data)

    # POST — open a new ticket
    if not request.user.organization_id:
        return Response({'detail': 'No organization.'}, status=400)

    serializer = SupportTicketCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    ticket = SupportTicket.objects.create(
        organization_id=request.user.organization_id,
        created_by=request.user,
        created_by_email=request.user.email,
        subject=serializer.validated_data['subject'],
        category=serializer.validated_data.get('category', 'duda'),
        priority=serializer.validated_data.get('priority', 'medium'),
    )
    TicketMessage.objects.create(
        ticket=ticket,
        author=request.user,
        author_email=request.user.email,
        is_staff=False,
        body=serializer.validated_data['body'],
    )
    return Response(SupportTicketDetailSerializer(ticket).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def ticket_detail(request, pk):
    ticket = _get_ticket_for_user(request.user, pk)
    if ticket is None:
        return Response({'detail': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(SupportTicketDetailSerializer(ticket).data)

    # PATCH — only the platform admin can change status/priority
    if not _is_platform_admin(request.user):
        return Response({'detail': 'Solo el administrador puede actualizar el estado.'}, status=403)

    allowed_fields = {'status', 'priority'}
    updates = {k: v for k, v in request.data.items() if k in allowed_fields}
    for field, value in updates.items():
        setattr(ticket, field, value)
    if updates.get('status') == 'closed' and not ticket.closed_at:
        from django.utils import timezone
        ticket.closed_at = timezone.now()
    elif updates.get('status') and updates['status'] != 'closed':
        ticket.closed_at = None
    ticket.save()

    return Response(SupportTicketDetailSerializer(ticket).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ticket_add_message(request, pk):
    ticket = _get_ticket_for_user(request.user, pk)
    if ticket is None:
        return Response({'detail': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)

    body = request.data.get('body', '').strip()
    if not body:
        return Response({'detail': 'El mensaje no puede estar vacío.'}, status=400)

    is_staff = _is_platform_admin(request.user)
    message = TicketMessage.objects.create(
        ticket=ticket,
        author=request.user,
        author_email=request.user.email,
        is_staff=is_staff,
        body=body,
    )

    # Any staff reply moves the ticket into in_progress — whether it was
    # freshly open or being reopened from closed.
    if is_staff and ticket.status != 'in_progress':
        ticket.status = 'in_progress'
        ticket.closed_at = None
        ticket.save(update_fields=['status', 'closed_at'])
    elif not is_staff and ticket.status == 'open':
        ticket.status = 'in_progress'
        ticket.save(update_fields=['status'])

    return Response(TicketMessageSerializer(message).data, status=status.HTTP_201_CREATED)
