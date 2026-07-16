"""Scan and Finding models for the scanner app."""
from django.db import models


class Scan(models.Model):
    """An individual security scan execution."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    ]

    url_asset = models.ForeignKey(
        'urls_manager.URLAsset',
        on_delete=models.CASCADE,
        related_name='scans',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error = models.TextField(blank=True, default='')
    engine_version = models.CharField(max_length=50, default='1.0.0')
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='scans',
    )

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Scan #{self.pk} - {self.url_asset.url} ({self.status})"

    @property
    def findings_count(self):
        return self.findings.count()

    @property
    def critical_count(self):
        return self.findings.filter(severity='CRITICAL').count()

    @property
    def high_count(self):
        return self.findings.filter(severity='HIGH').count()

    @property
    def medium_count(self):
        return self.findings.filter(severity='MEDIUM').count()

    @property
    def low_count(self):
        return self.findings.filter(severity='LOW').count()


class Finding(models.Model):
    """A security finding from a scan."""

    SEVERITY_CHOICES = [
        ('CRITICAL', 'Crítico'),
        ('HIGH', 'Alto'),
        ('MEDIUM', 'Medio'),
        ('LOW', 'Bajo'),
        ('INFO', 'Informativo'),
    ]

    CATEGORY_CHOICES = [
        # Existing categories
        ('headers', 'HTTP Headers'),
        ('ssl', 'SSL/TLS'),
        ('cookies', 'Cookies'),
        ('info_disclosure', 'Information Disclosure'),
        ('dns', 'DNS Configuration'),
        ('mixed_content', 'Mixed Content'),
        ('redirect', 'Open Redirect'),
        # Injection
        ('sqli', 'SQL Injection'),
        ('xss', 'Cross-Site Scripting'),
        ('nosqli', 'NoSQL Injection'),
        ('cmd_injection', 'OS Command Injection'),
        ('xxe', 'XXE Injection'),
        ('ssti', 'Server-Side Template Injection'),
        # Access control
        ('csrf', 'CSRF'),
        ('clickjacking', 'Clickjacking'),
        ('cors', 'CORS Misconfiguration'),
        ('ssrf', 'SSRF'),
        ('path_traversal', 'Path Traversal'),
        ('access_control', 'Broken Access Control'),
        ('bypass_403', '403 Bypass'),
        ('host_header', 'HTTP Host Header'),
        # Authentication
        ('auth', 'Authentication'),
        ('jwt', 'JWT Vulnerabilities'),
        ('oauth', 'OAuth'),
        ('websockets', 'WebSockets'),
        # Application security
        ('http_smuggling', 'HTTP Request Smuggling'),
        ('cache_poisoning', 'Web Cache Poisoning'),
        ('deserialization', 'Insecure Deserialization'),
        ('file_upload', 'File Upload Vulnerabilities'),
        ('prototype_pollution', 'Prototype Pollution'),
        ('graphql', 'GraphQL'),
        ('race_condition', 'Race Conditions'),
        ('api', 'API Security'),
        ('subdomain_takeover', 'Subdomain Takeover'),
        ('subdomain', 'Subdomain Discovery'),
        ('wordpress', 'WordPress'),
        ('technology', 'Technology'),
        ('cache_deception', 'Web Cache Deception'),
        ('llm', 'Web LLM Attacks'),
        ('http_methods', 'HTTP Methods'),
        ('crlf_injection', 'CRLF Injection'),
        ('sri', 'Subresource Integrity'),
        ('postmessage', 'postMessage Security'),
        ('other', 'Other'),
    ]

    scan = models.ForeignKey(
        Scan, on_delete=models.CASCADE, related_name='findings'
    )
    title = models.CharField(max_length=300)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField()
    recommendation = models.TextField(blank=True, default='')
    evidence = models.TextField(blank=True, default='')

    class Meta:
        ordering = [
            models.Case(
                models.When(severity='CRITICAL', then=0),
                models.When(severity='HIGH', then=1),
                models.When(severity='MEDIUM', then=2),
                models.When(severity='LOW', then=3),
                models.When(severity='INFO', then=4),
                default=5,
                output_field=models.IntegerField(),
            )
        ]

    def __str__(self):
        return f"[{self.severity}] {self.title}"
