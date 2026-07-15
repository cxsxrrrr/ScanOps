"""Read-only admin for the API audit trail — evidence must not be editable."""
from django.contrib import admin
from .models import APIRequestLog, AdminActionLog


class ReadOnlyAuditAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(APIRequestLog)
class APIRequestLogAdmin(ReadOnlyAuditAdmin):
    list_display = [
        'created_at', 'method', 'path', 'status_code',
        'ip_address', 'user_email', 'organization_name', 'response_time_ms',
    ]
    list_filter = ['method', 'status_code']
    search_fields = ['ip_address', 'path', 'user_email', 'organization_name']
    date_hierarchy = 'created_at'


@admin.register(AdminActionLog)
class AdminActionLogAdmin(ReadOnlyAuditAdmin):
    list_display = [
        'created_at', 'action', 'performed_by_email',
        'target_user_email', 'target_org_name', 'before_value', 'after_value',
    ]
    list_filter = ['action']
    search_fields = ['performed_by_email', 'target_user_email', 'target_org_name']
    date_hierarchy = 'created_at'
