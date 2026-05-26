"""
User and Organization models for Vigia.
"""
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


# Plan configuration: plan_key -> url_limit
PLAN_LIMITS = {
    'free': 1,
    'pro': 5,
    'ultimate': 10,
}

PLAN_MEMBER_LIMITS = {
    'free': 1,
    'pro': 5,
    'ultimate': 15,
}


class Organization(models.Model):
    """Organization that groups users and URL assets."""

    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('ultimate', 'Ultimate'),
    ]

    name = models.CharField(max_length=200)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    url_limit = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_plan_display()})"

    @property
    def plan_display_name(self):
        return self.get_plan_display()

    @property
    def plan_url_limit(self):
        """Return the URL limit for the current plan."""
        return PLAN_LIMITS.get(self.plan, 1)

    @property
    def member_limit(self):
        """Return the member limit for the current plan."""
        return PLAN_MEMBER_LIMITS.get(self.plan, 1)

    def sync_url_limit(self):
        """Sync url_limit field to match the current plan."""
        self.url_limit = self.plan_url_limit
        self.save(update_fields=['url_limit'])

    def set_plan(self, new_plan):
        """Change the organization's plan and update the URL limit."""
        if new_plan not in PLAN_LIMITS:
            raise ValueError(f"Invalid plan: {new_plan}")
        self.plan = new_plan
        self.url_limit = PLAN_LIMITS[new_plan]
        self.save(update_fields=['plan', 'url_limit', 'updated_at'])


class User(AbstractUser):
    """Custom user linked to Clerk Auth and an Organization."""

    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]

    clerk_user_id = models.CharField(max_length=200, unique=True, null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    accepted_terms_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.email} ({self.organization})"

    @property
    def is_admin_user(self):
        return self.role == 'admin'

    @property
    def has_accepted_terms(self):
        return self.accepted_terms_at is not None

    def accept_terms(self):
        """Record that the user has accepted the terms and conditions."""
        self.accepted_terms_at = timezone.now()
        self.save(update_fields=['accepted_terms_at'])


class Invitation(models.Model):
    """Team invitation with unique token."""
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='invitations'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_invitations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_invitations'
    )
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation {self.token} → {self.organization.name}"

    @property
    def is_active(self):
        return self.accepted_by is None
