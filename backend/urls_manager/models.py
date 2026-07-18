"""URLAsset model for managing audited URLs."""
from django.db import models


class URLAsset(models.Model):
    """A URL registered for security auditing."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ok', 'OK'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='url_assets',
    )
    url = models.URLField(max_length=2048)
    name = models.CharField(
        max_length=120, blank=True, default='',
        help_text='Optional user-facing label (e.g. "Sitio principal"). Falls back to the URL when empty.',
    )
    ownership_challenge_token = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    ownership_failure_reason = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    ownership_verification_method = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    ownership_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )
    last_scan_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    last_scan_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # -id tiebreaker: two rows created within the same timestamp tick
        # (auto_now_add resolution, or a fast test) would otherwise sort in
        # undefined order; id always increases with creation order.
        ordering = ['-created_at', '-id']
        verbose_name = 'URL Asset'
        verbose_name_plural = 'URL Assets'
        unique_together = ['organization', 'url']

    def __str__(self):
        return self.url
