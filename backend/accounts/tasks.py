"""Celery tasks for the accounts app."""
from celery import shared_task
from django.utils import timezone

from .models import Invitation


@shared_task
def cleanup_expired_invitations():
    """Delete expired, never-accepted invitations (scheduled daily via Celery beat)."""
    deleted, _ = Invitation.objects.filter(
        accepted_by__isnull=True,
        expires_at__lt=timezone.now(),
    ).delete()
    return deleted
