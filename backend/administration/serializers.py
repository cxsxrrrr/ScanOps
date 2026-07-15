"""Serializers for administration app."""
from rest_framework import serializers
from accounts.models import User, Organization, PLAN_LIMITS, PLAN_MEMBER_LIMITS

class AdminOrgUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating organizations via admin panel.

    url_limit is read-only here — it must always match the plan's tier
    (see Organization.set_plan). Letting admins set it independently used
    to desync the two, e.g. a plan='free' org left with url_limit=10 from
    a prior edit. Changing the plan always resets url_limit via set_plan().
    """

    class Meta:
        model = Organization
        fields = ['name', 'plan', 'url_limit']
        read_only_fields = ['url_limit']

    def validate_plan(self, value):
        if value not in PLAN_LIMITS:
            raise serializers.ValidationError(f"Invalid plan. Options: {', '.join(PLAN_LIMITS.keys())}")
        return value

    def update(self, instance, validated_data):
        new_plan = validated_data.pop('plan', None)
        instance = super().update(instance, validated_data)
        if new_plan and new_plan != instance.plan:
            instance.set_plan(new_plan)
        elif new_plan:
            # Plan unchanged but re-assert url_limit in case it had drifted
            # from an earlier direct edit, before this field was locked down.
            instance.sync_url_limit()
        return instance

class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users via admin panel."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role', 'organization', 'is_active']
        
    def validate_role(self, value):
        roles = dict(User.ROLE_CHOICES)
        if value not in roles:
            raise serializers.ValidationError(f"Invalid role. Options: {', '.join(roles.keys())}")
        return value

    def validate_organization(self, value):
        # Moving a user into a different org via the admin panel bypassed the
        # plan's member_limit entirely (no check at all) — enforce it here,
        # same limit the normal invite-accept flow already respects.
        if value is not None and value != self.instance.organization:
            member_limit = PLAN_MEMBER_LIMITS.get(value.plan, 1)
            if value.users.count() >= member_limit:
                raise serializers.ValidationError(
                    f"La organización de destino alcanzó su límite de miembros ({member_limit})."
                )
        return value
