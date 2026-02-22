"""Admin config for scanner."""
from django.contrib import admin
from .models import Scan, Finding


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ['id', 'url_asset', 'status', 'started_at', 'finished_at']
    list_filter = ['status']
    readonly_fields = ['started_at']


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'category', 'scan']
    list_filter = ['severity', 'category']
    search_fields = ['title', 'description']
