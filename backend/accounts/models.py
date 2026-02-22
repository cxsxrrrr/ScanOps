"""
User and Organization models for Auditoría Web.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    """Organization that groups users and URL assets."""

    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
    ]

    name = models.CharField(max_length=200)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    url_limit = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


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

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.email} ({self.organization})"

    @property
    def is_admin_user(self):
        return self.role == 'admin'
