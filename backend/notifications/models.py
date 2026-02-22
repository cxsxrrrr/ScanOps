"""Notification models."""
from django.db import models


class NotificationConfig(models.Model):
    """Email notification preferences per organization."""

    FREQUENCY_CHOICES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
    ]

    organization = models.OneToOneField(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='notification_config',
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='weekly')
    enabled = models.BooleanField(default=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Config for {self.organization.name} ({self.frequency})"


class EmailLog(models.Model):
    """Log of sent emails."""

    TYPE_CHOICES = [
        ('scheduled', 'Scheduled Report'),
        ('alert', 'High Severity Alert'),
    ]

    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='email_logs',
    )
    email_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    error = models.TextField(blank=True, default='')
    recipients = models.TextField(default='')

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.email_type} to {self.organization.name} ({self.status})"
