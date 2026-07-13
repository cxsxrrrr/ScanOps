"""Immutable audit trail of API requests (who called what, from where)."""
from django.conf import settings
from django.db import models


class APIRequestLog(models.Model):
    """One row per inbound API request — evidence trail for audits.

    Snapshots user_email/organization_name alongside the FKs so the record
    stays meaningful even if the user or org is later deleted (SET_NULL).
    """

    ip_address = models.GenericIPAddressField()
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    query_string = models.CharField(max_length=1000, blank=True, default='')
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='api_request_logs',
    )
    user_email = models.CharField(max_length=255, blank=True, default='')

    organization = models.ForeignKey(
        'accounts.Organization',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='api_request_logs',
    )
    organization_name = models.CharField(max_length=255, blank=True, default='')

    user_agent = models.CharField(max_length=500, blank=True, default='')
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['path']),
        ]
        verbose_name = 'API Request Log'
        verbose_name_plural = 'API Request Logs'

    def __str__(self):
        return f"{self.method} {self.path} from {self.ip_address} ({self.status_code})"
