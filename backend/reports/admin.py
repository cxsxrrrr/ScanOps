"""Admin config for reports."""
from django.contrib import admin
from .models import ExecutiveSummary


@admin.register(ExecutiveSummary)
class ExecutiveSummaryAdmin(admin.ModelAdmin):
    list_display = ['scan', 'ai_provider', 'token_usage', 'created_at']
    readonly_fields = ['content', 'token_usage']
