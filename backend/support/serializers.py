"""Serializers for the support app."""
from rest_framework import serializers
from .models import SupportTicket, TicketMessage, TicketAttachment


class TicketAttachmentSerializer(serializers.ModelSerializer):
    # Frontend and backend run on different ports/origins in dev, so a
    # relative /media/... URL would resolve against the wrong host —
    # build an absolute URI instead.
    image = serializers.SerializerMethodField()

    class Meta:
        model = TicketAttachment
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = fields

    def get_image(self, obj):
        request = self.context.get('request')
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class TicketMessageSerializer(serializers.ModelSerializer):
    attachments = TicketAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketMessage
        fields = ['id', 'author_email', 'is_staff', 'body', 'created_at', 'attachments']
        read_only_fields = fields


class SupportTicketListSerializer(serializers.ModelSerializer):
    """Lightweight shape for list views."""

    organization = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'organization', 'subject', 'category', 'priority',
            'status', 'created_by_email', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class SupportTicketDetailSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    organization = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'organization', 'subject', 'category', 'priority',
            'status', 'created_by_email', 'created_at', 'updated_at',
            'closed_at', 'messages',
        ]
        read_only_fields = [
            'id', 'organization', 'created_by_email', 'created_at',
            'updated_at', 'closed_at', 'messages',
        ]


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    body = serializers.CharField(write_only=True)

    class Meta:
        model = SupportTicket
        fields = ['subject', 'category', 'priority', 'body']
