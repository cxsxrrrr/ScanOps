"""Admin config for urls_manager."""
from django.contrib import admin
from .models import URLAsset


@admin.register(URLAsset)
class URLAssetAdmin(admin.ModelAdmin):
    list_display = ['url', 'organization', 'last_scan_status', 'last_scan_at', 'created_at']
    list_filter = ['last_scan_status', 'organization']
    search_fields = ['url']
