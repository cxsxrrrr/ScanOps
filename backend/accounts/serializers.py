"""Serializers for accounts app."""
from rest_framework import serializers
from .models import User, Organization


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ['id', 'name', 'plan', 'url_limit', 'user_count', 'created_at']
        read_only_fields = ['id', 'plan', 'url_limit', 'user_count', 'created_at']

    def get_user_count(self, obj):
        return obj.users.count()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    organization = OrganizationSerializer(read_only=True)
    organization_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'organization', 'organization_name', 'date_joined',
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined']

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
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'organization']
        read_only_fields = ['id', 'email', 'role']
