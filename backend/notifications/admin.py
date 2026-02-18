"""Admin config for notifications."""
from django.contrib import admin
from .models import NotificationConfig, EmailLog


@admin.register(NotificationConfig)
class NotificationConfigAdmin(admin.ModelAdmin):
    list_display = ['organization', 'frequency', 'enabled', 'last_sent_at']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['organization', 'email_type', 'status', 'sent_at']
    list_filter = ['email_type', 'status']
