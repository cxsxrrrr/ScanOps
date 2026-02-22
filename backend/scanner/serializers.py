"""Serializers for scanner app."""
from rest_framework import serializers
from .models import Scan, Finding


class FindingSerializer(serializers.ModelSerializer):
    """Serializer for Finding model."""

    class Meta:
        model = Finding
        fields = [
            'id', 'title', 'severity', 'category',
            'description', 'recommendation', 'evidence',
        ]


class ScanListSerializer(serializers.ModelSerializer):
    """Lightweight scan serializer for list views."""
    url = serializers.CharField(source='url_asset.url', read_only=True)
    findings_count = serializers.IntegerField(read_only=True)
    high_count = serializers.IntegerField(read_only=True)
    medium_count = serializers.IntegerField(read_only=True)
    low_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Scan
        fields = [
            'id', 'url', 'status', 'started_at', 'finished_at',
            'findings_count', 'high_count', 'medium_count', 'low_count',
        ]


class ScanDetailSerializer(serializers.ModelSerializer):
    """Detailed scan serializer with findings."""
    url = serializers.CharField(source='url_asset.url', read_only=True)
    findings = FindingSerializer(many=True, read_only=True)
    findings_count = serializers.IntegerField(read_only=True)
    high_count = serializers.IntegerField(read_only=True)
    medium_count = serializers.IntegerField(read_only=True)
    low_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Scan
        fields = [
            'id', 'url', 'status', 'started_at', 'finished_at',
            'error', 'engine_version', 'findings_count',
            'high_count', 'medium_count', 'low_count', 'findings',
        ]


class TriggerScanSerializer(serializers.Serializer):
    """Serializer for triggering a new scan."""
    url_asset_id = serializers.IntegerField()
