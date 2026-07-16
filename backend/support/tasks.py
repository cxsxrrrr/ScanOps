"""Celery tasks for support ticket email notifications.

Reuses the Resend sender and branded HTML wrapper from the notifications
app instead of duplicating email plumbing — support tickets are just
another kind of transactional email.
"""
import logging
from html import escape as _esc
from celery import shared_task

logger = logging.getLogger(__name__)


def _real_emails(emails):
    from accounts.clerk_api import is_placeholder_email
    return [e for e in emails if e and not is_placeholder_email(e)]


@shared_task
def notify_new_ticket(ticket_id):
    """Alert platform admins that a new support ticket needs attention."""
    from .models import SupportTicket
    from accounts.models import User
    from notifications.tasks import _send_with_resend, _build_email_wrapper

    try:
        ticket = SupportTicket.objects.select_related('organization').get(pk=ticket_id)
    except SupportTicket.DoesNotExist:
        return

    admins = _real_emails(User.objects.filter(role='admin').values_list('email', flat=True))
    if not admins:
        return

    body = f"""
    <h2 style="margin-top: 0;">🎫 Nuevo Ticket de Soporte</h2>
    <p><strong>{_esc(ticket.organization.name)}</strong> abrió un ticket de tipo
    <strong>{_esc(ticket.get_category_display())}</strong> (prioridad {_esc(ticket.get_priority_display())}):</p>
    <p style="font-size: 16px; font-weight: 600;">{_esc(ticket.subject)}</p>
    <p class="muted">Ingresa al panel de administración para responder.</p>
    """
    html_content = _build_email_wrapper(subject='Nuevo Ticket de Soporte', body_html=body)

    try:
        _send_with_resend(admins, f'🎫 Nuevo Ticket: {ticket.subject}', html_content)
    except Exception:
        logger.exception(f"Failed to notify admins of new ticket {ticket_id}")


@shared_task
def notify_ticket_reply(message_id):
    """Notify the other side of the conversation that a new reply landed."""
    from .models import TicketMessage
    from accounts.models import User
    from notifications.tasks import _send_with_resend, _build_email_wrapper

    try:
        message = TicketMessage.objects.select_related('ticket__organization').get(pk=message_id)
    except TicketMessage.DoesNotExist:
        return

    ticket = message.ticket

    if message.is_staff:
        recipients = _real_emails([ticket.created_by_email])
    else:
        recipients = _real_emails(User.objects.filter(role='admin').values_list('email', flat=True))

    if not recipients:
        return

    preview = message.body[:280] + ('…' if len(message.body) > 280 else '')
    responder = 'Soporte Vigia' if message.is_staff else ticket.created_by_email

    body = f"""
    <h2 style="margin-top: 0;">💬 Nueva respuesta en tu ticket</h2>
    <p><strong>{_esc(ticket.subject)}</strong> — {_esc(ticket.organization.name)}</p>
    <p style="border-left: 3px solid #2a88ff; padding-left: 12px;">{_esc(preview)}</p>
    <p class="muted">{_esc(responder)} respondió. Ingresa para ver la conversación completa.</p>
    """
    html_content = _build_email_wrapper(subject='Nueva Respuesta de Soporte', body_html=body)

    try:
        _send_with_resend(recipients, f'💬 Respuesta en: {ticket.subject}', html_content)
    except Exception:
        logger.exception(f"Failed to notify reply on ticket {ticket.id} (message {message_id})")
