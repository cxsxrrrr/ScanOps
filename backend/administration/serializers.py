"""Serializers for administration app."""
from rest_framework import serializers
from accounts.models import User, Organization, PLAN_LIMITS

class AdminOrgUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating organizations via admin panel."""
    
    class Meta:
        model = Organization
        fields = ['name', 'plan', 'url_limit']
        
    def validate_plan(self, value):
        if value not in PLAN_LIMITS:
            raise serializers.ValidationError(f"Invalid plan. Options: {', '.join(PLAN_LIMITS.keys())}")
        return value

class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users via admin panel."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role', 'organization']
        
    def validate_role(self, value):
        roles = dict(User.ROLE_CHOICES)
        if value not in roles:
            raise serializers.ValidationError(f"Invalid role. Options: {', '.join(roles.keys())}")
        return value
