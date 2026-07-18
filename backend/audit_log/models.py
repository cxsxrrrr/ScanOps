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


class AdminActionLog(models.Model):
    """Explicit before/after diff for sensitive admin-panel actions.

    APIRequestLog already records *that* an admin endpoint was hit; this
    records *what actually changed* (role, plan, org membership) — the
    generic request log doesn't diff request bodies, so a change here
    would otherwise be unrecoverable from the audit trail alone.
    """

    ACTION_CHOICES = [
        ('role_change', 'Role Change'),
        ('org_change', 'Organization Change'),
        ('plan_change', 'Plan Change'),
        ('block_change', 'Block/Unblock'),
    ]

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='admin_actions_performed',
    )
    performed_by_email = models.CharField(max_length=255, blank=True, default='')

    target_user_id = models.IntegerField(null=True, blank=True)
    target_user_email = models.CharField(max_length=255, blank=True, default='')
    target_org_id = models.IntegerField(null=True, blank=True)
    target_org_name = models.CharField(max_length=255, blank=True, default='')

    before_value = models.CharField(max_length=255, blank=True, default='')
    after_value = models.CharField(max_length=255, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Action Log'
        verbose_name_plural = 'Admin Action Logs'

    def __str__(self):
        target = self.target_user_email or self.target_org_name or '?'
        return f"{self.action}: {target} {self.before_value!r} -> {self.after_value!r}"
