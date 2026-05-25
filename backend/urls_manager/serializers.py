"""Serializers for urls_manager app."""
from rest_framework import serializers
from urllib.parse import urlparse
from .models import URLAsset


PLAN_NAMES = {
    'free': 'Free',
    'pro': 'Pro',
    'ultimate': 'Ultimate',
}


class URLAssetSerializer(serializers.ModelSerializer):
    """Serializer for URLAsset model."""

    class Meta:
        model = URLAsset
        fields = ['id', 'url', 'last_scan_status', 'last_scan_at', 'created_at']
        read_only_fields = ['id', 'last_scan_status', 'last_scan_at', 'created_at']

    def validate_url(self, value):
        """Validate URL format and protocol."""
        parsed = urlparse(value)

        if parsed.scheme not in ('http', 'https'):
            raise serializers.ValidationError(
                'URL must use http or https protocol.'
            )

        if not parsed.netloc or '.' not in parsed.netloc:
            raise serializers.ValidationError(
                'URL must have a valid domain name.'
            )

        if ' ' in value:
            raise serializers.ValidationError('URL must not contain spaces.')

        return value

    def validate(self, attrs):
        """Check URL limit for organization based on current plan."""
        request = self.context.get('request')
        if request and not self.instance:
            org = request.user.organization
            if org:
                current_count = URLAsset.objects.filter(organization=org).count()
                if current_count >= org.url_limit:
                    plan_name = PLAN_NAMES.get(org.plan, org.plan)
                    raise serializers.ValidationError(
                        f'Has alcanzado el límite de URLs de tu plan {plan_name} '
                        f'({org.url_limit} URL{"s" if org.url_limit > 1 else ""}). '
                        f'Actualiza tu plan para agregar más URLs.'
                    )
        return attrs
