"""Admin configuration for accounts app."""
from django.contrib import admin
from .models import User, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan', 'url_limit', 'created_at']
    search_fields = ['name']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'organization', 'role', 'date_joined']
    list_filter = ['role', 'organization']
    search_fields = ['email', 'first_name', 'last_name']
