"""Support ticket models — orgs reporting errors, incidents, or questions."""
from django.conf import settings
from django.db import models


class SupportTicket(models.Model):
    """A support request opened by an organization member."""

    CATEGORY_CHOICES = [
        ('error', 'Error'),
        ('incidencia', 'Incidencia'),
        ('duda', 'Duda'),
        ('otro', 'Otro'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
    ]

    STATUS_CHOICES = [
        ('open', 'Abierto'),
        ('in_progress', 'En progreso'),
        ('closed', 'Cerrado'),
    ]

    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='support_tickets',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='support_tickets',
    )
    created_by_email = models.CharField(max_length=255, blank=True, default='')

    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='duda')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"#{self.id} {self.subject} ({self.status})"


class TicketMessage(models.Model):
    """One message in a ticket's conversation thread."""

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='support_messages',
    )
    author_email = models.CharField(max_length=255, blank=True, default='')
    is_staff = models.BooleanField(default=False)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message on ticket #{self.ticket_id} by {self.author_email}"
