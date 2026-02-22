"""Serializers for reports app."""
from rest_framework import serializers
from .models import ExecutiveSummary
from scanner.serializers import FindingSerializer


class ExecutiveSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutiveSummary
        fields = ['id', 'ai_provider', 'content', 'token_usage', 'created_at']


class FullReportSerializer(serializers.Serializer):
    """Combined technical + executive report."""
    scan_id = serializers.IntegerField()
    url = serializers.CharField()
    scan_status = serializers.CharField()
    scan_date = serializers.DateTimeField()
    findings = FindingSerializer(many=True)
    executive_summary = ExecutiveSummarySerializer(allow_null=True)
    stats = serializers.DictField()
