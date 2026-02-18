"""Executive Summary model for reports."""
from django.db import models


class ExecutiveSummary(models.Model):
    """AI-generated executive summary for a scan."""

    PROVIDER_CHOICES = [
        ('gemini', 'Google Gemini'),
        ('openai', 'OpenAI'),
    ]

    scan = models.OneToOneField(
        'scanner.Scan',
        on_delete=models.CASCADE,
        related_name='executive_summary',
    )
    ai_provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='gemini')
    content = models.TextField()
    token_usage = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Executive Summaries'

    def __str__(self):
        return f"Summary for Scan #{self.scan_id}"
