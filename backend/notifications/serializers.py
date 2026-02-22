"""Serializers for notifications."""
from rest_framework import serializers
from .models import NotificationConfig, EmailLog


class NotificationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationConfig
        fields = ['id', 'frequency', 'enabled', 'last_sent_at']
        read_only_fields = ['id', 'last_sent_at']


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = ['id', 'email_type', 'sent_at', 'status', 'error']
