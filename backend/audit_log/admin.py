"""Read-only admin for the API audit trail — evidence must not be editable."""
from django.contrib import admin
from .models import APIRequestLog


@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'method', 'path', 'status_code',
        'ip_address', 'user_email', 'organization_name', 'response_time_ms',
    ]
    list_filter = ['method', 'status_code']
    search_fields = ['ip_address', 'path', 'user_email', 'organization_name']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
