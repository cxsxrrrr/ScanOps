"""Serializers for accounts app."""
from rest_framework import serializers
from .models import User, Organization, PLAN_LIMITS


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""
    user_count = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    member_limit = serializers.ReadOnlyField()
    plan_url_limit = serializers.SerializerMethodField()
    urls_used = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'plan', 'url_limit', 'plan_url_limit',
            'urls_used', 'user_count', 'member_count', 'member_limit', 'created_at',
        ]
        read_only_fields = [
            'id', 'plan', 'url_limit', 'plan_url_limit',
            'urls_used', 'user_count', 'member_count', 'member_limit', 'created_at',
        ]

    def get_user_count(self, obj):
        return obj.users.count()

    def get_member_count(self, obj):
        return obj.users.count()

    def get_plan_url_limit(self, obj):
        return PLAN_LIMITS.get(obj.plan, 1)

    def get_urls_used(self, obj):
        return obj.url_assets.count()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    organization = OrganizationSerializer(read_only=True)
    organization_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'organization', 'organization_name', 'date_joined',
            'accepted_terms_at', 'is_active',
        ]
        # is_active is read-only here so a user can never reactivate/suspend
        # themselves via their own profile PATCH — only the admin panel's
        # AdminUserUpdateSerializer (a separate serializer) can write it.
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'accepted_terms_at', 'is_active']

    def update(self, instance, validated_data):
        org_name = validated_data.pop('organization_name', None)
        if org_name:
            if instance.organization:
                instance.organization.name = org_name
                instance.organization.save()
            else:
                org = Organization.objects.create(name=org_name)
                instance.organization = org
        return super().update(instance, validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    """Simplified profile serializer."""
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'organization', 'accepted_terms_at',
        ]
        read_only_fields = ['id', 'email', 'role', 'accepted_terms_at']


class OrganizationLLMConfigSerializer(serializers.ModelSerializer):
    """Serializer for organization LLM config."""
    
    class Meta:
        from .models import OrganizationLLMConfig
        model = OrganizationLLMConfig
        fields = ['provider', 'api_key', 'model_name']
        extra_kwargs = {
            'api_key': {'write_only': True}
        }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Indicate if a key is set without revealing it
        ret['has_api_key'] = bool(instance.api_key)
        return ret
