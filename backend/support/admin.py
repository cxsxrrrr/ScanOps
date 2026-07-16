from django.contrib import admin
from .models import SupportTicket, TicketMessage


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ['author_email', 'is_staff', 'body', 'created_at']


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'organization', 'category', 'priority', 'status', 'created_at']
    list_filter = ['status', 'category', 'priority']
    search_fields = ['subject', 'created_by_email', 'organization__name']
    inlines = [TicketMessageInline]
